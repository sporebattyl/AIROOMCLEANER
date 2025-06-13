import logging
from typing import Optional, List, Any, Dict

from pydantic import Field, root_validator, SecretStr
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
    supervisor_url: str = Field(
        "http://supervisor/core/api",
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
        ["*"],
        alias="CORS_ALLOWED_ORIGINS",
        description="A list of origins that are allowed to make cross-origin requests."
    )

    @root_validator(skip_on_failure=True)
    def set_and_validate_api_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates that at least one API key is provided and sets the primary 'api_key'
        to be used by the application, preferring Google's key if both are set.
        """
        google_key = values.get("google_api_key")
        openai_key = values.get("openai_api_key")

        if google_key:
            values["api_key"] = google_key
        elif openai_key:
            values["api_key"] = openai_key

        if not values.get("api_key"):
            raise ValueError("An AI provider API key is required. Please set either GOOGLE_API_KEY or OPENAI_API_KEY.")

        return values


# Create a single, globally accessible instance of the settings.
settings = Settings()