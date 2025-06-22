from app.services.ha_service import HomeAssistantService
from app.core.config import settings
from app.core.exceptions import CameraError

class CameraService:
    """
    Service for interacting with cameras in Home Assistant.
    """

    def __init__(self, ha_service: HomeAssistantService):
        self.ha_service = ha_service

    async def get_image(self, camera_entity_id: str) -> bytes:
        """
        Gets an image from the specified camera.
        """
        try:
            # Use the camera proxy endpoint to get the actual image data
            image_data = await self.ha_service.get_camera_image(camera_entity_id)
            if not image_data:
                raise CameraError("Failed to get image from camera")
            return image_data
        except Exception as e:
            raise CameraError(f"Error getting camera image: {e}") from e
