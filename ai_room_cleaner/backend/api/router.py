import datetime
import magic
import secrets
from loguru import logger
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Security
from fastapi.responses import JSONResponse
import anyio
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.api.constants import ANALYZE_ROUTE, ALLOWED_MIME_TYPES, MIME_TYPE_CHUNK_SIZE
from backend.core.config import get_settings
from backend.core.state import get_state
from backend.core.exceptions import (
    AIProviderError,
    AppException,
    CameraError,
    ConfigError,
    ImageProcessingError,
    InvalidFileTypeError,
)
from backend.services.ai_service import AIService
from backend.services.history_service import HistoryService
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_scheme)):
    """Validates the API key from the X-API-KEY header."""
    if not api_key or api_key != get_settings().api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    return api_key


# Dependency to get the shared httpx client
def get_http_client(request: Request) -> httpx.AsyncClient:
    """Returns the shared httpx.AsyncClient instance."""
    return request.app.state.http_client


@router.get("/config")
async def get_frontend_config(request: Request, api_key: str = Security(get_api_key)):
    """Provides frontend configuration, including the API key."""
    return {"apiKey": get_settings().api_key.get_secret_value()}


@router.get("/health")
async def health_check(
    request: Request, client: httpx.AsyncClient = Depends(get_http_client)
):
    """Comprehensive health check for the service and its dependencies."""
    ai_service: AIService = get_state().ai_service
    health_data = {
        "status": "healthy",
        "service": "AI Room Cleaner",
        "timestamp": datetime.datetime.now().isoformat(),
        "dependencies": {
            "ai_service": await ai_service.health_check()
        },
    }

    if health_data["dependencies"]["ai_service"]["status"] != "ok":
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
    ai_service: AIService = get_state().ai_service

    # Validate image type by reading a small chunk, not the whole file
    chunk = await file.read(MIME_TYPE_CHUNK_SIZE)
    await file.seek(0)  # Reset file pointer for the service to read from the start
    mime_type = await anyio.to_thread.run_sync(lambda: magic.from_buffer(chunk, mime=True))
    if mime_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError(
            f"Invalid file type: {mime_type}. Allowed types are: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    try:
        # The AI service now handles the upload file directly, streaming it to avoid
        # loading the entire file into memory. This is more memory-efficient.
        result = await ai_service.analyze_image_from_upload(upload_file=file)
        return JSONResponse(content=result)

    except (AIProviderError, ConfigError, ImageProcessingError, InvalidFileTypeError) as e:
        logger.error(f"Service error during analysis: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred during secure analysis")
        raise AppException(status_code=500, detail="An unexpected error occurred.")
@router.get("/history")
async def get_history(request: Request):
    """Returns the analysis history."""
    history_service: HistoryService = get_state().history_service
    return await history_service.get_history()


@router.delete("/history")
async def clear_history(request: Request, api_key: str = Security(get_api_key)):
    """Clears the analysis history."""
    history_service: HistoryService = get_state().history_service
    await history_service.clear_history()
    return {"message": "History cleared successfully."}