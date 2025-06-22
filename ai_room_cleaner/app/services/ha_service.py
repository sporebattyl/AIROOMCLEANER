import httpx
from app.core.config import settings
from app.core.exceptions import HomeAssistantAPIError
from app.core.logging import log

class HomeAssistantService:
    def __init__(self):
        self.supervisor_token = settings.SUPERVISOR_TOKEN
        self.base_url = "http://supervisor/core/api"
        self.headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method, f"{self.base_url}{endpoint}", headers=self.headers, **kwargs
                )
                response.raise_for_status()
                if response.content:
                    return response.json()
                return {}
            except httpx.HTTPStatusError as e:
                log.error(f"HTTP error calling HA API: {e.response.status_code} - {e.response.text}")
                raise HomeAssistantAPIError(f"Error calling Home Assistant API: {e.response.text}")
            except Exception as e:
                log.error(f"An unexpected error occurred calling HA API: {e}")
                raise HomeAssistantAPIError(f"An unexpected error occurred: {e}")

    async def set_entity_state(self, entity_id: str, state: str, attributes: dict):
        log.info(f"Setting state for {entity_id}")
        payload = {"state": state, "attributes": attributes}
        await self._request("POST", f"/states/{entity_id}", json=payload)

    async def get_todo_list_items(self, entity_id: str) -> list:
        log.info(f"Getting items from to-do list {entity_id}")
        response = await self._request("GET", f"/todo/items/{entity_id}")
        return response or []

    async def create_todo_list_item(self, entity_id: str, item: str):
        log.info(f"Adding '{item}' to to-do list {entity_id}")
        await self._request("POST", f"/todo/items/{entity_id}", json={"item": item})

    async def clear_todo_list(self, entity_id: str):
        log.info(f"Clearing to-do list {entity_id}")
        items = await self.get_todo_list_items(entity_id)
        for item in items:
            uid = item.get("uid")
            if uid:
                await self._request("DELETE", f"/todo/items/{entity_id}/{uid}")
