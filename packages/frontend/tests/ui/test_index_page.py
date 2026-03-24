"""UI tests for the index page.

Verify rendered HTML structure, content, and HTMX wiring.
Run with: uv run pytest -m ui
"""

import pytest
from bs4 import BeautifulSoup
from httpx import AsyncClient

pytestmark = pytest.mark.ui


async def _get_soup(client: AsyncClient, path: str = "/") -> BeautifulSoup:
    response = await client.get(path)
    assert response.status_code == 200
    return BeautifulSoup(response.text, "html.parser")


# ─── Page structure ─────────────────────────────────────


async def test_page_has_doctype(client: AsyncClient):
    response = await client.get("/")
    assert response.text.strip().lower().startswith("<!doctype html>")


async def test_page_has_lang_attribute(client: AsyncClient):
    soup = await _get_soup(client)
    assert soup.find("html")["lang"] == "en"


async def test_page_has_viewport_meta(client: AsyncClient):
    soup = await _get_soup(client)
    meta = soup.find("meta", attrs={"name": "viewport"})
    assert meta is not None


async def test_page_has_charset_meta(client: AsyncClient):
    soup = await _get_soup(client)
    meta = soup.find("meta", attrs={"charset": True})
    assert meta["charset"].lower() == "utf-8"


# ─── Navigation ────────────────────────────────────────


async def test_nav_has_brand_link(client: AsyncClient):
    soup = await _get_soup(client)
    nav = soup.find("nav")
    assert nav is not None
    brand = nav.find("a", href="/")
    assert brand is not None
    assert "WELS" in brand.get_text()


async def test_nav_has_standings_link(client: AsyncClient):
    soup = await _get_soup(client)
    link = soup.find("a", href="/standings")
    assert link is not None


# ─── Content ───────────────────────────────────────────


async def test_page_title_contains_wels(client: AsyncClient):
    soup = await _get_soup(client)
    assert "WELS" in soup.title.string


async def test_page_has_dashboard_heading(client: AsyncClient):
    soup = await _get_soup(client)
    h1 = soup.find("h1")
    assert h1 is not None
    assert "Dashboard" in h1.get_text()


async def test_page_has_matches_section(client: AsyncClient):
    soup = await _get_soup(client)
    section = soup.find("section", id="matches")
    assert section is not None


# ─── HTMX wiring ──────────────────────────────────────


async def test_htmx_script_loaded(client: AsyncClient):
    soup = await _get_soup(client)
    scripts = soup.find_all("script", src=True)
    htmx_scripts = [s for s in scripts if "htmx" in s["src"]]
    assert len(htmx_scripts) == 1


async def test_matches_div_has_htmx_trigger(client: AsyncClient):
    soup = await _get_soup(client)
    div = soup.find(attrs={"hx-get": "/partials/matches"})
    assert div is not None
    assert div.get("hx-trigger") == "load"
    assert div.get("hx-swap") == "innerHTML"


# ─── Stylesheet ────────────────────────────────────────


async def test_stylesheet_linked(client: AsyncClient):
    soup = await _get_soup(client)
    link = soup.find("link", rel="stylesheet")
    assert link is not None
    assert "style.css" in link["href"]
