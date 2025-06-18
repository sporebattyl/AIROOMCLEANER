import os
import httpx

class HomeAssistantService:
    """Service for interacting with the Home Assistant API."""

    def __init__(self):
        self.supervisor_token = os.getenv("SUPERVISOR_TOKEN")
        self.base_url = "http://supervisor/core/api"
        self.headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json",
        }

    def get_camera_image(self, entity_id: str) -> bytes:
        """Fetches the latest image from a camera entity."""
        url = f"{self.base_url}/camera_proxy/{entity_id}"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        return response.content

    def update_todo_list(self, list_name: str, tasks: list[str]):
        """Updates a to-do list with a new set of tasks."""
        # This will be implemented later.
        pass

    def update_sensor(self, entity_id: str, state: str, attributes: dict):
        """Updates the state and attributes of a sensor."""
        # This will be implemented later.
        pass