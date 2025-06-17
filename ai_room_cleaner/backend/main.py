"""
Main application file for the AI Room Cleaner backend.
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from ai_room_cleaner.backend.api.router import limiter
from ai_room_cleaner.backend.api.router import router as api_router
from ai_room_cleaner.backend.core.config import get_settings
from ai_room_cleaner.backend.core.exceptions import AppException
from ai_room_cleaner.backend.core.logging import setup_logging
from ai_room_cleaner.backend.core.state import APP_STATE
from ai_room_cleaner.backend.middleware import LoggingMiddleware, RequestSizeLimitMiddleware
from ai_room_cleaner.backend.services.ai_service import AIService
from ai_room_cleaner.backend.services.history_service import HistoryService


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage application startup and shutdown events."""
    # Load environment variables from .env file in the project root
    # This ensures that settings are loaded before any other initialization
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded environment variables from: {env_path}")
    else:
        logger.warning(f".env file not found at {env_path}, continuing without it.")

    setup_logging()
    logger.info("--- AI Room Cleaner Starting Up ---")

    # Initialize services and state
    try:
        settings = get_settings()
        ai_service = AIService(settings)
        history_service = HistoryService()
        APP_STATE.initialize(ai_service, history_service, settings)
        fastapi_app.state.limiter = limiter
        logger.info("AI service and application state initialized.")

        logger.info(f"Camera Entity: {settings.camera_entity or 'Not set'}")
        logger.info(f"AI Model: {settings.AI_MODEL or 'Not set'}")
        logger.info(f"API Key configured: {bool(settings.api_key)}")
        logger.info(f"Supervisor URL: {settings.supervisor_url}")

        # Check for frontend files
        logger.info("Checking for frontend files...")
        frontend_dir_check = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "frontend")
        )
        if os.path.exists(frontend_dir_check):
            for filename in ["index.html", "style.css", "app.js"]:
                filepath = os.path.join(frontend_dir_check, filename)
                exists = os.path.exists(filepath)
                logger.info(f"  {filename}: {'✓' if exists else '✗'}")
        else:
            logger.error(f"Frontend directory not found at: {frontend_dir_check}")

        logger.info("Essential configuration is valid.")
    except (RuntimeError, ValueError) as e:
        logger.error(f"Failed to initialize application state: {e}", exc_info=True)
        sys.exit(1)

    # Create a shared httpx.AsyncClient
    async with httpx.AsyncClient() as client:
        fastapi_app.state.http_client = client
        logger.info("Shared httpx.AsyncClient created.")

        logger.info("--- Startup Complete ---")
        yield

    logger.info("--- AI Room Cleaner Shutting Down ---")
app = FastAPI(
    title="AI Room Cleaner",
    version="0.1.0",
    description="""
A smart home automation project that uses AI to identify messes in a room
and suggest cleaning tasks. It's designed to be integrated with Home Assistant
but can be run as a standalone service.
""",
    lifespan=lifespan
)

# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    """Custom exception handler for application-specific errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.detail},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """Custom exception handler for FastAPI's HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    """Generic exception handler for any other unhandled errors."""
    logger.exception("An unexpected error occurred", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected internal error occurred.",
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.
    """
    return _rate_limit_exceeded_handler(request, exc)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(LoggingMiddleware)


# Add the request size limit middleware
max_request_size = get_settings().MAX_REQUEST_SIZE_MB * 1024 * 1024
app.add_middleware(RequestSizeLimitMiddleware, max_size=max_request_size)


# Include the API router
app.include_router(api_router)

# Mount the frontend directory
# Mount the frontend directory, which is now inside the backend directory
# as a result of the unified Dockerfile build
frontend_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
    logger.info(f"Mounted frontend directory: {frontend_dist_dir}")
else:
    logger.error(f"Frontend dist directory not found at: {frontend_dist_dir}")

if __name__ == "__main__":
    import uvicorn

    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting AI Room Cleaner on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
