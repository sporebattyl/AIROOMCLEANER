from app.services.ha_service import HomeAssistantService
from app.core.config import settings

class CameraService:
    """
    Service for interacting with cameras in Home Assistant.
    """

    def __init__(self, ha_service: HomeAssistantService):
        self.ha_service = ha_service

    def get_image(self, camera_entity_id: str) -> bytes:
        """
        Gets an image from the specified camera.
        """
        image_data = self.ha_service.call_service(
            "camera", "snapshot", {"entity_id": camera_entity_id}
        )
        if not image_data:
            raise Exception("Failed to get image from camera")
        return image_data
