# API Reference

> **Last updated:** 2026-11-11
> **Changed:** The implemented service skeleton exposes the health endpoint; the job-endpoint contract remains planned for feature #5 and is not yet active.

---

## Base URL

```
http://localhost:8000/ai/v1
```

> Local dev. Change this to the Azure (US) URL when we go to production. `/health` sits outside `/ai/v1`.

---

## Standard Response Envelope

> We don't wrap successful responses. A success returns the resource itself. Every error uses one fixed shape.

**Success** returns the resource directly:
```json
{ "job_id": "job_01J...", "status": "queued" }
```

**Error** always returns this shape:
```json
{
  "error":      "not_found",
  "message":    "Job job_01J... was not found",
  "request_id": "req_01J...",
  "details":    ["optional", "list of field errors"]
}
```

Rules:
- `error` is always a fixed code from the list below. Never send free text in it.
- `message` is plain English, safe to show in logs and never shown raw to end users.
- `request_id` is always present. It is the same ID as `X-Request-Id` and the Langfuse trace.
- `details` is an **array of strings**. It only appears on `invalid_request`.
- Field names are `snake_case`. Dates are UTC ISO 8601 (`2026-11-11T10:30:00Z`).

**Error codes**

| Status | `error` | When |
|--------|---------|------|
| 400 | `invalid_request` | Body or params fail validation |
| 401 | `unauthorized` | Service key missing or wrong |
| 403 | `forbidden` | Workspace header doesn't match the resource |
| 404 | `not_found` | Job, intake or project doesn't exist |
| 409 | `conflict` | Job is in the wrong state for this action |
| 422 | `not_ready` | Input data isn't ready (for example, intake not submitted) |
| 429 | `rate_limited` | Too many requests |
| 500 | `internal_error` | Unexpected error |
| 503 | `model_unavailable` | Model server is down or timed out |

---

## Public Endpoints

> No service key needed.

---

### GET /health

Checks that the service, database, Redis and model server can be reached.

**Response 200**
```json
{
  "status": "ok",
  "checks": { "database": "ok", "redis": "ok", "model": "ok" },
  "model": "qwen3.5:4b",
  "version": "0.1.0"
}
```

| Status | Condition | Body |
|--------|-----------|------|
| 200 | All checks pass | `{ status: "ok", checks: {...} }` |
| 503 | Any check fails | `{ status: "degraded", checks: { "model": "down", ... } }` |

---

## Protected Endpoints

> Only the backend service calls these. The frontend never calls the AI service directly.

Every protected request needs these headers:
```
X-Service-Key:  <shared secret, from AI_SERVICE_KEY>
X-Workspace-Id: <workspace_id>
X-User-Id:      <user_id who triggered the action>
X-User-Role:    <consultant | lead | admin>
X-Request-Id:   <optional; generated if missing>
```

| Status | Condition | `message` |
|--------|-----------|-----------|
| 401 | `X-Service-Key` missing | `"Missing service key"` |
| 401 | `X-Service-Key` wrong | `"Invalid service key"` |
| 400 | `X-Workspace-Id` or `X-User-Id` missing | `"Missing required header: X-Workspace-Id"` |
| 403 | Body `workspace_id` ≠ `X-Workspace-Id` | `"Workspace mismatch"` |

---

### POST /ai/v1/jobs

Starts an agent job. It returns at once, and the agent runs in the background (Celery).

**Request body**
```json
{
  "agent":        "intake_summary",
  "workspace_id": "ws_01J...",
  "project_id":   "prj_01J...",
  "intake_id":    "int_01J..."
}
```

- `agent` must be a registered agent. In V1 that is only `intake_summary`.
- Optional `idempotency_key` (string): the same key returns the same `job_id`, so we never get duplicate jobs.

**Response 202**
```json
{
  "job_id":     "job_01J...",
  "agent":      "intake_summary",
  "status":     "queued",
  "created_at": "2026-11-11T10:30:00Z"
}
```

