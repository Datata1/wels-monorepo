from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="WELS — Handball Analytics Frontend", version="0.1.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Register partial routes (HTMX fragments)
from frontend.routes import router as partials_router  # noqa: E402

app.include_router(partials_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main dashboard page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Service liveness probe."""
    return {"status": "ok"}
