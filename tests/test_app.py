import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

import app.main as main_module
from app.api.routes.health import router as health_router


def test_create_app_does_not_open_a_port() -> None:
    app = main_module.create_app()
    assert app is not None
    assert app.title == "TekWissen CMS AI Service"


def test_router_added_to_routers(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_router = APIRouter()

    @dummy_router.get("/echo")
    def echo() -> dict[str, bool]:
        return {"ok": True}

    monkeypatch.setattr(main_module, "ROUTERS", [health_router, dummy_router])
    app = main_module.create_app()

    with TestClient(app) as client:
        response = client.get("/echo")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
