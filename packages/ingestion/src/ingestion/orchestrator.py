"""
Ingestion orchestrator — wires the pipeline stages together.

Flow per video:
  1. Open video, register match in DuckDB
  2. Warm-up phase: collect player detections for team classifier fitting
     (team labels are "unknown" during this phase)
  3. Fit team classifier on the accumulated samples
  4. Main phase: run full pipeline frame-by-frame and write to DuckDB
  5. Post-processing: compute velocities and ball-carrier flags via SQL

The orchestrator is the only place that knows about all pipeline stages.
Individual stages (detection, ball, team, court) have no knowledge of each other.

Each stage declares AVAILABLE at module level; the orchestrator checks this flag
before attempting construction. Stages that raise NotImplementedError (not yet
ported) are silently skipped — the pipeline degrades gracefully rather than crash.
"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

from ingestion.config import IngestionSettings
from ingestion.pipeline import ball as _ball_mod
from ingestion.pipeline import court as _court_mod
from ingestion.pipeline import detection as _det_mod
from ingestion.pipeline import team as _team_mod
from ingestion.pipeline.ball import BallDetector
from ingestion.pipeline.court import CourtMapper
from ingestion.pipeline.detection import PersonDetector
from ingestion.pipeline.team import TeamClassifier
from ingestion.storage.schema import connect
from ingestion.storage.writer import FrameWriter
from ingestion.types import BallState, Detection, FrameState, PlayerState
from ingestion.video import iter_frames
from ingestion.visualization.annotator import FrameAnnotator

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    def __init__(self, settings: IngestionSettings) -> None:
        self._settings = settings

        self._person_detector: PersonDetector | None = None
        if _det_mod.AVAILABLE:
            try:
                _det_path = settings.models_dir / settings.detection_model
                _det_path.parent.mkdir(parents=True, exist_ok=True)
                self._person_detector = PersonDetector(
                    model_path=str(_det_path),
                    confidence=settings.detection_confidence,
                    max_persons=settings.max_persons,
                    device=settings.device,
                    imgsz=settings.detection_imgsz,
                    half=settings.half,
                )
            except NotImplementedError:
                logger.warning("PersonDetector: not yet ported — person detection skipped")
        else:
            logger.info("PersonDetector: ultralytics not installed — person detection skipped")

        self._ball_detector: BallDetector | None = None
        if _ball_mod.AVAILABLE:
            try:
                _ball_path = settings.models_dir / settings.ball_model
                _ball_path.parent.mkdir(parents=True, exist_ok=True)
                self._ball_detector = BallDetector(
                    model_path=str(_ball_path),
                    confidence=settings.ball_confidence,
                    device=settings.device,
                )
            except NotImplementedError:
                logger.warning("BallDetector: not yet ported — ball detection skipped")
        else:
            logger.info("BallDetector: ultralytics not installed — ball detection skipped")

        self._team: TeamClassifier | None = None
        if _team_mod.AVAILABLE:
            try:
                self._team = TeamClassifier(n_teams=settings.n_teams)
            except NotImplementedError:
                logger.warning("TeamClassifier: not yet ported — team stage skipped")

        self._court: CourtMapper | None = None
        if settings.calibration_path is not None and _court_mod.AVAILABLE:
            try:
                self._court = CourtMapper.from_file(settings.calibration_path)
            except NotImplementedError:
                logger.warning("CourtMapper: not yet ported — court stage skipped")

    def run(
        self,
        video_path: Path,
        match_id: str,
        output_video_path: Path | None = None,
    ) -> None:
        """
        Process one video file end-to-end and write all results to DuckDB.

        Args:
            output_video_path: If provided, write an annotated copy of the video here.

        Raises ValueError if match_id already exists in the database.
        """
        settings = self._settings
        conn = connect(settings.duckdb_path)

        existing = conn.execute("SELECT 1 FROM matches WHERE match_id = ?", [match_id]).fetchone()
        if existing:
            raise ValueError(f"match_id '{match_id}' already exists in the database")

        warmup_limit = settings.team_warmup_frames

        if self._person_detector is not None and self._team is not None:
            logger.info("Phase 1: team classifier warm-up (%d frames)", warmup_limit)
            try:
                for vf in iter_frames(video_path):
                    if vf.frame_id >= warmup_limit:
                        break
                    players_raw = self._person_detector.detect(vf.frame)
                    for det in players_raw:
                        self._team.collect(vf.frame, det.bbox)
                self._team.fit()
                logger.info("Team classifier fitted")
            except NotImplementedError:
                logger.warning("Team warmup skipped: stage not yet ported")
        else:
            logger.info("Phase 1: skipped (person detector or team classifier unavailable)")

        meta = next(iter_frames(video_path))
        conn.execute(
            "INSERT INTO matches (match_id, video_path, fps, total_frames) VALUES (?,?,?,?)",
            [match_id, str(video_path), meta.fps, meta.total_frames],
        )
        conn.commit()

        annotator = FrameAnnotator() if output_video_path is not None else None
        video_writer = (
            _open_video_writer(output_video_path, meta.fps, meta.frame)
            if output_video_path is not None
            else None
        )

        logger.info("Phase 2: full pipeline (%d total frames)", meta.total_frames)
        with FrameWriter(conn, match_id) as writer:
            for vf in iter_frames(video_path):
                frame_state = self._process_frame(vf.frame, vf.frame_id, vf.timestamp_s)
                writer.write(frame_state)
                if video_writer is not None and annotator is not None:
                    video_writer.write(annotator.annotate(vf.frame, frame_state))

                if vf.frame_id % 500 == 0:
                    logger.info("  frame %d / %d", vf.frame_id, vf.total_frames)

        if video_writer is not None:
            video_writer.release()

        logger.info("Phase 3: post-processing (velocities + ball carrier)")
        _compute_velocities(conn, match_id, meta.fps)
        _mark_ball_carrier(conn, match_id)
        conn.commit()

        logger.info("Ingestion complete: %s", match_id)

    def _process_frame(self, frame: object, frame_id: int, timestamp_s: float) -> FrameState:
        assert isinstance(frame, np.ndarray)

        players_raw: list[Detection] = []
        if self._person_detector is not None:
            try:
                players_raw = self._person_detector.detect(frame)
            except NotImplementedError:
                pass

        ball_raw: Detection | None = None
        if self._ball_detector is not None:
            try:
                ball_raw = self._ball_detector.detect(frame)
            except NotImplementedError:
                pass

        players: list[PlayerState] = []
        for det in players_raw:
            team = "unknown"
            if self._team is not None:
                try:
                    team = self._team.classify(frame, det.bbox)
                except NotImplementedError:
                    pass

            court_pos: tuple[float, float] | None = None
            if self._court is not None:
                try:
                    court_pos = self._court.transform(det.bbox.foot)
                except NotImplementedError:
                    pass

            players.append(
                PlayerState(
                    track_id=det.track_id,
                    bbox=det.bbox,
                    confidence=det.confidence,
                    team=team,
                    court_pos=court_pos,
                )
            )

        ball: BallState | None = None
        if ball_raw is not None:
            ball_court_pos: tuple[float, float] | None = None
            if self._court is not None:
                try:
                    ball_court_pos = self._court.transform(ball_raw.bbox.center)
                except NotImplementedError:
                    pass
            ball = BallState(
                bbox=ball_raw.bbox,
                confidence=ball_raw.confidence,
                court_pos=ball_court_pos,
            )

        return FrameState(
            frame_id=frame_id,
            timestamp_s=timestamp_s,
            players=players,
            ball=ball,
        )


def _open_video_writer(
    path: Path,
    fps: float,
    reference_frame: np.ndarray,  # type: ignore[type-arg]
) -> cv2.VideoWriter:
    h, w = reference_frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
    return cv2.VideoWriter(str(path), fourcc, fps, (w, h))


# ---------------------------------------------------------------------------
# Post-processing SQL — runs after all frames are written
# ---------------------------------------------------------------------------


def _compute_velocities(conn: object, match_id: str, fps: float) -> None:
    """
    Fill velocity_x / velocity_y from position deltas using SQL window functions.
    Requires court_x/court_y to be non-NULL (i.e. calibration was provided).
    """
    import duckdb as _duckdb

    assert isinstance(conn, _duckdb.DuckDBPyConnection)

    conn.execute(
        """
        UPDATE players AS p
        SET velocity_x = sub.vx,
            velocity_y = sub.vy
        FROM (
            SELECT
                match_id,
                frame_id,
                track_id,
                (court_x - LAG(court_x) OVER w)
                    / NULLIF(frame_id - LAG(frame_id) OVER w, 0) * ? AS vx,
                (court_y - LAG(court_y) OVER w)
                    / NULLIF(frame_id - LAG(frame_id) OVER w, 0) * ? AS vy
            FROM players
            WHERE match_id = ?
            WINDOW w AS (PARTITION BY match_id, track_id ORDER BY frame_id)
        ) sub
        WHERE p.match_id = sub.match_id
          AND p.frame_id = sub.frame_id
          AND p.track_id = sub.track_id
        """,
        [fps, fps, match_id],
    )


def _mark_ball_carrier(conn: object, match_id: str) -> None:
    """Mark the player closest to the ball in each frame as has_ball=TRUE."""
    import duckdb as _duckdb

    assert isinstance(conn, _duckdb.DuckDBPyConnection)

    conn.execute(
        """
        UPDATE players AS p
        SET has_ball = TRUE
        FROM (
            SELECT pl.match_id, pl.frame_id, pl.track_id
            FROM players pl
            JOIN ball b ON pl.match_id = b.match_id AND pl.frame_id = b.frame_id
            WHERE pl.match_id = ?
              AND pl.court_x IS NOT NULL
              AND b.court_x  IS NOT NULL
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY pl.match_id, pl.frame_id
                ORDER BY (pl.court_x - b.court_x)^2 + (pl.court_y - b.court_y)^2
            ) = 1
        ) sub
        WHERE p.match_id = sub.match_id
          AND p.frame_id = sub.frame_id
          AND p.track_id = sub.track_id
        """,
        [match_id],
    )
