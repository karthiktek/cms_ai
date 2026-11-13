import asyncio
from collections.abc import Awaitable, Callable

import httpx
import redis.asyncio as redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import check_database_connection

router = APIRouter()


async def check_database() -> str:
    settings = get_settings()
    try:
        await check_database_connection(
            settings.DATABASE_URL,
            settings.HEALTH_TIMEOUT_SECONDS,
        )
        return "ok"
    except (SQLAlchemyError, OSError, TimeoutError, ValueError):
        return "down"


async def check_redis() -> str:
    settings = get_settings()
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        await client.aclose()
        return "ok"
    except (redis.RedisError, OSError, TimeoutError, ValueError):
        return "down"


async def check_model() -> str:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=settings.HEALTH_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{settings.MODEL_SERVER_URL}/api/tags")
            response.raise_for_status()
            payload = response.json()
            available_models = payload.get("models", [])
            names = [model.get("name", "") for model in available_models if isinstance(model, dict)]
            if settings.LLM_MODEL in names:
                return "ok"
            return "missing"
    except (httpx.HTTPError, ValueError, TypeError, OSError):
        return "down"


HEALTH_CHECKS: dict[str, Callable[[], Awaitable[str]]] = {
    "database": check_database,
    "redis": check_redis,
    "model": check_model,
}


async def run_health_checks() -> dict[str, str]:
    names = tuple(HEALTH_CHECKS)
    results = await asyncio.gather(*(check() for check in HEALTH_CHECKS.values()))
    return dict(zip(names, results, strict=True))


@router.get("/health")
async def health() -> JSONResponse:
    settings = get_settings()
    checks = await run_health_checks()
    response_body = {
        "status": "ok",
        "checks": checks,
        "model": settings.LLM_MODEL,
        "version": settings.APP_VERSION,
    }

    if any(value != "ok" for value in checks.values()):
        response_body = {
            "status": "degraded",
            "checks": checks,
            "model": settings.LLM_MODEL,
            "version": settings.APP_VERSION,
        }
        return JSONResponse(status_code=503, content=response_body)

    return JSONResponse(content=response_body)
