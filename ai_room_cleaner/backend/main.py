import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.core.config import settings
from backend.api.router import router as api_router, limiter as api_limiter
from backend.core.exceptions import AppException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Room Cleaner",
    version="0.1.0",
    description="""
A smart home automation project that uses AI to identify messes in a room
and suggest cleaning tasks. It's designed to be integrated with Home Assistant
but can be run as a standalone service.
"""
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
    logger.error(f"An unexpected error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": "An unexpected internal error occurred."},
    )

# Set up rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
app.state.limiter = api_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
# In a production environment, this should be a specific list of trusted domains.
# For development, we allow localhost and 127.0.0.1.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
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

@app.on_event("startup")
async def startup_event():
    """Log startup information and check configurations."""
    logger.info("--- AI Room Cleaner Starting Up ---")
    logger.info(f"Camera Entity: {settings.camera_entity or 'Not set'}")
    logger.info(f"AI Model: {settings.ai_model or 'Not set'}")
    logger.info(f"Supervisor URL: {settings.supervisor_url}")
    
    # Check for frontend files
    logger.info("Checking for frontend files...")
    if os.path.exists(frontend_dir):
        for filename in ["index.html", "style.css", "app.js"]:
            filepath = os.path.join(frontend_dir, filename)
            exists = os.path.exists(filepath)
            logger.info(f"  {filename}: {'✓' if exists else '✗'}")
    else:
        logger.error(f"Frontend directory does not exist: {frontend_dir}")
    
    # Pydantic validates on instantiation, so no need to call validate() here.
    # If there's a config error, it will raise an exception and prevent startup.
    logger.info("Essential configuration is valid.")
    logger.info("--- Startup Complete ---")

if __name__ == "__main__":
    import uvicorn
    
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting AI Room Cleaner on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")