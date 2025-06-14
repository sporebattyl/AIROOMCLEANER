import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import base64
from backend.services.ai_service import AIService
from backend.core.exceptions import (
    AIError,
    ConfigError,
    ImageProcessingError,
    AIProviderError,
    InvalidAPIKeyError,
    APIResponseError,
)
from backend.core.config import Settings
from pydantic import SecretStr

@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to provide mock settings."""
    settings = Settings(
        AI_PROVIDER="openai",
        AI_MODEL="gpt-4-turbo",
        OPENAI_API_KEY=SecretStr("fake_key"),
        GOOGLE_API_KEY=SecretStr("fake_key"),
        LOG_LEVEL="DEBUG",
        MAX_IMAGE_SIZE_MB=1,
        MAX_IMAGE_DIMENSION=1024,
        AI_PROMPT="Analyze this image."
    )
    monkeypatch.setattr("backend.core.config.get_settings", lambda: settings)
    return settings

@pytest.fixture
def mock_ai_provider():
    """Fixture to mock the AIProvider."""
    mock_provider = AsyncMock()
    mock_provider.analyze_image = AsyncMock(return_value=[{"mess": "test mess", "reason": "test reason"}])
    return mock_provider

@pytest.fixture
def ai_service(mock_settings, mock_ai_provider):
    """Fixture to create an AIService instance with a mocked provider."""
    with patch("backend.services.ai_service.get_ai_provider", return_value=mock_ai_provider) as mock_get_provider:
        service = AIService(mock_settings)
        service.ai_provider = mock_ai_provider
        return service

@pytest.mark.asyncio
async def test_analyze_room_for_mess_success(ai_service, mock_ai_provider):
    """Test successful room analysis delegates to the AI provider."""
    test_image = base64.b64encode(b"fake_image_data").decode()
    
    with patch('backend.services.ai_service.resize_image_with_vips', return_value=b"resized_data") as mock_resize:
        result = await ai_service.analyze_room_for_mess(test_image)
        
        assert result == [{"mess": "test mess", "reason": "test reason"}]
        mock_resize.assert_called_once()
        mock_ai_provider.analyze_image.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_room_invalid_base64(ai_service):
    """Test handling of invalid base64 data."""
    with pytest.raises(AIError, match="Invalid base64 image data"):
        await ai_service.analyze_room_for_mess("invalid_base64!")

@pytest.mark.asyncio
async def test_analyze_room_empty_image_data(ai_service):
    """Test handling of empty image data after base64 decoding."""
    empty_image = base64.b64encode(b"").decode()
    with pytest.raises(AIError, match="Invalid or empty image data provided."):
        await ai_service.analyze_room_for_mess(empty_image)

@pytest.mark.asyncio
async def test_image_processing_error(ai_service):
    """Test that an ImageProcessingError is raised if resizing fails."""
    test_image = base64.b64encode(b"fake_image_data").decode()
    with patch('backend.services.ai_service.resize_image_with_vips', side_effect=Exception("VIPS error")):
        with pytest.raises(ImageProcessingError, match="Failed to process image: VIPS error"):
            await ai_service.analyze_room_for_mess(test_image)

@pytest.mark.asyncio
async def test_ai_provider_error(ai_service, mock_ai_provider):
    """Test handling of an error from the AI provider."""
    test_image = base64.b64encode(b"fake_image_data").decode()
    mock_ai_provider.analyze_image.side_effect = AIProviderError("Provider failed")

    with patch('backend.services.ai_service.resize_image_with_vips', return_value=b"resized_data"):
        with pytest.raises(AIProviderError, match="Provider failed"):
            await ai_service.analyze_room_for_mess(test_image)

def test_initialization_with_unknown_provider(mock_settings):
    """Test that AIService raises a ConfigError for an unknown provider."""
    mock_settings.AI_PROVIDER = "unknown_provider"
    with pytest.raises(ConfigError, match="Unknown or unsupported AI provider: unknown_provider"):
        AIService(mock_settings)