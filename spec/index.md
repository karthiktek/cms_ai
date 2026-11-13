# Feature Specifications Index

> **Last updated:** 2026-11-13
> **Changed:** Added Flower to the dev tools and documented the local observability setup.

This is the single source of truth for every feature in the **TekWissen CMS – AI Service**:
what is planned, what is being built, and what has shipped.

> Scope: AI service only. Frontend and main-backend features live in the backend team's repo.

---

## How to use this file

- **Before starting any work**, check this index. If the feature is `done`, the
  code already exists. If it is `planned`, the spec is ready to implement.
  If it is `not-specced`, write the spec first and then switch it to `planned`.
- **When you start a feature**, change its status to `in-progress`.
- **When the feature ships**, change its status to `done` and fill in the date.
- Build features **in the order listed**. Later features depend on earlier ones.

---

## Status Key

| Symbol | Status | Meaning |
|--------|--------|---------|
| 📝 | not-specced | Agreed in the plan, spec not written yet |
| 📋 | planned | Spec written, not yet started |
| 🚧 | in-progress | Currently being implemented |
| ✅ | done | Implemented, tested (tests + eval where needed), merged |

---

## Features — V1 (Intake Summary)

| # | Status | Feature | Spec document | Endpoints / changes | Implemented |
|---|--------|---------|---------------|---------------------|-------------|
| 1 | ✅ done — verified on real services | Service skeleton | `spec/specification/service_skeleton.md` | App factory, config, `GET /health`, Docker Compose (Redis, Postgres+pgvector, Ollama, Langfuse) | 2026-11-12 |
| 1b | ✅ done | Local dev setup | `spec/specification/local_dev_setup.md` | `uv run python -m app.doctor`, `.env` validation, no-Docker setup notes | 2026-11-11 |
| 2 | 📝 not-specced | Service auth & errors | `spec/specification/service-auth.md` | `X-Service-Key` and workspace headers, request ID, standard error shape | — |
| 3 | 📝 not-specced | AI database base | `spec/specification/ai-database.md` | `ai` schema, `ai.jobs`, `ai.runs`, row-level security, `workspace_session` | — |
| 4 | 📝 not-specced | Model gateway | `spec/specification/model-gateway.md` | Qwen3.5-4B client, versioned prompts, forced JSON + one retry, Langfuse tracing | — |
| 5 | 📝 not-specced | Job system | `spec/specification/job-system.md` | `POST /ai/v1/jobs`, `GET /ai/v1/jobs/{job_id}`, agent registry, Celery task, Redis job cache | — |
| 6 | 📋 planned | Intake Summary Agent | `spec/specification/intake_agent.md` | Agent `intake_summary`, `ai.intake_summaries`, prompt `intake_summary@v1`, rules, samples, eval | — |
| 7 | 📝 not-specced | Verified results | `spec/specification/verified-results.md` | `POST /ai/v1/jobs/{job_id}/verified`, version 2 save, learning event | — |

> Feature 5 depends on the open question **"how backend data is loaded"** (see Open questions below).
> Build it with a fake `backend_data` source until that's answered.

---

## Features — Later phases

| # | Status | Feature | Spec document | Endpoints / changes | Implemented |
|---|--------|---------|---------------|---------------------|-------------|
| 8 | 📝 not-specced | Project Understanding | `spec/specification/project-understanding.md` | Agent `project_understanding`: facts with sources, conflicts, gaps, readiness | — |
| 9 | 📝 not-specced | Knowledge search | `spec/specification/knowledge-search.md` | Embeddings, `ai.knowledge_chunks`, hybrid search (BM25 + vector + rerank) | — |
| 10 | 📝 not-specced | Stakeholder & RACI | `spec/specification/stakeholder-raci.md` | Agent `stakeholder_raci` | — |
| 11 | 📝 not-specced | Current / Future state | `spec/specification/current-future-state.md` | Agent `current_future_state` | — |
| 12 | 📝 not-specced | Impact analysis | `spec/specification/impact-analysis.md` | Agent `impact`, `ai.item_links` | — |
| 13 | 📝 not-specced | Dependency & Risk | `spec/specification/dependency-risk.md` | Agents `dependency`, `risk` | — |
| 14 | 📝 not-specced | Change engine | `spec/specification/change-engine.md` | Change sets, staged versions, `base_version`, undo | — |
| 15 | 📝 not-specced | Workspace Agent | `spec/specification/workspace-agent.md` | `POST /ai/v1/workspace/messages`; intents ask, explain, edit, update-from-notes | — |
| 16 | 📝 not-specced | Document outputs | `spec/specification/document-outputs.md` | Word / Excel / PPT export | — |
| 17 | 📝 not-specced | Learning Agent | `spec/specification/learning-agent.md` | Learning events → training data (SFT/LoRA, later DPO/KTO) | — |

