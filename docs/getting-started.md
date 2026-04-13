# Getting Started

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.12+ | |
| [uv](https://docs.astral.sh/uv/) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| NVIDIA GPU | For ingestion and ML training. CUDA 12.1+. CPU fallback available but slow. |

## Setup

Clone the repo and install everything:

```bash
git clone <repo-url> && cd wels-monorepo
make setup
```

This installs venvs and dependencies for `backend`, `frontend`, `ingestion`, and `ml`,
downloads the moon task runner, and installs pre-commit hooks.

To set up an individual package only:

```bash
cd packages/ingestion && uv sync
cd packages/ml && uv sync
```

## Running the web platform

```bash
make dev
```

| Service | URL |
|---------|-----|
| Backend API | [http://localhost:8000](http://localhost:8000) |
| Frontend | [http://localhost:3000](http://localhost:3000) |
| Docs | [http://localhost:8080](http://localhost:8080) |

Press `Ctrl+C` to stop all services.

## Processing a match video

```bash
cd packages/ingestion

# Basic run (no court calibration — pixel positions only)
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz

# With court calibration (enables real-world metres, required for ML)
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz \
    --calibration data/court_cal.json

# On a CPU-only machine
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz --device cpu
```

Results are written to `data/matches.duckdb`. See [Ingestion — Running](ingestion/running.md)
for the full CLI reference and [Storage](storage.md) for what gets stored.

## Training the ML model

Once you have ingested matches and added action labels to DuckDB:

```bash
cd packages/ml
uv run wels-train
```

See [ML — Training](ml/training.md) for the full workflow including annotation.

## Common commands

```bash
make lint           # ruff check (all packages)
make format         # ruff format (all packages)
make typecheck      # ty check (all packages)
make test           # pytest (all packages, non-integration)
```

Or run per-package with moon:

```bash
./tools/moon run ingestion:test
./tools/moon run ml:lint
```

## Adding dependencies

Use `uv add` inside the relevant package directory:

```bash
cd packages/backend  && uv add some-library
cd packages/ingestion && uv add --dev some-dev-tool
```

Or use the `/add-dep` skill.
