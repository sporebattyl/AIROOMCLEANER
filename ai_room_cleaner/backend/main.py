import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.router import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Room Cleaner", version="0.1.0")

# Add CORS middleware for Home Assistant ingress
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    try:
        settings.validate()
        logger.info("Essential configuration is valid.")
    except ValueError as e:
        logger.warning(f"Configuration validation failed on startup: {e}")
    logger.info("--- Startup Complete ---")

if __name__ == "__main__":
    import uvicorn
    
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting AI Room Cleaner on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")