import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_missing_ai_service_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_SERVICE_KEY", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_defaults_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/cms_ai")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")

    settings = Settings()  # type: ignore[call-arg]

    assert settings.LLM_MODEL == "qwen3.5:4b"
    assert settings.API_PORT == 8000
