import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from backend.main import app, lifespan
from backend.core.exceptions import AppException
from pydantic import SecretStr

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client

def test_app_exception_handler(client):
    """Test the custom AppException handler."""
    @app.get("/test-app-exception")
    async def _():
        raise AppException(status_code=418, detail="I'm a teapot")

    response = client.get("/test-app-exception")
    assert response.status_code == 418
    assert response.json() == {"error": "AppException", "message": "I'm a teapot"}

def test_generic_exception_handler(client):
    """Test the generic exception handler."""
    @app.get("/test-generic-exception")
    async def _():
        raise ValueError("A generic error")

    response = client.get("/test-generic-exception")
    assert response.status_code == 500
    assert response.json()["error"] == "InternalServerError"

def test_request_size_limit_middleware(client):
    """Test the request size limit middleware."""
    # This test simulates a request with a Content-Length header that exceeds the limit.
    # The limit is set in config, but we can assume a default for testing.
    # The actual middleware logic is what's being tested here.
    
    # Create a route to test the middleware
    @app.post("/test-size-limit")
    async def _(request: dict):
        return {"status": "ok"}
    
    # Test a request that is too large
    large_size = 11 * 1024 * 1024  # 11MB
    response = client.post(
        "/test-size-limit",
        headers={"Content-Length": str(large_size)},
        json={"data": "a" * 100} # small payload, but header is what matters
    )
    assert response.status_code == 413

    # Test a request without content-length
    response = client.post("/test-size-limit", content="some data")
    assert response.status_code == 411

@pytest.mark.asyncio
async def test_lifespan_startup_success():
    """Test successful application startup in the lifespan manager."""
    with patch('backend.main.setup_logging') as mock_setup_logging, \
         patch('backend.main.initialize_state', new_callable=AsyncMock) as mock_initialize_state, \
         patch('backend.main.get_settings') as mock_get_settings:
        
        mock_get_settings.return_value = MagicMock(
            camera_entity='cam1', AI_MODEL='model1', api_key=SecretStr('key'), supervisor_url='url'
        )
        
        async with lifespan(app):
            mock_setup_logging.assert_called_once()
            mock_initialize_state.assert_called_once()
            # If no exception is raised, the test passes.

@pytest.mark.asyncio
async def test_lifespan_startup_failure():
    """Test failed application startup in the lifespan manager."""
    with patch('backend.main.setup_logging'), \
         patch('backend.main.initialize_state', side_effect=Exception("Initialization failed")), \
         patch('backend.main.get_settings'), \
         patch('sys.exit') as mock_exit:
        
        async with lifespan(app):
            pass
        mock_exit.assert_called_once_with(1)