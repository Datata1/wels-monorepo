# ML — Overview

The ML package predicts **what a player will do next** (pass, shoot, dribble, hold)
from a short sequence of recent frames. It reads from DuckDB and never touches video.

## Three-stage pipeline

```
Stage 1 — Computer Vision (ingestion)
  Video → per-frame positions, teams, ball → DuckDB

Stage 2 — Training (ml: wels-train)
  DuckDB (with action labels) → GCN + LSTM → checkpoint

Stage 3 — Scoring (ml: wels-score)
  DuckDB + checkpoint → action_predictions, formations, possession_phases → DuckDB
```

The stages are independent. You can improve detection without retraining the
prediction model. After training a new checkpoint, re-run `wels-score` to update
the pre-computed predictions in DuckDB.

The backend reads exclusively from the three scoring output tables —
no on-the-fly inference at request time. This makes serving a 60-minute match instant.

## Action classes

| Class | Description |
|-------|-------------|
| `pass` | Player passes the ball to a teammate |
| `shot` | Player attempts a goal throw |
| `dribble` | Player moves with the ball (bouncing) |
| `hold` | Player holds the ball, scanning for options |

Start with these four. The architecture supports adding more classes
(feint, block, intercept, screen) without changes — only annotation is required.

## Why graphs?

A handball scene is naturally a **graph**: players and the ball are nodes,
connected by spatial and tactical relationships (edges). A flat feature vector
— just concatenating all positions — loses the relational information that
determines what action a player will take.

```
Team A nodes ─── teammate edges ─── Team A nodes
     │                                    │
  opponent edges                    opponent edges
     │                                    │
Team B nodes ─── teammate edges ─── Team B nodes
     │
  ball edge
     │
   Ball node
```

## Node features (10 per player)

| Feature | Source | Dim |
|---------|--------|-----|
| Court position (x, y) | `court_x`, `court_y` from DuckDB | 2 |
| Velocity (vx, vy) | Post-processed by ingestion | 2 |
| Distance to ball | Euclidean to ball `court_pos` | 1 |
| Distance to goal | Euclidean to `(40, 10)` | 1 |
| Has ball | Is this the ball carrier? | 1 |
| Team encoding | One-hot: A / B / unknown | 3 |

## Edge features (4 per edge)

| Feature | Description |
|---------|-------------|
| Distance | Euclidean court distance between two players |
| Relative position (dx, dy) | Vector from node i to node j |
| Same team | Binary: are they on the same team? |

Edges are built using **k-NN by court distance** (default k=5). This keeps the
graph sparse and avoids connecting players on opposite sides of the court.

## Model architecture

Each frame becomes a graph. The model processes a **sequence of 25 graphs**
(1 second at 25 FPS) and predicts the action at the end of that window.

```
Per frame (× 25):
  node features (10-d)
      │
  GCNConv(10 → 64) → ReLU
      │
  GCNConv(64 → 128) → ReLU
      │
  global mean pool
      │
  128-d frame embedding

Across 25 frames:
  [emb_t-24, ..., emb_t]  →  LSTM(hidden=128)  →  last hidden state
      │
  Linear(128 → 4)  →  softmax  →  action probabilities
```

::: ml.models.action.ActionPredictor
    options:
      show_source: false

## Batch scoring outputs

`wels-score` writes three tables to DuckDB. The backend reads from these directly.

### `action_predictions`

Per-frame action probabilities for the ball carrier. Only frames where a ball carrier
exists and a full history window is available are included.

| Column | Description |
|--------|-------------|
| `match_id`, `frame_id`, `track_id` | PK — identifies ball carrier at this frame |
| `pass_prob`, `shot_prob`, `dribble_prob`, `hold_prob` | Softmax probabilities |
| `predicted_action` | Argmax of the four probabilities |

### `formations`

Rule-based formation label for each team, sampled every 5 frames.

| Label | Description |
|-------|-------------|
| `6-0` | Compact defensive line — low y-spread, shallow depth gap |
| `5-1` | One player significantly pressed forward |
| `4-2` | Two distinct depth layers |
| `attack` | Team primarily in opponent's half |
| `transition` | Players spread across the full court |
| `unknown` | Fewer than 4 court-mapped players |

### `possession_phases`

Continuous possession sequences derived from the per-frame ball carrier.
Short interruptions (dropped detections, ball out of frame) are smoothed out.

| Column | Description |
|--------|-------------|
| `phase_id` | Sequential ID within the match |
| `team` | `"A"` or `"B"` |
| `start_frame` / `end_frame` | Frame range |
| `start_time_s` / `end_time_s` | Timestamps in seconds |
| `duration_s` | Generated column: `end_time_s - start_time_s` |

## Scoring CLI

```bash
cd packages/ml

# Auto-discover checkpoint in data/models/
uv run wels-score 2026-04-13_wels_vs_linz

# Explicit checkpoint path
uv run wels-score 2026-04-13_wels_vs_linz \
    --checkpoint data/models/action_predictor_best.pt

# CPU-only machine, custom DB path
uv run wels-score 2026-04-13_wels_vs_linz \
    --device cpu --db /data/matches.duckdb

# Verbose logging
uv run wels-score 2026-04-13_wels_vs_linz --verbose
```

Formations and possession phases are written even if no checkpoint is available —
only `action_predictions` requires a trained model.

Re-running `wels-score` on the same match is safe: existing results are cleared before
the new ones are written.

## Direct inference (for scripts and notebooks)

`ActionInference` is available for ad-hoc use outside of the scoring pipeline:

```python
from ml.inference import ActionInference
from ml.config import MLSettings

settings = MLSettings()
predictor = ActionInference(settings.models_dir / "action_predictor_best.pt", settings)
probs = predictor.predict(
    match_id="2026-04-13_wels_vs_linz",
    center_frame=15000,
    actor_track_id=7,
)
# {"pass": 0.62, "shot": 0.25, "dribble": 0.08, "hold": 0.05}
```
