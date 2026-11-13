# Coding Conventions

> **Last updated:** 2026-11-12
> **Changed:** Documented the shared async database probe and name-keyed health check registry pattern.

These rules apply to every change in this codebase.
When in doubt, match the existing code — don't introduce new patterns.

---

## Language & Module System

- Python 3.12+ only.
- Type hints on every function, argument and return value; type checking with mypy in strict mode.
- No `Any` unless unavoidable and commented; prefer Pydantic models.
- Absolute imports from the `app` package (`from app.data.repositories import jobs`). No relative imports across packages.
- `async` for all I/O: database, Redis, model calls, HTTP. Celery tasks call async code through one shared helper.
- Dependencies managed with `uv`; versions locked in `uv.lock`.
- FastAPI app lifecycle code uses a single `lifespan` context manager passed to `FastAPI(lifespan=...)`; deprecated `@app.on_event("startup"/"shutdown")` hooks are not used.
- The application and `app.doctor` use `app.config.Settings` as their single environment configuration source; do not implement separate `.env` parsing in the doctor. Tests that need isolation pass `_env_file=None` or explicitly set environment variables.
- Database connectivity probes shared by health and Doctor live in `app.database`; pass the SQLAlchemy URL unchanged and configure the caller's timeout.
- Formatting and linting with Ruff; no unused imports, no commented-out code, no `print()` (use the logger).
- `snake_case` for functions, variables, files and JSON fields; `PascalCase` for classes and Pydantic models; `UPPER_CASE` for constants.

---

## Response Envelope

Success responses return the resource directly. Errors always use one shape (as agreed in the AI API Agreement).

Success (example: job created):
```json
{
  "job_id": "job_9a3c5d81",
  "status": "queued"
}
```

Error:
```json
{
  "error": "not_found",
  "message": "Job not found",
  "request_id": "req_5f2c9a11"
}
```

- `error` is always a fixed code from the list in `data-contracts.md` (e.g. `invalid_request`, `unauthorized`, `forbidden`, `not_found`, `not_ready`, `rate_limited`, `internal_error`, `model_unavailable`).
- `message` is short, plain English and safe to show; never a stack trace or internal detail.
- `request_id` is always included, so the backend team can report issues.
- Validation errors (`400`) may add `"details": [{ "field": "...", "problem": "..." }]`.
- Field names in `snake_case`; dates in UTC ISO 8601 (`2026-11-11T10:30:00Z`); empty values as `null`, never missing.

---

## Error Handling

- API routes never contain `try/except` for business logic; errors raise typed exceptions (`NotFoundError`, `ForbiddenError`, `NotReadyError`, `ModelUnavailableError`…) handled by one FastAPI exception handler that returns the standard error shape.
- Agents and Celery tasks catch errors at the job level: the job is set to `failed` with a clear `error_reason`; nothing is half-saved (one database transaction per save).
- Invalid model output: retry once with the validation errors; then `failed`. Never save output that fails its schema.
- Model server unavailable or timeout: Celery retries with backoff (max 3); then `failed` with `model_unavailable`.
- Logs are structured (JSON) and include `request_id`, `job_id`, `workspace_id`, `project_id`, `agent`, `step`.
- Never log client answers, personal data, prompts or secrets in application logs. Full prompts and outputs go to Langfuse only, with personal data masked.

---

## Security Rules

- Every request must include a valid `X-Service-Key`; otherwise `401`.
- Every request must include `X-Workspace-Id`, `X-User-Id`, `X-User-Role`; data access is always scoped to that workspace (row-level security).
- The workspace is set by the server for each job; the model never chooses or sees other workspaces.
- Client answers, notes and files are passed to the model inside marked data blocks and are never treated as instructions.
- Never hardcode secrets, model endpoints or connection strings — always environment variables.
- Never expose internal fields (prompts, raw model output, trace IDs of other workspaces, stack traces) in API responses.
- Read backend data only with the read-only database user (if direct access is agreed); never write to the `core` schema.
- Agents only create drafts and proposals; they never approve or publish anything.
- No outside AI services: all models run on TekWissen's own servers.

---

## Testing Rules

- Tests live in `tests/`, mirroring the `app/` structure: `tests/<area>/test_<feature>.py`.
- pytest + pytest-asyncio; API tests use FastAPI's test client (no real port opened).
- Agent tests use a **fake model gateway** with fixed responses; no real model calls in unit tests.
- Database tests run against a test database; each test runs in a transaction that is rolled back.
- Celery tasks are tested by calling the task function directly (eager mode).
- Sample inputs and expected outputs live in `tests/samples/<agent>/`; the evaluation (`eval` script) runs them against the real model.
- Required for every change:
  - unit tests for every new rule, schema and repository function
  - an agent test for every new agent step
  - a security test for every new endpoint (missing key → 401, other workspace → 403/404)
- Run the evaluation after any prompt, model or schema change; results must not get worse.

---

## Adding a New Feature

Follow this sequence every time — no exceptions:

1. Write the spec in `spec/specification/<feature>.md` (purpose, inputs, outputs, steps, rules, test cases).
2. Add a row to `spec/index.md` (status: `planned`).
3. Update the affected memory files first if the feature changes them: `agent-memory/api-reference.md`, `agent-memory/architecture.md` (Agents section), `agent-memory/database.md`.
4. Change the row to `in-progress`, then implement: schema → repository → rules → agent step → task → API route.
5. Add prompts as new versioned files in `prompts/` (never edit a released prompt; create a new version).
6. Write tests; run the full test suite and the evaluation.
7. Update `spec/index.md`.
8. Set the `spec/index.md` row to `done` and add the date.

---

## What NOT to Do

- Do not call a model outside the model gateway.
- Do not put prompts inside agent code; prompts live in `prompts/`, versioned.
- Do not save model output that has not passed its Pydantic schema and validation rules.
- Do not invent facts, fill gaps with guesses, or let prompts allow it.
- Do not write SQL outside `app/data/queries/`.
- Do not query the database without a `workspace_session`.
- Do not update AI outputs in place; always insert a new version.
- Do not keep data only in Redis; it is a cache, never the only copy.
- Do not run long AI work inside an API request; use a Celery task and return a `job_id`.
- Do not write to the backend's `core` schema.
- Do not expose stack traces, prompts or internal fields in API responses.
- Do not hardcode secrets, model names or URLs; use environment variables.
- Do not switch the model for one agent in code; models are set in config (`LLM_MODEL`).
- Do not skip writing a spec before implementing.
- Do not leave `agent-memory/` files out of sync with the code.