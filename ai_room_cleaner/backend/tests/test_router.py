import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from ai_room_cleaner.backend.main import app
from ai_room_cleaner.backend.api.constants import ANALYZE_ROUTE
from ai_room_cleaner.backend.core.state import get_state

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with patch('ai_room_cleaner.backend.main.get_settings'), \
         patch('ai_room_cleaner.backend.main.AIService'), \
         patch('ai_room_cleaner.backend.main.HistoryService'):
        with TestClient(app) as test_client:
            yield test_client

def test_analyze_image_no_api_key(client):
    """Test that a 401 is returned if no API key is provided."""
    response = client.post(
        ANALYZE_ROUTE,
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")}
    )
    assert response.status_code == 401

def test_analyze_image_invalid_file_type(client):
    """Test that a 400 is returned for an invalid file type."""
    response = client.post(
        ANALYZE_ROUTE,
        files={"file": ("test.txt", b"fake_text_data", "text/plain")},
        headers={"X-API-KEY": "test-key"}
    )
    assert response.status_code == 400

def test_get_history_initially_empty(client):
    """Test that the history is initially empty."""
    with patch('ai_room_cleaner.backend.api.router.get_state') as mock_get_state:
        mock_state = mock_get_state.return_value
        mock_state.history_service.get_history = AsyncMock(return_value=[])
        response = client.get("/history")
        assert response.status_code == 200
        assert response.json() == []

def test_clear_history_no_api_key(client):
    """Test that clearing history without an API key fails."""
    response = client.delete("/history")
    assert response.status_code == 401

def test_clear_history_with_api_key(client):
    """Test that clearing history with a valid API key succeeds."""
    with patch('ai_room_cleaner.backend.api.router.get_state') as mock_get_state:
        mock_state = mock_get_state.return_value
        mock_state.history_service.clear_history = AsyncMock()
        response = client.delete("/history", headers={"X-API-KEY": "test-key"})
        assert response.status_code == 200
        assert response.json() == {"message": "History cleared successfully."}

def test_history_lifecycle(client):
    """Test the full lifecycle of the history endpoint."""
    with patch('ai_room_cleaner.backend.api.router.get_state') as mock_get_state:
        mock_state = mock_get_state.return_value
        
        # 1. Initially, history is empty
        mock_state.history_service.get_history = AsyncMock(return_value=[])
        response = client.get("/history")
        assert response.status_code == 200
        assert response.json() == []

        # 2. Add an item to the history (by calling analyze)
        mock_state.ai_service.analyze_room_for_mess = AsyncMock(return_value=[{"result": "messy"}])
        mock_state.history_service.add_history_entry = AsyncMock()
        client.post(
            ANALYZE_ROUTE,
            files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
            headers={"X-API-KEY": "test-key"}
        )

        # 3. Get history and verify the new item is there
        mock_state.history_service.get_history.return_value = [{"result": "messy"}]
        response = client.get("/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 1
        assert history[0]["result"] == "messy"

        # 4. Clear the history
        mock_state.history_service.clear_history = AsyncMock()
        response = client.delete("/history", headers={"X-API-KEY": "test-key"})
        assert response.status_code == 200

        # 5. Get history again and verify it's empty
        mock_state.history_service.get_history.return_value = []
        response = client.get("/history")
        assert response.status_code == 200
        assert response.json() == []

def test_get_config(client):
    """Test the /config endpoint."""
    response = client.get("/config", headers={"X-API-KEY": "test-key"})
    assert response.status_code == 200
    assert "apiKey" in response.json()
    assert response.json()["apiKey"] is not None

def test_get_config_no_api_key(client):
    """Test that the /config endpoint requires an API key."""
    response = client.get("/config")
    assert response.status_code == 401

def test_health_check(client):
    """Test the /health endpoint."""
    with patch('ai_room_cleaner.backend.api.router.get_state') as mock_get_state:
        mock_state = mock_get_state.return_value
        mock_state.ai_service.health_check = AsyncMock(return_value={"status": "ok"})
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["dependencies"]["ai_service"]["status"] == "ok"

def test_health_check_degraded(client):
    """Test the /health endpoint when a dependency is unhealthy."""
    with patch('ai_room_cleaner.backend.api.router.get_state') as mock_get_state:
        mock_state = mock_get_state.return_value
        mock_state.ai_service.health_check = AsyncMock(return_value={"status": "unhealthy"})
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["dependencies"]["ai_service"]["status"] == "unhealthy"
