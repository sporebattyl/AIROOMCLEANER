"""
API router for the AI Room Cleaner backend.
"""
import datetime

import httpx
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    Security,
    UploadFile,
)
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import SecretStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from .constants import (
    ALLOWED_MIME_TYPES,
    ANALYZE_ROUTE,
)
from ..core.config import get_settings
from ..core.exceptions import (
    AIProviderError,
    AppException,
    ConfigError,
    ImageProcessingError,
    InvalidFileTypeError,
)
from ..core.state import get_state
from ..services.ai_service import AIService
from ..services.history_service import HistoryService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_scheme)):
    """Validates the API key from the X-API-KEY header."""
    settings = get_settings()
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="API key not configured on server")

    settings_api_key: SecretStr = settings.api_key
    if not api_key or api_key != settings_api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    return api_key

# Dependency to get the shared httpx client
def get_http_client(request: Request) -> httpx.AsyncClient:
    """Returns the shared httpx.AsyncClient instance."""
    return request.app.state.http_client


@router.get("/config")
async def get_frontend_config(_: str = Security(get_api_key)):
    """Provides frontend configuration."""
    settings = get_settings()
    return {
        "apiKey": settings.api_key.get_secret_value() if settings.api_key else None,
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": settings.AI_MODEL,
        "max_image_size_mb": settings.MAX_IMAGE_SIZE_MB,
        "max_image_dimension": settings.MAX_IMAGE_DIMENSION,
    }


@router.get("/health")
async def health_check():
    """Comprehensive health check for the service and its dependencies."""
    state = get_state()
    if not state.ai_service:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    ai_service: AIService = state.ai_service
    health_data = {
        "status": "healthy",
        "service": "AI Room Cleaner",
        "timestamp": datetime.datetime.now().isoformat(),
        "dependencies": {"ai_service": await ai_service.health_check()},
    }

    if health_data["dependencies"]["ai_service"]["status"] != "ok":
        health_data["status"] = "degraded"

    return health_data


@router.post(ANALYZE_ROUTE)
@limiter.limit("10/minute")
async def analyze_room_secure(
    file: UploadFile = File(...), _: str = Security(get_api_key)
):
    """
    Securely analyzes an image by streaming it to the AI service.
    This endpoint avoids loading the entire file into memory.
    """
    logger.info("Received request for secure room analysis")
    state = get_state()
    if not state.ai_service:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    ai_service: AIService = state.ai_service

    # Validate image type by checking the filename extension
    if not file.filename:
        raise InvalidFileTypeError("File has no name.")

    file_extension = file.filename.split(".")[-1].lower()
    if f"image/{file_extension}" not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError(
            f"Invalid file type: {file.filename}. "
            f"Allowed types are: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    try:
        # The AI service now handles the upload file directly, streaming it to avoid
        # loading the entire file into memory. This is more memory-efficient.
        result = await ai_service.analyze_image_from_upload(upload_file=file)
        return JSONResponse(content=result)

    except (
        AIProviderError,
        ConfigError,
        ImageProcessingError,
        InvalidFileTypeError,
    ) as e:
        logger.error(f"Service error during analysis: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred during secure analysis")
        raise AppException(
            status_code=500, detail="An unexpected error occurred."
        ) from e


@router.get("/history")
async def get_history():
    """Returns the analysis history."""
    state = get_state()
    if not state.history_service:
        raise HTTPException(status_code=500, detail="History service not initialized")
    history_service: HistoryService = state.history_service
    return await history_service.get_history()


@router.delete("/history")
async def clear_history(_: str = Security(get_api_key)):
    """Clears the analysis history."""
    state = get_state()
    if not state.history_service:
        raise HTTPException(status_code=500, detail="History service not initialized")
    history_service: HistoryService = state.history_service
    await history_service.clear_history()
    return {"message": "History cleared successfully."}
