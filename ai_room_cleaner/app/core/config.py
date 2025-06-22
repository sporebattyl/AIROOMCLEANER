from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    LOG_LEVEL: str = Field(..., alias="LOG_LEVEL")
    AI_PROVIDER: str = Field(..., alias="AI_PROVIDER")
    OPENAI_API_KEY: str | None = Field(None, alias="OPENAI_API_KEY")
    GOOGLE_API_KEY: str | None = Field(None, alias="GOOGLE_API_KEY")
    AI_MODEL: str = Field(..., alias="AI_MODEL")
    PROMPT: str = Field(..., alias="PROMPT")
    CAMERA_ENTITY_ID: str = Field(..., alias="CAMERA_ENTITY")
    CLEANLINESS_SENSOR_ENTITY: str = Field(..., alias="CLEANLINESS_SENSOR_ENTITY")
    TODO_LIST_ENTITY_ID: str = Field(..., alias="TODO_LIST_ENTITY")
    RECHECK_INTERVAL_MINUTES: int = Field(..., alias="RUN_INTERVAL_MINUTES")
    SUPERVISOR_TOKEN: str = Field(..., alias="SUPERVISOR_TOKEN")
    SLUG: str = Field("ai_room_cleaner", alias="SLUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
