import pytest
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from ai_room_cleaner.backend.main import app, lifespan, app_exception_handler, generic_exception_handler, RequestSizeLimitMiddleware
from ai_room_cleaner.backend.core.exceptions import AppException
from pydantic import SecretStr

def test_app_exception_handler():
    """Test the custom AppException handler."""
    test_app = FastAPI()
    test_app.add_exception_handler(AppException, app_exception_handler)  # type: ignore

    @test_app.get("/test-app-exception")
    async def _():
        raise AppException(status_code=418, detail="I'm a teapot")

    with TestClient(test_app) as client:
        response = client.get("/test-app-exception")
        assert response.status_code == 418
        assert response.json() == {"error": "AppException", "message": "I'm a teapot"}

def test_generic_exception_handler():
    """Test the generic exception handler."""
    test_app = FastAPI()
    test_app.add_exception_handler(Exception, generic_exception_handler)

    @test_app.get("/test-generic-exception")
    async def _():
        raise ValueError("A generic error")

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/test-generic-exception")
        assert response.status_code == 500
        assert response.json()["error"] == "InternalServerError"

def test_request_size_limit_middleware():
    """Test the request size limit middleware."""
    test_app = FastAPI()
    test_app.add_middleware(RequestSizeLimitMiddleware, max_size=1024)

    @test_app.post("/test-size-limit")
    async def _(request: dict):
        return {"status": "ok"}

    with TestClient(test_app) as client:
        # Test a request that is too large
        response = client.post(
            "/test-size-limit",
            headers={"Content-Length": "2048"},
            json={"data": "a" * 100}
        )
        assert response.status_code == 413

        # Test a request that is within the limit
        response = client.post(
            "/test-size-limit",
            json={"data": "a" * 100}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_lifespan_startup_success():
    """Test successful application startup in the lifespan manager."""
    with patch('ai_room_cleaner.backend.main.setup_logging') as mock_setup_logging, \
         patch('ai_room_cleaner.backend.core.state.APP_STATE.initialize') as mock_initialize, \
         patch('ai_room_cleaner.backend.main.get_settings') as mock_get_settings:
        
        mock_settings = MagicMock()
        mock_settings.AI_PROVIDER = "openai"
        mock_get_settings.return_value = mock_settings
        
        async with lifespan(app):
            mock_setup_logging.assert_called_once()
            mock_initialize.assert_called_once()

@pytest.mark.asyncio
async def test_lifespan_startup_failure():
    """Test failed application startup in the lifespan manager."""
    with patch('ai_room_cleaner.backend.main.setup_logging'), \
         patch('ai_room_cleaner.backend.main.get_settings', side_effect=ValueError("Initialization failed")), \
         patch('sys.exit') as mock_exit:
        
        async with lifespan(app):
            pass
        mock_exit.assert_called_once_with(1)