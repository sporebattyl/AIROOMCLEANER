import os
from contextlib import asynccontextmanager
from loguru import logger
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.core.config import get_settings
from backend.api.router import router as api_router, limiter as api_limiter
from backend.core.exceptions import AppException
from backend.core.state import State
from backend.services.ai_service import AIService

# Configure logging
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", serialize=True, level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("--- AI Room Cleaner Starting Up ---")
    
    # Initialize services and state
    try:
        settings = get_settings()
        ai_service = AIService(settings)
        app.state.state = State(ai_service=ai_service, settings=settings)
        app.state.limiter = api_limiter
        logger.info("AI service and application state initialized.")
        
        logger.info(f"Camera Entity: {settings.camera_entity or 'Not set'}")
        logger.info(f"AI Model: {settings.ai_model or 'Not set'}")
        logger.info(f"API Key configured: {bool(settings.api_key)}")
        logger.info(f"Supervisor URL: {settings.supervisor_url}")
        
        # Check for frontend files
        logger.info("Checking for frontend files...")
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
        if os.path.exists(frontend_dir):
            for filename in ["index.html", "style.css", "app.js"]:
                filepath = os.path.join(frontend_dir, filename)
                exists = os.path.exists(filepath)
                logger.info(f"  {filename}: {'✓' if exists else '✗'}")
        else:
            logger.error(f"Frontend directory not found at: {frontend_dir}")
        
        logger.info("Essential configuration is valid.")
    except Exception as e:
        logger.error(f"Failed to initialize application state: {e}", exc_info=True)
        import sys
        sys.exit(1)
    
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
async def app_exception_handler(request: Request, exc: AppException):
    """Custom exception handler for application-specific errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.detail},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for FastAPI's HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "message": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Generic exception handler for any other unhandled errors."""
    logger.exception("An unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": "An unexpected internal error occurred."},
    )

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include the API router
app.include_router(api_router, prefix="/api")

# Mount the frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
    logger.info(f"Mounted frontend directory: {frontend_dir}")
else:
    logger.error(f"Frontend directory not found at: {frontend_dir}")

# Add middleware to log all requests for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting AI Room Cleaner on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")