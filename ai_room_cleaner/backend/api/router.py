import logging
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from backend.core.config import settings
from backend.core.state import app_state
from backend.services.ai_service import analyze_room_for_mess
from backend.services.camera_service import get_camera_image
from backend.core.exceptions import AIError, CameraError, ConfigError

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Room Cleaner"}

@router.get("/tasks")
async def get_tasks():
    """Get the current list of cleaning tasks"""
    return app_state.get_tasks()

@router.post("/analyze")
async def analyze_room():
    """Analyze the room for messes using AI"""
    try:
        logger.info("=== Starting room analysis ===")
        settings.validate()
        
        logger.info("Attempting to get camera image...")
        image_base64 = await get_camera_image()
        logger.info(f"Successfully retrieved camera image (length: {len(image_base64)} characters)")
        
        logger.info("Starting AI analysis in a background thread...")
        messes = await run_in_threadpool(analyze_room_for_mess, image_base64)
        logger.info(f"Analysis complete. Found {len(messes)} items: {messes}")
        
        app_state.set_tasks(messes)
        
        return {"tasks": messes, "count": len(messes)}
        
    except (ConfigError, CameraError, AIError) as e:
        logger.error(f"Error during room analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")