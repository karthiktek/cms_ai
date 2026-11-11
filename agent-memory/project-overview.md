# Project Overview

> **Last updated:** 2026-11-11
> **Changed:** Added the working service skeleton: app factory, config, health checks, Celery worker, Alembic migration, Docker setup, and the baseline test suite.

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
| Cache & broker | Redis | Job input/result cache, Celery broker, locks |
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
| Local environment | Docker Compose | Redis, PostgreSQL, Ollama, Langfuse, API, workers |

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
| `REDIS_URL` | `redis://localhost:6379/0` | Cache and locks |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery results |
| `MODEL_SERVER_URL` | `http://localhost:11434` | Ollama (dev) or vLLM (prod) endpoint |
| `LLM_MODEL` | `qwen3.5:4b` | Language model name (confirm exact tag at setup) |
| `EMBED_MODEL` | `qwen3-embedding:0.6b` | Embedding model name (confirm exact tag at setup) |
| `LLM_TIMEOUT_SECONDS` | `60` | Max time per model call |
| `LLM_MAX_RETRIES` | `1` | Retries on invalid output |
| `JOB_CACHE_TTL_SECONDS` | `86400` | Expiry of job data in Redis |
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
| `eval` | `uv run python -m tests.eval` | Run evaluation on sample inputs |
| `lint` | `uv run ruff check . && uv run mypy .` | Lint and type check |
| `format` | `uv run ruff format .` | Format code |

---

## Test Status

| Suite | Tests | Status |
|-------|-------|--------|
| Schemas | 0 | — |
| Rules | 0 | — |
| Model gateway | 0 | — |
| Intake Summary Agent | 0 | — |
| Evaluation (sample intakes) | 0 | — |
| Service skeleton | 11 | passed |

> Update this table after every test suite is added or changed.