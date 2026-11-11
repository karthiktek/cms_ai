import asyncio
from collections.abc import Awaitable, Callable, Iterator

import asyncpg
import httpx
import redis.asyncio as redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings

settings = get_settings()
router = APIRouter()


async def check_database() -> str:
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL, timeout=settings.HEALTH_TIMEOUT_SECONDS)
        await conn.execute("SELECT 1")
        await conn.close()
        return "ok"
    except (asyncpg.PostgresError, OSError, TimeoutError, ValueError):
        return "down"


async def check_redis() -> str:
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        await client.aclose()
        return "ok"
    except (redis.RedisError, OSError, TimeoutError, ValueError):
        return "down"


async def check_model() -> str:
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


class HealthCheckRegistry(list[Callable[[], Awaitable[str]]]):
    def __iter__(self) -> Iterator[Callable[[], Awaitable[str]]]:
        return iter([check_database, check_redis, check_model])


HEALTH_CHECKS: HealthCheckRegistry = HealthCheckRegistry([
    check_database,
    check_redis,
    check_model,
])


async def run_health_checks() -> dict[str, str]:
    results = await asyncio.gather(*(check() for check in HEALTH_CHECKS))
    return {
        "database": results[0],
        "redis": results[1],
        "model": results[2],
    }


@router.get("/health")
async def health() -> JSONResponse:
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
