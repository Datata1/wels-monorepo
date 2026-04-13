# ML — Training

Training requires two things: ingested match data in DuckDB and action labels.
The ingestion pipeline provides the data; labels must be added manually.

## How many labels do you need?

| Labels | Expected result |
|--------|-----------------|
| 200 | Proof of concept — likely overfits |
| 500 | Reasonable baseline for 4 action classes |
| 1 000+ | Solid model |
| 3 000+ | Strong model with rare classes (feint, block, ...) |

One full 60-minute match contains thousands of action moments.
**Labeling 2–3 matches is enough to start.**

## Step 1 — Ingest your matches

Run ingestion for each match you want to use for training.
Court calibration is required — training needs `court_x` / `court_y` values.

```bash
cd packages/ingestion
uv run wels-ingest data/videos/match1.mp4 match_1 --calibration data/court_cal.json
uv run wels-ingest data/videos/match2.mp4 match_2 --calibration data/court_cal.json
```

## Step 2 — Add action labels

Labels are rows in the `action_labels` table. Add them using a video annotation
tool or a simple Python script.

### Option A — Video annotation tool

Use [CVAT](https://app.cvat.ai) or [Label Studio](https://labelstud.io):

1. Create a video annotation task with temporal segments
2. For each ball carrier, mark the **start and end frame** and assign an action class
3. Note the `track_id` from the DuckDB `players` table
4. Export as JSON/CSV and import:

```python
import duckdb

db = duckdb.connect("data/matches.duckdb")
db.execute("""
    INSERT INTO action_labels (match_id, frame_id, track_id, action)
    VALUES (?, ?, ?, ?)
""", ["match_1", 15000, 7, "shot"])
db.commit()
```

### Option B — Direct DuckDB insert

For a quick start, look up frames visually using the court position data
and insert labels manually:

```python
import duckdb

db = duckdb.connect("data/matches.duckdb")

# Find frames where a specific player has the ball
df = db.execute("""
    SELECT p.frame_id, p.track_id, p.court_x, p.court_y,
           b.court_x AS ball_x, b.court_y AS ball_y
    FROM players p
    JOIN ball b USING (match_id, frame_id)
    WHERE p.match_id = 'match_1'
      AND p.has_ball = TRUE
      AND p.team = 'A'
    ORDER BY p.frame_id
    LIMIT 20
""").df()
print(df)

# Insert a label
db.execute("""
    INSERT INTO action_labels (match_id, frame_id, track_id, action)
    VALUES ('match_1', 15000, 7, 'shot')
""")
db.commit()
```

## Step 3 — Train

```bash
cd packages/ml
uv sync
uv run wels-train
```

The trainer reads all labeled windows from DuckDB, splits into train/val (80/20),
and trains for 50 epochs by default. The best checkpoint is saved to
`data/models/action_best.pt`.

Common overrides:

```bash
uv run wels-train --epochs 100
uv run wels-train --device cpu
uv run wels-train --db /path/to/matches.duckdb
uv run wels-train --verbose
```

Training output:

```
10:00:01  INFO  Training on cuda
10:00:03  INFO  Dataset: 847 samples, 4 classes
10:00:05  INFO  Epoch 1/50  loss=1.3842  val_acc=0.312
10:00:07  INFO    Saved checkpoint (val_acc=0.312)
10:00:09  INFO  Epoch 2/50  loss=1.1203  val_acc=0.401
10:00:11  INFO    Saved checkpoint (val_acc=0.401)
...
10:08:44  INFO  Training complete. Best val_acc=0.783. Checkpoint: data/models/action_best.pt
```

## Step 4 — Score matches

After training, run `wels-score` for each match you want the backend to serve.
This pre-computes action predictions, formations, and possession phases into DuckDB.

```bash
cd packages/ml

# Score a single match (auto-discovers data/models/action_predictor_best.pt)
uv run wels-score match_1

# Or point explicitly at the checkpoint
uv run wels-score match_1 --checkpoint data/models/action_predictor_best.pt
uv run wels-score match_2 --checkpoint data/models/action_predictor_best.pt
```

Expected output:

```
10:08:55  INFO      Loaded action predictor from data/models/action_predictor_best.pt
10:08:55  INFO      Scoring match: match_1
10:08:55  INFO      Step 1/3: action predictions
10:08:55  INFO        4320 ball-carrier frames to score
10:09:12  INFO      Step 2/3: formation classification
10:09:14  INFO      Step 3/3: possession phases
10:09:14  INFO        143 possession phases written
10:09:14  INFO      Scoring complete: match_1
```

Scoring is safe to re-run — existing results are deleted before the new ones are written.

Formations and possession phases are written even without a checkpoint.
If you want basic analytics before training a model:

```bash
uv run wels-score match_1  # no --checkpoint needed for formations + possession
```

## Step 5 — Evaluate

After training, check the confusion matrix to understand where the model makes mistakes:

```python
import torch
from torch.utils.data import DataLoader
from ml.config import MLSettings
from ml.data.dataset import ActionDataset
from ml.models.action import ActionPredictor
from ml.training.evaluate import confusion_matrix

settings = MLSettings()
dataset = ActionDataset(settings.duckdb_path)
loader = DataLoader(dataset, batch_size=1, collate_fn=lambda b: b)

model = ActionPredictor()
model.load_state_dict(torch.load("data/models/action_best.pt", weights_only=True))

device = torch.device("cuda")
model.to(device)

matrix = confusion_matrix(model, loader, device)
for true_label, preds in matrix.items():
    print(f"{true_label:10s}  {preds}")
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WELS_DUCKDB_PATH` | `data/matches.duckdb` | Database to read from |
| `WELS_MODELS_DIR` | `data/models` | Where to save checkpoints |
| `WELS_WINDOW_SIZE` | `25` | Frames per training sample (1 second @ 25 FPS) |
| `WELS_K_NEIGHBORS` | `5` | k-NN edges in the player graph |
| `WELS_EPOCHS` | `50` | Training epochs |
| `WELS_LEARNING_RATE` | `0.001` | Adam optimizer learning rate |
| `WELS_BATCH_SIZE` | `32` | Batch size (currently 1 sample at a time; reserved for future batching) |
| `WELS_VAL_SPLIT` | `0.2` | Fraction of data held out for validation |
| `WELS_DEVICE` | `cuda` | `cuda` or `cpu` |
