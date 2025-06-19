import pytest
from unittest.mock import patch, AsyncMock
from app.main import main

@pytest.mark.asyncio
async def test_main():
    """
    Test the main function.
    """
    with patch("app.main.HomeAssistantService") as mock_ha_service, \
         patch("app.main.CameraService") as mock_camera_service, \
         patch("app.main.AIService") as mock_ai_service, \
         patch("app.main.HistoryService") as mock_history_service:
        
        mock_ha_service.return_value.call_service.return_value = {"some_key": "some_value"}
        mock_camera_service.return_value.get_image.return_value = b"test_image"
        mock_ai_service.return_value.analyze_image = AsyncMock(return_value={
            "cleanliness_score": 90,
            "todo_list": ["Clean the floor"],
        })

        await main()

        mock_ha_service.return_value.set_state.assert_any_call(
            "sensor.ai_room_cleaner_cleanliness_score", "0", {"unit_of_measurement": "%"}
        )
        mock_ha_service.return_value.set_state.assert_any_call(
            "sensor.ai_room_cleaner_last_analysis", "Never", {}
        )
        mock_camera_service.return_value.get_image.assert_called_once()
        mock_ai_service.return_value.analyze_image.assert_called_once()
        mock_history_service.return_value.add_to_history.assert_called_once()
        mock_ha_service.return_value.set_state.assert_any_call(
            "sensor.ai_room_cleaner_cleanliness_score", "90", {"unit_of_measurement": "%"}
        )
