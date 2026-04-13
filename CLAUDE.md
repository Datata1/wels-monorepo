# CLAUDE.md — WELS Monorepo

## Project Overview

**WELS** is a handball analytics platform for trainers and analysts. It ingests match videos through a computer vision pipeline, stores structured frame-by-frame data in DuckDB, trains a GCN + LSTM model to predict player actions, and surfaces insights via a web dashboard.

## Architecture

```
Browser ──(HTML + HTMX)──> Frontend (port 3000)
                                 │
                           httpx.AsyncClient
                                 │
                                 ▼
                           Backend API (port 8000)
                                 │
                           data/matches.duckdb
                                 ▲
                                 │
                          wels-ingest CLI
                          (CV pipeline)
                                 │
                           Match video (MP4)
```

**Package boundaries** — packages communicate through DuckDB (data) and HTTP (services), never by importing each other:

| Package | Reads | Writes |
|---------|-------|--------|
| `ingestion` | video file | `data/matches.duckdb` |
| `ml` | `data/matches.duckdb` (read-only) | `data/models/*.pt` |
| `backend` | `data/matches.duckdb`, `data/models/*.pt` | HTTP responses |
| `frontend` | backend HTTP | HTML responses |

## Repository Layout

```
wels-monorepo/
├── packages/
│   ├── backend/          # FastAPI REST API (port 8000)
│   │   └── src/backend/
│   │       ├── app.py        # FastAPI app factory
│   │       ├── config.py     # pydantic-settings (WELS_ prefix)
│   │       ├── models.py     # Pydantic domain models
│   │       └── routes/       # API route modules
│   ├── frontend/         # HTMX + Jinja2 server (port 3000)
│   │   └── src/frontend/
│   │       ├── app.py
│   │       ├── routes/
│   │       ├── static/css/
│   │       └── templates/
│   │           ├── base.html
│   │           └── components/macros.html
│   ├── ingestion/        # CV pipeline: video → DuckDB
│   │   └── src/ingestion/
│   │       ├── pipeline/     # detection, pose, team, court (pure functions)
│   │       ├── storage/      # DuckDB schema + FrameWriter
│   │       ├── types.py      # shared dataclasses (BoundingBox, FrameState, …)
│   │       ├── orchestrator.py
│   │       ├── config.py
│   │       └── cli.py        # wels-ingest entry point
│   └── ml/               # GCN + LSTM action predictor
│       └── src/ml/
│           ├── data/         # DuckDB queries, graph construction, Dataset
│           ├── models/       # ActionPredictor (GCN + LSTM)
│           ├── training/     # training loop + evaluation
│           ├── inference.py  # load checkpoint → predict
│           └── config.py
├── data/                 # runtime data — not committed
│   ├── matches.duckdb    # all match data
│   ├── models/           # YOLO weights + trained checkpoints
│   └── videos/           # recommended location for match recordings
├── docs/                 # MkDocs documentation
├── .moon/                # Moon workspace config
├── .github/
│   ├── workflows/tests.yml      # CI: lint + typecheck + test (all 4 packages)
│   └── instructions/python.instructions.md
├── Makefile
├── ruff.toml             # Shared lint/format config
└── ty.toml               # Shared type-check config (all rules as errors)
```

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.12+ |
| API framework | FastAPI + Uvicorn |
| Templating | Jinja2 + HTMX |
| Data models | Pydantic v2 |
| Config | pydantic-settings (`WELS_` prefix) |
| HTTP client | httpx (async) |
| Storage | **DuckDB** (`data/matches.duckdb`) |
| Object detection | **YOLO11** (ultralytics) + ByteTrack |
| ML framework | **PyTorch** + **PyTorch Geometric** |
| Package manager | **uv** (not pip, not Poetry) |
| Build backend | hatchling |
| Task runner | **moon** (`./tools/moon`) |
| Linter/formatter | **ruff** |
| Type checker | **ty** (all rules as errors) |
| Test framework | pytest + pytest-asyncio |
| Docs | MkDocs Material |
| CI | GitHub Actions |

## Common Commands

```bash
# First-time setup
make setup          # install all venvs + pre-commit hooks

# Development
make dev            # backend + frontend + docs (parallel)
make run-backend    # → http://localhost:8000
make run-frontend   # → http://localhost:3000
make docs           # → http://localhost:8080

# Code quality (all packages)
make lint
make format
make typecheck
make test
make test-integration

# Video ingestion (requires GPU or --device cpu)
cd packages/ingestion
uv run wels-ingest <video> <match_id> [--calibration court.json]

# ML training
cd packages/ml
uv run wels-train

# Moon (parallel + cached)
./tools/moon run :lint
./tools/moon run :typecheck
./tools/moon run :test
```

