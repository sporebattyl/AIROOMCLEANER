import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.constants import ANALYZE_ROUTE

@pytest.fixture
def client(mock_settings):
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client

@pytest.mark.asyncio
async def test_analyze_image_success(client):
    """Test successful image analysis via the API."""
    with patch("backend.services.ai_service.AIService.analyze_image_from_upload", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = {"result": "messy"}
        response = client.post(
            ANALYZE_ROUTE,
            files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
            headers={"X-API-KEY": "test-key"}
        )
        assert response.status_code == 200
        assert response.json() == {"result": "messy"}
        mock_analyze.assert_called_once()

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
