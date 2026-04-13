# Architecture

## Monorepo Layout

```
wels-monorepo/
├── packages/
│   ├── backend/          # FastAPI API server (port 8000)
│   │   ├── src/backend/
│   │   │   ├── app.py        # FastAPI application
│   │   │   ├── config.py     # Settings via pydantic-settings
│   │   │   ├── models.py     # Pydantic domain models
│   │   │   └── routes/       # API route handlers
│   │   └── tests/
│   └── frontend/         # HTMX frontend server (port 3000)
│       ├── src/frontend/
│       │   ├── app.py        # FastAPI app serving HTML
│       │   ├── config.py     # Settings (backend_url, etc.)
│       │   ├── routes/       # Partial HTML route handlers
│       │   ├── static/css/   # Hand-authored semantic CSS
│       │   └── templates/    # Jinja2 templates
│       │       ├── components/   # Reusable macros
│       │       └── partials/     # HTMX partial fragments
│       └── tests/
├── docs/                 # MkDocs documentation (this site)
├── tools/                # Downloaded binaries (moon)
├── Makefile              # Orchestration commands
├── mkdocs.yml            # Documentation config
├── ruff.toml             # Shared linting config
└── ty.toml               # Shared type checking config
```

## Design Decisions

### Separate packages, separate venvs

Each package under `packages/` is a standalone Python project with its own `pyproject.toml` and `.venv`. This ensures:

- **No dependency conflicts** between backend and frontend
- **Independent versioning** and deployment
- **Fast installs** — changing one package doesn't reinstall the other

### Frontend → Backend communication

The frontend fetches data from the backend API over HTTP using `httpx.AsyncClient`:

```
Browser ──(HTML)──▶ Frontend (port 3000)
                         │
                    httpx.AsyncClient
                         │
                         ▼
                    Backend API (port 8000)
```

HTMX loads partial HTML fragments from the frontend, which in turn fetches JSON from the backend and renders it through Jinja2 templates.

### HTMX + Jinja2 component model

Instead of a JavaScript framework, we use server-rendered HTML with:

- **`{% macro %}`** — reusable UI components with props (like React components)
- **`{% include %}`** — static partial inclusion
- **HTMX attributes** — `hx-get`, `hx-target`, `hx-swap` for dynamic updates without JavaScript

Components live in `templates/components/macros.html` and are imported with:

```jinja
{% from "components/macros.html" import match_card, status_badge %}
```

### Plain CSS with design tokens

Styling uses hand-authored semantic CSS with CSS custom properties as design tokens. No build step or external tooling is required — `style.css` is committed directly and served as a static file.

## Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **uv** | Package management, venvs | `pyproject.toml` per package |
| **ruff** | Linting + formatting | `ruff.toml` (root) |
| **ty** | Type checking | `ty.toml` (root) |
| **pytest** | Testing | `pyproject.toml` per package |
| **pre-commit** | Git hooks (ruff + ty) | `.pre-commit-config.yaml` |
| **GitHub Actions** | CI (lint + typecheck + test) | `.github/workflows/tests.yml` |
