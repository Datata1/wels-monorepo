# Running Ingestion

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| NVIDIA GPU | CUDA 12.1+. Without one, set `--device cpu` — inference is ~10× slower |
| Python 3.12+ | Already required by the monorepo |
| Video file | 720p minimum, 25+ FPS, standard codec (MP4, MKV, AVI, MOV) |

## First-time setup

Install the ingestion package and its dependencies:

```bash
cd packages/ingestion
uv sync
```

YOLO model weights are downloaded automatically on first use and cached in `data/models/`.

## Basic usage

```bash
cd packages/ingestion

uv run wels-ingest <video_path> <match_id>
```

`match_id` is a unique identifier you choose — it's used as the primary key across
all DuckDB tables. A date-based slug works well:

```bash
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz
```

## Common flags

```bash
# Skip pose estimation (faster, uses less VRAM — good for a quick first run)
uv run wels-ingest match.mp4 my_match --no-pose

# Run on CPU (no GPU available)
uv run wels-ingest match.mp4 my_match --device cpu

# Use a court calibration file (enables real-world court coordinates)
uv run wels-ingest match.mp4 my_match --calibration data/court_cal.json

# Write to a different database file
uv run wels-ingest match.mp4 my_match --db /tmp/test.duckdb

# Verbose logging (shows per-frame progress)
uv run wels-ingest match.mp4 my_match --verbose
```

## Court calibration

Without a calibration file, all `court_x` / `court_y` values in DuckDB are `NULL`.
Player and ball positions are still tracked in pixel coordinates, but you lose the
ability to run court-position analytics and ML training.

A calibration file maps four pixel points in the video frame to their known positions
on the standard 40m × 20m handball court:

```json
{
  "src": [[120, 400], [1160, 400], [1160, 680], [120, 680]],
  "dst": [[0, 0], [40, 0], [40, 20], [0, 20]]
}
```

**Creating a calibration file:**

Run the interactive calibration tool from the POC (run once per camera angle):

```bash
cd /path/to/CV-POC-Wels
uv run python calibrate.py --input data/videos/match.mp4
```

Click four court corners in the video frame when prompted. The tool writes a
`court_cal.json` file you can reuse for all matches filmed from the same angle.

!!! tip
    A single calibration file works for an entire season if the camera position
    does not change between matches.

## Environment variables

All settings can be configured via environment variables with the `WELS_` prefix
instead of CLI flags. Useful for setting persistent defaults:

```bash
export WELS_DEVICE=cpu
export WELS_DUCKDB_PATH=/data/wels/matches.duckdb
export WELS_DETECTION_CONFIDENCE=0.35
export WELS_TEAM_WARMUP_FRAMES=200
```

Full list of settings: `packages/ingestion/src/ingestion/config.py`.

## Expected output

```
10:24:01  INFO      Phase 1: team classifier warm-up (150 frames)
10:24:08  INFO      Team classifier fitted
10:24:08  INFO      Phase 2: full pipeline (90000 total frames)
10:24:08  INFO        frame 0 / 90000
10:25:43  INFO        frame 500 / 90000
...
11:18:32  INFO      Phase 3: post-processing (velocities + ball carrier)
11:18:45  INFO      Ingestion complete: 2026-04-13_wels_vs_linz
```

Processing time depends on hardware and whether pose estimation is enabled:

| Setup | Approximate speed |
|-------|-------------------|
| RTX 3060, pose enabled | ~35 FPS (real-time) |
| RTX 3060, no pose | ~60 FPS |
| CPU only | ~2–5 FPS |

## Verifying the result

Open DuckDB and query the result directly:

```bash
cd packages/ingestion
uv run python -c "
import duckdb
db = duckdb.connect('../../data/matches.duckdb', read_only=True)
print(db.execute(\"SELECT match_id, total_frames, fps FROM matches\").df())
print(db.execute(\"SELECT COUNT(*) FROM players WHERE match_id = '2026-04-13_wels_vs_linz'\").fetchone())
"
```
