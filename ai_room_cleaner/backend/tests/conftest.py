import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Mock the 'magic' library at the module level to prevent ImportError
mock_magic = MagicMock()
mock_magic.from_buffer.return_value = "image/jpeg"
sys.modules['magic'] = mock_magic

import pytest
import asyncio
from backend.core.config import get_settings
from backend.services.ai_service import AIService
from backend.services.history_service import HistoryService
from backend.services.ai_providers import AIProvider
from backend.core.state import State

def pytest_configure(config):
    """
    Set default environment variables before test collection.
    This ensures that the settings model can be validated when it's
    imported by other modules during the collection phase.
    """
    os.environ["AI_PROVIDER"] = "openai"
    os.environ["AI_MODEL"] = "test_model"
    os.environ["AI_API_KEY"] = "test-api-key"
    os.environ["API_KEY"] = "test-key"

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Fixture to automatically clear the settings cache before each test.
    This ensures that tests can independently modify environment variables
    without affecting each other.
    """
    get_settings.cache_clear()

@pytest.fixture
def mock_settings():
    """Returns the application settings for tests."""
    return get_settings()

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def ai_service(mock_settings):
    """Create AI service instance for testing with a mocked provider."""
    with patch('backend.services.ai_service.get_ai_provider') as mock_get_ai_provider:
        mock_provider = MagicMock(spec=AIProvider)
        mock_provider.analyze_image.return_value = [{"result": "messy"}]
        mock_provider.health_check.return_value = True
        mock_get_ai_provider.return_value = mock_provider
        
        service = AIService(mock_settings)
        yield service

@pytest.fixture
def history_service():
    """Create a mock HistoryService."""
    return HistoryService()

@pytest.fixture
async def app_state(ai_service, history_service, mock_settings):
    """Create application state for testing."""
    return State(ai_service, history_service, mock_settings)