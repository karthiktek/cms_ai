# Architecture & Project Structure

> **Last updated:** 2026-11-12
> **Changed:** Added the shared database probe to the app structure and documented the name-keyed health check map.

---

## Folder Map

```
sdd-template/
│
├── AGENTS.md
├── README.md
│
├── spec/
│   ├── index.md
│   ├── team-guide.md
│   └── specification/
│       └── intake_agent.md
│
├── agent-memory/
│   ├── flow.md
│   ├── project-overview.md
│   ├── architecture.md
│   ├── api-reference.md
│   ├── database.md
│   └── conventions.md
│
├── app/                           ← source code
│   ├── main.py                    — creates the FastAPI app (no server start here)
│   ├── config.py                  — settings from environment variables (pydantic-settings)
│   ├── database.py                — shared SQLAlchemy async `SELECT 1` probe for health and Doctor
│   │
│   ├── api/                       — HTTP layer (thin)
│   │   ├── deps.py                — service-key check, workspace headers, request ID
│   │   ├── errors.py              — typed exceptions + one handler → standard error shape
│   │   └── routes/
│   │       ├── health.py          — GET /health
│   │       └── jobs.py            — POST /ai/v1/jobs, GET /ai/v1/jobs/{id}, POST …/verified
│   │
│   ├── router/
│   │   └── registry.py            — maps agent name ("intake_summary") → agent runner
│   │
│   ├── tasks/                     — Celery
│   │   ├── celery_app.py          — Celery app + Redis broker config + system task discovery
│   │   └── run_agent.py           — one task: load input → run agent → save → update job
│   │
│   ├── agents/                    — one folder per agent (LangGraph)
│   │   └── intake_summary/
│   │       ├── graph.py           — steps wired together
│   │       ├── nodes.py           — check, summarise, validate, save
│   │       └── state.py           — typed graph state
│   │
│   ├── gateway/                   — the only place that calls models
│   │   ├── client.py              — Ollama / vLLM client (Qwen3.5-4B, embeddings)
│   │   ├── prompts.py             — loads versioned prompts from prompts/
│   │   ├── structured.py          — forced JSON + schema validation + one retry
│   │   └── tracing.py             — Langfuse tracing
│   │
│   ├── prompts/                   — versioned prompt files
│   │   └── intake_summary@v1.md
│   │
│   ├── schemas/                   — Pydantic models
│   │   ├── jobs.py                — JobCreate, Job, JobStatus
│   │   ├── intake.py              — IntakeInput, IntakeSummary
│   │   └── errors.py              — ErrorResponse
│   │
│   ├── rules/                     — deterministic checks, no model calls
│   │   └── intake_summary.py      — key points must match real questions, limits, categories
│   │
│   ├── cache/
│   │   └── job_cache.py           — Redis: put/get job input and result (with expiry)
│   │
│   ├── sources/
│   │   └── backend_data.py        — loads intake + project data from the backend (method TBD)
│   │
│   └── data/                      — database access
│       ├── db.py                  — async engine, workspace_session (row-level security)
│       ├── models.py              — SQLAlchemy table models (ai schema)
│       ├── queries/               — named SQL statements, one file per table
│       └── repositories/          — async functions agents/tasks/routes call
│
├── migrations/                    ← Alembic migrations (ai schema)
│
├── tests/
│   ├── api/                       — endpoint + security tests
│   ├── agents/                    — agent tests with a fake gateway
│   ├── rules/                     — rule unit tests
│   ├── data/                      — repository tests (rolled-back transactions)
│   ├── samples/intake_summary/    — sample intakes + expected summaries
│   └── eval.py                    — evaluation runner (real model)
│
├── docker-compose.yml             ← Redis, PostgreSQL+pgvector, Ollama, Langfuse, api, worker
├── Dockerfile
├── pyproject.toml / uv.lock
├── .env.example                   ← env var names only, no secrets
├── .githooks/
│   └── pre-commit                ← runs `update_worklog.py` and stages `spec/index.md`
├── scripts/
│   └── update_worklog.py         ← syncs the work log from `git log` into the marker block
└── README.md
```

See `agent-memory/flow.md` for detailed startup, connection, health, migration, worker, and planned request-flow diagrams.

---

## Layered Design

```
Backend team request
      │
      ▼
  API layer            app/api        auth headers, validation, returns job_id (no AI work)
      │
      ▼
  Router               app/router     agent name → agent runner
      │
      ▼
  Job queue            app/tasks      Celery task (Redis broker)
      │
      ▼
  Input loading        app/sources    backend data → Redis cache (app/cache)
      │
      ▼
  Agent                app/agents     LangGraph steps
      │
      ├──► Rules       app/rules      deterministic checks
      ├──► Gateway     app/gateway    model calls (Qwen3.5-4B), prompts, tracing
      │
      ▼
  Repositories         app/data       async, workspace-scoped
      │
      ▼
  PostgreSQL (ai schema)
```

