import datetime
from loguru import logger
import httpx
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.api.constants import ANALYZE_ROUTE
from backend.core.config import settings
from backend.core.state import State
from backend.core.exceptions import AppException, AIError, CameraError, ConfigError

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health")
async def health_check(request: Request):
    """Comprehensive health check for the service and its dependencies."""
    state: State = request.app.state.state
    health_data = {
        "status": "healthy",
        "service": "AI Room Cleaner",
        "timestamp": datetime.datetime.now().isoformat(),
        "dependencies": {},
    }

    # Check AI Service Connectivity
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.AI_API_ENDPOINT)
            response.raise_for_status()
            health_data["dependencies"]["ai_service"] = {"status": "ok"}
    except httpx.RequestError as e:
        health_data["dependencies"]["ai_service"] = {
            "status": "error",
            "error": f"Failed to connect to AI service: {e}",
        }
        health_data["status"] = "degraded"

    return health_data


@router.post(ANALYZE_ROUTE)
@limiter.limit("10/minute")
async def analyze_room_secure(request: Request, image: UploadFile = File(...)):
    """
    Securely proxies image analysis requests to the external AI service.
    This endpoint uses the centrally managed API key from the settings.
    """
    logger.info("Received request for secure room analysis")

    # Validate image type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or missing content type: {image.content_type}. Must be an image.",
        )

    try:
        api_key = settings.AI_API_KEY.get_secret_value()
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"image": (image.filename, await image.read(), image.content_type)}

        async with httpx.AsyncClient() as client:
            logger.info(f"Proxying request to {settings.AI_API_ENDPOINT}")
            response = await client.post(
                settings.AI_API_ENDPOINT, headers=headers, files=files
            )
            response.raise_for_status()
            logger.info("Successfully received response from AI service")
            return JSONResponse(content=response.json(), status_code=response.status_code)

    except httpx.HTTPStatusError as e:
        logger.error(f"Error from AI service: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code, detail="Error from AI service"
        )
    except Exception as e:
        logger.exception("An unexpected error occurred during secure analysis")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred."
        )