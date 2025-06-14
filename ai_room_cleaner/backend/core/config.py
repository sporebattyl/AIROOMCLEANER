from functools import lru_cache
from typing import Optional
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
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
    
    OPENAI_API_KEY: Optional[SecretStr] = Field(None, description="The API key for OpenAI.")
    GOOGLE_API_KEY: Optional[SecretStr] = Field(None, description="The API key for Google Gemini.")
    
    LOG_LEVEL: str = Field("INFO", description="The logging level for the application.")
    MAX_IMAGE_SIZE_MB: int = Field(10, description="Maximum image size in megabytes.")
    MAX_IMAGE_DIMENSION: int = Field(2048, description="Maximum dimension (width or height) for images.")
    AI_PROMPT: str = Field("Analyze this image and identify areas of mess. Return a list of tasks to clean it up.", description="The prompt to send to the AI.")

    @field_validator("AI_PROVIDER")
    def validate_ai_provider(cls, v):
        if v.lower() not in ["openai", "google"]:
            raise ValueError("AI_PROVIDER must be 'openai' or 'google'")
        return v.lower()

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    The lru_cache decorator ensures that the Settings object is only created once,
    improving performance by avoiding repeated file reads and object initializations.
    """
    return Settings()

settings = get_settings()