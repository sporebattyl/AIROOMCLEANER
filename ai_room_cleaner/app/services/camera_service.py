import httpx
from app.core.config import settings
from app.core.exceptions import CameraError
from app.core.logging import log

class CameraService:
    def __init__(self):
        self.supervisor_token = settings.SUPERVISOR_TOKEN
        self.base_url = "http://supervisor/core/api"
        self.camera_entity_id = settings.CAMERA_ENTITY
        self.headers = {"Authorization": f"Bearer {self.supervisor_token}"}

    async def get_camera_image(self) -> bytes:
        log.info(f"Fetching image from camera entity: {self.camera_entity_id}")
        url = f"{self.base_url}/camera_proxy/{self.camera_entity_id}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                log.error(f"Failed to get camera image: {e.response.status_code} - {e.response.text}")
                raise CameraError(f"Could not retrieve camera image for {self.camera_entity_id}")
            except Exception as e:
                log.error(f"An unexpected error occurred fetching camera image: {e}")
                raise CameraError(f"An unexpected error occurred: {e}")
