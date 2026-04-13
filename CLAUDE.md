# CLAUDE.md — WELS Monorepo

## Project Overview

**WELS** is a handball analytics platform for trainers and analysts. It ingests video data, runs ML inference, and surfaces match insights via a web dashboard. The platform is early-stage: the backend API and frontend shell are implemented; the ingestion and ML packages are scaffolded but empty.

## Architecture

```
Browser ──(HTML + HTMX)──> Frontend (port 3000)
                                 │
                           httpx.AsyncClient
                                 │
                                 ▼
                           Backend API (port 8000)
                                 │
                           SQLite (local dev)
                           PostgreSQL (production)
```

- **Frontend** is a FastAPI app that serves Jinja2 HTML. It talks to the backend over HTTP and returns either full pages or HTMX partial fragments.
- **Backend** is a FastAPI JSON API at `/api/v1/`. Data models are Pydantic v2. No ORM or migrations exist yet — only a `database_url` config placeholder.
- **Ingestion** and **ML** packages are placeholders (`.gitkeep` only).

## Repository Layout

```
wels-monorepo/
├── packages/
│   ├── backend/          # FastAPI REST API
│   │   ├── src/backend/
│   │   │   ├── app.py        # FastAPI app factory
│   │   │   ├── config.py     # pydantic-settings config (WELS_ prefix)
│   │   │   ├── models.py     # Pydantic data models (mostly empty)
│   │   │   └── routes/       # API route modules (add new routes here)
│   │   └── tests/
│   ├── frontend/         # HTMX + Jinja2 HTML server
│   │   ├── src/frontend/
│   │   │   ├── app.py        # FastAPI app factory
│   │   │   ├── config.py     # pydantic-settings config (WELS_ prefix)
│   │   │   ├── routes/       # Page + partial routes (add new routes here)
│   │   │   ├── static/css/   # Hand-authored CSS with design tokens
│   │   │   └── templates/
│   │   │       ├── base.html          # Layout shell
│   │   │       ├── index.html         # Homepage
│   │   │       └── components/macros.html  # Jinja2 macro components
│   │   └── tests/
│   ├── ingestion/        # (placeholder)
│   └── ml/               # (placeholder)
├── docs/                 # MkDocs documentation source
├── .moon/                # Moon workspace config
├── .github/workflows/    # CI (lint + typecheck + test on PR)
├── Makefile              # Top-level developer commands
├── ruff.toml             # Shared lint/format config
├── ty.toml               # Shared type-check config (all rules as errors)
└── .pre-commit-config.yaml
```

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.12+ |
| API framework | FastAPI + Uvicorn (both packages) |
| Templating | Jinja2 |
| Frontend interaction | HTMX (no JS build step) |
| Data models | Pydantic v2 |
| Config | pydantic-settings (env vars with `WELS_` prefix) |
| HTTP client | httpx (async) |
| Package manager | **uv** (not pip, not Poetry) |
| Build backend | hatchling |
| Task runner | **moon** (binary at `./tools/moon`) |
| Linter/formatter | **ruff** (replaces black + flake8 + isort) |
| Type checker | **ty** (Astral's checker, all rules as errors) |
| Test framework | pytest + pytest-asyncio |
| Docs | MkDocs Material |
| CI | GitHub Actions |

## Common Commands

```bash
# First-time setup
make setup          # install all venvs, pre-commit hooks

# Development
make dev            # start backend + frontend + docs (parallel)
make run-backend    # backend only  → http://localhost:8000
make run-frontend   # frontend only → http://localhost:3000
make docs           # docs server   → http://localhost:8080

# Code quality
make lint           # ruff check (all packages)
make format         # ruff format (all packages)
make typecheck      # ty (all packages)
make test           # pytest (all packages)
make test-integration  # integration tests only
make test-ui           # UI/HTML tests only (frontend)

# Moon-based (parallel + cached)
./tools/moon run :lint
./tools/moon run :typecheck
./tools/moon run :test
```

## Development Conventions

### Adding a new backend route
1. Create a module in `packages/backend/src/backend/routes/`.
2. Define an `APIRouter` and add it to the app in `app.py`.
3. Use Pydantic v2 models for request/response bodies; define them in `models.py` or a local `schemas.py`.

### Adding a new frontend page
1. Create a module in `packages/frontend/src/frontend/routes/`.
2. Register the router in `app.py`.
3. Add a Jinja2 template under `templates/`.
4. For HTMX partials return an HTML fragment (not a full page) — use `TemplateResponse` with a partial template.
5. Use macros from `templates/components/macros.html` for reusable UI pieces.

### Adding a dependency
Use `uv add` inside the relevant package directory (not `pip install`):
```bash
cd packages/backend && uv add some-library
```
Or use the `add-dep` skill: `/add-dep <package> to <backend|frontend>`.

### Code style
- Line length: 100 characters (configured in `ruff.toml`).
- All imports sorted and grouped by ruff.
- All type hints required — `ty` runs with every rule as an error.
- Pre-commit hooks enforce lint + format + typecheck on every commit.

### Configuration
Both packages use `pydantic-settings`. Environment variables are prefixed with `WELS_`:
```bash
export WELS_DATABASE_URL="postgresql://..."
export WELS_BACKEND_URL="http://localhost:8000"  # used by frontend
```

### Testing
- Async tests use `@pytest.mark.asyncio`.
- Integration tests are marked `@pytest.mark.integration`.
- UI tests parse rendered HTML with BeautifulSoup4.
- Each package has its own pytest config in `pyproject.toml`.

## CI

GitHub Actions runs on every PR:
1. Lint (ruff)
2. Type check (ty, GitHub annotation format)
3. Test (pytest, JUnit XML)
4. Posts a summary comment on the PR with pass/fail status.

## Available Claude Skills

Custom skills are defined under `.claude/skills/` and invocable as slash commands:

| Skill | Purpose |
|-------|---------|
| `/new-package <name>` | Scaffold a new Python package in the monorepo |
| `/new-component <desc>` | Add a Jinja2 macro component to the frontend |
| `/new-route <desc>` | Scaffold a new route (backend or frontend) |
| `/add-dep <dep> to <pkg>` | Add a dependency via uv |
| `/check` | Run the full quality suite (lint + typecheck + test) |

## Key Design Decisions

- **Two separate FastAPI apps** (not one): frontend and backend have independent venvs, ports, and can be scaled separately. The frontend is a "thin BFF" (Backend for Frontend) that calls the real API.
- **HTMX, not React/Vue**: no JavaScript build toolchain. Dynamic UI is achieved via server-sent HTML fragments.
- **uv over pip/Poetry**: faster installs, deterministic lockfiles, first-class workspace support.
- **moon for task caching**: tasks are only re-run when their inputs change (content-hashed). Speeds up CI significantly on unchanged packages.
- **ruff + ty, not black/mypy**: both are written in Rust; they're an order of magnitude faster and maintained by the same team (Astral).
