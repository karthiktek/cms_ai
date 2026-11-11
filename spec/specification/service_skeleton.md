# Service Skeleton — Specification

> **Last updated:** 2026-11-11
> **Changed:** First version. The skeleton is the permanent base that every later feature builds on.

---

## Overview

Creates the permanent, runnable base of the AI service: the project setup, config from environment variables, the FastAPI app factory, a health endpoint, a Celery worker that starts, the empty `ai` database schema, and Docker Compose for local services. It has no agents, no tables and no model calls yet. This is **not a throwaway prototype**. Every later feature adds to this base and never rebuilds it.

---

## Current State

- Only documentation exists (`AGENTS.md`, `agent-memory/`, `spec/`).
- No `app/` folder, no `pyproject.toml`, no Docker files.

---

## Interface Specification

### GET /health

| Property | Value |
|----------|-------|
| Method | GET |
| Path | `/health` (outside `/ai/v1`) |
| Auth required | No |
| Route | `app/api/routes/health.py` |

**Success response: 200 OK**
```json
{
  "status": "ok",
  "checks": { "database": "ok", "redis": "ok", "model": "ok" },
  "model": "qwen3.5:4b",
  "version": "0.1.0"
}
```

**Degraded response: 503**
```json
{
  "status": "degraded",
  "checks": { "database": "ok", "redis": "ok", "model": "down" },
  "model": "qwen3.5:4b",
  "version": "0.1.0"
}
```

| Check | How | Result values |
|-------|-----|---------------|
| database | `SELECT 1` with a 2 s timeout | `ok` / `down` |
| redis | `PING` with a 2 s timeout | `ok` / `down` |
| model | `GET {MODEL_SERVER_URL}/api/tags` with a 2 s timeout; `LLM_MODEL` must be in the list | `ok` / `down` / `missing` |

- Each check is a small async function in a list (`HEALTH_CHECKS`) in `app/api/routes/health.py`. Later features add checks to the list without changing the endpoint.
- Checks run in parallel. One failing check never stops the others.
- Health checks are the only place, besides `gateway/`, allowed to contact the model server, and only to list models, never to generate.

### Config (`app/config.py`)

Uses `pydantic-settings`. It reads `.env`. A missing required value stops the app at startup with a clear error.

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `APP_ENV` | No | `dev` | `dev` / `test` / `prod` |
| `APP_VERSION` | No | `0.1.0` | Shown in `/health` |
| `API_PORT` | No | `8000` | |
| `AI_SERVICE_KEY` | Yes | — | Used from feature #2 |
| `DATABASE_URL` | Yes | — | Local Docker Postgres **or** Supabase Postgres; the code is the same |
| `REDIS_URL` | Yes | — | |
| `CELERY_BROKER_URL` | Yes | — | |
| `CELERY_RESULT_BACKEND` | Yes | — | |
| `MODEL_SERVER_URL` | Yes | — | Ollama (dev) / vLLM (prod) |
| `LLM_MODEL` | No | `qwen3.5:4b` | The only LLM |
| `EMBED_MODEL` | No | `qwen3-embedding:0.6b` | Used later |
| `LLM_TIMEOUT_SECONDS` | No | `60` | |
| `LLM_MAX_RETRIES` | No | `1` | |
| `JOB_CACHE_TTL_SECONDS` | No | `86400` | |
| `HEALTH_TIMEOUT_SECONDS` | No | `2` | |
| `LOG_LEVEL` | No | `INFO` | |

Later features add `CORE_DATABASE_URL`, the file storage settings (Supabase Storage → Azure Blob) and the Langfuse keys. They **add** fields with defaults and never rename existing ones.

### App factory (`app/main.py`)

- `create_app() -> FastAPI` builds the app and returns it. It never starts a server.
- Routers are registered from one list, `ROUTERS`. Each feature adds its router to that list. No route logic lives in `main.py`.
- `app = create_app()` is created at module level so Uvicorn can find it.
- Logs are JSON lines with `time`, `level`, `message` and `request_id` (when present).

