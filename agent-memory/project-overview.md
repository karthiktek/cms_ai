# Project Overview

> **Last updated:** 2026-11-13
> **Changed:** Added the VS Code one-window startup task workflow.

---

## What this project is

TekWissen CMS AI is the AI agent service behind the TekWissen Change Management System.
It runs three agents on private Qwen models: the Client Agent (runs client and stakeholder intakes),
the TekWissen Agent (builds the project understanding, drafts the change assessment and assists
consultants in their workspace) and the Learning Agent (improves the agents from consultant edits).
It is a backend-only Python service: the backend team calls it through its API, and it has no frontend
of its own. It never publishes anything to clients; consultants approve every output through the main product.

---

## Technology Stack

| Concern | Choice | Notes |
|---------|--------|-------|
| Runtime | Python 3.12+ | Async I/O throughout |
| Framework | FastAPI + Uvicorn | AI backend API; SSE for streamed replies |
| Language | Python (typed) | Type checking in strict mode |
| Agent orchestration | LangGraph | Agent steps, routing, parallel workers, human-approval pauses |
| Schemas & validation | Pydantic v2 | Every input, output, event and model response |
| Language model | Qwen3.5-4B | One model for all agents; forced JSON output |
| Embedding model | Qwen3-Embedding 0.6B | Fact matching and document search |
| Model serving | Ollama (development) → vLLM (production) | Private, on TekWissen servers; no outside AI services |
| Background jobs | Celery | Agent runs as async jobs (`job_id`) |
| Cache & broker | Redis | On Upstash free plan all roles use DB 0, separated by key names; local Docker may use separate DB numbers |
| Database | PostgreSQL + SQLAlchemy + Alembic | `ai` schema: drafts, facts, analyses, versions, runs |
| Vector search | pgvector | Inside PostgreSQL |
| File storage | Supabase Storage → Azure Blob (production) | Uploaded files, generated documents |
| Document input | Docling | Word, PDF, Excel, PPT → text |
| Document output | python-docx, openpyxl | Word and Excel exports (PowerPoint in V2) |
| Privacy | Presidio | Personal data detection and masking |
| Tracing | Langfuse (self-hosted) | Every model call: prompt version, tokens, time |
| Metrics | Prometheus + Grafana | Service health, latency, failures |
| Auth | Service key + user/role/workspace headers | Users are authenticated by the backend team |
| Tests | pytest | Unit, agent (fake model), evaluation on samples |
| Packaging | uv | Locked dependencies |
| Local environment | Ollama app + Supabase session pooler + Upstash Redis | No-Docker developer setup for model, Postgres and cache |

---

## Dependencies

> Versions are pinned in `uv.lock` at setup. List here once pinned.

```toml
[project]
dependencies = [
  "fastapi",
  "uvicorn",
  "pydantic",
  "pydantic-settings",
  "langgraph",
  "celery",
  "redis",
  "sqlalchemy",
  "asyncpg",
  "alembic",
  "pgvector",
  "httpx",
  "ollama",
  "langfuse",
  "docling",
  "python-docx",
  "openpyxl",
  "presidio-analyzer",
  "presidio-anonymizer",
  "prometheus-client",
]

[dependency-groups]
dev = [
  "pytest",
  "pytest-asyncio",
  "ruff",
  "mypy",
]
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_ENV` | `development` | `development` / `staging` / `production` |
| `API_PORT` | `8000` | AI backend HTTP port |
| `AI_SERVICE_KEY` | — | Key the backend team uses to call this service |
| `DATABASE_URL` | — | PostgreSQL connection (AI service user) |
| `CORE_DATABASE_URL` | — | Read-only connection to backend data (if direct access is agreed) |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache and locks; use DB 0 on Upstash |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker; use DB 0 on Upstash, separated by broker key names |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery results; use DB 0 on Upstash, separated by result key names |
| `MODEL_SERVER_URL` | `http://localhost:11434` | Ollama (dev) or vLLM (prod) endpoint |
| `LLM_MODEL` | `qwen3.5:4b` | Language model name (confirm exact tag at setup) |
| `EMBED_MODEL` | `qwen3-embedding:0.6b` | Embedding model name (confirm exact tag at setup) |
| `LLM_TIMEOUT_SECONDS` | `60` | Max time per model call |
| `LLM_MAX_RETRIES` | `1` | Retries on invalid output |
| `JOB_CACHE_TTL_SECONDS` | `86400` | Expiry of job data in Redis |
| `HEALTH_TIMEOUT_SECONDS` | `2` | Shared timeout for health and Doctor live checks; remote dev databases such as Supabase Sydney may need `15` |
| `FILE_STORAGE_URL` | — | File storage endpoint |
| `FILE_STORAGE_KEY` | — | File storage access key |
| `LANGFUSE_HOST` | `http://localhost:3000` | Langfuse server |
| `LANGFUSE_PUBLIC_KEY` | — | Langfuse key |
| `LANGFUSE_SECRET_KEY` | — | Langfuse secret |
| `LOG_LEVEL` | `INFO` | Logging level |

