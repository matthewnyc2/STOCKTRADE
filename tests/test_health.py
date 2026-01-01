"""
Tests for the health check endpoint.
Written first as per TDD methodology.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check_returns_200(client):
    """Test that the health check endpoint returns 200 status code."""
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_returns_correct_json(client):
    """Test that the health check endpoint returns the expected JSON structure."""
    response = await client.get("/")
    assert response.json() == {"status": "healthy", "service": "crypto-quant-lab"}


@pytest.mark.asyncio
async def test_health_check_content_type(client):
    """Test that the response has application/json content type."""
    response = await client.get("/")
    assert response.headers["content-type"] == "application/json"
