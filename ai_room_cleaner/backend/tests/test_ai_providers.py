import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pydantic import SecretStr
from ai_room_cleaner.backend.services.ai_providers import (
    get_ai_provider,
    OpenAIProvider,
    GoogleGeminiProvider,
    AIProvider,
)
from ai_room_cleaner.backend.core.config import AppSettings
from ai_room_cleaner.backend.core.exceptions import (
    AIError,
    ConfigError,
    InvalidAPIKeyError,
    APIResponseError,
    AIProviderError,
)
import json

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
        camera_entity=None,
        api_key=None,
        supervisor_url=None,
        cors_allowed_origins=["http://localhost:8080"],
        vips_cache_max=100,
        high_risk_dimension_threshold=4096,
        LOG_LEVEL="INFO",
        MAX_IMAGE_SIZE_MB=10,
        MAX_IMAGE_DIMENSION=2048,
        AI_PROMPT="Test prompt",
        MAX_REQUEST_SIZE_MB=10,
    )

class TestAIProvider(AIProvider):
    """A concrete implementation of AIProvider for testing purposes."""
    async def analyze_image(self, image_data: bytes, prompt: str, mime_type: str = "image/jpeg"):
        return [{"mess": "test", "reason": "test"}]

    async def health_check(self) -> bool:
        return True

def test_parse_ai_response_valid_json(mock_settings):
    provider = TestAIProvider(mock_settings)
    response_text = '```json\n{"tasks": [{"mess": "clean this", "reason": "it is dirty"}]}\n```'
    result = provider._parse_ai_response(response_text)
    assert result == [{"mess": "clean this", "reason": "it is dirty"}]

def test_parse_ai_response_legacy_list(mock_settings):
    provider = TestAIProvider(mock_settings)
    response_text = '["mess 1", "mess 2"]'
    result = provider._parse_ai_response(response_text)
    assert result == [
        {"mess": "mess 1", "reason": "N/A"},
        {"mess": "mess 2", "reason": "N/A"},
    ]

def test_parse_ai_response_invalid_json_fallback(mock_settings):
    provider = TestAIProvider(mock_settings)
    response_text = "This is not json"
    with patch.object(provider, '_parse_text_response', return_value=[{"mess": "parsed from text", "reason": "fallback"}]) as mock_fallback:
        result = provider._parse_ai_response(response_text)
        mock_fallback.assert_called_once_with(response_text)
        assert result == [{"mess": "parsed from text", "reason": "fallback"}]

def test_parse_ai_response_malformed_dict(mock_settings):
    provider = TestAIProvider(mock_settings)
    response_text = '{"some_other_key": "some_value"}'
    with pytest.raises(AIError, match="AI response is not in the expected format."):
        provider._parse_ai_response(response_text)

def test_parse_text_response(mock_settings):
    provider = TestAIProvider(mock_settings)
    text = """
    - task 1
    * task 2
    "task 3"
    """
    result = provider._parse_text_response(text)
    assert len(result) == 3
    assert result[0]["mess"] == "task 1"
    assert result[1]["mess"] == "task 2"
    assert result[2]["mess"] == "task 3"

def test_parse_text_response_empty_and_comments(mock_settings):
    provider = TestAIProvider(mock_settings)
    text = """
    # comment
    
    another line
    """
    result = provider._parse_text_response(text)
    assert len(result) == 1
    assert result[0]["mess"] == "another line"

def test_get_ai_provider_openai(mock_settings):
    """Test if get_ai_provider returns OpenAIProvider."""
    with patch('ai_room_cleaner.backend.services.ai_providers.OpenAIProvider') as mock_openai:
        get_ai_provider("openai", mock_settings)
        mock_openai.assert_called_once_with(mock_settings)

def test_get_ai_provider_google(mock_settings):
    """Test if get_ai_provider returns GoogleGeminiProvider."""
    mock_settings.AI_PROVIDER = "google"
    with patch('ai_room_cleaner.backend.services.ai_providers.GoogleGeminiProvider') as mock_google:
        get_ai_provider("google", mock_settings)
        mock_google.assert_called_once_with(mock_settings)

def test_get_ai_provider_unknown(mock_settings):
    """Test if get_ai_provider raises ConfigError for unknown provider."""
    with pytest.raises(ConfigError):
        get_ai_provider("unknown_provider", mock_settings)

# -- OpenAIProvider Tests --

@patch('backend.services.ai_providers.openai.AsyncOpenAI')
def test_openai_provider_init_success(mock_async_openai, mock_settings):
    """Test successful initialization of OpenAIProvider."""
    provider = OpenAIProvider(mock_settings)
    assert provider.client is not None
    mock_async_openai.assert_called_once_with(api_key=mock_settings.ai_api_key.get_secret_value())

def test_openai_provider_init_no_api_key(mock_settings):
    """Test OpenAIProvider initialization with no API key."""
    mock_settings.ai_api_key = None
    with pytest.raises(ConfigError, match="OpenAI API key is not configured."):
        OpenAIProvider(mock_settings)

