import time
import json
from .config import get_config
from .ai_service import AIService
from .camera_service import CameraService
from .ha_service import HomeAssistantService

def main():
    """Main application loop."""
    config = get_config()
    ha_service = HomeAssistantService()
    camera_service = CameraService(ha_service)
    ai_service = AIService(config)

    # Create sensor entities
    ha_service.set_state(f"sensor.ai_room_cleaner_cleanliness_score", "0", {"unit_of_measurement": "%"})
    ha_service.set_state(f"sensor.ai_room_cleaner_last_analysis", "Never", {})

    while True:
        try:
            print("Analyzing room...")
            image_data = camera_service.get_image(config.camera_entity_id)
            analysis_result = ai_service.analyze_image(image_data)
            
            score = analysis_result.get("cleanliness_score", 0)
            tasks = analysis_result.get("todo_list", [])

            # Update sensors
            ha_service.set_state(f"sensor.ai_room_cleaner_cleanliness_score", str(score), {"unit_of_measurement": "%"})
            ha_service.set_state(f"sensor.ai_room_cleaner_last_analysis", time.strftime("%Y-%m-%d %H:%M:%S"), {})

            # Update to-do list
            todo_entity_id = f"todo.{config.todo_list_name.lower().replace(' ', '_')}"
            try:
                # Get current tasks from Home Assistant
                current_items_response = ha_service.call_service("todo", "get_items", {"entity_id": todo_entity_id})
                current_items = current_items_response.get(todo_entity_id, {}).get('items', [])
                current_tasks_map = {item['summary']: item for item in current_items}

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

        print(f"Waiting for {config.recheck_interval_minutes} minutes...")
        time.sleep(config.recheck_interval_minutes * 60)

if __name__ == "__main__":
    main()