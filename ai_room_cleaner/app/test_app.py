import os
import time
from unittest.mock import MagicMock, patch

# Set mock environment variables for testing
os.environ["SUPERVISOR_CONFIG_camera_entity_id"] = "camera.test_camera"
os.environ["SUPERVISOR_CONFIG_ai_provider"] = "Google Gemini"
os.environ["SUPERVISOR_CONFIG_api_key"] = "test_api_key" # This will be used by the mock
os.environ["SUPERVISOR_CONFIG_recheck_interval_minutes"] = "1"
os.environ["SUPERVISOR_CONFIG_todo_list_name"] = "Test To-Do List"
os.environ["SUPERVISOR_TOKEN"] = "test_supervisor_token"

# Import the main function after setting environment variables
from .main import main

def run_test():
    """
    Runs a single iteration of the main application loop with a mocked
    Home Assistant service to validate the core logic.
    """
    print("--- Starting Application Test ---")

    # Create a mock for the HomeAssistantService
    mock_ha_service = MagicMock()

    # Simulate get_camera_image to return a dummy image (a single black pixel)
    dummy_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf\x00\xff\xd9'
    mock_ha_service.get_camera_image.return_value = dummy_image
    
    # Mock the AI response
    mock_ai_response = {
        "cleanliness_score": 75,
        "todo_list": ["Pick up clothes", "Make the bed"]
    }

    # Use a patch to replace the real services with our mocks
    with patch('app.main.HomeAssistantService', return_value=mock_ha_service), \
         patch('app.main.AIService.analyze_image', return_value=mock_ai_response):

        print("Running one loop of the main application...")
        
        # We need to run main in a way that it executes once and exits.
        # The main function has an infinite loop, so we'll patch time.sleep
        # to raise an exception after the first call.
        with patch('time.sleep', side_effect=SystemExit("Test loop finished")):
            try:
                main()
            except SystemExit as e:
                print(e)

    print("\n--- Verifying Mock Calls ---")
    
    # Check if the camera image was fetched
    mock_ha_service.get_camera_image.assert_called_once_with("camera.test_camera")
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
    run_test()