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

    def call_service(self, domain: str, service: str, data: dict):
        """Calls a service in Home Assistant."""
        url = f"{self.base_url}/services/{domain}/{service}"
        response = httpx.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def set_state(self, entity_id: str, state: str, attributes: dict):
        """Sets the state and attributes of an entity."""
        url = f"{self.base_url}/states/{entity_id}"
        payload = {"state": state, "attributes": attributes}
        response = httpx.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
