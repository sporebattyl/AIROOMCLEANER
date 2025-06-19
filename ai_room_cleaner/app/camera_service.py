from app.ha_service import HomeAssistantService

class CameraService:
    """Service for fetching images from Home Assistant cameras."""

    def __init__(self, ha_service: HomeAssistantService):
        self.ha_service = ha_service

    def get_image(self, entity_id: str) -> bytes:
        """Gets the latest image from the specified camera entity."""
        return self.ha_service.get_camera_image(entity_id)
