from app.services.ai_service import AIService
from app.services.camera_service import CameraService
from app.services.ha_service import HomeAssistantService
from app.services.history_service import HistoryService
from app.core.config import Settings, settings

def get_settings() -> Settings:
    return settings

def get_ai_service() -> AIService:
    return AIService(get_settings())

def get_camera_service() -> CameraService:
    return CameraService(get_ha_service())

def get_ha_service() -> HomeAssistantService:
    return HomeAssistantService()

def get_history_service() -> HistoryService:
    return HistoryService()