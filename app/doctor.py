from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
import redis.asyncio as redis
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.database import check_database_connection

PLACEHOLDER_TOKENS = (
    "<",
    ">",
    "[",
    "]",
    "YOUR-",
    "CHANGE-ME",
)


@dataclass
class DoctorCheck:
    ok: bool
    message: str
    status: str | None = None

    def render(self) -> str:
        rendered_status = self.status or ("OK" if self.ok else "FAIL")
        return f"{rendered_status}: {self.message}"


def _settings_or_load(settings: Settings | None) -> Settings:
    if settings is not None:
        return settings
    return Settings()  # type: ignore[call-arg]


def _has_placeholder(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    upper = text.upper()
    return any(token in upper for token in PLACEHOLDER_TOKENS)


def check_env_file() -> DoctorCheck:
    if os.path.exists(".env"):
        return DoctorCheck(True, ".env present")
    return DoctorCheck(False, ".env missing — run: copy .env.example .env")


def check_required_vars(settings: Settings | None = None) -> DoctorCheck:
    config = _settings_or_load(settings)
    if _has_placeholder(config.AI_SERVICE_KEY):
        return DoctorCheck(False, "AI_SERVICE_KEY is empty or has a placeholder", status="FAIL")
    return DoctorCheck(True, "Required variables are set")


def check_database_url(settings: Settings | None = None) -> DoctorCheck:
    database_url = _settings_or_load(settings).DATABASE_URL
    if not database_url:
        return DoctorCheck(False, "DATABASE_URL is missing — add it to .env", status="FAIL")
    if not database_url.startswith("postgresql+asyncpg://"):
        return DoctorCheck(False, "Use postgresql+asyncpg:// not postgresql://")
    return DoctorCheck(True, "Database URL prefix is valid")


def check_password_encoding(settings: Settings | None = None) -> DoctorCheck:
    database_url = _settings_or_load(settings).DATABASE_URL
    if not database_url:
        return DoctorCheck(False, "DATABASE_URL is missing — add it to .env", status="SKIP")
    try:
        parsed = urlsplit(database_url)
    except ValueError:
        return DoctorCheck(False, "Password has '@' — replace with %40; secrets are masked as ****")
    password = parsed.password or ""
    if any(char in password for char in "@#/:"):
        return DoctorCheck(False, "Password has '@' — replace with %40; secrets are masked as ****")
    return DoctorCheck(True, "Password is URL-safe")


def check_supabase_pooler(settings: Settings | None = None) -> DoctorCheck:
    database_url = _settings_or_load(settings).DATABASE_URL
    if not database_url:
        return DoctorCheck(False, "DATABASE_URL is missing — add it to .env", status="SKIP")
    parsed = urlsplit(database_url)
    hostname = (parsed.hostname or "").lower()
    if "supabase.com" in hostname and (parsed.port != 5432 or "pooler" not in hostname):
        return DoctorCheck(False, "Use the Session pooler URL, not direct/transaction")
    return DoctorCheck(True, "Supabase pooler URL is correct")


def check_redis_urls(settings: Settings | None = None) -> DoctorCheck:
    config = _settings_or_load(settings)
    redis_url = config.REDIS_URL
    celery_url = config.CELERY_BROKER_URL
    celery_result = config.CELERY_RESULT_BACKEND

    if not redis_url or not celery_url or not celery_result:
        missing = []
        if not redis_url:
            missing.append("REDIS_URL")
        if not celery_url:
            missing.append("CELERY_BROKER_URL")
        if not celery_result:
            missing.append("CELERY_RESULT_BACKEND")
        return DoctorCheck(False, f"{' / '.join(missing)} is missing — add it to .env", status="FAIL")
    if not redis_url.startswith("rediss://"):
        return DoctorCheck(False, "Use rediss:// for Upstash Redis")
    if "ssl_cert_reqs=required" not in celery_url.lower():
        return DoctorCheck(False, "Add ?ssl_cert_reqs=required to CELERY_BROKER_URL")
    if "ssl_cert_reqs=required" not in celery_result.lower():
        return DoctorCheck(False, "Add ?ssl_cert_reqs=required to CELERY_RESULT_BACKEND")
    return DoctorCheck(True, "Redis URLs are configured for TLS")


async def _check_database_async(settings: Settings | None = None) -> DoctorCheck:
    database_url = _settings_or_load(settings).DATABASE_URL
    if not database_url:
        return DoctorCheck(False, "DATABASE_URL is missing — add it to .env", status="SKIP")
    if not database_url.startswith("postgresql+asyncpg://"):
        return DoctorCheck(False, "Use postgresql+asyncpg:// not postgresql://")
    try:
        await check_database_connection(
            database_url,
            timeout_seconds=_settings_or_load(settings).HEALTH_TIMEOUT_SECONDS,
        )
        return DoctorCheck(True, "Database connection OK")
    except (SQLAlchemyError, OSError, TimeoutError, ValueError) as exc:
        return DoctorCheck(False, f"Cannot reach database: {exc.__class__.__name__}")


def check_database(settings: Settings | None = None) -> DoctorCheck:
    return asyncio.run(_check_database_async(settings))


async def _check_redis_async(settings: Settings | None = None) -> DoctorCheck:
    redis_url = _settings_or_load(settings).REDIS_URL
    if not redis_url:
        return DoctorCheck(False, "REDIS_URL is missing — add it to .env", status="SKIP")
    try:
        timeout = _settings_or_load(settings).HEALTH_TIMEOUT_SECONDS
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        await client.ping()
        await client.aclose()
        return DoctorCheck(True, "Redis connection OK")
    except (redis.RedisError, OSError, TimeoutError, ValueError) as exc:
        return DoctorCheck(False, f"Cannot reach Redis: {exc.__class__.__name__}")


def check_redis(settings: Settings | None = None) -> DoctorCheck:
    return asyncio.run(_check_redis_async(settings))


def check_model(settings: Settings | None = None) -> DoctorCheck:
    config = _settings_or_load(settings)
    model_server_url = config.MODEL_SERVER_URL
    llm_model = config.LLM_MODEL
    if not model_server_url:
        return DoctorCheck(False, "MODEL_SERVER_URL is missing — add it to .env", status="SKIP")
    try:
        response = httpx.get(
            f"{model_server_url}/api/tags",
            timeout=config.HEALTH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        available_models = payload.get("models", [])
        names = [
            model.get("name", "")
            for model in available_models
            if isinstance(model, dict)
        ]
        if llm_model and llm_model in names:
            return DoctorCheck(True, "Ollama model is available")
        return DoctorCheck(False, f"Run: ollama pull {llm_model or 'qwen3.5:4b'}")
    except (httpx.HTTPError, ValueError, TypeError, OSError) as exc:
        return DoctorCheck(False, f"Cannot reach Ollama: {exc.__class__.__name__}")


def check_llm_think(settings: Settings | None = None) -> DoctorCheck:
    llm_think = str(_settings_or_load(settings).LLM_THINK).strip().lower()
    if llm_think in {"", "false"}:
        return DoctorCheck(True, "LLM_THINK is false")
    return DoctorCheck(False, "Set LLM_THINK=false")


def run_doctor_checks() -> list[DoctorCheck]:
    try:
        settings = _settings_or_load(None)
    except ValidationError as exc:
        missing_fields = {
            str(error["loc"][0]) for error in exc.errors() if error["type"] == "missing"
        }
        checks = [check_env_file()]
        if "AI_SERVICE_KEY" in missing_fields:
            checks.append(DoctorCheck(False, "AI_SERVICE_KEY is empty or has a placeholder", status="FAIL"))
        else:
            checks.append(DoctorCheck(True, "Required variables are set"))

        if "DATABASE_URL" in missing_fields:
            checks.append(DoctorCheck(False, "DATABASE_URL is missing — add it to .env", status="FAIL"))
            checks.extend(
                DoctorCheck(False, "DATABASE_URL is missing — dependent check skipped", status="SKIP")
                for _ in range(3)
            )
        else:
            checks.extend([check_database_url(), check_password_encoding(), check_supabase_pooler()])

        redis_fields = {"REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"}
        if missing_fields & redis_fields:
            names = " / ".join(sorted(missing_fields & redis_fields))
            checks.append(DoctorCheck(False, f"{names} is missing — add it to .env", status="FAIL"))
            checks.append(DoctorCheck(False, "REDIS_URL is missing — dependent check skipped", status="SKIP"))
        else:
            checks.append(check_redis_urls())

        if "DATABASE_URL" in missing_fields:
            checks.append(DoctorCheck(False, "DATABASE_URL is missing — dependent check skipped", status="SKIP"))
        else:
            checks.append(check_database())
        if "REDIS_URL" in missing_fields:
            checks.append(DoctorCheck(False, "REDIS_URL is missing — dependent check skipped", status="SKIP"))
        else:
            checks.append(check_redis())
        if "MODEL_SERVER_URL" in missing_fields:
            checks.append(DoctorCheck(False, "MODEL_SERVER_URL is missing — dependent check skipped", status="SKIP"))
        else:
            checks.append(check_model())
        checks.append(check_llm_think())
        return checks

    return [
        check_env_file(),
        check_required_vars(settings),
        check_database_url(settings),
        check_password_encoding(settings),
        check_supabase_pooler(settings),
        check_redis_urls(settings),
        check_database(settings),
        check_redis(settings),
        check_model(settings),
        check_llm_think(settings),
    ]


def main() -> int:
    checks = run_doctor_checks()
    normalized: list[DoctorCheck] = []
    for check in checks:
        if isinstance(check, DoctorCheck):
            item = check
        else:
            item = DoctorCheck(bool(check), str(check))
        normalized.append(item)
        print(item.render())
    return 0 if all(check.ok for check in normalized) else 1


if __name__ == "__main__":
    raise SystemExit(main())