## Development Conventions

### Adding a new backend route
1. Create a module in `packages/backend/src/backend/routes/`.
2. Define an `APIRouter` and register it in `app.py`.
3. Use Pydantic v2 models in `models.py` or a local `schemas.py`.

### Adding a new frontend page
1. Create a module in `packages/frontend/src/frontend/routes/`.
2. Register the router in `app.py`.
3. Add a Jinja2 template under `templates/`.
4. For HTMX partials, return an HTML fragment via `TemplateResponse`.
5. Use macros from `templates/components/macros.html`.

### Working on the ingestion pipeline
- `pipeline/` modules are **pure functions** — no file I/O, no DB calls, no global state inside them.
- All data passed between stages uses the typed dataclasses in `types.py`.
- The four pipeline stubs (`detection`, `pose`, `team`, `court`) have `NotImplementedError` bodies; port them from `CV-POC-Wels/pipeline/` one at a time.
- `torch` and `ultralytics` are in the `[cv]` optional group — install with `uv sync --all-extras` on GPU machines.

### Working on the ML package
- `ml` reads DuckDB **read-only** — it never writes to the database.
- `data/features.py` contains all DuckDB queries; keep SQL out of other modules.
- `data/graphs.py` converts frame dicts to PyG `Data` objects — no I/O.
- `models/action.py` is a plain `nn.Module` — no DuckDB, no file I/O.
- Use `WELS_DEVICE=cpu` on machines without a GPU.

### Adding a dependency
```bash
cd packages/<name> && uv add <package>
```
For ingestion CV deps (torch, ultralytics): `uv add --optional cv <package>`
Or use the `/add-dep` skill.

### Configuration
All packages use `pydantic-settings` with `WELS_` prefix:
```bash
export WELS_DEVICE=cuda
export WELS_DUCKDB_PATH=data/matches.duckdb
export WELS_BACKEND_URL=http://localhost:8000   # used by frontend
```

### Testing
- Non-integration tests require no GPU and no video files — run anywhere.
- Integration tests are marked `@pytest.mark.integration` and excluded from CI.
- Ingestion unit tests (types, storage) only need `duckdb` + `numpy`; no torch.
- ML unit tests (graph construction, model shape) need torch but no GPU.

## CI

GitHub Actions runs on every PR across all four packages:
1. Lint (ruff)
2. Type check (ty, GitHub annotation format)
3. Test (`pytest -m "not integration"`)
4. Posts a pass/fail summary comment on the PR

Ingestion installs without the `[cv]` extras (no torch/ultralytics on CI).
ML installs normally; torch runs on CPU on the GitHub runner and is cached between runs.

## Available Claude Skills

Custom skills are defined under `.claude/commands/` and invocable as slash commands:

| Skill | Purpose |
|-------|---------|
| `/new-package <name>` | Scaffold a new Python package in the monorepo |
| `/new-component <desc>` | Add a Jinja2 macro component to the frontend |
| `/new-route <desc>` | Scaffold a new route (backend or frontend) |
| `/add-dep <dep> to <pkg>` | Add a dependency via uv |
| `/check` | Run the full quality suite (lint + typecheck + test) |
| `/port-pipeline <module>` | Port a pipeline stub from CV-POC into the ingestion package |
| `/train` | Run wels-train and report results |

## Key Design Decisions

- **Package boundaries via DuckDB + HTTP**: packages never import each other. `ingestion` writes DuckDB, `ml` reads it, `backend` serves it.
- **Pipeline modules are pure**: `pipeline/` functions take typed inputs, return typed outputs — no side effects. This makes them testable without a GPU.
- **torch/ultralytics are optional in ingestion**: unit tests run without GPU deps; the `[cv]` group is only installed on machines that process video.
- **Ingestion triggered as FastAPI BackgroundTask**: no separate worker queue. Sufficient for batch processing; can be extracted later if needed.
- **Two separate FastAPI apps**: frontend and backend have independent venvs and ports.
- **HTMX, not React/Vue**: no JavaScript build toolchain.
- **uv over pip/Poetry**: faster installs, deterministic lockfiles.
- **moon for task caching**: tasks only re-run when inputs change.
- **ruff + ty, not black/mypy**: both written in Rust; order-of-magnitude faster.
