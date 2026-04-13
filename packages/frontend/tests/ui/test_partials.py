"""UI tests for HTMX partial fragments.

Verify the HTML structure of partial responses that HTMX swaps into the page.
Run with: uv run pytest -m ui
"""

import pytest
from bs4 import BeautifulSoup
from httpx import AsyncClient

pytestmark = pytest.mark.ui


async def _get_soup(client: AsyncClient, path: str) -> BeautifulSoup:
    response = await client.get(path)
    assert response.status_code == 200
    return BeautifulSoup(response.text, "html.parser")


# ─── Matches partial ──────────────────────────────────


async def test_matches_partial_has_cards(client: AsyncClient):
    """Each match is rendered as a card div."""
    soup = await _get_soup(client, "/partials/matches")
    assert soup.find("div", class_="match-card") is not None


async def test_matches_partial_shows_team_names(client: AsyncClient):
    soup = await _get_soup(client, "/partials/matches")
    text = soup.get_text()
    assert "THW Kiel" in text
    assert "SG Flensburg-Handewitt" in text


async def test_matches_partial_shows_scores(client: AsyncClient):
    soup = await _get_soup(client, "/partials/matches")
    text = soup.get_text()
    assert "28" in text
    assert "25" in text


async def test_matches_partial_has_details_button(client: AsyncClient):
    soup = await _get_soup(client, "/partials/matches")
    btn = soup.find("button", attrs={"hx-get": True})
    assert btn is not None
    assert "/partials/match/" in btn["hx-get"]


# ─── Match detail partial ─────────────────────────────


async def test_match_detail_shows_teams(client: AsyncClient):
    soup = await _get_soup(client, "/partials/match/1")
    text = soup.get_text()
    assert "THW Kiel" in text


async def test_match_detail_shows_timeline(client: AsyncClient):
    soup = await _get_soup(client, "/partials/match/1")
    text = soup.get_text()
    assert "Niklas Ekberg" in text


async def test_match_detail_shows_player_stats(client: AsyncClient):
    soup = await _get_soup(client, "/partials/match/1")
    tables = soup.find_all("table")
    assert len(tables) >= 2


# ─── Standings partial ────────────────────────────────


async def test_standings_has_table(client: AsyncClient):
    soup = await _get_soup(client, "/partials/standings")
    assert soup.find("table") is not None


async def test_standings_shows_team_names(client: AsyncClient):
    soup = await _get_soup(client, "/partials/standings")
    text = soup.get_text()
    assert "THW Kiel" in text
    assert "SC Magdeburg" in text


async def test_standings_shows_points(client: AsyncClient):
    """Points = wins*2 + draws. THW Kiel: 18*2+1=37."""
    soup = await _get_soup(client, "/partials/standings")
    text = soup.get_text()
    assert "37" in text
