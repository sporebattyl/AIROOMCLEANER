import os
import yaml
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

def find_config_file():
    """Find the config.yaml file in common locations."""
    # Correctly determine the base directory (two levels up from core)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # List of potential paths for config.yaml
    potential_paths = [
        os.path.join(base_dir, "config.yaml"),
        os.path.join(base_dir, "config", "config.yaml"),
        "/config/config.yaml",  # Path for Home Assistant addons
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            logger.info(f"Found configuration file at: {path}")
            return path
            
    logger.warning("config.yaml not found in standard locations.")
    return None

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = find_config_file()
    if not config_path:
        return {}
        
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Error loading or parsing config.yaml: {e}")
        return {}

# Load the configuration once at startup
_config = load_config()

class Settings:
    def __init__(self):
        # Directly access keys from the loaded config
        self.camera_entity: Optional[str] = os.getenv("CAMERA_ENTITY_ID") or _config.get("camera_entity")
        self.supervisor_token: Optional[str] = os.getenv("SUPERVISOR_TOKEN")
        self.google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY") or _config.get("google_api_key")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY") or _config.get("openai_api_key")
        self.api_key: Optional[str] = self.google_api_key or self.openai_api_key
        self.ai_model: str = os.getenv("AI_MODEL") or _config.get("ai_model", "gemini-1.5-pro")
        
        # Load values that will be moved from hardcoded to config
        self.supervisor_url: str = _config.get("supervisor_url", "http://supervisor/core/api")
        self.ai_prompt: str = _config.get("ai_prompt", 
            "Analyze this room image and identify any items that are out of place or contributing to messiness. "
            "For each item, describe what needs to be cleaned or organized. "
            "Return the output as a JSON array of strings, with each string being a specific cleaning task."
        )
        self.cors_allowed_origins: List[str] = _config.get("cors_allowed_origins", ["*"])

    def validate(self):
        """Validate that essential settings are configured."""
        if not self.camera_entity:
            raise ValueError("CAMERA_ENTITY_ID is not configured.")
        if not self.supervisor_token:
            raise ValueError("SUPERVISOR_TOKEN is not available.")
        if not self.api_key:
            raise ValueError("API key (GOOGLE_API_KEY or OPENAI_API_KEY) is not configured.")

# Instantiate settings to be imported by other modules
settings = Settings()