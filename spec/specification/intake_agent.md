# Intake Summary Agent — Specification

> **Last updated:** 2026-11-11
> **Changed:** Aligned docs with sdd-template folder structure

---

## Overview

Adds the first AI agent, `intake_summary`. It reads one submitted client intake (questions and answers) and writes a short, grounded summary: what the change is about, a problem category, key points linked to the question they came from, and the gaps (things the intake did not answer). The output is saved as a **draft** (`ai_draft`) so a TekWissen consultant can review and verify it. This is the base for later agents: Project Understanding merges several verified intake summaries.

---

## Current State

These features must be done before this one starts (see `spec/index.md`):
- **Service skeleton** (#1): app factory, config, `/health`, Docker Compose.
- **Service auth & errors** (#2): service-key and workspace headers, standard error shape.
- **AI database base** (#3): `ai` schema, `ai.jobs`, `ai.runs`, row-level security, `workspace_session`.
- **Model gateway** (#4): Qwen3.5-4B client, prompt loader, forced JSON with one retry, Langfuse tracing.
- **Job system** (#5): `POST /ai/v1/jobs`, `GET /ai/v1/jobs/{job_id}`, agent registry, Celery `run_agent` task, Redis job cache.

Not yet existing:
- No agent is registered yet. The registry is empty.
- There is no `ai.intake_summaries` table.
- How intake data is loaded from the backend is **an open question**. `app/sources/backend_data.py` returns data from a fake source until the backend team answers.

---

## Interface Specification

This feature adds **no new endpoint**. It registers the agent `intake_summary` on the existing job endpoints.

### POST /ai/v1/jobs (with `agent: "intake_summary"`)

| Property | Value |
|----------|-------|
| Method | POST |
| Path | `/ai/v1/jobs` |
| Auth required | Yes (service key + workspace headers) |
| Route | `app/api/routes/jobs.py` (existing) |
| Agent | `app/agents/intake_summary/graph.py` (new) |

**Request headers**
```
X-Service-Key:  <AI_SERVICE_KEY>
X-Workspace-Id: ws_01J...
X-User-Id:      usr_01J...
X-User-Role:    consultant
```

**Request body**
```json
{
  "agent": "intake_summary",
  "workspace_id": "ws_01J...",
  "project_id": "prj_01J...",
  "intake_id": "int_01J..."
}
```

**Success response: 202 Accepted**
```json
{ "job_id": "job_01J...", "agent": "intake_summary", "status": "queued", "created_at": "2026-11-11T10:30:00Z" }
```

### Agent input: `IntakeInput` (loaded by `backend_data.py`, cached in Redis)

```json
{
  "workspace_id": "ws_01J...",
  "project_id": "prj_01J...",
  "intake_id": "int_01J...",
  "project_name": "Payroll move to Workday",
  "client_name": "Acme Corp",
  "submitted_at": "2026-11-10T08:00:00Z",
  "answers": [
    { "question_id": "q_01", "question_text": "What change are you planning?", "answer": "Moving payroll from our legacy system to Workday." },
    { "question_id": "q_07", "question_text": "When should it go live?", "answer": "Q2 next year." },
    { "question_id": "q_09", "question_text": "What is the budget?", "answer": "" }
  ]
}
```

### Agent output: `IntakeSummary` (returned in `GET /ai/v1/jobs/{job_id}` → `result`)

```json
{
  "output_id": "out_01J...",
  "version": 1,
  "status": "ai_draft",
  "summary": "Acme Corp plans to move payroll from a legacy system to Workday, with go-live targeted for Q2 next year. The main concern is keeping payroll accurate during the switch.",
  "problem_category": "technology_change",
  "key_points": [
    { "text": "Payroll moves from the legacy system to Workday", "from_question": "q_01" },
    { "text": "Go-live is targeted for Q2 next year", "from_question": "q_07" }
  ],
  "gaps": [
    { "question_id": "q_09", "field": "budget", "reason": "Not answered in the intake" }
  ]
}
```

**Field rules**

| Field | Rule |
|-------|------|
| `summary` | 2–4 sentences, max 600 characters, plain English, only facts from the answers |
| `problem_category` | One of `process_change`, `technology_change`, `organisation_change`, `policy_compliance_change` *(list to be confirmed)* |
| `key_points` | 1–8 items, each up to 200 characters, no duplicates; `from_question` must be a real `question_id` with a non-empty answer |
| `gaps` | Every empty or "don't know" answer that matters; `question_id` must exist in the input |

### Agent steps (LangGraph)

| # | Step | What it does | Model call? |
|---|------|--------------|-------------|
| 1 | **read** | Read `IntakeInput` from the Redis cache | No |
| 2 | **check** | Validate the input schema. If every answer is empty, fail with `not_ready` | No |
| 3 | **mark** | Mark empty or "don't know" answers as gap candidates | No |
| 4 | **summarise** | Call the gateway with prompt `intake_summary@v1`; answers go in a data block; JSON is forced | Yes (Qwen3.5-4B) |
| 5 | **validate** | Pydantic schema check, then the rules in `app/rules/intake_summary.py` | No |
| 6 | **retry** | If validation fails, call again **once**, sending the errors back. If it still fails, the job fails | Yes (max 1) |
| 7 | **save** | `save_summary_draft()` inserts version 1 (`ai_draft`) in one transaction | No |
| 8 | **finish** | Cache the result in Redis, set the job to `done`, record the run | No |

**Failure cases**

| Case | Job status | `error` |
|------|-----------|---------|
| Intake not found | `failed` | `not_found` |
| All answers empty | `failed` | `not_ready` |
| Model down or timed out (60 s) | `failed` | `model_unavailable` |
| Output still invalid after the retry | `failed` | `internal_error` (raw output saved in `ai.runs` for debugging) |

---

## Database Changes

### New table: `ai.intake_summaries`

```sql
CREATE TABLE ai.intake_summaries (
  id               TEXT        PRIMARY KEY,
  output_id        TEXT        NOT NULL,                 -- same across versions
  workspace_id     TEXT        NOT NULL,
  project_id       TEXT        NOT NULL,
  intake_id        TEXT        NOT NULL,
  job_id           TEXT        REFERENCES ai.jobs(id),
  run_id           TEXT        REFERENCES ai.runs(id),
  version          INTEGER     NOT NULL,
  status           TEXT        NOT NULL CHECK (status IN ('ai_draft', 'verified')),
  summary          TEXT        NOT NULL,
  problem_category TEXT        NOT NULL,
  key_points       JSONB       NOT NULL DEFAULT '[]',
  gaps             JSONB       NOT NULL DEFAULT '[]'
);
```

## Memory updates after the build

- `agent-memory/architecture.md`
- `agent-memory/database.md`
- `spec/index.md`