import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.constants import ANALYZE_ROUTE
from backend.core.state import get_state

@pytest.fixture
def client(app_state):
    """Create a test client for the FastAPI application."""
    app.dependency_overrides[get_state] = lambda: asyncio.run(app_state)
    with TestClient(app) as client:
        yield client


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
