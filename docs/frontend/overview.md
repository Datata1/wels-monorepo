# Frontend Overview

The frontend is a FastAPI server that renders HTML using Jinja2 templates with HTMX for interactivity and semantic CSS with design tokens for styling.

## Running

```bash
make run-frontend
# → http://localhost:3000
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WELS_BACKEND_URL` | `http://localhost:8000` | Backend API base URL |

## Project Structure

```
src/frontend/
├── app.py            # FastAPI app, static mounts, page routes
├── config.py         # BaseSettings configuration
├── routes/
│   └── __init__.py   # HTMX partial HTML endpoints
├── static/
│   └── css/
│       └── style.css     # Semantic CSS with design tokens
└── templates/
    ├── base.html         # Root layout (nav, footer, scripts)
    ├── index.html        # Dashboard page
    └── components/
        └── macros.html   # Reusable UI components
```

## How It Works

1. Browser requests a full page (e.g., `/`)
2. Frontend renders `index.html` extending `base.html`
3. HTMX partials can be added under `routes/` to fetch data from the backend and return HTML fragments
4. HTMX swaps fragments into the page — no JavaScript required

## Routes

::: frontend.routes
    options:
      show_source: true
      heading_level: 3

## Application

::: frontend.app
    options:
      show_source: true
      heading_level: 3