@pytest.mark.asyncio
@patch('backend.services.ai_providers.openai.AsyncOpenAI')
async def test_openai_analyze_image_success(mock_async_openai, mock_settings):
    """Test successful image analysis with OpenAIProvider."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"tasks": [{"mess": "clean room", "reason": "messy"}]}'
    
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_async_openai.return_value = mock_client

    provider = OpenAIProvider(mock_settings)
    result = await provider.analyze_image(b"fake_image_data", "prompt")
    assert result == [{"mess": "clean room", "reason": "messy"}]

@pytest.mark.asyncio
@patch('backend.services.ai_providers.openai.AsyncOpenAI')
async def test_openai_analyze_image_api_error(mock_async_openai, mock_settings):
    """Test OpenAI API error during image analysis."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
    mock_async_openai.return_value = mock_client

    provider = OpenAIProvider(mock_settings)
    with pytest.raises(AIProviderError, match="An unexpected error occurred with OpenAI."):
        await provider.analyze_image(b"fake_image_data", "prompt")

@pytest.mark.asyncio
@patch('backend.services.ai_providers.openai.AsyncOpenAI')
async def test_openai_health_check_success(mock_async_openai, mock_settings):
    """Test successful health check for OpenAIProvider."""
    mock_client = MagicMock()
    mock_client.models.list = AsyncMock()
    mock_async_openai.return_value = mock_client

    provider = OpenAIProvider(mock_settings)
    assert (await provider.health_check())["status"] == "ok"

@pytest.mark.asyncio
@patch('backend.services.ai_providers.openai.AsyncOpenAI')
async def test_openai_health_check_failure(mock_async_openai, mock_settings):
    """Test failed health check for OpenAIProvider."""
    mock_client = MagicMock()
    mock_client.models.list = AsyncMock(side_effect=Exception("API Error"))
    mock_async_openai.return_value = mock_client

    provider = OpenAIProvider(mock_settings)
    with pytest.raises(AIProviderError):
        await provider.health_check()

# -- GoogleGeminiProvider Tests --

@patch('ai_room_cleaner.backend.services.ai_providers.GenerativeModel')
@patch('ai_room_cleaner.backend.services.ai_providers.configure')
def test_google_provider_init_success(mock_configure, mock_genai_model, mock_settings):
    """Test successful initialization of GoogleGeminiProvider."""
    mock_settings.AI_PROVIDER = "google"
    provider = GoogleGeminiProvider(mock_settings)
    assert provider.client is not None
    mock_configure.assert_called_once_with(api_key=mock_settings.ai_api_key.get_secret_value())
    mock_genai_model.assert_called_once_with(mock_settings.AI_MODEL)

def test_google_provider_init_no_api_key(mock_settings):
    """Test GoogleGeminiProvider initialization with no API key."""
    mock_settings.AI_PROVIDER = "google"
    mock_settings.ai_api_key = None
    with pytest.raises(ConfigError, match="Google API key is not configured."):
        GoogleGeminiProvider(mock_settings)

@pytest.mark.asyncio
@patch('ai_room_cleaner.backend.services.ai_providers.GenerativeModel')
async def test_google_analyze_image_success(mock_genai_model, mock_settings):
    """Test successful image analysis with GoogleGeminiProvider."""
    mock_response = MagicMock()
    mock_response.parts = [MagicMock()]
    mock_response.parts[0].text = '{"tasks": [{"mess": "clean room", "reason": "messy"}]}'
    
    mock_client = MagicMock()
    mock_client.generate_content_async = AsyncMock(return_value=mock_response)
    mock_genai_model.return_value = mock_client
    
    provider = GoogleGeminiProvider(mock_settings)
    result = await provider.analyze_image(b"fake_image_data", "prompt")
    assert result == [{"mess": "clean room", "reason": "messy"}]

@pytest.mark.asyncio
@patch('ai_room_cleaner.backend.services.ai_providers.GenerativeModel')
async def test_google_analyze_image_api_error(mock_genai_model, mock_settings):
    """Test Google API error during image analysis."""
    mock_client = MagicMock()
    mock_client.generate_content_async = AsyncMock(side_effect=Exception("API Error"))
    mock_genai_model.return_value = mock_client

    provider = GoogleGeminiProvider(mock_settings)
    with pytest.raises(AIProviderError, match="Failed to analyze image with Gemini."):
        await provider.analyze_image(b"fake_image_data", "prompt")

@pytest.mark.asyncio
@patch('ai_room_cleaner.backend.services.ai_providers.GenerativeModel')
async def test_google_health_check_success(mock_genai_model, mock_settings):
    """Test successful health check for GoogleGeminiProvider."""
    mock_client = MagicMock()
    mock_client.count_tokens = AsyncMock()
    mock_genai_model.return_value = mock_client

    provider = GoogleGeminiProvider(mock_settings)
    assert (await provider.health_check())["status"] == "ok"

@pytest.mark.asyncio
@patch('ai_room_cleaner.backend.services.ai_providers.GenerativeModel')
async def test_google_health_check_failure(mock_genai_model, mock_settings):
    """Test failed health check for GoogleGeminiProvider."""
    mock_client = MagicMock()
    mock_client.count_tokens = MagicMock(side_effect=Exception("API Error"))
    mock_genai_model.return_value = mock_client

    provider = GoogleGeminiProvider(mock_settings)
    with pytest.raises(AIProviderError):
        await provider.health_check()