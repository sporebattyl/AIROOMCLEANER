import os
from typing import Dict, Any
import httpx
from app.core.exceptions import HomeAssistantError

class HomeAssistantService:
    """
    Service for interacting with the Home Assistant API.
    """

    def __init__(self):
        # Ensure the Supervisor token is correctly set for authorization
        self.base_url = "http://supervisor/core/api"
        token = os.getenv("SUPERVISOR_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)

    async def get_state(self, entity_id: str) -> Dict[str, Any]:
        """
        Gets the state of an entity in Home Assistant.
        """
        try:
            response = await self.client.get(f"/states/{entity_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HomeAssistantError(f"Error getting state for {entity_id}: {e}") from e

    async def set_state(self, entity_id: str, state: str, attributes: Dict[str, Any]):
        """
        Sets the state of an entity in Home Assistant.
        """
        try:
            response = await self.client.post(
                f"/states/{entity_id}",
                json={"state": state, "attributes": attributes},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HomeAssistantError(f"Error setting state for {entity_id}: {e}") from e

    async def call_service(self, domain: str, service: str, service_data: Dict[str, Any]):
        """
        Calls a service in Home Assistant.
        """
        try:
            response = await self.client.post(
                f"/services/{domain}/{service}",
                json=service_data,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HomeAssistantError(f"Error calling service {domain}.{service}: {e}") from e