> Add all env vars here as they are introduced.
> Never list actual secret values — reference keys only.

---

## Scripts

| Script | Command | Use |
|--------|---------|-----|
| `start` | `uv run uvicorn app.main:app --host 0.0.0.0 --port $API_PORT` | Production API |
| `dev` | `uv run uvicorn app.main:app --reload` | Development API |
| `worker` | `uv run celery -A app.tasks worker --loglevel=info` | Run agent jobs |
| `up` | `docker compose up -d` | Start Redis, PostgreSQL, Ollama, Langfuse |
| `migrate` | `uv run alembic upgrade head` | Apply database migrations |
| `test` | `uv run pytest` | Run all tests |
| `doctor` | `uv run python -m app.doctor` | Validate `.env` and local service connectivity without Docker |
| `eval` | `uv run python -m tests.eval` | Run evaluation on sample inputs |
| `lint` | `uv run ruff check . && uv run mypy .` | Lint and type check |
| `format` | `uv run ruff format .` | Format code |

---

## Local dev without Docker

Local developers work without Docker. The supported setup is:
- Ollama Windows app for the model server
- Supabase Session Pooler for PostgreSQL
- Upstash Redis for the broker and cache

Use `uv run python -m app.doctor` before starting the API or workers. It checks for missing `.env` values, placeholder secrets, invalid database URLs, redis/TLS issues, model reachability, and the `LLM_THINK=false` rule without printing raw secrets. Doctor and `/health` use the shared SQLAlchemy database connectivity probe. When the secret URL values are still blank, the doctor reports them as missing and the developer must paste them manually before live connectivity checks can pass.

## See it running

Open these local and service dashboards while developing:

| Tool | URL |
|------|-----|
| API docs | `http://localhost:8000/docs` |
| Flower task monitor | `http://localhost:5555` |
| Supabase Table Editor (`ai` schema) | `https://supabase.com/dashboard/project/<project-ref>/editor?schema=ai` |
| Upstash Data Browser | `https://console.upstash.com/redis` |
| Ollama model list | `http://localhost:11434/api/tags` |

Start each local process in its own terminal from `sdd-template/`:

```powershell
uv run uvicorn app.main:app --port 8000
uv run celery -A app.tasks.celery_app worker --pool=solo -l info
uv run celery -A app.tasks.celery_app flower --port=5555
```

The `solo` worker pool is suitable for the local Windows development environment. The API and Flower monitor are separate from the worker process.

## One-window setup

In VS Code, choose **Terminal → Run Task → Start all** to launch the API, Celery worker, and Flower in parallel in separate terminals grouped as `services`. Use **Terminal → Run Task → Doctor** to check local service configuration and **Terminal → Run Task → Tests** to run the test suite. The workspace Python interpreter is set to `.venv`.

---

## Test Status

| Suite | Tests | Status |
|-------|-------|--------|
| Schemas | 0 | — |
| Rules | 0 | — |
| Model gateway | 0 | — |
| Intake Summary Agent | 0 | — |
| Evaluation (sample intakes) | 0 | — |
| Service skeleton | 13 | pending full run |
| Doctor / local dev validation | 12 | pending full run |
| Full suite | 29 | pending full run |

> Update this table after every test suite is added or changed.