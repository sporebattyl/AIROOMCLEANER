import pytest
from unittest.mock import patch, MagicMock
from pydantic import SecretStr

from ai_room_cleaner.backend.utils.image_processing import (
    resize_image_with_vips,
    configure_pyvips,
    VIPS_AVAILABLE,
)
from ai_room_cleaner.backend.core.config import AppSettings
from ai_room_cleaner.backend.core.exceptions import ImageProcessingError

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

@pytest.fixture
def fake_image_bytes():
    # A 1x1 red pixel GIF
    return b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

@patch("backend.utils.image_processing.pyvips", create=True)
def test_configure_pyvips(mock_pyvips, mock_settings):
    """Test pyvips configuration."""
    if VIPS_AVAILABLE:
        configure_pyvips(mock_settings)
        mock_pyvips.cache_set_max.assert_called_with(mock_settings.vips_cache_max)
    else:
        pytest.skip("pyvips not available")

@patch("backend.utils.image_processing.pyvips", create=True)
def test_resize_image_with_vips_success(mock_pyvips, mock_settings, fake_image_bytes):
    """Test successful image resizing."""
    if VIPS_AVAILABLE:
        mock_image = MagicMock()
        mock_image.width = 800
        mock_image.height = 600
        mock_image.bands = 3
        mock_image.write_to_buffer.return_value = b"resized_image"
        mock_pyvips.Image.new_from_buffer.return_value = mock_image

        resized = resize_image_with_vips(fake_image_bytes, mock_settings)
        assert resized == b"resized_image"
    else:
        pytest.skip("pyvips not available")

def test_resize_image_without_vips(mock_settings, fake_image_bytes):
    """Test that an ImageProcessingError is raised if pyvips is not available."""
    if not VIPS_AVAILABLE:
        with pytest.raises(ImageProcessingError):
            resize_image_with_vips(fake_image_bytes, mock_settings)
    else:
        pytest.skip("pyvips is available")

def test_resize_image_with_empty_data(mock_settings):
    """Test resizing with empty image data."""
    with pytest.raises(ImageProcessingError):
        resize_image_with_vips(b"", mock_settings)

@patch("backend.utils.image_processing.pyvips", create=True)
def test_resize_image_vips_error(mock_pyvips, mock_settings, fake_image_bytes):
    """Test handling of a pyvips error."""
    if VIPS_AVAILABLE:
        mock_pyvips.Image.new_from_buffer.side_effect = Exception("VIPS Error")
        with pytest.raises(ImageProcessingError):
            resize_image_with_vips(fake_image_bytes, mock_settings)
    else:
        pytest.skip("pyvips not available")