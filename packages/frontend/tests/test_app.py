from httpx import AsyncClient


async def test_index_returns_html(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "WELS" in response.text


async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
