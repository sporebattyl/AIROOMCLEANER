import datetime
import magic
from loguru import logger
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Security
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_executor
from fastapi.security import APIKeyHeader
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
from backend.services.ai_service import AIService
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_scheme)):
    """Validates the API key from the X-API-KEY header."""
    if not api_key:
        # 401 Unauthorized: The client must authenticate itself to get the requested response.
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    # In a real-world scenario, you would validate the key against a database
    # or a secrets manager. For this example, we just check for its presence.
    return api_key


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
    file: UploadFile = File(...),
    api_key: str = Security(get_api_key),
):
    """
    Securely analyzes an image by streaming it to the AI service.
    This endpoint avoids loading the entire file into memory.
    """
    logger.info("Received request for secure room analysis")
    ai_service: AIService = request.app.state.state.ai_service

    # Validate image type by reading a small chunk, not the whole file
    chunk = await file.read(2048)
    await file.seek(0)  # Reset file pointer for the service to read from the start
    mime_type = await run_in_executor(None, lambda: magic.from_buffer(chunk, mime=True))
    if mime_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError(
            f"Invalid file type: {mime_type}. Allowed types are: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    try:
        # The AI service now handles API key management and remote calls.
        result = await ai_service.analyze_image_from_upload(upload_file=file)
        return JSONResponse(content=result)

    except (AIProviderError, ConfigError, ImageProcessingError, InvalidFileTypeError) as e:
        logger.error(f"Service error during analysis: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred during secure analysis")
        raise AppException(status_code=500, detail="An unexpected error occurred.")