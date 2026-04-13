# ML — Overview

The ML package predicts **what a player will do next** (pass, shoot, dribble, hold)
from a short sequence of recent frames. It reads from DuckDB and never touches video.

## Two-stage architecture

```
Stage 1 — Computer Vision (ingestion package)
  Video → per-frame positions, teams, ball → DuckDB

Stage 2 — Action Prediction (ml package)
  DuckDB → graphs → GCN + LSTM → action probabilities
```

The stages are independent. You can improve detection without retraining the
prediction model, and vice versa.

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

## Inference

Once a checkpoint exists at `data/models/action_best.pt`, the backend can call:

```python
from ml.inference import ActionInference

predictor = ActionInference(Path("data/models/action_best.pt"))
probs = predictor.predict(
    match_id="2026-04-13_wels_vs_linz",
    center_frame=15000,
    actor_track_id=7,
)
# {"pass": 0.62, "shot": 0.25, "dribble": 0.08, "hold": 0.05}
```