| Status | Condition | Body |
|--------|-----------|------|
| 202 | Job queued | `{ job_id, agent, status: "queued", created_at }` |
| 400 | Unknown agent or missing field | `{ error: "invalid_request", details: [...] }` |
| 403 | Workspace mismatch | `{ error: "forbidden", ... }` |
| 409 | A job for this intake is already queued or running | `{ error: "conflict", ... }` (includes the existing `job_id` in `message`) |
| 422 | Intake not submitted or empty | `{ error: "not_ready", ... }` |
| 429 | Too many jobs | `{ error: "rate_limited", ... }` |

---

### GET /ai/v1/jobs/{job_id}

Gets the job status, and the result once it's done.

**Response 200: still working**
```json
{
  "job_id": "job_01J...",
  "agent":  "intake_summary",
  "status": "running",
  "created_at": "2026-11-11T10:30:00Z",
  "updated_at": "2026-11-11T10:30:04Z"
}
```

**Response 200: done**
```json
{
  "job_id": "job_01J...",
  "agent":  "intake_summary",
  "status": "done",
  "result": {
    "output_id": "out_01J...",
    "version":   1,
    "status":    "ai_draft",
    "summary":   "The client is moving payroll from a legacy system to Workday...",
    "problem_category": "technology_change",
    "key_points": [
      { "text": "Go-live planned for Q2", "from_question": "q_07" }
    ],
    "gaps": [
      { "field": "budget", "reason": "Not answered in the intake" }
    ]
  },
  "run_id":     "run_01J...",
  "created_at": "2026-11-11T10:30:00Z",
  "updated_at": "2026-11-11T10:30:22Z"
}
```

**Response 200: failed**
```json
{
  "job_id": "job_01J...",
  "status": "failed",
  "error":  { "error": "model_unavailable", "message": "Model timed out after 60s" }
}
```

Job status values: `queued → running → done | failed`

| Status | Condition | Body |
|--------|-----------|------|
| 200 | Job found (any status) | the job, as above |
| 403 | Job belongs to another workspace | `{ error: "forbidden", ... }` |
| 404 | Unknown `job_id` | `{ error: "not_found", ... }` |

> Polling for now: every 2–3 s, stop after ~2 min. Webhook or SSE is still to be agreed with the backend team.

---

### POST /ai/v1/jobs/{job_id}/verified

The backend calls this after the user reviews and saves the summary. The AI service stores the verified version (version 2) and records a learning event.

**Request body**
```json
{
  "output_id":   "out_01J...",
  "verified_by": "usr_01J...",
  "verified_at": "2026-11-11T11:05:00Z",
  "result": {
    "summary": "...edited text...",
    "problem_category": "process_change",
    "key_points": [ { "text": "...", "from_question": "q_07" } ],
    "gaps": []
  }
}
```

**Response 200**
```json
{
  "output_id": "out_01J...",
  "version":   2,
  "status":    "verified",
  "changed":   true
}
```

- `changed` is `false` if the user approved the draft without edits. We still record that as a learning signal.

| Status | Condition | Body |
|--------|-----------|------|
| 200 | Verified version saved | `{ output_id, version: 2, status: "verified", changed }` |
| 400 | Result fails the schema | `{ error: "invalid_request", details: [...] }` |
| 403 | Workspace mismatch | `{ error: "forbidden", ... }` |
| 404 | Unknown job or `output_id` | `{ error: "not_found", ... }` |
| 409 | Job not `done`, or already verified | `{ error: "conflict", ... }` |

---

## Planned Endpoints (not V1)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/ai/v1/jobs/{job_id}/events` | SSE progress stream (if chosen over polling) |
| POST | `/ai/v1/jobs` with `agent: "project_understanding"` | Merge intakes into Project Understanding |
| POST | `/ai/v1/jobs` with `agent: "stakeholder_raci"`, `impact`, `risk` … | Change Assessment analyses |
| POST | `/ai/v1/workspace/messages` | Workspace Agent (ask / edit / update-from-notes) |
| POST | `/ai/v1/proposals/{proposal_id}/accept` | Accept staged changes |
| GET | `/ai/v1/outputs/{output_id}/versions` | Version history |