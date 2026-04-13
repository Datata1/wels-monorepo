Run the action prediction model training and report results. $ARGUMENTS

## Steps

1. **Check prerequisites** — verify `data/matches.duckdb` exists and has action labels:
   ```python
   import duckdb
   db = duckdb.connect("data/matches.duckdb", read_only=True)
   count = db.execute("SELECT COUNT(*) FROM action_labels").fetchone()[0]
   ```
   If the database doesn't exist or has 0 labels, stop and tell the user what's missing. Link to `docs/ml/training.md` for the annotation workflow.

2. **Run training** from the ml package directory:
   ```bash
   cd packages/ml && uv run wels-train --verbose
   ```
   Pass through any arguments the user provided (e.g. `--epochs 100 --device cpu`).

3. **Report results** — when training completes, summarise:
   - Number of training samples found
   - Best validation accuracy achieved
   - Checkpoint path written
   - If accuracy is low (< 0.4), note that more labeled data is likely needed and reference the label counts in `docs/ml/training.md`

4. **Verify the checkpoint** — confirm `data/models/action_best.pt` was created:
   ```bash
   ls -lh data/models/action_best.pt
   ```

## If training fails

- **"No module named torch"** — run `cd packages/ml && uv sync` first
- **"No data"** — the DuckDB database is empty or has no action_labels rows; see `docs/ml/training.md`
- **CUDA out of memory** — rerun with `--device cpu` or reduce `WELS_BATCH_SIZE`
- **Import error from torch_geometric** — run `cd packages/ml && uv sync` to ensure dependencies are installed
