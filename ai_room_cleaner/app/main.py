import asyncio
import time
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.ai_service import AIService
from app.services.camera_service import CameraService
from app.services.ha_service import HomeAssistantService
from app.services.history_service import HistoryService
from app.dependencies import get_ai_service, get_camera_service, get_ha_service, get_history_service
from app.core.exceptions import AIError, CameraError, HomeAssistantError

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ha_service = get_ha_service()
    slug = settings.SLUG
    ha_service.set_state(f"sensor.{slug}_cleanliness_score", "0", {"unit_of_measurement": "%"})
    ha_service.set_state(f"sensor.{slug}_last_analysis", "Never", {})
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

async def analyze_room_task():
    """Background task to analyze the room."""
    ha_service = get_ha_service()
    camera_service = get_camera_service()
    ai_service = get_ai_service()
    history_service = get_history_service()
    slug = settings.SLUG

    while True:
        try:
            image_data = camera_service.get_image(settings.CAMERA_ENTITY_ID)
            analysis_result = await ai_service.analyze_image(image_data)

            score = analysis_result.get("cleanliness_score", 0)
            tasks = analysis_result.get("todo_list", [])

            # Update sensors
            ha_service.set_state(f"sensor.{slug}_cleanliness_score", str(score), {"unit_of_measurement": "%"})
            ha_service.set_state(f"sensor.{slug}_last_analysis", time.strftime("%Y-%m-%d %H:%M:%S"), {})
            history_service.add_to_history(analysis_result)

            # Update to-do list
            todo_entity_id = settings.TODO_LIST_ENTITY_ID
            # Clear existing items
            ha_service.call_service("todo", "remove_item", {"entity_id": todo_entity_id, "item": "all"})
            # Add new items
            for task in tasks:
                ha_service.call_service("todo", "add_item", {"item": task, "entity_id": todo_entity_id})

        except (AIError, CameraError, HomeAssistantError) as e:
            print(f"An error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        await asyncio.sleep(settings.RECHECK_INTERVAL_MINUTES * 60)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(analyze_room_task())

@app.get("/health")
async def health_check():
    return {"status": "ok"}
