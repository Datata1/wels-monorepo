"""Integration tests for the frontend server.

These tests verify the full request/response cycle through
the frontend FastAPI app: page rendering, static files.
Run with: uv run pytest -m integration
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_index_returns_200(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


async def test_index_contains_htmx_script(client: AsyncClient) -> None:
    response = await client.get("/")
    assert "htmx.org" in response.text


async def test_static_css_served(client: AsyncClient) -> None:
    response = await client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_unknown_route_returns_404(client: AsyncClient) -> None:
    response = await client.get("/nonexistent-page")
    assert response.status_code == 404
