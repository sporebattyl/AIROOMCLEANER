import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from backend.services.ai_service import analyze_room_for_mess
from backend.services.camera_service import get_camera_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Room Cleaner", version="0.1.0")

# Store the latest analysis results
latest_tasks = []

# Get the frontend directory path
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

def get_frontend_file(filename: str):
    """Helper function to get frontend file path and check if it exists"""
    filepath = os.path.join(frontend_dir, filename)
    logger.info(f"Looking for {filename} at: {filepath}")
    if os.path.exists(filepath):
        logger.info(f"Found {filename}")
        return filepath
    else:
        logger.error(f"File not found: {filepath}")
        return None

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page"""
    filepath = get_frontend_file("index.html")
    if filepath:
        return FileResponse(filepath, media_type="text/html")
    else:
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=500)

@app.get("/style.css")
async def serve_css():
    """Serve CSS file"""
    filepath = get_frontend_file("style.css")
    if filepath:
        return FileResponse(filepath, media_type="text/css")
    else:
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/app.js")
async def serve_js():
    """Serve JS file"""
    filepath = get_frontend_file("app.js")
    if filepath:
        return FileResponse(filepath, media_type="application/javascript")
    else:
        raise HTTPException(status_code=404, detail="JS file not found")

# Also serve from /static/ path for completeness
@app.get("/static/style.css")
async def serve_static_css():
    """Serve CSS file from static path"""
    return await serve_css()

@app.get("/static/app.js")
async def serve_static_js():
    """Serve JS file from static path"""
    return await serve_js()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Room Cleaner"}

@app.get("/api/tasks")
async def get_tasks():
    """Get the current list of cleaning tasks"""
    return latest_tasks

@app.post("/api/analyze")
async def analyze_room():
    """Analyze the room for messes using AI"""
    global latest_tasks
    
    try:
        logger.info("Starting room analysis...")
        
        # Get image from camera
        image_base64 = get_camera_image()
        if not image_base64:
            raise HTTPException(status_code=500, detail="Failed to get camera image")
        
        logger.info("Successfully retrieved camera image")
        
        # Analyze image for messes
        messes = analyze_room_for_mess(image_base64)
        
        logger.info(f"Analysis complete. Found {len(messes)} items")
        
        # Update the stored tasks
        latest_tasks = messes
        
        return messes
        
    except Exception as e:
        logger.error(f"Error during room analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Log startup information and check for frontend files"""
    logger.info(f"Frontend directory: {frontend_dir}")
    logger.info("Checking for frontend files...")
    
    # List all files in the frontend directory
    if os.path.exists(frontend_dir):
        logger.info("Files in frontend directory:")
        for item in os.listdir(frontend_dir):
            item_path = os.path.join(frontend_dir, item)
            if os.path.isfile(item_path):
                logger.info(f"  File: {item}")
            elif os.path.isdir(item_path):
                logger.info(f"  Directory: {item}")
    else:
        logger.error(f"Frontend directory does not exist: {frontend_dir}")
    
    # Check for specific files
    for filename in ["index.html", "style.css", "app.js"]:
        filepath = os.path.join(frontend_dir, filename)
        exists = os.path.exists(filepath)
        logger.info(f"  {filename}: {'✓' if exists else '✗'}")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting AI Room Cleaner on {host}:{port}")
    
    # Log configuration
    camera_entity = os.getenv("CAMERA_ENTITY_ID", "Not set")
    ai_model = os.getenv("AI_MODEL", "Not set")
    logger.info(f"Camera Entity: {camera_entity}")
    logger.info(f"AI Model: {ai_model}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")