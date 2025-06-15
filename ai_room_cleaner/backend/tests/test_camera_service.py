import pytest
import httpx
from unittest.mock import patch, MagicMock
from pydantic import SecretStr

from backend.services.camera_service import get_camera_image
from backend.core.config import AppSettings
from backend.core.exceptions import CameraError, ConfigError

@pytest.fixture
def mock_settings():
    """Fixture for AppSettings."""
    return AppSettings(
        AI_PROVIDER="openai",
        AI_MODEL="gpt-4-turbo",
        AI_API_ENDPOINT=None,
        ai_api_key=SecretStr("fake-key"),
        OPENAI_MAX_TOKENS=1000,
        history_file_path="/data/history.json",
        camera_entity="camera.test_camera",
        api_key=SecretStr("supervisor-key"),
        supervisor_url="http://supervisor.local",
        cors_allowed_origins=["http://localhost:8080"],
        vips_cache_max=100,
        high_risk_dimension_threshold=4096,
        LOG_LEVEL="INFO",
        MAX_IMAGE_SIZE_MB=10,
        MAX_IMAGE_DIMENSION=2048,
        AI_PROMPT="Test prompt",
        MAX_REQUEST_SIZE_MB=10,
    )

@pytest.mark.asyncio
async def test_get_camera_image_success(mock_settings):
    """Test successful image fetching from camera."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_bytes"
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        image_base64 = await get_camera_image("camera.test_camera", mock_settings)
        assert image_base64 == "ZmFrZV9pbWFnZV9ieXRlcw=="  # "fake_image_bytes" base64 encoded

@pytest.mark.asyncio
async def test_get_camera_image_invalid_entity_id(mock_settings):
    """Test with an invalid camera entity ID."""
    with pytest.raises(ValueError):
        await get_camera_image("", mock_settings)

@pytest.mark.asyncio
async def test_get_camera_image_no_supervisor_token(mock_settings):
    """Test without a supervisor token configured."""
    mock_settings.api_key = None
    with pytest.raises(ConfigError):
        await get_camera_image("camera.test_camera", mock_settings)

@pytest.mark.asyncio
async def test_get_camera_image_http_error(mock_settings):
    """Test handling of HTTP errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        with pytest.raises(CameraError):
            await get_camera_image("camera.test_camera", mock_settings)

@pytest.mark.asyncio
async def test_get_camera_image_request_error(mock_settings):
    """Test handling of request errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError(
            "Connection Error", request=MagicMock()
        )
        with pytest.raises(CameraError):
            await get_camera_image("camera.test_camera", mock_settings)