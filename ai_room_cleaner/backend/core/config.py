import os
import yaml
import logging
from typing import Optional, List, Any, Dict
from pydantic import Field, validator, root_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from .exceptions import ConfigError

logger = logging.getLogger(__name__)

def yaml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A pydantic-settings source that loads variables from a YAML file
    at the specified path.
    """
    config_path = find_config_file()
    if not config_path:
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Error loading or parsing config.yaml: {e}")
        return {}

def find_config_file():
    """Find the config.yaml file in common locations."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    potential_paths = [
        os.path.join(base_dir, "config.yaml"),
        os.path.join(base_dir, "config", "config.yaml"),
        "/config/config.yaml",
    ]
    for path in potential_paths:
        if os.path.exists(path):
            logger.info(f"Found configuration file at: {path}")
            return path
    logger.warning("config.yaml not found in standard locations.")
    return None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        yaml_file=find_config_file()
    )

    camera_entity: Optional[str] = Field(None, alias="CAMERA_ENTITY_ID")
    supervisor_token: Optional[SecretStr] = Field(None, alias="SUPERVISOR_TOKEN")
    google_api_key: Optional[SecretStr] = Field(None, alias="GOOGLE_API_KEY")
    openai_api_key: Optional[SecretStr] = Field(None, alias="OPENAI_API_KEY")
    api_key: Optional[SecretStr] = None
    ai_model: str = Field("gemini-1.5-pro-latest", alias="AI_MODEL")
    supervisor_url: str = Field("http://supervisor/core/api", alias="SUPERVISOR_URL")
    ai_prompt: str = Field(
        "Analyze this room image for messiness. Identify items that are out of place. "
        "Return a JSON object with a 'tasks' key, containing a list of objects. "
        "Each object should have a 'mess' (e.g., 'clothes on the floor') and a 'reason' "
        "(e.g., 'Reduces cleanliness and could be a trip hazard').",
        alias="AI_PROMPT"
    )
    cors_allowed_origins: List[str] = Field(["*"], alias="CORS_ALLOWED_ORIGINS")

    @root_validator(pre=True)
    def load_yaml_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        yaml_config = yaml_config_settings_source(cls)
        # YAML config keys might not have the alias format, so we map them
        mapping = {
            "camera_entity": "CAMERA_ENTITY_ID",
            "google_api_key": "GOOGLE_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "ai_model": "AI_MODEL",
            "ai_prompt": "AI_PROMPT",
            "cors_allowed_origins": "CORS_ALLOWED_ORIGINS",
            "supervisor_url": "SUPERVISOR_URL"
        }
        for yaml_key, env_alias in mapping.items():
            if yaml_key in yaml_config:
                values[env_alias] = yaml_config[yaml_key]
        return values

    @root_validator(pre=False, skip_on_failure=True)
    def set_api_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["api_key"] = values.get("google_api_key") or values.get("openai_api_key")
        return values

    def validate(self):
        """Validate that essential settings are configured."""
        if not self.camera_entity:
            raise ConfigError("CAMERA_ENTITY_ID is not configured.")
        if not self.supervisor_token:
            raise ConfigError("SUPERVISOR_TOKEN is not available.")
        if not self.api_key:
            raise ConfigError("API key (GOOGLE_API_KEY or OPENAI_API_KEY) is not configured.")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            yaml_config_settings_source,
        )

settings = Settings()