**Rule:** dependencies flow in one direction only (top → down).
- Agents use rules, gateway and repositories; they never import API code.
- Repositories never import agents, tasks or routes.
- Only `gateway/` talks to models. Only `data/` talks to PostgreSQL. Only `cache/` talks to Redis (besides Celery).

---

## Key Design Decisions

- **Separate AI backend.** The backend team calls this service over HTTP; it never serves the frontend directly. *Why:* clear ownership, independent deployment, and the AI can change without touching the main app.
- **Async jobs (`job_id`) with Celery.** Requests return immediately; agents run as Celery tasks. *Why:* model calls take seconds to minutes, and HTTP requests must stay fast and reliable.
- **Router + agent registry.** One `/jobs` endpoint; the `agent` field selects the agent. *Why:* new agents are added by registering them, without new endpoints.
- **Redis as working cache only.** Job input and result are cached with an expiry; the database holds the durable copy. *Why:* fast hand-off between steps without risking data loss.
- **Drafts saved by AI, verified versions saved by backend (Option A).** *Why:* keeps both the AI version and the user-verified version for tracing and later learning.
- **One language model: Qwen3.5-4B.** Set in config (`LLM_MODEL`). *Why:* fast and simple to run; quality comes from step-by-step agents, rules and validation. The model can be swapped by config if evaluation requires it.
- **Model gateway.** All model calls go through one module. *Why:* one place for prompts, forced JSON, retries, limits and tracing; models can change without touching agents.
- **Pydantic everywhere.** *Why:* every input and output is checked; small models are forced into exact formats.
- **Row-level security per workspace.** *Why:* one client's data can never leak into another project, even if a query is wrong.
- **App factory in `main.py`.** It creates the app but never starts a server; Uvicorn starts it. *Why:* tests import the app without opening a port.
- **Prompts as versioned files.** *Why:* prompt changes are tracked, tested and can be rolled back.

---

## Agents

### `intake_summary`

- **Purpose:** Read one submitted intake and produce a grounded summary draft with a problem category, key points and unanswered gaps.
- **Steps:** `read` (load cached intake), `check` (validate input and reject all-empty answers), `mark` (identify gap candidates), `summarise` (generate structured output through the model gateway), `validate` (check schema and deterministic rules), `retry` (retry once with validation errors), `save` (persist the `ai_draft`), `finish` (cache the result, update the job and record the run).
- **Output fields:** `summary`, `problem_category`, `key_points`, `gaps`.

### Planned agents

- `project_understanding` — planned; combine verified intake summaries into project facts, conflicts, gaps and readiness; steps and output fields TBD.
- `stakeholder_raci` — planned; assess stakeholders and responsibility assignments; steps and output fields TBD.
- `current_future_state` — planned; describe current and future states; steps and output fields TBD.
- `impact` — planned; analyze change impacts and linked items; steps and output fields TBD.
- `dependency` — planned; identify dependencies between change items; steps and output fields TBD.
- `risk` — planned; identify and assess change risks; steps and output fields TBD.
- `workspace` — planned; answer questions, explain analyses, edit drafts and update from notes; steps and output fields TBD.
- `learning` — planned; learn from verified versions and consultant feedback; steps and output fields TBD.

## Request Flow — Intake Summary (V1)

1. The backend team sends `POST /ai/v1/jobs` with `{ agent: "intake_summary", workspace_id, project_id, intake_id }` and the service headers.
2. `api/deps.py` checks the service key and workspace headers; the body is validated with `JobCreate`.
3. A job row is created (`queued`) and the response `{ job_id, status: "queued" }` is returned immediately.
4. `router/registry.py` resolves `intake_summary` and the Celery task `run_agent` is queued.
5. The task sets the job to `running` and calls `sources/backend_data.py` to load the intake answers and project details (method to be agreed with the backend team).
6. The input is stored in Redis (`ai:job:{job_id}:input`) with an expiry.
7. The Intake Summary Agent runs:
   1. **check** — validate the input against `IntakeInput`
   2. **summarise** — the gateway calls Qwen3.5-4B with prompt `intake_summary@v1`, answers passed as a data block, JSON output forced
   3. **validate** — schema check + rules (key points reference real questions, allowed category, limits); one retry with errors if needed
   4. **save** — `save_summary_draft()` inserts version 1 (`ai_draft`) in one transaction
8. The result is cached in Redis (`ai:job:{job_id}:result`); the job is set to `done` (or `failed` with a reason).
9. Each model call is recorded in `runs` and traced in Langfuse.
10. The backend calls `GET /ai/v1/jobs/{job_id}` (or receives a callback, to be agreed) and gets the summary.
11. The user reviews and verifies the summary in the frontend; the backend saves the verified version and calls `POST /ai/v1/jobs/{job_id}/verified`.
12. The AI service saves the verified version (version 2, `verified`) and records a learning event.