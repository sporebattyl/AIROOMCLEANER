from typing import Dict, Any
import httpx
from app.core.config import settings
from app.core.exceptions import HomeAssistantError

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

    def get_state(self, entity_id: str) -> Dict[str, Any]:
        """
        Gets the state of an entity in Home Assistant.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{settings.SUPERVISOR_URL}/api/states/{entity_id}",
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HomeAssistantError(f"Error getting state for {entity_id}: {e}") from e

    def set_state(self, entity_id: str, state: str, attributes: Dict[str, Any]):
        """
        Sets the state of an entity in Home Assistant.
        """
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{settings.SUPERVISOR_URL}/api/states/{entity_id}",
                    headers=self.headers,
                    json={"state": state, "attributes": attributes},
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HomeAssistantError(f"Error setting state for {entity_id}: {e}") from e

    def call_service(self, domain: str, service: str, service_data: Dict[str, Any]):
        """
        Calls a service in Home Assistant.
        """
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{settings.SUPERVISOR_URL}/api/services/{domain}/{service}",
                    headers=self.headers,
                    json=service_data,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HomeAssistantError(f"Error calling service {domain}.{service}: {e}") from e
