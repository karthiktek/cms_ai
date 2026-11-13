import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_missing_ai_service_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_SERVICE_KEY", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_defaults_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/cms_ai")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.LLM_MODEL == "qwen3.5:4b"
    assert settings.LLM_THINK is False
    assert settings.API_PORT == 8000


def test_llm_think_can_be_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/cms_ai")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_THINK", "true")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.LLM_THINK is True


def test_settings_load_values_from_temporary_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "AI_SERVICE_KEY=dotenv-service-key\n"
        "DATABASE_URL=postgresql+asyncpg://localhost/test\n"
        "REDIS_URL=redis://localhost:6379/0\n"
        "CELERY_BROKER_URL=redis://localhost:6379/1\n"
        "CELERY_RESULT_BACKEND=redis://localhost:6379/2\n"
        "MODEL_SERVER_URL=http://localhost:11434\n"
        "LLM_MODEL=dotenv-model\n",
        encoding="utf-8",
    )
    for name in (
        "AI_SERVICE_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "MODEL_SERVER_URL",
        "LLM_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=dotenv_path)  # type: ignore[call-arg]

    assert settings.AI_SERVICE_KEY == "dotenv-service-key"
    assert settings.LLM_MODEL == "dotenv-model"
