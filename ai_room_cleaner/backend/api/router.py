import datetime
import magic
from loguru import logger
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.api.constants import ANALYZE_ROUTE, ALLOWED_MIME_TYPES
from backend.core.config import settings
from backend.core.state import State
from backend.core.exceptions import (
    AIProviderError,
    AppException,
    CameraError,
    ConfigError,
    ImageProcessingError,
    InvalidFileTypeError,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Dependency to get the shared httpx client
def get_http_client(request: Request) -> httpx.AsyncClient:
    """Returns the shared httpx.AsyncClient instance."""
    return request.app.state.http_client


@router.get("/health")
async def health_check(
    request: Request, client: httpx.AsyncClient = Depends(get_http_client)
):
    """Comprehensive health check for the service and its dependencies."""
    state: State = request.app.state.state
    health_data = {
        "status": "healthy",
        "service": "AI Room Cleaner",
        "timestamp": datetime.datetime.now().isoformat(),
        "dependencies": {},
    }

    # Check AI Service Connectivity
    if not settings.AI_API_ENDPOINT:
        health_data["dependencies"]["ai_service"] = {
            "status": "error",
            "error": "AI_API_ENDPOINT is not configured.",
        }
        health_data["status"] = "degraded"
    else:
        try:
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
async def analyze_room_secure(
    request: Request,
    image: UploadFile = File(...),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Securely proxies image analysis requests to the external AI service.
    This endpoint uses the centrally managed API key from the settings.
    """
    logger.info("Received request for secure room analysis")

    # Validate image type
    content = await image.read()
    await image.seek(0)
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError(
            f"Invalid file type: {mime_type}. Allowed types are: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    try:
        if not settings.AI_API_KEY:
            raise ConfigError("AI_API_KEY is not configured.")
        if not settings.AI_API_ENDPOINT:
            raise ConfigError("AI_API_ENDPOINT is not configured.")

        api_key = settings.AI_API_KEY.get_secret_value()
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"image": (image.filename, content, image.content_type)}

        logger.info(f"Proxying request to {settings.AI_API_ENDPOINT}")
        response = await client.post(
            settings.AI_API_ENDPOINT, headers=headers, files=files
        )
        response.raise_for_status()
        logger.info("Successfully received response from AI service")
        return JSONResponse(content=response.json(), status_code=response.status_code)

    except httpx.HTTPStatusError as e:
        logger.error(f"Error from AI service: {e.response.status_code} - {e.response.text}")
        raise AIProviderError(detail="Error from AI service")
    except ConfigError as e:
        logger.error(f"Configuration error: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred during secure analysis")
        raise AppException(status_code=500, detail="An unexpected error occurred.")