### Celery (`app/tasks/celery_app.py`)

- Creates the Celery app with the broker and backend from config.
- Finds tasks automatically in `app/tasks/` modules. `celery_app.py` holds no task logic.
- `app/tasks/system.py` has one task, `ping`, that returns `"pong"`. It stays permanently as a worker check.
- The `run_agent` task comes in feature #5, in its own module.

---

## Database Changes

No tables. The first Alembic migration creates only:

```sql
CREATE SCHEMA IF NOT EXISTS ai;
CREATE EXTENSION IF NOT EXISTS vector;
```

- Alembic lives in `migrations/`, uses async, and reads `DATABASE_URL`.
- Alembic's version table goes in the `ai` schema (`ai.alembic_version`), so it never clashes with the backend's or Supabase's own schemas.
- Works the same on local Docker Postgres and on Supabase Postgres.

---

## Built to evolve

This skeleton is the permanent base of the AI service. Later features **add to it**. They never replace or rebuild it.

**Rules that keep it growable**
- **Routes:** each feature adds its own router file in `app/api/routes/` and adds it to `ROUTERS` in `main.py`.
- **Config:** one `Settings` class. New fields always have defaults or are clearly required. Existing names never change.
- **Health checks:** new services (storage, Langfuse, embeddings) add a function to `HEALTH_CHECKS`.
- **Celery:** each task area gets its own module in `app/tasks/`.
- **Database:** only Alembic migrations change the schema. Never edit an old migration; add a new one.
- **Environments:** dev, Supabase and Azure differ only in `.env` values, never in code.
- **Folders:** all the target folders are created now (empty with `__init__.py`), so every feature knows where its code goes.

**How it grows**

| Feature | Adds to the skeleton |
|---------|---------------------|
| #2 Auth & errors | `api/deps.py`, `api/errors.py`; error handler registered in `main.py` |
| #3 AI database | `data/db.py`, `data/models.py`, `ai.jobs` + `ai.runs` + row-level security migration |
| #4 Model gateway | `gateway/` files, `prompts/`, Langfuse config + health check |
| #5 Job system | `routes/jobs.py`, `router/registry.py`, `tasks/run_agent.py`, `cache/job_cache.py`, `sources/backend_data.py` |
| #6 Intake Summary | `agents/intake_summary/`, `schemas/intake.py`, `rules/intake_summary.py`, prompt, migration |
| Later | New agent = new folder + registry entry. Production = new `.env` (Azure) only |

**Test:** after each feature, the skeleton's own tests (health, config, ping) must still pass.

---

## Implementation Checklist

### Project setup

