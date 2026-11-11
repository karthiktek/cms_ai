from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "dev"
    APP_VERSION: str = "0.1.0"
    API_PORT: int = 8000
    AI_SERVICE_KEY: str = Field(...)
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)
    CELERY_BROKER_URL: str = Field(...)
    CELERY_RESULT_BACKEND: str = Field(...)
    MODEL_SERVER_URL: str = Field(...)
    LLM_MODEL: str = "qwen3.5:4b"
    LLM_THINK: bool = False
    EMBED_MODEL: str = "qwen3-embedding:0.6b"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 1
    JOB_CACHE_TTL_SECONDS: int = 86400
    HEALTH_TIMEOUT_SECONDS: int = 2
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
