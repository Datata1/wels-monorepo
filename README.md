# WELS — Handball Analytics Platform

A monorepo for a handball analytics platform that helps trainers analyze matches, ingest video data, perform computer vision, and predict actions to adjust strategy.

## Repository Structure

```
wels-monorepo/
├── packages/
│   ├── backend/    # FastAPI backend (API layer above the database)
│   └── frontend/   # HTMX-based frontend served by FastAPI
├── Makefile        # Top-level commands for managing all packages
└── ruff.toml       # Shared ruff linting config
```

Each Python package under `packages/` has its **own virtual environment** managed by [uv](https://docs.astral.sh/uv/).

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ruff](https://docs.astral.sh/ruff/) (installed per-package via uv)

## Quick Start

```bash
# Set up all packages (creates venvs + installs deps)
make setup

# Run the backend
make run-backend

# Run the frontend
make run-frontend

# Lint all packages
make lint

# Format all packages
make format

# Run all tests
make test
```

## Package Management

Each package is an independent Python project with its own `pyproject.toml` and `.venv`.

```bash
# Add a dependency to the backend
cd packages/backend && uv add <package>

# Add a dev dependency to the frontend
cd packages/frontend && uv add --dev <package>
```
