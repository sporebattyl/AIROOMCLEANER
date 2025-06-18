import os
from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration."""
    camera_entity_id: str
    ai_provider: str
    api_key: str
    recheck_interval_minutes: int
    todo_list_name: str
    prompt: str | None

def get_config() -> Config:
    """Loads configuration from environment variables."""
    api_key = os.getenv("SUPERVISOR_CONFIG_api_key")
    if not api_key:
        raise ValueError("API key is not configured. Please set it in the addon configuration.")

    return Config(
        camera_entity_id=os.getenv("SUPERVISOR_CONFIG_camera_entity_id", "camera.your_camera"),
        ai_provider=os.getenv("SUPERVISOR_CONFIG_ai_provider", "Google Gemini"),
        api_key=api_key,
        recheck_interval_minutes=int(os.getenv("SUPERVISOR_CONFIG_recheck_interval_minutes", 60)),
        todo_list_name=os.getenv("SUPERVISOR_CONFIG_todo_list_name", "AI Room Cleaner"),
        prompt=os.getenv("SUPERVISOR_CONFIG_prompt"),
    )