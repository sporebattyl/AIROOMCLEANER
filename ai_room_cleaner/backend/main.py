import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from backend.services.ai_service import analyze_room_for_mess
from backend.services.camera_service import get_camera_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Room Cleaner", version="0.1.0")

# Store the latest analysis results
latest_tasks = []

# Mount static files (frontend)
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/static", StaticFiles(directory=static_files_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page"""
    try:
        with open(os.path.join(static_files_path, "index.html")) as f:
            content = f.read()
        # Fix the static file paths in the HTML
        content = content.replace('href="/static/style.css"', 'href="/static/style.css"')
        content = content.replace('src="/static/app.js"', 'src="/static/app.js"')
        return content
    except FileNotFoundError:
        logger.error(f"index.html not found at {static_files_path}")
        return HTMLResponse(content="<h1>Frontend files not found</h1>", status_code=500)

# Add explicit routes for CSS and JS files to help with debugging
@app.get("/style.css")
async def serve_css():
    """Serve CSS file directly"""
    css_path = os.path.join(static_files_path, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    else:
        logger.error(f"CSS file not found at {css_path}")
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/app.js")
async def serve_js():
    """Serve JS file directly"""
    js_path = os.path.join(static_files_path, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    else:
        logger.error(f"JS file not found at {js_path}")
        raise HTTPException(status_code=404, detail="JS file not found")

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

# Add a startup event to log file paths for debugging
@app.on_event("startup")
async def startup_event():
    logger.info(f"Static files directory: {static_files_path}")
    logger.info(f"Frontend files exist:")
    for filename in ["index.html", "style.css", "app.js"]:
        filepath = os.path.join(static_files_path, filename)
        exists = os.path.exists(filepath)
        logger.info(f"  {filename}: {'✓' if exists else '✗'} ({filepath})")

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