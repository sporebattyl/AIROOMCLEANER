import datetime
from loguru import logger
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.config import get_settings
from backend.core.state import State
from backend.services.camera_service import get_camera_image
from backend.core.exceptions import AppException, AIError, CameraError, ConfigError

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint for the service and its dependencies."""
    state: State = request.app.state.state
    ai_service_health = await state.ai_service.health_check()
    
    overall_status = "healthy"
    if ai_service_health["status"] != "ok":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "AI Room Cleaner",
        "dependencies": {
            "ai_service": ai_service_health
        }
    }

@router.get("/history")
async def get_history(request: Request):
    """Get the analysis history"""
    state: State = request.app.state.state
    return state.get_history()

@router.post("/analyze")
@limiter.limit("5/minute")
async def analyze_room(request: Request):
    """Analyze the room for messes using AI"""
    logger.info("=== Starting room analysis ===")
    try:
        state: State = request.app.state.state
        settings = get_settings()

        if not settings.camera_entity:
            raise ConfigError("Camera entity ID is not configured.")

        logger.info("Attempting to get camera image...")
        image_base64 = await get_camera_image(settings.camera_entity, settings)
        if not image_base64 or len(image_base64) < 100:
            raise CameraError("Received empty or invalid image data from camera.")
        logger.info(f"Successfully retrieved camera image (length: {len(image_base64)} characters)")
        
        logger.info("Starting AI analysis in a background thread...")
        messes = await state.ai_service.analyze_room_for_mess(image_base64)
        logger.info(f"Analysis complete. Found {len(messes)} items: {messes}")
        
        total_possible_score = 100
        mess_penalty = min(len(messes) * 10, 80)
        cleanliness_score = max(total_possible_score - mess_penalty, 20)

        analysis_result = {
            "id": datetime.datetime.now().isoformat(),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks": messes,
            "cleanliness_score": cleanliness_score
        }

        await state.add_analysis_to_history(analysis_result)
        
        return analysis_result
    except ConfigError as e:
        logger.error(f"Configuration error during analysis: {e.detail}")
        raise HTTPException(status_code=400, detail=e.detail)
    except CameraError as e:
        logger.error(f"Camera error during analysis: {e.detail}")
        raise HTTPException(status_code=502, detail=e.detail) # 502 Bad Gateway
    except AIError as e:
        logger.error(f"AI service error during analysis: {e.detail}")
        raise HTTPException(status_code=503, detail=e.detail) # 503 Service Unavailable
    except AppException as e:
        logger.error(f"An application error occurred during analysis: {e.detail}")
        raise e  # Re-raise to be handled by the global handler
    except Exception as e:
        logger.exception("An unexpected error occurred during room analysis.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during analysis.")