import pytest
from pydantic import ValidationError
from backend.core.config import get_settings

@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Fixture to clear the settings cache before each test."""
    get_settings.cache_clear()

def test_settings_load_from_env(monkeypatch):
    """Test that settings are correctly loaded from environment variables."""
    monkeypatch.setenv("CAMERA_ENTITY_ID", "camera.test_camera")
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-supervisor-token")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    
    settings = get_settings()
    
    assert settings.camera_entity == "camera.test_camera"
    assert settings.supervisor_token.get_secret_value() == "test-supervisor-token"
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "test-google-api-key"

def test_settings_api_key_validation_google_preferred(monkeypatch):
    """Test that the Google API key is preferred when both are provided."""
    monkeypatch.setenv("CAMERA_ENTITY_ID", "camera.test_camera")
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-supervisor-token")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    
    settings = get_settings()
    
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "google-key"

def test_settings_api_key_validation_openai_fallback(monkeypatch):
    """Test that the OpenAI API key is used when it's the only one provided."""
    monkeypatch.setenv("CAMERA_ENTITY_ID", "camera.test_camera")
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-supervisor-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    
    settings = get_settings()
    
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "openai-key"

def test_settings_missing_api_key_raises_error(monkeypatch):
    """Test that a validation error is raised if no API key is provided."""
    monkeypatch.setenv("CAMERA_ENTITY_ID", "camera.test_camera")
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-supervisor-token")
    
    with pytest.raises(ValidationError, match="An AI provider API key is required"):
        get_settings()

def test_settings_missing_required_field_raises_error(monkeypatch):
    """Test that a validation error is raised if a required field (e.g., camera_entity) is missing."""
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-supervisor-token")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    
    with pytest.raises(ValidationError, match="Field required"):
        get_settings()