import os
import logging
from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from backend.services.ai_service import analyze_room_for_mess
from backend.services.camera_service import get_camera_image
from backend.core.config import settings
from backend.core.exceptions import AIError, CameraError, ConfigError

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

# Store the latest analysis results
latest_tasks = []

# Get the frontend directory path
# Mount the entire frontend directory as static files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Mounted frontend directory: {frontend_dir}")
else:
    logger.error(f"Frontend directory not found at: {frontend_dir}")

# API Router
api_router = APIRouter()

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Room Cleaner"}

@api_router.get("/tasks")
async def get_tasks():
    """Get the current list of cleaning tasks"""
    return latest_tasks

@api_router.post("/analyze")
async def analyze_room():
    """Analyze the room for messes using AI"""
    global latest_tasks
    
    try:
        logger.info("=== Starting room analysis ===")
        
        # Validate essential configuration
        settings.validate()
        
        logger.info("Attempting to get camera image...")
        image_base64 = await get_camera_image()
        logger.info(f"Successfully retrieved camera image (length: {len(image_base64)} characters)")
        
        logger.info("Starting AI analysis in a background thread...")
        messes = await run_in_threadpool(analyze_room_for_mess, image_base64)
        logger.info(f"Analysis complete. Found {len(messes)} items: {messes}")
        
        latest_tasks = messes
        
        return {"tasks": messes, "count": len(messes)}
        
    except (ConfigError, CameraError, AIError) as e:
        logger.error(f"Error during room analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An AI processing error occurred.")
    except HTTPException:
        # Re-raise HTTP exceptions from FastAPI
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")

# Add middleware to log all requests for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Include the API router
app.include_router(api_router, prefix="/api")

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