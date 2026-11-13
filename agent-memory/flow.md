# Service Flow

> **Last updated:** 2026-11-12
> **Changed:** Verified feature #1 against live PostgreSQL, Redis, and Ollama using the shared health timeout.

---

## 1. Big picture

The current application registers only `GET /health`. That route checks PostgreSQL, Redis, and the configured model server. Celery is configured with broker and result-backend URLs, and Alembic uses `DATABASE_URL`; job endpoints, worker tasks, and most application data flows remain planned.

## 2. Connections

Who connects to what, through which setting, from which file. A green check below means the named code implements or configures that connection; it does not necessarily mean a live remote service has been tested.

```
Backend team ──HTTP──► API process (configured port 8000)
                       app/main.py: health router only
                       /health currently has no auth
                              │
                ┌─────────────┼────────────────┐
                │             │                │
          DATABASE_URL     REDIS_URL     MODEL_SERVER_URL
             SQLAlchemy URL   redis client  HTTP /api/tags
                ▼             ▼                ▼
          PostgreSQL       Redis         Model server
          SELECT 1         PING          configured LLM_MODEL

Worker process (Celery configuration)
  app/tasks/celery_app.py
       │                    │
 CELERY_BROKER_URL   CELERY_RESULT_BACKEND
       └──────────── Redis ─────────────┘

Alembic ── DATABASE_URL ──► PostgreSQL (version table schema: ai)
Doctor ── env/config + connectivity checks for PostgreSQL, Redis, model server
```

### Connection table

