import logging
from functools import lru_cache
from typing import Optional, List, Any, Dict

from pydantic import Field, model_validator, SecretStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Settings are loaded from environment variables or a .env file.
    Pydantic's BaseSettings provides automatic validation and type casting.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required settings from environment. The application will fail to start if these
    # are not provided in the environment or a .env file.
    camera_entity: str = Field(
        ...,
        alias="CAMERA_ENTITY_ID",
        description="The entity ID of the camera in Home Assistant."
    )
    supervisor_token: SecretStr = Field(
        ...,
        alias="SUPERVISOR_TOKEN",
        description="The Home Assistant Supervisor token for API access."
    )

    # API Keys - at least one of these must be provided.
    google_api_key: Optional[SecretStr] = Field(None, alias="GOOGLE_API_KEY", description="Google AI API Key.")
    openai_api_key: Optional[SecretStr] = Field(None, alias="OPENAI_API_KEY", description="OpenAI API Key.")

    # Derived setting - this will be populated by a validator below.
    api_key: Optional[SecretStr] = Field(None, description="The API key to be used for the selected AI service.")

    # Configuration with default values. These can be overridden by environment variables.
    ai_model: str = Field(
        "gemini-1.5-pro-latest",
        alias="AI_MODEL",
        description="The specific AI model to use for image analysis."
    )
    supervisor_url: HttpUrl = Field(
        default=HttpUrl("http://supervisor/core/api"),
        alias="SUPERVISOR_URL",
        description="URL for the Home Assistant Supervisor API."
    )
    ai_prompt: str = Field(
        "Analyze this room image for messiness. Identify items that are out of place. "
        "Return a JSON object with a 'tasks' key, containing a list of objects. "
        "Each object should have a 'mess' (e.g., 'clothes on the floor') and a 'reason' "
        "(e.g., 'Reduces cleanliness and could be a trip hazard').",
        alias="AI_PROMPT",
        description="The instruction or prompt for the AI to perform its analysis."
    )
    cors_allowed_origins: List[str] = Field(
        default=["http://localhost", "http://localhost:8000", "http://127.0.0.1:8000"],
        alias="CORS_ALLOWED_ORIGINS",
        description="A list of origins that are allowed to make cross-origin requests."
    )
    history_file_path: str = Field(
        default="data/analysis_history.json",
        alias="HISTORY_FILE_PATH",
        description="The file path to store analysis history."
    )

    @model_validator(mode='before')
    @classmethod
    def set_and_validate_api_key(cls, values: Any) -> Any:
        """
        Validates that at least one API key is provided and sets the primary 'api_key'
        to be used by the application, preferring Google's key if both are set.
        """
        if isinstance(values, dict):
            google_key = values.get("google_api_key")
            openai_key = values.get("openai_api_key")

            key = google_key or openai_key
            if not key:
                raise ValueError("An AI provider API key is required. Please set either GOOGLE_API_KEY or OPENAI_API_KEY.")

            values["api_key"] = key

        return values


@lru_cache()
def get_settings(**kwargs) -> Settings:
    """
    Returns a cached instance of the Settings object.
    The lru_cache decorator ensures that the Settings object is only created once.
    Accepts keyword arguments for testing purposes.
    """
    return Settings(**kwargs)