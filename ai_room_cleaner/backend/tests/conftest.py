import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from backend.core.config import Settings
from backend.services.ai_service import AIService
from backend.core.state import State

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.ai_model = "gemini-1.5-pro-latest"
    settings.camera_entity = "camera.test"
    settings.supervisor_token = MagicMock()
    settings.supervisor_token.get_secret_value.return_value = "test-token"
    settings.google_api_key = MagicMock()
    settings.google_api_key.get_secret_value.return_value = "test-key"
    settings.openai_api_key = None
    settings.max_image_size_mb = 5
    settings.max_image_dimension = 2048
    settings.history_file_path = "test_history.json"
    settings.ai_prompt = "Test prompt"
    settings.vips_cache_max = 100
    settings.vips_concurrency = 4
    settings.high_risk_dimension_threshold = 8000
    return settings

@pytest.fixture
async def ai_service(mock_settings):
    """Create AI service instance for testing."""
    with patch('backend.services.ai_service.genai'), \
         patch('backend.services.ai_service.configure_pyvips'):
        service = AIService(mock_settings)
        return service

@pytest.fixture
async def app_state(ai_service, mock_settings):
    """Create application state for testing."""
    return State(ai_service, mock_settings)