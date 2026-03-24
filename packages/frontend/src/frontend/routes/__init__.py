import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from frontend.app import TEMPLATES_DIR
from frontend.config import settings

router = APIRouter(prefix="/partials", tags=["partials"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def _fetch_json(path: str) -> list | dict:
    """Fetch JSON from the backend API."""
    try:
        async with httpx.AsyncClient(base_url=settings.backend_url) as client:
            response = await client.get(path, timeout=5.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return []


@router.get("/matches", response_class=HTMLResponse)
async def matches_partial(request: Request):
    """Return an HTML fragment of matches for HTMX swap."""
    matches = await _fetch_json("/api/v1/matches")
    return templates.TemplateResponse(request, "partials/matches.html", {"matches": matches})


@router.get("/match/{match_id}", response_class=HTMLResponse)
async def match_detail_partial(request: Request, match_id: int):
    """Return detailed match view as an HTML fragment."""
    match = await _fetch_json(f"/api/v1/matches/{match_id}")
    return templates.TemplateResponse(request, "partials/match_detail.html", {"match": match})


@router.get("/standings", response_class=HTMLResponse)
async def standings_partial(request: Request):
    """Return team standings as an HTML fragment."""
    teams = await _fetch_json("/api/v1/teams")
    return templates.TemplateResponse(request, "partials/standings.html", {"teams": teams})
