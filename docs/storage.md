# Data Storage

All match data is stored in a single [DuckDB](https://duckdb.org/) file at
`data/matches.duckdb`. DuckDB is a serverless analytical database — no process
to start, no configuration, just a file.

## Why DuckDB

| | JSONL (old) | DuckDB (current) |
|---|---|---|
| Cross-match queries | Load every file into memory | Single SQL query |
| Frame window lookups | Full file scan | Indexed, instant |
| Schema enforcement | Silent — missing fields ignored | Types enforced at insert |
| Aggregations (avg speed, possession %) | Python loops | Native SQL window functions |
| Storage (10 matches) | ~2 GB | ~500–800 MB (columnar compression) |

## Schema

```
matches ──< frames ──< players
                  ──< ball
                  ──< action_labels

Scoring outputs (written by wels-score):
matches ──< action_predictions
        ──< formations
        ──< possession_phases
```

### `matches`

One row per ingested video.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | TEXT PK | Unique slug, e.g. `2026-04-13_wels_vs_linz` |
| `video_path` | TEXT | Absolute path to the source video |
| `fps` | DOUBLE | Frames per second of the source video |
| `total_frames` | INTEGER | Total frame count |
| `team_a_name` | TEXT | Human-readable team name (set manually or via API) |
| `team_b_name` | TEXT | Human-readable team name |
| `ingested_at` | TIMESTAMP | When ingestion completed |

### `frames`

One row per video frame.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | TEXT FK | References `matches.match_id` |
| `frame_id` | INTEGER | Zero-based frame index |
| `timestamp_s` | DOUBLE | `frame_id / fps` — seconds into the match |
| `player_count` | INTEGER | Total detected players in this frame |
| `on_court_count` | INTEGER | Players whose `on_court = TRUE` |

### `players`

One row per player per frame. At 25 FPS, 60 min, 14 players: ~1.26 million rows per match.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` + `frame_id` + `track_id` | PK | Composite primary key |
| `team` | TEXT | `"A"`, `"B"`, or `"unknown"` |
| `court_x` / `court_y` | DOUBLE | Position in metres on the 40×20m court. `NULL` if no calibration or out-of-bounds |
| `pixel_foot_x` / `pixel_foot_y` | DOUBLE | Bottom-center of bounding box in pixels |
| `velocity_x` / `velocity_y` | DOUBLE | m/s, computed from position delta (0 until post-processing) |
| `confidence` | DOUBLE | YOLO detection confidence |
| `on_court` | BOOLEAN | Whether the player is considered on the playing area |
| `has_ball` | BOOLEAN | Nearest player to the ball in this frame |
| `bbox_x1/y1/x2/y2` | INTEGER | Pixel bounding box |

### `ball`

One row per frame where the ball was detected (frames with no ball detection have no row).

| Column | Type | Description |
|--------|------|-------------|
| `match_id` + `frame_id` | PK | |
| `court_x` / `court_y` | DOUBLE | Ball court position in metres (`NULL` without calibration) |
| `pixel_x` / `pixel_y` | DOUBLE | Ball center in pixels |
| `confidence` | DOUBLE | Detection confidence |
| `bbox_x1/y1/x2/y2` | INTEGER | Pixel bounding box |

### `action_labels`

Manual annotations added for ML training. Not populated by ingestion — added
separately via the annotation workflow.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` + `frame_id` + `track_id` | PK | Which player, which frame |
| `action` | TEXT | `"pass"`, `"shot"`, `"dribble"`, `"hold"`, ... |
| `annotator` | TEXT | Who labeled it (default: `"manual"`) |

### `action_predictions`

Pre-computed per-frame action probabilities for the ball carrier.
Written by `wels-score`. Only frames where a full history window exists are included.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` + `frame_id` + `track_id` | PK | Ball carrier at this frame |
| `pass_prob` / `shot_prob` / `dribble_prob` / `hold_prob` | DOUBLE | Softmax output |
| `predicted_action` | TEXT | Argmax: `"pass"`, `"shot"`, `"dribble"`, or `"hold"` |

### `formations`

Rule-based formation label per team, sampled every 5 frames.
Written by `wels-score` regardless of whether a checkpoint exists.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` + `frame_id` + `team` | PK | |
| `formation` | TEXT | `"6-0"`, `"5-1"`, `"4-2"`, `"attack"`, `"transition"`, or `"unknown"` |

### `possession_phases`

Continuous possession sequences. Short interruptions (dropped detection,
ball out of frame) are smoothed over. Written by `wels-score`.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` + `phase_id` | PK | Sequential ID per match |
| `team` | TEXT | `"A"` or `"B"` |
| `start_frame` / `end_frame` | INTEGER | Frame range |
| `start_time_s` / `end_time_s` | DOUBLE | Timestamps in seconds |
| `duration_s` | DOUBLE (virtual) | `end_time_s - start_time_s` |

## Common queries

Open a DuckDB shell:

```bash
cd packages/ingestion && uv run python -c "import duckdb; duckdb.connect('../../data/matches.duckdb').execute('.mode table').execute('.tables')"
```

Or use the Python API directly:

```python
import duckdb
db = duckdb.connect("data/matches.duckdb", read_only=True)
```

### List all ingested matches

```sql
SELECT match_id, total_frames, fps, ingested_at FROM matches ORDER BY ingested_at DESC;
```

### Ball possession by team

```sql
SELECT
    p.team,
    COUNT(*) AS frames_with_ball,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS possession_pct
FROM players p
WHERE p.has_ball = TRUE
  AND p.match_id = '2026-04-13_wels_vs_linz'
  AND p.team IN ('A', 'B')
GROUP BY p.team;
```

### Player heatmap data (position density)

```sql
SELECT
    ROUND(court_x) AS zone_x,
    ROUND(court_y) AS zone_y,
    COUNT(*) AS frames
FROM players
WHERE match_id = '2026-04-13_wels_vs_linz'
  AND track_id = 7
  AND on_court = TRUE
GROUP BY zone_x, zone_y
ORDER BY frames DESC;
```

### Team speed comparison

```sql
SELECT
    team,
    ROUND(AVG(SQRT(velocity_x^2 + velocity_y^2)), 2) AS avg_speed_ms,
    ROUND(MAX(SQRT(velocity_x^2 + velocity_y^2)), 2) AS max_speed_ms
FROM players
WHERE match_id = '2026-04-13_wels_vs_linz'
  AND on_court = TRUE
  AND team IN ('A', 'B')
GROUP BY team;
```

### Load a frame window (for ML)

```sql
SELECT frame_id, track_id, team, court_x, court_y, velocity_x, velocity_y, has_ball
FROM players
WHERE match_id = '2026-04-13_wels_vs_linz'
  AND frame_id BETWEEN 1000 AND 1024
  AND court_x IS NOT NULL
ORDER BY frame_id, track_id;
```

### Formation timeline for a match

```sql
SELECT frame_id, team, formation
FROM formations
WHERE match_id = '2026-04-13_wels_vs_linz'
ORDER BY frame_id, team;
```

### Possession phases sorted by duration

```sql
SELECT phase_id, team, start_time_s, end_time_s, duration_s
FROM possession_phases
WHERE match_id = '2026-04-13_wels_vs_linz'
ORDER BY duration_s DESC;
```

### Action prediction distribution

```sql
SELECT predicted_action, COUNT(*) AS frames, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM action_predictions
WHERE match_id = '2026-04-13_wels_vs_linz'
GROUP BY predicted_action
ORDER BY frames DESC;
```

## Backup and export

```python
db = duckdb.connect("data/matches.duckdb")

# Export one table to Parquet (portable, compact)
db.execute("COPY players TO 'export/players.parquet' (FORMAT PARQUET)")

# Full database backup
db.execute("EXPORT DATABASE 'backup/' (FORMAT PARQUET)")
```
