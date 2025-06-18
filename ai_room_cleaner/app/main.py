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

    while True:
        try:
            image_data = camera_service.get_image(config.camera_entity_id)
            analysis_result = ai_service.analyze_image(image_data)

            # This is a placeholder for the actual implementation
            print(f"Analysis result: {analysis_result}")

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(config.recheck_interval_minutes * 60)

if __name__ == "__main__":
    main()