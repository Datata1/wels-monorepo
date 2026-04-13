"""
ML output tables in DuckDB.

These tables are written by wels-score (batch scoring job) and read by the backend.
The core ingestion tables (matches, frames, players, ball, action_labels) are defined
and created by packages/ingestion/src/ingestion/storage/schema.py.

Call connect() to get a writable connection with the ML tables already applied.
"""

from pathlib import Path

import duckdb

_ML_SCHEMA_SQL = """
-- Pre-computed action probabilities for the ball carrier at each frame.
-- Populated by wels-score. Only rows where a ball carrier could be identified
-- and a full window of history existed are included.
CREATE TABLE IF NOT EXISTS action_predictions (
    match_id         TEXT    NOT NULL,
    frame_id         INTEGER NOT NULL,
    track_id         INTEGER NOT NULL,  -- ball carrier at this frame
    pass_prob        DOUBLE  NOT NULL,
    shot_prob        DOUBLE  NOT NULL,
    dribble_prob     DOUBLE  NOT NULL,
    hold_prob        DOUBLE  NOT NULL,
    predicted_action TEXT    NOT NULL,  -- argmax of the four probabilities
    PRIMARY KEY (match_id, frame_id, track_id)
);

-- Rule-based formation label per team per frame.
-- Populated by wels-score regardless of whether a ML checkpoint exists.
CREATE TABLE IF NOT EXISTS formations (
    match_id  TEXT    NOT NULL,
    frame_id  INTEGER NOT NULL,
    team      TEXT    NOT NULL,   -- 'A' | 'B'
    formation TEXT    NOT NULL,   -- see analysis/formation.py for labels
    PRIMARY KEY (match_id, frame_id, team)
);

-- Continuous possession phases: one row per uninterrupted possession sequence.
-- Derived from the per-frame has_ball column; short interruptions are smoothed out.
CREATE TABLE IF NOT EXISTS possession_phases (
    match_id      TEXT    NOT NULL,
    phase_id      INTEGER NOT NULL,
    team          TEXT    NOT NULL,
    start_frame   INTEGER NOT NULL,
    end_frame     INTEGER NOT NULL,
    start_time_s  DOUBLE  NOT NULL,
    end_time_s    DOUBLE  NOT NULL,
    duration_s    DOUBLE  NOT NULL GENERATED ALWAYS AS (end_time_s - start_time_s) VIRTUAL,
    PRIMARY KEY (match_id, phase_id)
);

CREATE INDEX IF NOT EXISTS idx_action_pred_match_frame
    ON action_predictions (match_id, frame_id);

CREATE INDEX IF NOT EXISTS idx_formations_match_frame
    ON formations (match_id, frame_id);

CREATE INDEX IF NOT EXISTS idx_possession_match
    ON possession_phases (match_id, start_frame);
"""


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    """
    Open the DuckDB database for reading and writing ML output tables.
    Creates ML tables if they don't exist yet (idempotent).
    The file must already exist — run wels-ingest first.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}\nRun wels-ingest on a match video first."
        )
    conn = duckdb.connect(str(db_path))
    conn.execute(_ML_SCHEMA_SQL)
    return conn
