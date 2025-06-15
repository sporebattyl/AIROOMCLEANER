from functools import lru_cache
from typing import Optional
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    """
    Centralized application configuration using pydantic-settings.
    Settings are loaded from environment variables or a .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    AI_PROVIDER: str = Field("openai", description="The AI provider to use ('openai' or 'google').")
    AI_MODEL: str = Field("gpt-4-turbo", description="The specific AI model to use.")
    AI_API_ENDPOINT: Optional[str] = Field(None, description="The API endpoint for the AI service.")
    ai_api_key: SecretStr = Field(..., description="The API key for the AI service.")
    OPENAI_MAX_TOKENS: int = Field(1000, description="The maximum number of tokens for OpenAI API calls.")

    history_file_path: str = Field("/data/history.json", description="The path to the history file.")
    camera_entity: Optional[str] = Field(None, description="The camera entity to use for taking pictures.")
    api_key: Optional[SecretStr] = Field(None, description="The API key for the service.")
    supervisor_url: Optional[str] = Field(None, description="The URL for the supervisor.")
    cors_allowed_origins: list[str] = Field(["http://localhost:8080", "http://127.0.0.1:8080"], description="A list of allowed CORS origins.")

    vips_cache_max: int = Field(100, description="Maximum number of operations to cache for vips.")
    high_risk_dimension_threshold: int = Field(4096, description="Dimension threshold for high-risk images.")
    
    LOG_LEVEL: str = Field("INFO", description="The logging level for the application.")
    MAX_IMAGE_SIZE_MB: int = Field(10, description="Maximum image size in megabytes.")
    MAX_IMAGE_DIMENSION: int = Field(2048, description="Maximum dimension (width or height) for images.")
    AI_PROMPT: str = Field("Analyze this image and identify areas of mess. Return a list of tasks to clean it up.", description="The prompt to send to the AI.")
    MAX_REQUEST_SIZE_MB: int = Field(10, description="Maximum request body size in megabytes.")

    @field_validator("AI_PROVIDER")
    def validate_ai_provider(cls, v):
        if v.lower() not in ["openai", "google"]:
            raise ValueError("AI_PROVIDER must be 'openai' or 'google'")
        return v.lower()

@lru_cache()
def get_settings() -> AppSettings:
    """
    Returns a cached instance of the AppSettings object.
    The lru_cache decorator ensures that the AppSettings object is only created once,
    improving performance by avoiding repeated file reads and object initializations.
    """
    return AppSettings()

settings = get_settings()