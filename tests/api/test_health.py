from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app import database as database_module
from app.api.routes import health as health_module


@pytest.mark.asyncio
async def test_database_check_uses_full_sqlalchemy_url(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = "postgresql+asyncpg://user:password@db.example.test:5432/ai"
    settings = health_module.get_settings()
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)

    connection = AsyncMock()
    connection_context = MagicMock()
    connection_context.__aenter__ = AsyncMock(return_value=connection)
    connection_context.__aexit__ = AsyncMock(return_value=None)
    engine = MagicMock()
    engine.connect.return_value = connection_context
    engine.dispose = AsyncMock()
    create_engine = MagicMock(return_value=engine)
    monkeypatch.setattr(database_module, "create_async_engine", create_engine)

    assert await health_module.check_database() == "ok"

    create_engine.assert_called_once_with(database_url)
    connection.execute.assert_awaited_once()
    assert str(connection.execute.await_args.args[0]) == "SELECT 1"
    engine.dispose.assert_awaited_once()


def test_health_all_ok(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_database() -> str:
        return "ok"

    async def fake_redis() -> str:
        return "ok"

    async def fake_model() -> str:
        return "ok"

    monkeypatch.setitem(health_module.HEALTH_CHECKS, "database", fake_database)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "redis", fake_redis)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "model", fake_model)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["redis"] == "ok"
    assert payload["checks"]["model"] == "ok"


def test_health_database_down(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_database() -> str:
        return "down"

    async def fake_redis() -> str:
        return "ok"

    async def fake_model() -> str:
        return "ok"

    monkeypatch.setitem(health_module.HEALTH_CHECKS, "database", fake_database)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "redis", fake_redis)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "model", fake_model)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "down"


def test_health_redis_down(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_database() -> str:
        return "ok"

    async def fake_redis() -> str:
        return "down"

    async def fake_model() -> str:
        return "ok"

    monkeypatch.setitem(health_module.HEALTH_CHECKS, "database", fake_database)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "redis", fake_redis)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "model", fake_model)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "down"


def test_health_model_down(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_database() -> str:
        return "ok"

    async def fake_redis() -> str:
        return "ok"

    async def fake_model() -> str:
        return "down"

    monkeypatch.setitem(health_module.HEALTH_CHECKS, "database", fake_database)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "redis", fake_redis)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "model", fake_model)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["model"] == "down"


def test_health_model_missing(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_database() -> str:
        return "ok"

    async def fake_redis() -> str:
        return "ok"

    async def fake_model() -> str:
        return "missing"

    monkeypatch.setitem(health_module.HEALTH_CHECKS, "database", fake_database)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "redis", fake_redis)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "model", fake_model)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["model"] == "missing"


def test_health_no_auth_needed(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code in {200, 503}


def test_added_health_check_is_returned(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_check() -> str:
        return "ok"

    for name in health_module.HEALTH_CHECKS:
        monkeypatch.setitem(health_module.HEALTH_CHECKS, name, fake_check)
    monkeypatch.setitem(health_module.HEALTH_CHECKS, "new_check", fake_check)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["checks"]["new_check"] == "ok"