| # | From | To | Setting | Protocol / port | File | Used for | Status |
|---|------|----|---------|-----------------|------|----------|--------|
| 1 | Backend team | API | `AI_SERVICE_KEY` is a required setting, but not used by current middleware | HTTP; `API_PORT` defaults to 8000 | `app/main.py`, `app/config.py` | `/health` is registered; key authentication and `/ai/v1` routes are planned | ✅ `/health` is unauthenticated · 📋 auth and AI routes (#2) |
| 2 | API | PostgreSQL | `DATABASE_URL` | Shared SQLAlchemy async probe accepts the full `postgresql+asyncpg://` URL; port and TLS are URL-dependent | `app/database.py`, `app/api/routes/health.py` | Health `SELECT 1` with configured timeout | ✅ |
| 3 | API | PostgreSQL | `DATABASE_URL` | Planned database access | `planned: app/data/db.py` | Jobs, results, row-level security | 📋 #3 |
| 4 | API | Redis | `REDIS_URL` | Redis URL; `PING` | `app/api/routes/health.py` | Health check | ✅ |
| 5 | API | Redis cache | `REDIS_URL` | Planned cache access | `planned: app/cache/job_cache.py` | Job input/result cache | 📋 #5 |
| 6 | API | Redis broker | `CELERY_BROKER_URL` | Passed to Celery; TLS/query options come from the URL | `planned: app/api/routes/jobs.py` | Send job to worker | 📋 #5 |
| 7 | API | Model server | `MODEL_SERVER_URL`, `LLM_MODEL` | HTTP; `/api/tags` | `app/api/routes/health.py` | Checks that the configured model name is listed; does not run inference | ✅ |
| 8 | Worker | Redis broker | `CELERY_BROKER_URL` | Configured as Celery broker; URL options are passed through | `app/tasks/celery_app.py` | Celery task queue configuration; no broker `ping` is implemented here | ✅ configured |
| 9 | Worker | Redis results | `CELERY_RESULT_BACKEND` | Configured as Celery backend; URL options are passed through | `app/tasks/celery_app.py` | Celery result-backend configuration; no live check is implemented here | ✅ configured |
| 10 | Worker | Redis cache | `REDIS_URL` | Planned cache access | `planned: app/cache/job_cache.py` | Read input / write result | 📋 #5 |
| 11 | Worker | PostgreSQL | `DATABASE_URL` | Planned database access | `planned: app/data/repositories/` | Save drafts and runs | 📋 #3/#6 |
| 12 | Worker | Model server | `MODEL_SERVER_URL`, `LLM_MODEL` | Planned HTTP model calls | `planned: app/gateway/client.py` | Generate summaries; `LLM_THINK` defaults to false | 📋 #4 |
| 13 | Worker | Backend data | Open question | DB read-only or API, undecided | `planned: app/sources/backend_data.py` | Load intake data | 📋 #5 (open) |
| 14 | Alembic | PostgreSQL | `DATABASE_URL` | Async SQLAlchemy engine in online mode | `migrations/env.py` | Run migrations with the Alembic version table in schema `ai`; migration `0001_ai_schema` creates the schema | ✅ |
| 15 | Doctor | PostgreSQL, Redis, model server | `DATABASE_URL`, `REDIS_URL`, `MODEL_SERVER_URL`, `HEALTH_TIMEOUT_SECONDS` plus required settings | Shared timeout for SQL `SELECT 1`, Redis connect/read and model `/api/tags` | `app/doctor.py`, `app/database.py` | Validates setup and checks these three services; checks Redis TLS URL settings but does not ping Celery broker/result URLs; output avoids printing secret values | ✅ |
| 16 | Worker / API | Langfuse | Langfuse keys | Planned HTTPS | `planned: app/gateway/tracing.py` | Trace model calls | 📋 #4 |

### Redis: one server, three jobs

| Setting | Redis DB | What lives there |
|---------|----------|------------------|
| `REDIS_URL` | DB 0 on Upstash | Application cache keys use the `ai:job:` namespace; job cache is planned and has a 24-hour TTL (`JOB_CACHE_TTL_SECONDS=86400`) |
| `CELERY_BROKER_URL` | DB 0 on Upstash | Celery broker queue/task keys use Celery's broker key names, separate from the `ai:job:` cache namespace |
| `CELERY_RESULT_BACKEND` | DB 0 on Upstash | Celery result keys use the `celery-task-meta-` namespace, separate from broker and application cache keys |

On the Upstash free plan, all three roles use database 0 on the same Redis server. They are logically separated by their key names, not by Redis database number. The local Docker defaults may use separate database numbers.

### Environments

These are deployment targets, not environment choices enforced by the checked files. The application reads URL settings from its environment; actual service providers and model deployments must be verified in each deployment's `.env` or secret configuration.

| Service | Dev target | Prod target |
|---------|------------|-------------|
| PostgreSQL | Supabase session pooler | Azure Database for PostgreSQL |
| Redis | Upstash | Azure Cache for Redis |
| Model server | Ollama app, `qwen3.5:4b` | vLLM, Qwen3.5-4B |
| API + worker | Uvicorn + Celery on laptop | Azure containers |

## 3. Service startup

### API process

| Step | Behavior | Status |
|------|----------|--------|
| 1 | Uvicorn imports `app.main:app`; module initialization loads required settings from `.env` / environment and configures logging. | ✅ built |
| 2 | `create_app()` creates the FastAPI app with the `lifespan` logger and registers routers from `ROUTERS`. Currently only the health router is registered. | ✅ built |
| 3 | HTTP middleware accepts or generates `X-Request-Id`, stores it on request state, and returns it in the response header. | ✅ built |
| 4 | Run locally with `uv run uvicorn app.main:app --reload --port 8000`; the configured `API_PORT` default is 8000, but this command supplies its port explicitly. | ✅ built |
| 5 | Startup/shutdown currently log service events; database pools and other dependencies are not initialized in the lifespan. | ✅ built |

### Worker process

Run with `uv run celery -A app.tasks.celery_app worker --loglevel=info`. Celery creates its app using broker/backend settings and discovers task modules under `app.tasks`. The permanent `app.tasks.system.ping` task is registered and can be called eagerly in tests. Agent job tasks are planned in feature #5.

## 4. Health check

`GET /health` is public and is the only currently registered route. `HEALTH_CHECKS` is a plain dictionary from check name to async check function. `run_health_checks()` runs all values concurrently with `asyncio.gather()` and returns results under their dictionary keys; adding a check requires one new dictionary entry. Any value other than `ok` makes the response `503` with `status: degraded`.

| Check | Current behavior | Status |
|-------|------------------|--------|
| Database | Calls `app.database.check_database_connection` with the full `DATABASE_URL` and `HEALTH_TIMEOUT_SECONDS`; the helper creates/disposes a SQLAlchemy async engine and runs `SELECT 1` without rewriting the URL. | ✅ built |
| Redis | Creates a Redis client from `REDIS_URL`, issues `PING`, and closes the client. | ✅ built |
| Model | Requests `{MODEL_SERVER_URL}/api/tags`, then verifies the configured `LLM_MODEL` is listed; this does not generate text. | ✅ built |

## 5. Doctor

Run `uv run python -m app.doctor`. `Settings` loads environment and `.env` values. Doctor reports whether `.env` exists, checks required values and URL shape, tests database/Redis/model connectivity, checks Redis TLS query options and `LLM_THINK=false`, and avoids printing secret values.

| Check | Current behavior | Status |
|-------|------------------|--------|
| Database URL validation | Requires the `postgresql+asyncpg://` prefix and checks password URL-safety and Supabase session-pooler shape. | ✅ built |
| Database connectivity | Calls the same `app.database.check_database_connection` helper used by `/health`, with `HEALTH_TIMEOUT_SECONDS`. | ✅ built |
| Redis | Pings `REDIS_URL` with connect/read timeouts from `HEALTH_TIMEOUT_SECONDS`; validates `rediss://` and `ssl_cert_reqs=required` for both Celery URLs. Does not connect to either Celery URL. | ✅ built |
| Model | Requests `/api/tags` with `HEALTH_TIMEOUT_SECONDS` and checks `LLM_MODEL` availability. | ✅ built |

## 6. Database migrations

Run `uv run alembic upgrade head`. `migrations/env.py` loads `DATABASE_URL`; online mode creates an async SQLAlchemy engine with `NullPool`, runs migrations through a synchronous Alembic connection bridge, then disposes the engine. Offline mode configures Alembic with the URL directly. Both modes put Alembic's version table in schema `ai`. The current `0001_ai_schema` migration creates schema `ai` and the `vector` extension; it creates no application tables.

Status: ✅ built and applied to the configured dev database on 2026-11-12.

## 7. Background worker (Celery)

`app/tasks/celery_app.py` creates the `cms_ai` Celery app from `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`, sets task tracking/time limit, and autodiscovers `system` under `app.tasks`. `app/tasks/system.py` defines `app.tasks.system.ping`, returning `"pong"`. The eager test imports the app's discovered task registry and runs the task without Redis.

| Capability | Status |
|------------|--------|
| Celery app and broker/result-backend configuration | ✅ built |
| Task discovery and permanent ping task | ✅ built |
| Intake job execution task | 📋 planned, feature #5 |

## 8. Agent job flow — Intake Summary

Every step below is planned; none of the job routes, persistence path, gateway, or Intake Summary agent is currently registered or implemented. Feature numbers identify the planned implementation tranche.

| Step | Planned flow | Feature | Status |
|------|--------------|---------|--------|
| 1 | Backend sends `POST /ai/v1/jobs` with `agent`, `workspace_id`, `project_id`, and `intake_id`, plus service/workspace/user headers. | #2 auth/errors, #5 job system | 📋 planned |
| 2 | Validate headers/body, create a queued job, and return a `job_id` immediately. | #2 auth/errors, #3 database, #5 job system | 📋 planned |
| 3 | Resolve `intake_summary` through the agent registry and enqueue the `run_agent` Celery task. | #5 job system | 📋 planned |
| 4 | Load intake/project data through the backend source, whose access method (read-only DB or API) remains an open question; cache input with a TTL. | #5 job system | 📋 planned |
| 5 | Validate the intake, reject all-empty answers, and identify missing-information gaps. | #6 Intake Summary | 📋 planned |
| 6 | Build a grounded summary through the model gateway and versioned `intake_summary@v1` prompt; treat submitted answers as data, not instructions. | #4 model gateway, #6 Intake Summary | 📋 planned |
| 7 | Validate structured output against the schema and deterministic rules; retry once with validation feedback if needed. | #4 model gateway, #6 Intake Summary | 📋 planned |
| 8 | Save the result as an `ai_draft` in the `ai` schema, scoped to the workspace; record run/model-call metadata. | #3 database, #4 model gateway, #6 Intake Summary | 📋 planned |
| 9 | Cache the result, update job status to `done` or `failed`, and expose status/result to the backend. | #3 database, #5 job system | 📋 planned |
| 10 | Deliver results by polling or webhook/SSE; polling versus push delivery remains undecided. | #5 job system | 📋 planned |
| 11 | Accept the backend's user-verified summary, save a new verified version, and record a learning event. | #3 database, #7 verified results | 📋 planned |

## 9. Open points

- **Backend data loading:** read-only database access or an API? Keep the source behind a replaceable interface until agreed. Impacts feature #5.
- **Result delivery:** polling, webhook, or SSE? The API reference currently describes polling as the interim proposal. Impacts feature #5.
- **Service authentication details:** workspace/user/role headers and error behavior are planned in feature #2; the current `/health` route remains unauthenticated.
- **Verified-result contract:** exact schema and learning-event behavior are planned in feature #7.

## 10. Real-service verification

On 2026-11-12, `uv run python -m app.doctor` passed all checks with the configured 15-second dev timeout. `uv run alembic upgrade head` applied `0001_ai_schema`. A live `GET /health` returned `status: ok` with database, Redis, and model checks all `ok`.

### Change log

| Date | Change |
|------|--------|
| 2026-11-12 | Added the connection map; corrected health, Celery, Alembic, and doctor claims to match the current code. |
| 2026-11-12 | Added sections 3–9 for startup, health, doctor, migrations, Celery, planned Intake Summary flow, and open points. |
| 2026-11-12 | Shared the SQLAlchemy database probe between health and Doctor; documented the plain-dict health registry and its extensible result keys. |
| 2026-11-12 | Configured all Upstash Redis roles on DB 0, separated by key names. |
| 2026-11-12 | Shared `HEALTH_TIMEOUT_SECONDS` across Doctor database, Redis, and model live checks. |
| 2026-11-12 | Verified feature #1 on live services after Doctor, migration, and `/health` passed. |