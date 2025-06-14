import logging
import os
from functools import lru_cache
from typing import Optional, List, Any, Dict

from pydantic import Field, model_validator, SecretStr, HttpUrl, validator
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
    max_image_size_mb: int = Field(
        default=1,
        alias="MAX_IMAGE_SIZE_MB",
        description="Max image file size in megabytes."
    )
    max_image_dimension: int = Field(
        default=2048,
        alias="MAX_IMAGE_DIMENSION",
        description="Max width or height for an image."
    )

    # VIPS configuration for memory and performance tuning.
    vips_concurrency: int = Field(
        default=4,
        alias="VIPS_CONCURRENCY",
        description="Number of worker threads for vips operations."
    )
    vips_cache_max: int = Field(
        default=100,
        alias="VIPS_CACHE_MAX_MEM",
        description="Max memory for vips operation cache in MB."
    )
    high_risk_dimension_threshold: int = Field(
        default=8000,
        alias="HIGH_RISK_DIMENSION_THRESHOLD",
        description="Image dimension above which aggressive downsampling is triggered."
    )

    @validator('max_image_size_mb')
    def validate_max_image_size(cls, v):
        if v <= 0 or v > 50:
            raise ValueError('max_image_size_mb must be between 1 and 50')
        return v
    
    @validator('max_image_dimension')
    def validate_max_image_dimension(cls, v):
        if v < 100 or v > 10000:
            raise ValueError('max_image_dimension must be between 100 and 10000')
        return v
    
    @validator('vips_concurrency')
    def validate_vips_concurrency(cls, v):
        if v < 1 or v > 16:
            raise ValueError('vips_concurrency must be between 1 and 16')
        return v
    
    @validator('history_file_path')
    def validate_history_file_path(cls, v):
        # Ensure directory exists or can be created
        dir_path = os.path.dirname(v)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except OSError as e:
                raise ValueError(f'Cannot create directory for history file: {e}')
        return v

    @model_validator(mode='after')
    def validate_ai_model_and_keys(self) -> 'Settings':
        """Validate that the AI model matches available API keys."""
        if self.ai_model:
            model_lower = self.ai_model.lower()
            if ("gemini" in model_lower or "google" in model_lower) and not self.google_api_key:
                raise ValueError(f"Google API key required for model: {self.ai_model}")
            elif ("gpt" in model_lower or "openai" in model_lower) and not self.openai_api_key:
                raise ValueError(f"OpenAI API key required for model: {self.ai_model}")
        return self


@lru_cache()
def get_settings(**kwargs) -> Settings:
    """
    Returns a cached instance of the Settings object.
    The lru_cache decorator ensures that the Settings object is only created once.
    Accepts keyword arguments for testing purposes.
    """
    return Settings(**kwargs)