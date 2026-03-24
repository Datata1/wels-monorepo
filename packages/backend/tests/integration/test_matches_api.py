"""Integration tests for the backend API routes."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


# ─── Health ─────────────────────────────────────────────


async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ─── Matches ────────────────────────────────────────────


async def test_list_matches_returns_demo_data(client: AsyncClient):
    response = await client.get("/api/v1/matches")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "home_team" in data[0]


async def test_get_match_by_valid_id(client: AsyncClient):
    response = await client.get("/api/v1/matches/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["home_team"] == "THW Kiel"


async def test_get_match_not_found(client: AsyncClient):
    response = await client.get("/api/v1/matches/999")
    assert response.status_code == 404


async def test_get_match_invalid_id_returns_422(client: AsyncClient):
    response = await client.get("/api/v1/matches/not-a-number")
    assert response.status_code == 422


async def test_match_contains_player_stats(client: AsyncClient):
    response = await client.get("/api/v1/matches/1")
    data = response.json()
    assert len(data["home_players"]) > 0
    assert "goals" in data["home_players"][0]


async def test_match_events_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/matches/1/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0
    assert "event_type" in events[0]


async def test_match_events_not_found(client: AsyncClient):
    response = await client.get("/api/v1/matches/999/events")
    assert response.status_code == 404


# ─── Teams ──────────────────────────────────────────────


async def test_list_teams(client: AsyncClient):
    response = await client.get("/api/v1/teams")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    assert "name" in data[0]
    assert "wins" in data[0]


async def test_unknown_route_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
