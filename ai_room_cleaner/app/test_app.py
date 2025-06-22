import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, patch

# Add the parent directory to the path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Set mock environment variables for testing
os.environ["AI_PROVIDER"] = "google_gemini"
os.environ["GOOGLE_API_KEY"] = "test_api_key"
os.environ["CAMERA_ENTITY_ID"] = "camera.test_camera"
os.environ["RECHECK_INTERVAL_MINUTES"] = "1"
os.environ["TODO_LIST_ENTITY_ID"] = "todo.test_to-do_list"
os.environ["SUPERVISOR_TOKEN"] = "test_supervisor_token"

# Import the task to be tested
from app.main import analyze_room_task
from app.core.config import settings

async def run_test():
    """
    Runs a single iteration of the main application loop with a mocked
    Home Assistant service to validate the core logic.
    """
    print("--- Starting Application Test ---")

    # Create a mock for the HomeAssistantService
    mock_ha_service = AsyncMock()

    # Simulate get_camera_image to return a dummy image (a single black pixel)
    dummy_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf\x00\xff\xd9'
    mock_ha_service.get_camera_image.return_value = dummy_image
    
    # Mock the AI response
    mock_ai_response = {
        "cleanliness_score": 75,
        "todo_list": ["Pick up clothes", "Make the bed"]
    }

    # Use a patch to replace the real services with our mocks
    with patch('app.main.get_ha_service', return_value=mock_ha_service), \
         patch('app.main.get_camera_service') as mock_get_camera_service, \
         patch('app.services.ai_service.AIService.analyze_image', new_callable=AsyncMock, return_value=mock_ai_response), \
         patch('app.main.get_history_service'):

        # Mock the CameraService to return a dummy image
        mock_camera_service_instance = AsyncMock()
        mock_camera_service_instance.get_image.return_value = dummy_image
        mock_get_camera_service.return_value = mock_camera_service_instance

        print("Running one loop of the analyze_room_task...")
        
        # We need to run analyze_room_task in a way that it executes once and exits.
        # The task has an infinite loop, so we'll patch asyncio.sleep
        # to raise an exception after the first call.
        with patch('asyncio.sleep', side_effect=SystemExit("Test loop finished")):
            try:
                await analyze_room_task()
            except SystemExit as e:
                print(e)

    print("\n--- Verifying Mock Calls ---")
    
    # Check if the camera image was fetched
    mock_camera_service_instance.get_image.assert_called_once_with(settings.CAMERA_ENTITY_ID)
    print("✓ Camera image was fetched.")

    # Check if sensors were updated
    mock_ha_service.set_state.assert_any_call('sensor.ai_room_cleaner_cleanliness_score', '75', {'unit_of_measurement': '%'})
    print("✓ Cleanliness score sensor was updated.")
    
    # Check if the to-do list was updated
    mock_ha_service.call_service.assert_any_call('todo', 'add_item', {'item': 'Pick up clothes', 'entity_id': 'todo.test_to-do_list'})
    mock_ha_service.call_service.assert_any_call('todo', 'add_item', {'item': 'Make the bed', 'entity_id': 'todo.test_to-do_list'})
    print("✓ To-do list was updated.")

    print("\n--- Test Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_test())
