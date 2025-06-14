import pytest
from pydantic import ValidationError
from backend.core.config import get_settings, Settings

@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    """Clear settings cache and set default env vars for tests."""
    get_settings.cache_clear()
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "test_model")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

def test_settings_load_from_env(monkeypatch):
    """Test that settings are correctly loaded from environment variables."""
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("AI_MODEL", "gemini-pro")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-api-key")
    
    settings = get_settings()
    
    assert settings.AI_PROVIDER == "google"
    assert settings.AI_MODEL == "gemini-pro"
    assert settings.GOOGLE_API_KEY is not None
    assert settings.GOOGLE_API_KEY.get_secret_value() == "google-api-key"

def test_invalid_ai_provider_raises_error(monkeypatch):
    """Test that an invalid AI_PROVIDER value raises a validation error."""
    monkeypatch.setenv("AI_PROVIDER", "invalid_provider")
    with pytest.raises(ValidationError, match="AI_PROVIDER must be 'openai' or 'google'"):
        get_settings()

def test_settings_defaults_are_applied():
    """Test that default values are applied when env vars are not set."""
    # Note: API keys don't have defaults and are required, so they are set in the fixture.
    settings = get_settings()
    
    assert settings.LOG_LEVEL == "INFO"
    assert settings.MAX_IMAGE_SIZE_MB == 10
    assert settings.MAX_IMAGE_DIMENSION == 2048
    assert settings.AI_PROMPT == "Analyze this image and identify areas of mess. Return a list of tasks to clean it up."

def test_openai_api_key_is_loaded(monkeypatch):
    """Test that the OpenAI API key is loaded correctly."""
    monkeypatch.setenv("OPENAI_API_KEY", "my-openai-key")
    settings = get_settings()
    assert settings.OPENAI_API_KEY is not None
    assert settings.OPENAI_API_KEY.get_secret_value() == "my-openai-key"

def test_google_api_key_is_loaded(monkeypatch):
    """Test that the Google API key is loaded correctly."""
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "my-google-key")
    settings = get_settings()
    assert settings.GOOGLE_API_KEY is not None
    assert settings.GOOGLE_API_KEY.get_secret_value() == "my-google-key"