# Feature Specifications Index

> **Last updated:** 2026-11-11
> **Changed:** Added the tracker sections for work log, current phase, known issues, and the final decision on worklog automation.

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
| 1 | ✅ done | Service skeleton | `spec/specification/service_skeleton.md` | App factory, config, `GET /health`, Docker Compose (Redis, Postgres+pgvector, Ollama, Langfuse) | 2026-11-11 |
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
- Jobs run on Celery with Redis broker
- Redis is cache only; PostgreSQL `ai` schema is the durable store
- Option A: AI saves `ai_draft`, backend sends verified version, both kept
- IDs are TEXT with a short prefix
- Work log updates are managed by `scripts/update_worklog.py` and the local `.githooks/pre-commit` hook.

## Current phase

- Phase: V1 service skeleton complete.
- Next: feature #2, service auth & errors.

## Known issues

- No open issues. Status: fixed.

## Eval results

| Date | Agent | Prompt | Score |
|------|-------|--------|-------|

## Work log

<!-- WORKLOG:START -->
| Date | What was done | Result |
|------|---------------|--------|
| 2026-11-11 | Updated the tracker and verified the repo checks for the worklog automation task. | tests passed (ruff + mypy + pytest) |
<!-- WORKLOG:END -->