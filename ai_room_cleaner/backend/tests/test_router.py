import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.constants import ANALYZE_ROUTE
from backend.core.state import get_state

@pytest.fixture
async def client(app_state):
    """Create a test client for the FastAPI application."""
    app.dependency_overrides[get_state] = lambda: app_state
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analyze_image_no_api_key(client):
    """Test that a 401 is returned if no API key is provided."""
    response = client.post(
        ANALYZE_ROUTE,
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_analyze_image_invalid_file_type(client):
    """Test that a 400 is returned for an invalid file type."""
    response = client.post(
        ANALYZE_ROUTE,
        files={"file": ("test.txt", b"fake_text_data", "text/plain")},
        headers={"X-API-KEY": "test-key"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_history_initially_empty(client):
    """Test that the history is initially empty."""
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_clear_history_no_api_key(client):
    """Test that clearing history without an API key fails."""
    response = client.delete("/history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_clear_history_with_api_key(client):
    """Test that clearing history with a valid API key succeeds."""
    response = client.delete("/history", headers={"X-API-KEY": "test-key"})
    assert response.status_code == 200
    assert response.json() == {"message": "History cleared successfully."}


@pytest.mark.asyncio
async def test_history_lifecycle(client):
    """Test the full lifecycle of the history endpoint."""
    # 1. Initially, history is empty
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []

    # 2. Add an item to the history (by calling analyze)
    client.post(
        ANALYZE_ROUTE,
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        headers={"X-API-KEY": "test-key"}
    )

    # 3. Get history and verify the new item is there
    response = client.get("/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["result"] == "messy"

    # 4. Clear the history
    response = client.delete("/history", headers={"X-API-KEY": "test-key"})
    assert response.status_code == 200

    # 5. Get history again and verify it's empty
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_config(client):
    """Test the /config endpoint."""
    response = client.get("/config", headers={"X-API-KEY": "test-key"})
    assert response.status_code == 200
    assert "apiKey" in response.json()
    assert response.json()["apiKey"] == "test-key"

@pytest.mark.asyncio
async def test_get_config_no_api_key(client):
    """Test that the /config endpoint requires an API key."""
    response = client.get("/config")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_health_check(client):
    """Test the /health endpoint."""
    with patch('backend.services.ai_service.AIService.health_check', new_callable=AsyncMock) as mock_health_check:
        mock_health_check.return_value = {"status": "ok"}
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["dependencies"]["ai_service"]["status"] == "ok"

@pytest.mark.asyncio
async def test_health_check_degraded(client):
    """Test the /health endpoint when a dependency is unhealthy."""
    with patch('backend.services.ai_service.AIService.health_check', new_callable=AsyncMock) as mock_health_check:
        mock_health_check.return_value = {"status": "unhealthy"}
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["dependencies"]["ai_service"]["status"] == "unhealthy"
