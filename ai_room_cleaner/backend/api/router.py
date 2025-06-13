import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.config import settings
from backend.core.state import app_state
from backend.services.ai_service import analyze_room_for_mess
from backend.services.camera_service import get_camera_image
from backend.core.exceptions import AppException, AIError, CameraError, ConfigError

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Room Cleaner"}

@router.get("/tasks")
async def get_tasks():
    """Get the current list of cleaning tasks"""
    return await app_state.get_tasks()

@router.post("/analyze")
@limiter.limit("5/minute")
async def analyze_room(request: Request):
    """Analyze the room for messes using AI"""
    logger.info("=== Starting room analysis ===")

    if not settings.camera_entity:
        raise ConfigError(detail="Camera entity ID is not configured.")

    logger.info("Attempting to get camera image...")
    image_base64 = await get_camera_image(settings.camera_entity)
    logger.info(f"Successfully retrieved camera image (length: {len(image_base64)} characters)")
    
    logger.info("Starting AI analysis in a background thread...")
    messes = await run_in_threadpool(analyze_room_for_mess, image_base64)
    logger.info(f"Analysis complete. Found {len(messes)} items: {messes}")
    
    await app_state.set_tasks(messes)
    
    # Calculate a simple cleanliness score based on number of messes
    total_possible_score = 100
    mess_penalty = min(len(messes) * 10, 80)  # Max 80 point penalty
    cleanliness_score = max(total_possible_score - mess_penalty, 20)  # Min score of 20
    
    return {
        "tasks": messes,
        "cleanliness_score": cleanliness_score
    }