from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator
from enum import Enum
from typing import List, Optional
from typing_extensions import Self
import os

class AIProvider(str, Enum):
    OPENAI = "openai"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    """Application configuration."""

    # Addon specific
    SLUG: str = Field(os.path.basename(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), description="Addon slug")

    # Core AI Configuration
    AI_PROVIDER: AIProvider = Field(AIProvider.OPENAI, description="AI provider to use", alias='ai_provider')
    OPENAI_API_KEY: Optional[SecretStr] = Field(None, description="OpenAI API key")
    OPENAI_MODEL: str = Field("gpt-4-vision-preview", description="AI model name to use", alias='openai_model')
    AI_PROMPT: str = Field("Analyze the image and create a to-do list for cleaning.", description="The prompt for the AI", alias='ai_prompt')

    # Home Assistant Integration
    SUPERVISOR_URL: str = Field("http://supervisor/core", description="Home Assistant Supervisor URL")
    SUPERVISOR_TOKEN: Optional[SecretStr] = Field(None, description="Home Assistant Supervisor token")
    CAMERA_ENTITY_ID: str = Field(..., description="Camera entity ID to use for analysis", alias='camera_entity_id')
    TODO_LIST_ENTITY_ID: str = Field(..., description="To-do list entity ID", alias='todo_list_entity_id')

    # Application Settings
    LOG_LEVEL: str = Field("INFO", description="Logging level", alias='log_level')
    HISTORY_FILE_PATH: str = Field("/data/history.json", description="Path to the history file")

    # Image Processing
    MAX_IMAGE_SIZE_MB: int = Field(10, ge=1, le=100, description="Maximum image size in MB")
    MAX_IMAGE_DIMENSION: int = Field(2048, ge=256, le=8192, description="Maximum image dimension")

    # VIPS Configuration
    VIPS_CACHE_MAX: int = Field(100, ge=10, le=1000, description="VIPS cache max MB")
    HIGH_RISK_DIMENSION_THRESHOLD: int = Field(8000, description="High risk dimension threshold for images")

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: List[str] = Field(["*"], description="CORS allowed origins")

    # Re-check Interval
    RECHECK_INTERVAL_MINUTES: int = Field(60, description="How often to re-analyze the room")

    @model_validator(mode='after')
    def validate_api_keys(self) -> Self:
        """Ensure appropriate API key is set for selected provider"""
        if self.AI_PROVIDER == AIProvider.OPENAI and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using the OpenAI provider")
        return self

    @property
    def current_api_key(self) -> SecretStr:
        """Get the API key for the current provider"""
        if self.AI_PROVIDER == AIProvider.OPENAI:
            if not self.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not set")
            return self.OPENAI_API_KEY
        raise ValueError(f"No API key available for provider: {self.AI_PROVIDER}")


settings: Settings = Settings()
