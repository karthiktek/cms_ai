import pytest
from fastapi.testclient import TestClient

from app.api.routes import health as health_module


def test_health_all_ok(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_database() -> str:
        return "ok"

    async def fake_redis() -> str:
        return "ok"

    async def fake_model() -> str:
        return "ok"

    monkeypatch.setattr(health_module, "check_database", fake_database)
    monkeypatch.setattr(health_module, "check_redis", fake_redis)
    monkeypatch.setattr(health_module, "check_model", fake_model)

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

    monkeypatch.setattr(health_module, "check_database", fake_database)
    monkeypatch.setattr(health_module, "check_redis", fake_redis)
    monkeypatch.setattr(health_module, "check_model", fake_model)

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

    monkeypatch.setattr(health_module, "check_database", fake_database)
    monkeypatch.setattr(health_module, "check_redis", fake_redis)
    monkeypatch.setattr(health_module, "check_model", fake_model)

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

    monkeypatch.setattr(health_module, "check_database", fake_database)
    monkeypatch.setattr(health_module, "check_redis", fake_redis)
    monkeypatch.setattr(health_module, "check_model", fake_model)

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

    monkeypatch.setattr(health_module, "check_database", fake_database)
    monkeypatch.setattr(health_module, "check_redis", fake_redis)
    monkeypatch.setattr(health_module, "check_model", fake_model)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["model"] == "missing"


def test_health_no_auth_needed(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code in {200, 503}
