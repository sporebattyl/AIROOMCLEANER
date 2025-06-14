from functools import lru_cache
from pydantic import Field, SecretStr
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

    AI_API_KEY: SecretStr = Field(..., description="The API key for the external AI service.")
    AI_API_ENDPOINT: str = Field(..., description="The endpoint URL for the AI service.")
    LOG_LEVEL: str = Field("INFO", description="The logging level for the application.")

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    The lru_cache decorator ensures that the Settings object is only created once,
    improving performance by avoiding repeated file reads and object initializations.
    """
    return Settings()

settings = get_settings()