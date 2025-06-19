import time
import json
from core.config import settings
from services.ai_service import AIService
from services.camera_service import CameraService
from services.ha_service import HomeAssistantService
from services.history_service import HistoryService
from dependencies import get_ai_service, get_camera_service, get_ha_service, get_history_service
import asyncio

async def main():
    """Main application loop."""
    ha_service = get_ha_service()
    camera_service = get_camera_service()
    ai_service = get_ai_service()
    history_service = get_history_service()

    # Create sensor entities
    ha_service.set_state(f"sensor.ai_room_cleaner_cleanliness_score", "0", {"unit_of_measurement": "%"})
    ha_service.set_state(f"sensor.ai_room_cleaner_last_analysis", "Never", {})

    try:
        print("Analyzing room...")
        image_data = camera_service.get_image(settings.CAMERA_ENTITY)
        analysis_result = await ai_service.analyze_image(image_data)
        
        score = analysis_result.get("cleanliness_score", 0)
        tasks = analysis_result.get("todo_list", [])

        # Update sensors
        ha_service.set_state(f"sensor.ai_room_cleaner_cleanliness_score", str(score), {"unit_of_measurement": "%"})
        ha_service.set_state(f"sensor.ai_room_cleaner_last_analysis", time.strftime("%Y-%m-%d %H:%M:%S"), {})
        history_service.add_to_history(analysis_result)

        # Update to-do list
        todo_entity_id = f"todo.{settings.TODO_LIST_NAME.lower().replace(' ', '_')}"
        try:
            # Get current tasks from Home Assistant
            current_items_response = ha_service.call_service("todo", "get_items", {"entity_id": todo_entity_id})
            if current_items_response:
                current_items = current_items_response.get(todo_entity_id, {}).get('items', [])
                if not isinstance(current_items, list):
                    current_items = []
                current_tasks_map = {item['summary']: item for item in current_items}
            else:
                current_items = []
                current_tasks_map = {}

            # Add new tasks
            for task in tasks:
                if task not in current_tasks_map:
                    ha_service.call_service("todo", "add_item", {"item": task, "entity_id": todo_entity_id})

            # Mark completed tasks
            for summary, item in current_tasks_map.items():
                if summary not in tasks and item['status'] == 'needs_action':
                    ha_service.call_service("todo", "update_item", {
                        "uid": item['uid'],
                        "entity_id": todo_entity_id,
                        "status": "completed"
                    })
        except Exception as e:
            print(f"Error updating to-do list: {e}")


        print(f"Analysis complete. Score: {score}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
