from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolate_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    test_settings = {
        "AI_SERVICE_KEY": "test-service-key",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/cms_ai",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "MODEL_SERVER_URL": "http://localhost:11434",
        "APP_ENV": "test",
        "APP_VERSION": "0.1.0",
        "API_PORT": "8000",
    }
    for name, value in test_settings.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
