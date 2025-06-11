import base64
import httpx
import logging
from backend.core.config import settings
from backend.core.exceptions import CameraError, ConfigError

logger = logging.getLogger(__name__)

async def get_camera_image() -> str:
    """
    Fetches the image from the specified Home Assistant camera entity.
    Raises:
        ConfigError: If required configuration is missing.
        CameraError: If the image cannot be fetched.
    """
    if not settings.camera_entity or not settings.supervisor_token:
        raise ConfigError("Camera entity or supervisor token is not configured.")

    api_url = f"{settings.supervisor_url}/camera_proxy/{settings.camera_entity}"
    headers = {"Authorization": f"Bearer {settings.supervisor_token}"}

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching camera image from: {api_url}")
            response = await client.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            
            logger.info("Successfully fetched camera image.")
            return base64.b64encode(response.content).decode("utf-8")
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching image: {e.response.status_code} - {e.response.text}")
        raise CameraError(f"Failed to fetch camera image: {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.error(f"Request error getting camera image: {e}")
        raise CameraError(f"Failed to connect to camera: {e}") from e