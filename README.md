# WELS — Handball Analytics Platform

A monorepo for a handball analytics platform. It processes match video with computer vision, stores structured match data in DuckDB, and predicts player actions with a GCN + LSTM model — surfacing insights via a web dashboard.

## How it works

```
match.mp4  →  [wels-ingest]  →  data/matches.duckdb  →  Backend API  →  Frontend
                                        ↑
                               [wels-train]  ←  action labels
                                        ↓
                               data/models/action_best.pt
```

1. **Ingest** — run `wels-ingest` on a match video; the CV pipeline detects players, estimates poses, classifies teams, and maps positions to court coordinates
2. **Analyse** — the backend reads DuckDB and serves heatmaps, possession stats, and speed comparisons via a REST API
3. **Train** — annotate action labels in DuckDB, then run `wels-train` to train the GCN + LSTM action predictor
4. **Predict** — the backend calls the trained model at request time and returns action probabilities per player per frame

## Repository structure

```
wels-monorepo/
├── packages/
│   ├── backend/        # FastAPI REST API (port 8000)
│   ├── frontend/       # HTMX + Jinja2 web UI (port 3000)
│   ├── ingestion/      # CV pipeline: video → DuckDB
│   └── ml/             # GCN + LSTM model: DuckDB → action predictions
├── data/               # Runtime data — not committed
│   ├── matches.duckdb  # All match data
│   ├── models/         # YOLO weights + trained checkpoints
│   └── videos/         # Recommended location for match recordings
├── docs/               # MkDocs documentation
├── .moon/              # Moon workspace config
├── Makefile
├── ruff.toml           # Shared lint/format config
└── ty.toml             # Shared type-check config
```

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.12+ | |
| [uv](https://docs.astral.sh/uv/) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| NVIDIA GPU (CUDA 12.1+) | Required for video ingestion and ML training. CPU fallback available but slow. |

## Quick start

**Linux / macOS**
```bash
make setup   # venvs, deps, moon, pre-commit hooks
make dev     # backend + frontend + docs in parallel
```

**Windows**
```powershell
.\Make.ps1 setup
.\Make.ps1 dev
```

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| Docs | http://localhost:8080 |

## Processing a match video

```bash
cd packages/ingestion

# Basic run
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz

# With court calibration (enables real-world metre coordinates)
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz \
    --calibration data/court_cal.json

# CPU-only machine
uv run wels-ingest data/videos/match.mp4 2026-04-13_wels_vs_linz --device cpu
```

Install the CV runtime deps on the machine that processes video:
```bash
cd packages/ingestion && uv sync --all-extras
```

## Training the action predictor

```bash
cd packages/ml
uv sync
uv run wels-train   # reads data/matches.duckdb, writes data/models/action_best.pt
```

See [ML — Training](docs/ml/training.md) for the full annotation and training workflow.

## Commands

```bash
make lint             # ruff check (all packages)
make format           # ruff format (all packages)
make typecheck        # ty (all packages)
make test             # pytest — non-integration tests (all packages)
make test-integration # integration tests (require GPU + video files)
make docs             # docs server at http://localhost:8080
```

Moon (parallel + cached):
```bash
./tools/moon run :lint
./tools/moon run :test
./tools/moon run :typecheck
```

## Adding dependencies

```bash
cd packages/<name> && uv add <package>        # runtime dep
cd packages/<name> && uv add --dev <package>  # dev dep

# Ingestion CV deps (torch, ultralytics) are in the [cv] optional group:
cd packages/ingestion && uv add --optional cv <package>
```

## Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| [uv](https://docs.astral.sh/uv/) | Package management, venvs | `pyproject.toml` per package |
| [ruff](https://docs.astral.sh/ruff/) | Linting + formatting | `ruff.toml` |
| [ty](https://github.com/astral-sh/ty) | Type checking | `ty.toml` |
| [moon](https://moonrepo.dev/) | Parallel task runner + caching | `.moon/`, `moon.yml` per package |
| [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) | Documentation | `mkdocs.yml` |
| [pre-commit](https://pre-commit.com/) | Git hooks | `.pre-commit-config.yaml` |
| [GitHub Actions](https://github.com/features/actions) | CI | `.github/workflows/tests.yml` |
