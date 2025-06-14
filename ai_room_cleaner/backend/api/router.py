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
    """Comprehensive health check for service and dependencies."""
    state: State = request.app.state.state
    health_data = {
        "status": "healthy",
        "service": "AI Room Cleaner",
        "timestamp": datetime.datetime.now().isoformat(),
        "dependencies": {}
    }
    
    overall_healthy = True
    
    # Check AI service
    try:
        ai_health = await state.ai_service.health_check()
        health_data["dependencies"]["ai_service"] = ai_health
        if ai_health["status"] != "ok":
            overall_healthy = False
    except Exception as e:
        health_data["dependencies"]["ai_service"] = {
            "status": "error",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check camera connectivity
    try:
        settings = get_settings()
        if settings.camera_entity:
            # Quick camera connectivity test
            await get_camera_image(settings.camera_entity, settings)
            health_data["dependencies"]["camera"] = {"status": "ok"}
        else:
            health_data["dependencies"]["camera"] = {
                "status": "not_configured",
                "error": "Camera entity not configured"
            }
    except Exception as e:
        health_data["dependencies"]["camera"] = {
            "status": "error",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check file system
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"health_check")
        health_data["dependencies"]["filesystem"] = {"status": "ok"}
    except Exception as e:
        health_data["dependencies"]["filesystem"] = {
            "status": "error",
            "error": str(e)
        }
        overall_healthy = False
    
    health_data["status"] = "healthy" if overall_healthy else "degraded"
    
    return health_data

@router.get("/history")
async def get_history(request: Request):
    """Get the analysis history"""
    state: State = request.app.state.state
    return state.get_history()

from pydantic import BaseModel, Field
from typing import Optional

class AnalyzeRequest(BaseModel):
    """Optional request body for analysis endpoint."""
    camera_override: Optional[str] = Field(None, description="Override default camera entity")
    max_items: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of mess items to return")

@router.post("/analyze")
@limiter.limit("3/minute")  # Reduced from 5 to 3 for more conservative limiting
async def analyze_room(
    request: Request,
    body: Optional[AnalyzeRequest] = None
):
    """Analyze the room for messes using AI with enhanced validation."""
    logger.info("=== Starting room analysis ===")
    
    # Add request validation
    if body and body.camera_override:
        # Validate camera entity format
        if not body.camera_override.startswith('camera.'):
            raise HTTPException(
                status_code=400,
                detail="Camera entity must start with 'camera.'"
            )
    
    try:
        state: State = request.app.state.state
        settings = get_settings()

        camera_entity = (body.camera_override if body and body.camera_override
                        else settings.camera_entity)
        
        if not camera_entity:
            raise ConfigError("Camera entity ID is not configured.")

        logger.info("Attempting to get camera image...")
        image_base64 = await get_camera_image(camera_entity, settings)
        if not image_base64 or len(image_base64) < 100:
            raise CameraError("Received empty or invalid image data from camera.")
        logger.info(f"Successfully retrieved camera image (length: {len(image_base64)} characters)")
        
        logger.info("Starting AI analysis in a background thread...")
        messes = await state.ai_service.analyze_room_for_mess(image_base64)
        logger.info(f"Analysis complete. Found {len(messes)} items: {messes}")
        
        # Limit number of returned items
        max_items = body.max_items if body and body.max_items is not None else 10
        if len(messes) > max_items:
            logger.info(f"Limiting results from {len(messes)} to {max_items} items")
            messes = messes[:max_items]

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