---

## Team Documentation

| Document | Purpose |
|----------|---------|
| `spec/team-guide.md` | How the AI service works. Read it on day one |
| `AGENTS.md` | Instructions for the AI coding agent (not for humans) |
| `agent-memory/architecture.md` (Agents section) | What each agent does and returns |
| `spec/index.md` | Feature status, open questions, decisions and eval results |

## Open questions

- How the AI service loads backend data (read-only DB or API)
- Result delivery: polling, webhook or SSE
- X-User-Role values
- snake_case vs camelCase
- Final problem_category list

## Decisions

- Only LLM: Qwen3.5-4B (`LLM_MODEL` env var)
- Qwen3.5 thinking OFF for agent calls (`LLM_THINK=false`)
- Jobs run on Celery with Redis broker
- Redis is cache only; PostgreSQL `ai` schema is the durable store
- Option A: AI saves `ai_draft`, backend sends verified version, both kept
- IDs are TEXT with a short prefix
- Dev without Docker: Ollama app + Supabase + Upstash
- Dev Supabase is in ap-southeast-2 (Sydney); dev timeout 15s; move to ap-south-1 if latency is a problem.
- Work log updates are managed by `scripts/update_worklog.py` and the local `.githooks/pre-commit` hook.
- The doctor and application use `app.config.Settings` as the shared environment configuration source; doctor output never prints secret values.

## Current phase

- Phase: Feature #1 and local dev setup (#1b) are complete; live services and the full repository checks pass.
- Next: feature #2, service auth & errors; API, solo worker, and Flower are running locally for development.

## Known issues

- An earlier short Doctor database probe timed out; the shared 15-second timeout now passes live Doctor, migrations, and `/health` checks. Status: fixed.
- Doctor database connectivity previously passed `postgresql+asyncpg://` directly to `asyncpg.connect`; both Doctor and health now use the shared SQLAlchemy async-engine helper. Status: fixed.

## Eval results

| Date | Agent | Prompt | Score |
|------|-------|--------|-------|

## Work log

<!-- WORKLOG:START -->
| Date | What was done | Result |
|------|---------------|--------|
| 2026-11-11 | Feature #1 cleanup: moved env reads behind functions, added `LLM_THINK`, and verified the repo checks. | tests passed (ruff + mypy + pytest) |
| 2026-11-11 | Feature #1b local dev setup: added `app.doctor`, hardened offline `.env` validation, documented the no-Docker setup, and verified the doctor tests. | tests passed (doctor + full suite) |
| 2026-11-11 | Fixed the doctor to read `.env` values at runtime, kept secret values masked in output, and re-ran the repo validation. | tests passed (ruff + mypy + pytest) |
| 2026-11-12 | Made `Settings` the shared app/doctor configuration source, isolated tests, and added temporary-dotenv and AI key placeholder coverage. | passed: doctor, ruff, mypy app, pytest (26 passed; one third-party deprecation warning) |
| 2026-11-12 | Added `agent-memory/flow.md` with code-verified connection statuses and documented implemented-vs-planned boundaries. | passed: documentation cross-check against config, health, Celery, Alembic, and doctor code |
| 2026-11-12 | Fixed `/health` database connectivity with a SQLAlchemy async engine, verified Celery ping discovery through the app registry, and completed flow sections 3–9 and documentation references. | passed: Ruff, mypy app (19 files), pytest (27 passed; one third-party deprecation warning) |
| 2026-11-12 | Replaced the health registry class with a name-keyed dict, shared one SQLAlchemy database probe with Doctor, and tested dynamic health-check registration. | pending validation |
| 2026-11-12 | Configured Upstash Redis cache, broker, and result URLs to use DB 0; ran live Doctor checks. | blocked: PostgreSQL connection timed out; Redis and Ollama passed; migrations/API checks not run |
| 2026-11-12 | Diagnosed the PostgreSQL timeout with DNS, TCP checks on 5432/6543, Google HTTPS comparison, and a 20-second SQL probe. | passed: DNS/TCP and 20-second database probe; migrations/API health not requested or run |
| 2026-11-12 | Shared the configurable health timeout, set dev timeout to 15 seconds for Sydney, applied Alembic migrations, and verified `/health` on live services. | passed: Doctor, migration, and `/health` all green |
| 2026-11-13 | Reviewed the remaining local-dev documentation and test/config changes; ran Ruff, mypy app, and pytest before grouped commits. | passed: Ruff, mypy app, pytest (29 passed; one third-party deprecation warning) |
| 2026-11-13 | Added Flower to dev dependencies and documented the API, task monitor, database, Redis, and model URLs with local start commands; verified a real worker ping in Flower. | passed: uv sync; ping SUCCESS; Ruff, mypy app, pytest (29 passed; one third-party deprecation warning) |
<!-- WORKLOG:END -->