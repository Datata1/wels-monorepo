# WELS — Handball Analytics Platform

A monorepo for a handball analytics platform that helps trainers analyze matches, ingest video data, perform computer vision, and predict actions to adjust strategy.

## Repository Structure

```
wels-monorepo/
├── packages/
│   ├── backend/    # FastAPI API server (port 8000)
│   └── frontend/   # HTMX + Jinja2 frontend served by FastAPI (port 3000)
├── docs/           # MkDocs documentation source
├── .moon/          # moon workspace config
├── Makefile        # Top-level commands for managing all packages
├── mkdocs.yml      # Documentation site config
├── ruff.toml       # Shared linting/formatting config
└── ty.toml         # Shared type checking config
```

Each Python package under `packages/` has its **own virtual environment** managed by [uv](https://docs.astral.sh/uv/).

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

All other tools (ruff, ty, Tailwind CSS, moon) are installed automatically via `make setup`.

## Quick Start

```bash
# Set up everything (venvs, deps, Tailwind, moon, pre-commit hooks)
make setup

# Start the full platform (backend + frontend + Tailwind watcher + docs)
make dev
```

This launches:

| Service  | URL                        |
|----------|----------------------------|
| Backend  | http://localhost:8000       |
| Frontend | http://localhost:3000       |
| Docs     | http://localhost:8080       |

Press `Ctrl+C` to stop all services.

## Commands

### Development

```bash
make dev              # Start all services in parallel
make run-backend      # Backend only
make run-frontend     # Frontend only
make docs             # Documentation site only
```

### Code Quality

```bash
make lint             # Lint all packages (ruff)
make format           # Auto-format all packages (ruff)
make typecheck        # Type check all packages (ty)
make test             # Run all tests (pytest)
make test-integration # Integration tests only
make test-ui          # UI tests only (frontend)
```

### moon (parallel + cached)

[moon](https://moonrepo.dev/) is used for parallel task execution with content-aware caching:

```bash
./tools/moon run :lint       # Lint all packages in parallel
./tools/moon run :test       # Test all packages in parallel
./tools/moon run :typecheck  # Type check all packages in parallel
```

### Tailwind CSS

```bash
make tailwind         # One-off build (minified)
make tailwind-watch   # Watch mode
```

### Documentation

```bash
make docs             # Live-reload server at http://localhost:8080
make docs-build       # Build static site to site/
```

## Package Management

Each package is an independent Python project with its own `pyproject.toml` and `.venv`.

```bash
# Add a dependency to the backend
cd packages/backend && uv add <package>

# Add a dev dependency to the frontend
cd packages/frontend && uv add --dev <package>
```

## Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| [uv](https://docs.astral.sh/uv/) | Package management, venvs | `pyproject.toml` per package |
| [ruff](https://docs.astral.sh/ruff/) | Linting + formatting | `ruff.toml` |
| [ty](https://github.com/astral-sh/ty) | Type checking | `ty.toml` |
| [moon](https://moonrepo.dev/) | Parallel task runner + caching | `.moon/workspace.yml`, `moon.yml` per package |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first CSS (standalone CLI) | `input.css` (v4 syntax) |
| [MkDocs](https://www.mkdocs.org/) | Documentation | `mkdocs.yml` |
| [pre-commit](https://pre-commit.com/) | Git hooks (lint + format + typecheck) | `.pre-commit-config.yaml` |
| [GitHub Actions](https://github.com/features/actions) | CI (lint + typecheck + test) | `.github/workflows/tests.yml` |
