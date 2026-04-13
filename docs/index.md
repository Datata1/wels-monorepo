# WELS — Handball Analytics Platform

A monorepo for a handball analytics platform that helps trainers analyze matches, ingest video data, and predict actions to adjust strategy.

## Quick Links

| | |
|---|---|
| [Getting Started](getting-started.md) | Set up your local environment |
| [Architecture](architecture.md) | System overview and design decisions |
| [Backend API](backend/api.md) | FastAPI endpoints and models |
| [Frontend](frontend/overview.md) | HTMX templates and components |
| [Contributing](contributing.md) | Code style, testing, and PR workflow |

## Tech Stack

- **Python 3.12+** with [uv](https://docs.astral.sh/uv/) for package management
- **FastAPI** — backend API and frontend server
- **HTMX** + **Jinja2** — server-rendered frontend with dynamic partial updates
- **Semantic CSS** — hand-authored with CSS custom properties (design tokens)
- **Pydantic v2** — data models and settings
- **ruff** — linting and formatting
- **ty** — type checking
- **pytest** — testing with integration and UI test markers
