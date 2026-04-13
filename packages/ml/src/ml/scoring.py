"""
Batch scoring job: reads ingested match data, writes pre-computed predictions.

Run this after wels-ingest and (optionally) wels-train:

    wels-score <match_id>

Three outputs are written to DuckDB:

  action_predictions  — per-frame action probabilities for the ball carrier
                        (requires a trained checkpoint; skipped if none exists)

  formations          — per-frame formation label for each team
                        (rule-based, no checkpoint needed)

  possession_phases   — smoothed possession phases with start/end timestamps
                        (derived from has_ball column, no checkpoint needed)

The backend reads from these tables. No on-the-fly inference at request time.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from ml.analysis import formation as formation_classifier
from ml.analysis.possession import PossessionPhase, detect_phases
from ml.config import MLSettings
from ml.storage.schema import connect

logger = logging.getLogger(__name__)

# Score every Nth frame for formations (formations change slowly — no need per-frame)
_FORMATION_STRIDE = 5


class MatchScorer:
    """
    Scores one match end-to-end and writes results to DuckDB.

    Usage:
        scorer = MatchScorer(settings, checkpoint_path)
        scorer.score(match_id)
    """

    def __init__(
        self,
        settings: MLSettings,
        checkpoint_path: Path | None = None,
    ) -> None:
        self._settings = settings
        self._checkpoint = checkpoint_path

        # Action predictor is optional — scoring still runs without a checkpoint
        self._predictor = None
        if checkpoint_path is not None and checkpoint_path.exists():
            from ml.inference import ActionInference

            self._predictor = ActionInference(checkpoint_path, settings)
            logger.info("Loaded action predictor from %s", checkpoint_path)
        else:
            logger.warning(
                "No checkpoint found at %s — action_predictions will be skipped",
                checkpoint_path,
            )

    def score(self, match_id: str) -> None:
        """Score one match and write all output tables."""
        conn = connect(self._settings.duckdb_path)

        # Guard: ensure the match was ingested
        row = conn.execute("SELECT fps FROM matches WHERE match_id = ?", [match_id]).fetchone()
        if row is None:
            raise ValueError(f"Match '{match_id}' not found in database. Run wels-ingest first.")
        fps = float(row[0])

        # Clear any existing scoring results for this match (allow re-scoring)
        _clear_match(conn, match_id)

        logger.info("Scoring match: %s", match_id)

        if self._predictor is not None:
            logger.info("Step 1/3: action predictions")
            _score_actions(conn, match_id, self._predictor, self._settings)
        else:
            logger.info("Step 1/3: action predictions — skipped (no checkpoint)")

        logger.info("Step 2/3: formation classification")
        _classify_formations(conn, match_id)

        logger.info("Step 3/3: possession phases")
        _detect_possession(conn, match_id, fps, self._settings)

        conn.commit()
        conn.close()
        logger.info("Scoring complete: %s", match_id)


# ---------------------------------------------------------------------------
# Step 1 — Action predictions
# ---------------------------------------------------------------------------


def _score_actions(
    conn: duckdb.DuckDBPyConnection,
    match_id: str,
    predictor: object,
    settings: MLSettings,
) -> None:
    """Write action_predictions rows for every ball-carrier frame."""
    from ml.inference import ActionInference

    assert isinstance(predictor, ActionInference)

    # Find all frames where a ball carrier exists and enough history is available
    carriers = conn.execute(
        """
        SELECT frame_id, track_id
        FROM players
        WHERE match_id = ?
          AND has_ball = TRUE
          AND frame_id >= ?
          AND court_x IS NOT NULL
        ORDER BY frame_id
        """,
        [match_id, settings.window_size - 1],
    ).fetchall()

    logger.info("  %d ball-carrier frames to score", len(carriers))

    batch: list[tuple] = []
    for frame_id, track_id in carriers:
        try:
            probs = predictor.predict(match_id, int(frame_id), int(track_id))
        except ValueError:
            continue  # not enough history for this frame

        predicted = max(probs, key=lambda k: probs[k])
        batch.append(
            (
                match_id,
                int(frame_id),
                int(track_id),
                probs["pass"],
                probs["shot"],
                probs["dribble"],
                probs["hold"],
                predicted,
            )
        )

        if len(batch) >= 500:
            _insert_predictions(conn, batch)
            batch = []

    if batch:
        _insert_predictions(conn, batch)


def _insert_predictions(
    conn: duckdb.DuckDBPyConnection,
    batch: list[tuple],  # type: ignore[type-arg]
) -> None:
    conn.executemany(
        "INSERT INTO action_predictions VALUES (?,?,?,?,?,?,?,?)",
        batch,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Step 2 — Formation classification
# ---------------------------------------------------------------------------


def _classify_formations(
    conn: duckdb.DuckDBPyConnection,
    match_id: str,
) -> None:
    """Write formations rows for both teams at every _FORMATION_STRIDE frames."""
    # Determine which side each team defends by their average position
    side_row = conn.execute(
        """
        SELECT team, AVG(court_x) AS avg_x
        FROM players
        WHERE match_id = ? AND team IN ('A', 'B') AND court_x IS NOT NULL
        GROUP BY team
        """,
        [match_id],
    ).fetchall()

    # Team with lower avg_x defends the left goal (x=0)
    defending_left: dict[str, bool] = {}
    if len(side_row) == 2:
        teams_by_x = sorted(side_row, key=lambda r: r[1])
        defending_left[teams_by_x[0][0]] = True
        defending_left[teams_by_x[1][0]] = False
    else:
        # Fallback: can't determine sides
        for team, _ in side_row:
            defending_left[team] = True

    frame_ids = conn.execute(
        """
        SELECT DISTINCT frame_id
        FROM players
        WHERE match_id = ? AND court_x IS NOT NULL
        ORDER BY frame_id
        """,
        [match_id],
    ).fetchall()

    batch: list[tuple] = []
    for (frame_id,) in frame_ids:
        if int(frame_id) % _FORMATION_STRIDE != 0:
            continue

        for team in ("A", "B"):
            positions = conn.execute(
                """
                SELECT court_x, court_y FROM players
                WHERE match_id = ? AND frame_id = ? AND team = ?
                  AND on_court = TRUE AND court_x IS NOT NULL
                """,
                [match_id, frame_id, team],
            ).fetchall()

            label = formation_classifier.classify(
                [(float(x), float(y)) for x, y in positions],
                defending_left=defending_left.get(team, True),
            )
            batch.append((match_id, int(frame_id), team, label))

        if len(batch) >= 1000:
            conn.executemany("INSERT INTO formations VALUES (?,?,?,?)", batch)
            conn.commit()
            batch = []

    if batch:
        conn.executemany("INSERT INTO formations VALUES (?,?,?,?)", batch)
        conn.commit()


# ---------------------------------------------------------------------------
# Step 3 — Possession phases
# ---------------------------------------------------------------------------


def _detect_possession(
    conn: duckdb.DuckDBPyConnection,
    match_id: str,
    fps: float,
    settings: MLSettings,
) -> None:
    """Write possession_phases from per-frame ball-carrier data."""
    rows = conn.execute(
        """
        SELECT f.frame_id, f.timestamp_s, p.team
        FROM frames f
        LEFT JOIN (
            SELECT frame_id, team
            FROM players
            WHERE match_id = ? AND has_ball = TRUE
        ) p ON f.frame_id = p.frame_id
        WHERE f.match_id = ?
        ORDER BY f.frame_id
        """,
        [match_id, match_id],
    ).fetchall()

    frame_dicts = [{"frame_id": r[0], "timestamp_s": r[1], "team": r[2]} for r in rows]

    phases: list[PossessionPhase] = detect_phases(frame_dicts, fps=fps)

    if phases:
        conn.executemany(
            """
            INSERT INTO possession_phases
                (match_id, phase_id, team, start_frame, end_frame, start_time_s, end_time_s)
            VALUES (?,?,?,?,?,?,?)
            """,
            [
                (
                    match_id,
                    p.phase_id,
                    p.team,
                    p.start_frame,
                    p.end_frame,
                    p.start_time_s,
                    p.end_time_s,
                )
                for p in phases
            ],
        )
        conn.commit()

    logger.info("  %d possession phases written", len(phases))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_match(conn: duckdb.DuckDBPyConnection, match_id: str) -> None:
    """Remove any existing scoring results for this match so re-scoring is safe."""
    for table in ("action_predictions", "formations", "possession_phases"):
        conn.execute(f"DELETE FROM {table} WHERE match_id = ?", [match_id])
    conn.commit()
