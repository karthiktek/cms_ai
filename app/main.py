import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from starlette.responses import Response

from app.api.routes.health import router as health_router
from app.config import get_settings
from app.logging import configure_logging

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger("cms_ai")

ROUTERS: list[APIRouter] = [health_router]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("service_started", extra={"request_id": "system"})
    try:
        yield
    finally:
        logger.info("service_stopped", extra={"request_id": "system"})


def create_app() -> FastAPI:
    app = FastAPI(
        title="TekWissen CMS AI Service",
        version=settings.APP_VERSION,
        description="AI backend service for TekWissen CMS",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def add_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    for router in ROUTERS:
        app.include_router(router)

    return app


app = create_app()
