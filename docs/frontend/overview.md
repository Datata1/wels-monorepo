# Frontend Overview

The frontend is a FastAPI server that renders HTML using Jinja2 templates with HTMX for interactivity and Tailwind CSS for styling.

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
│       ├── input.css     # Tailwind v4 source
│       └── style.css     # Compiled output
└── templates/
    ├── base.html         # Root layout (nav, footer, scripts)
    ├── index.html        # Dashboard page
    ├── standings.html    # Standings page
    ├── components/
    │   └── macros.html   # Reusable UI components
    └── partials/
        ├── matches.html       # Match list fragment
        ├── match_detail.html  # Match detail fragment
        └── standings.html     # Standings table fragment
```

## How It Works

1. Browser requests a full page (e.g., `/`)
2. Frontend renders `index.html` extending `base.html`
3. HTMX attribute `hx-get="/partials/matches"` fires on page load
4. Frontend route fetches JSON from the backend API via `httpx`
5. Frontend renders the partial template and returns an HTML fragment
6. HTMX swaps the fragment into the page — no JavaScript required

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
