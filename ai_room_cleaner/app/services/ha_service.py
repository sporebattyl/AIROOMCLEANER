from typing import Dict, Any
import httpx
from core.config import settings

class HomeAssistantService:
    """
    Service for interacting with the Home Assistant API.
    """

    def __init__(self):
        token = settings.SUPERVISOR_TOKEN.get_secret_value() if settings.SUPERVISOR_TOKEN else ""
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def set_state(self, entity_id: str, state: str, attributes: Dict[str, Any]):
        """
        Sets the state of an entity in Home Assistant.
        """
        with httpx.Client() as client:
            client.post(
                f"{settings.SUPERVISOR_URL}/api/states/{entity_id}",
                headers=self.headers,
                json={"state": state, "attributes": attributes},
            )

    def call_service(self, domain: str, service: str, service_data: Dict[str, Any]):
        """
        Calls a service in Home Assistant.
        """
        with httpx.Client() as client:
            client.post(
                f"{settings.SUPERVISOR_URL}/api/services/{domain}/{service}",
                headers=self.headers,
                json=service_data,
            )