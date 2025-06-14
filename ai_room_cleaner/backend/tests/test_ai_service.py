import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from backend.services.ai_service import AIService, ConfigError, AIError

def test_initialization_gemini():
    """Test that the AIService initializes correctly with Gemini."""
    mock_settings = SimpleNamespace(
        ai_model="gemini-1.5-pro-latest",
        google_api_key=MagicMock(),
        openai_api_key=None
    )
    mock_settings.google_api_key.get_secret_value.return_value = 'test-google-key'

    with patch('backend.services.ai_service.get_settings', return_value=mock_settings):
        with patch('backend.services.ai_service.genai') as mock_genai:
            service = AIService(mock_settings)
            mock_genai.configure.assert_called_once_with(api_key='test-google-key')
            assert service.gemini_client is not None
            assert service.openai_client is None

def test_initialization_openai():
    """Test that the AIService initializes correctly with OpenAI."""
    mock_settings = SimpleNamespace(
        ai_model="gpt-4",
        google_api_key=None,
        openai_api_key=MagicMock()
    )
    mock_settings.openai_api_key.get_secret_value.return_value = 'test-openai-key'

    with patch('backend.services.ai_service.get_settings', return_value=mock_settings):
        with patch('backend.services.ai_service.openai') as mock_openai:
            service = AIService(mock_settings)
            mock_openai.AsyncOpenAI.assert_called_once_with(api_key='test-openai-key')
            assert service.openai_client is not None
            assert service.gemini_client is None

def test_initialization_no_key():
    """Test that a ConfigError is raised if no API key is provided."""
    mock_settings = SimpleNamespace(
        ai_model="gemini-1.5-pro-latest",
        google_api_key=None,
        openai_api_key=None
    )
    with patch('backend.services.ai_service.get_settings', return_value=mock_settings):
        with pytest.raises(ConfigError, match="Google API key is not configured"):
            AIService(mock_settings)

def test_initialization_no_model():
    """Test that a ConfigError is raised if no model is specified."""
    mock_settings = SimpleNamespace(
        ai_model="",
        google_api_key=MagicMock(),
        openai_api_key=None
    )
    with patch('backend.services.ai_service.get_settings', return_value=mock_settings):
        with pytest.raises(ConfigError, match="AI model not specified"):
            AIService(mock_settings)

def test_unsupported_model():
    """Test that an unsupported model raises an AIError."""
    mock_settings = SimpleNamespace(
        ai_model="unsupported-model",
        google_api_key=MagicMock(),
        openai_api_key=None
    )
    with patch('backend.services.ai_service.get_settings', return_value=mock_settings):
        with pytest.raises(AIError, match="Unsupported or unrecognized AI model"):
            AIService(mock_settings)