| File | Change |
|------|--------|
| `pyproject.toml` | Create: Python 3.12; deps fastapi, uvicorn[standard], pydantic, pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic, redis, celery, httpx; dev deps pytest, pytest-asyncio, ruff, mypy; ruff + mypy + pytest settings |
| `.env.example` | Create: all the variables above, required values left empty; comments show local and Supabase `DATABASE_URL` examples |
| `.gitignore` | Create: `.env`, `__pycache__`, `.venv`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache` |

### App: files with code

| File | Change |
|------|--------|
| `app/__init__.py` | Create (empty) |
| `app/config.py` | Create the `Settings` class and `get_settings()` (cached) |
| `app/logging.py` | Create the JSON log setup |
| `app/main.py` | Create `create_app()` with the `ROUTERS` list and logging |
| `app/api/__init__.py` | Create (empty) |
| `app/api/routes/__init__.py` | Create (empty) |
| `app/api/routes/health.py` | Create `GET /health` and the `HEALTH_CHECKS` list (database, redis, model) |
| `app/tasks/__init__.py` | Create (empty) |
| `app/tasks/celery_app.py` | Create the Celery app with task autodiscovery |
| `app/tasks/system.py` | Create the `ping` task |

### App: empty folders for later features (`__init__.py` only)

| Folder | Filled by |
|--------|-----------|
| `app/router/` | #5 |
| `app/agents/` | #6 |
| `app/gateway/` | #4 |
| `app/prompts/` | #4 (no `__init__.py`; add `.gitkeep`) |
| `app/schemas/` | #2 |
| `app/rules/` | #6 |
| `app/cache/` | #5 |
| `app/sources/` | #5 |
| `app/data/` | #3 |

### Database setup

| File | Change |
|------|--------|
| `alembic.ini` | Create |
| `migrations/env.py` | Create: async, reads `DATABASE_URL`, version table in the `ai` schema |
| `migrations/versions/0001_ai_schema.py` | Create the `ai` schema and the vector extension |

### Local services

| File | Change |
|------|--------|
| `docker-compose.yml` | Create: `postgres` (pgvector/pgvector:pg16), `redis` (redis:7), `ollama`, `langfuse`, `api`, `worker`; the `postgres` service is optional when using Supabase |
| `Dockerfile` | Create: Python 3.12 slim, installs with uv, runs uvicorn; the same image runs the worker |

### Tests

| File | Change |
|------|--------|
| `tests/__init__.py` | Create (empty) |
| `tests/conftest.py` | Create: test settings and an app client |
| `tests/api/test_health.py` | Create: test cases 1–6 |
| `tests/test_config.py` | Create: test cases 7–8 |
| `tests/test_tasks.py` | Create: test case 9 |
| `tests/test_app.py` | Create: test cases 10–11 |

> Tests mock the database, Redis and the model server. They never need Docker or Supabase running.

### Memory updates after the build

| File | Update |
|------|--------|
| `agent-memory/project-overview.md` | Deps, scripts, test count |
| `agent-memory/architecture.md` | Files and folders created |
| `agent-memory/api-reference.md` | Confirm `/health` |
| `agent-memory/database.md` | `ai` schema and Alembic set up |
| `agent-memory/conventions.md` | `ROUTERS`, `HEALTH_CHECKS` and task module rules |
| `spec/index.md` | #1 → ✅ done, with the date |

---

## Test Cases

| # | Description | Expected |
|---|-------------|----------|
| 1 | All checks pass | 200, `status: "ok"` |
| 2 | Database down (mocked) | 503, `checks.database: "down"` |
| 3 | Redis down (mocked) | 503, `checks.redis: "down"` |
| 4 | Model server down (mocked) | 503, `checks.model: "down"` |
| 5 | Model server up but `LLM_MODEL` not pulled | 503, `checks.model: "missing"` |
| 6 | `/health` needs no service key | 200 without headers |
| 7 | Missing `AI_SERVICE_KEY` at startup | settings fail with a clear error naming the variable |
| 8 | Defaults applied (`LLM_MODEL`, `API_PORT`) | `qwen3.5:4b`, `8000` |
| 9 | Celery `ping` task runs eagerly in tests | returns `"pong"` |
| 10 | `create_app()` does not open a port | the import is safe in tests |
| 11 | A router added to `ROUTERS` is served | a test router responds 200 |

---

## Scope

**In scope**
- Project setup, config, JSON logs, app factory with `ROUTERS`
- `/health` with `HEALTH_CHECKS` (database, redis, model)
- A Celery app with task autodiscovery and the `ping` task
- Alembic with the empty `ai` schema (works on local Postgres and Supabase)
- All target folders created empty
- Docker Compose and Dockerfile
- Tests for all of the above

**Out of scope**
- Service-key auth and the error shape (#2)
- Tables and row-level security (#3)
- Model calls, prompts and Langfuse wiring (#4)
- Job endpoints, `run_agent`, the Redis job cache (#5)
- File storage (Supabase Storage / Azure Blob)
- Azure deployment and CI

---

## Current stage

Spec written. Ready to implement.