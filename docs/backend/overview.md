# Backend Overview

The backend is a FastAPI application that exposes a RESTful JSON API for handball match data.

## Running

```bash
make run-backend
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

## Configuration

Settings are managed via environment variables with the `WELS_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `WELS_APP_NAME` | `WELS Handball Analytics` | Application name |
| `WELS_DEBUG` | `false` | Debug mode |
| `WELS_DATABASE_URL` | `sqlite:///./wels.db` | Database connection string |

## Project Structure

```
src/backend/
├── app.py        # FastAPI application factory + health check
├── config.py     # BaseSettings configuration
├── models.py     # Pydantic domain models + demo data
└── routes/
    └── __init__.py   # API route handlers
```

## Models

::: backend.models
    options:
      members:
        - PlayerStats
        - MatchEvent
        - Match
        - TeamOverview
      show_source: false
