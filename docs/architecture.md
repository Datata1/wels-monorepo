# Architecture

## System overview

```
Browser ──(HTML + HTMX)──▶ Frontend (port 3000)
                                │
                          httpx.AsyncClient
                                │
                                ▼
                          Backend API (port 8000)
                                │
                          data/matches.duckdb
                                ▲
                         ┌──────┴───────┐
                  wels-ingest        wels-score
                 (CV pipeline)    (batch scoring)
                         │              │
                  Match video    trained *.pt
                    (MP4)        checkpoint
```

## Full data flow

```
┌─────────────┐
│  match.mp4  │
└──────┬──────┘
       │  wels-ingest <video> <match_id>
       ▼
┌───────────────────────────────────┐
│  Ingestion pipeline               │
│  (packages/ingestion)             │
│                                   │
│  1. Detect players + ball         │
│  2. Track identities              │
│  3. Estimate body pose            │
│  4. Classify teams by jersey      │
│  5. Map pixels → court metres     │
└─────────────────┬─────────────────┘
                  │  FrameState (typed dataclass)
                  ▼
┌─────────────────────────────┐
│  data/matches.duckdb        │
│  matches / frames /         │
│  players / ball /           │
│  action_labels              │
└──────────┬──────────────────┘
           │                    ╔══════════════════════╗
           │                    ║  Manual annotation   ║
           │                    ║  action_labels table ║
           │                    ╚══════════╤═══════════╝
           │                               │
           │           ┌───────────────────┘
           │           │
           │           ▼
           │  ┌─────────────────────┐
           │  │  wels-train         │
           │  │  (packages/ml)      │
           │  │                     │
           │  │  GCN + LSTM model   │
           │  └──────────┬──────────┘
           │             │  data/models/action_predictor_best.pt
           │             ▼
           │  ┌─────────────────────────────────┐
           │  │  wels-score <match_id>           │
           │  │  (packages/ml)                   │
           │  │                                  │
           │  │  1. Action predictions           │
           │  │     (GCN + LSTM per ball carrier)│
           │  │  2. Formation labels             │
           │  │     (rule-based, every 5 frames) │
           │  │  3. Possession phases            │
           │  │     (smoothed from has_ball)     │
           │  └──────────┬──────────────────────┘
           │             │  writes back to DuckDB
           ▼             ▼
┌────────────────────────────────────────┐
│  data/matches.duckdb (complete)        │
│  + action_predictions                  │
│  + formations                          │
│  + possession_phases                   │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌──────────────────────────────────┐
│  Backend API (port 8000)         │
│  (packages/backend)              │
│                                  │
│  GET /api/v1/matches             │
│  GET /api/v1/analytics/heatmap   │
│  GET /api/v1/predictions         │
└─────────────────┬────────────────┘
                  │  JSON
                  ▼
┌─────────────────────────────────┐
│  Frontend (port 3000)           │
│  (packages/frontend)            │
│                                 │
│  Jinja2 templates + HTMX        │
│  Match list, heatmap viewer,    │
│  formation timeline             │
└─────────────────────────────────┘
```

## Monorepo layout

```
wels-monorepo/
├── packages/
│   ├── backend/          # FastAPI REST API (port 8000)
│   │   └── src/backend/
│   │       ├── app.py
│   │       ├── config.py
│   │       ├── models.py
│   │       └── routes/
│   ├── frontend/         # HTMX + Jinja2 server (port 3000)
│   │   └── src/frontend/
│   │       ├── app.py
│   │       ├── routes/
│   │       ├── static/css/
│   │       └── templates/
│   ├── ingestion/        # CV pipeline: video → DuckDB
│   │   └── src/ingestion/
│   │       ├── pipeline/     # detection, pose, team, court
│   │       ├── storage/      # DuckDB schema + writer
│   │       ├── orchestrator.py
│   │       └── cli.py
│   └── ml/               # GCN + LSTM model: train, score, analyse
│       └── src/ml/
│           ├── data/         # feature queries, graph construction, dataset
│           ├── models/       # ActionPredictor (GCN + LSTM)
│           ├── training/     # training loop + evaluation
│           ├── analysis/     # formation classifier, possession phase detector
│           ├── storage/      # ML output table schema
│           ├── scoring.py    # MatchScorer (writes 3 output tables)
│           ├── inference.py  # ActionInference (loads checkpoint)
│           └── cli.py        # wels-score entry point
├── data/                 # runtime data (not committed)
│   ├── matches.duckdb
│   ├── models/
│   └── videos/           # recommended location for match recordings
├── docs/                 # MkDocs documentation
├── Makefile
├── ruff.toml
└── ty.toml
```

## Package boundaries

Packages communicate through **DuckDB** (data) and **HTTP** (services).
They never import each other.

| Package | Reads from | Writes to |
|---------|-----------|-----------|
| `ingestion` | video file | `data/matches.duckdb` (matches, frames, players, ball) |
| `ml` | `data/matches.duckdb` | `data/matches.duckdb` (action_predictions, formations, possession_phases) + `data/models/*.pt` |
| `backend` | `data/matches.duckdb` | HTTP responses |
| `frontend` | backend HTTP | HTML responses |

The backend never calls the ML model directly — it only reads pre-computed results
from DuckDB. This means a 60-minute match is served instantly without GPU at request time.

Each package can evolve, be replaced, or be scaled independently.

## Design decisions

### Two separate FastAPI apps

Frontend and backend have independent venvs and ports. The frontend is a "thin BFF"
(Backend for Frontend) that calls the real API over HTTP. Benefits:

- No dependency conflicts between packages
- Can be deployed and scaled separately
- Frontend can be swapped for a different UI without changing the API

### HTMX, not React/Vue

No JavaScript build toolchain. Dynamic UI is achieved via server-sent HTML fragments.
HTMX attributes (`hx-get`, `hx-target`, `hx-swap`) trigger partial page updates.

### DuckDB, not PostgreSQL

Single file, zero config, columnar storage. Ideal for the analytical query patterns
(time-window scans, cross-match aggregations) this platform needs.
See [Storage](storage.md) for the full schema.

### Ingestion is a CLI, not a service

`wels-ingest` runs as a command-line tool, not a persistent process.
The backend triggers it as a `FastAPI BackgroundTask` when the trainer uploads a video.
This is simpler than a separate worker queue and sufficient for the expected scale
(processing a full match takes 30–90 minutes depending on hardware).

### uv over pip/Poetry

Faster installs, deterministic lockfiles, first-class workspace support.

### ruff + ty, not black/mypy

Both are written in Rust — orders of magnitude faster. Maintained by the same team (Astral).

## Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **uv** | Package management, venvs | `pyproject.toml` per package |
| **ruff** | Linting + formatting | `ruff.toml` (root) |
| **ty** | Type checking | `ty.toml` (root) |
| **pytest** | Testing | `pyproject.toml` per package |
| **moon** | Task runner (parallel, cached) | `.moon/` |
| **pre-commit** | Git hooks (ruff + ty) | `.pre-commit-config.yaml` |
| **GitHub Actions** | CI (lint + typecheck + test) | `.github/workflows/` |
