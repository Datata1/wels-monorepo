from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from frontend.app import app

# Demo data returned by the mocked backend
MOCK_MATCHES = [
    {
        "id": 1,
        "home_team": "THW Kiel",
        "away_team": "SG Flensburg-Handewitt",
        "home_score": 28,
        "away_score": 25,
        "date": "2026-03-20",
        "venue": "Wunderino Arena",
        "status": "completed",
        "events": [
            {
                "minute": 3,
                "event_type": "goal",
                "team": "THW Kiel",
                "player": "Niklas Ekberg",
                "description": "Left wing shot from 7m",
            }
        ],
        "home_players": [
            {
                "name": "Sander Sagosen",
                "goals": 8,
                "assists": 4,
                "saves": 0,
                "turnovers": 2,
                "minutes_played": 55,
            }
        ],
        "away_players": [
            {
                "name": "Jim Gottfridsson",
                "goals": 7,
                "assists": 5,
                "saves": 0,
                "turnovers": 3,
                "minutes_played": 58,
            }
        ],
    },
]

MOCK_TEAMS = [
    {
        "name": "THW Kiel",
        "wins": 18,
        "losses": 3,
        "draws": 1,
        "goals_scored": 612,
        "goals_conceded": 540,
    },
    {
        "name": "SC Magdeburg",
        "wins": 17,
        "losses": 4,
        "draws": 1,
        "goals_scored": 635,
        "goals_conceded": 558,
    },
]


def _mock_backend_response(path: str) -> dict | list:
    """Return mock data based on the backend API path."""
    if path == "/api/v1/matches":
        return MOCK_MATCHES
    if path.startswith("/api/v1/matches/") and path.endswith("/events"):
        return MOCK_MATCHES[0]["events"]
    if path.startswith("/api/v1/matches/"):
        return MOCK_MATCHES[0]
    if path == "/api/v1/teams":
        return MOCK_TEAMS
    return []


@pytest.fixture
async def client():
    """Async HTTP client with mocked backend calls."""

    async def mock_get(self, path, **kwargs):
        data = _mock_backend_response(path)
        return httpx.Response(
            200,
            json=data,
            request=httpx.Request("GET", path),
        )

    transport = ASGITransport(app=app)
    with patch("frontend.routes.httpx.AsyncClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.get = lambda path, **kwargs: mock_get(mock_instance, path, **kwargs)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_instance

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
