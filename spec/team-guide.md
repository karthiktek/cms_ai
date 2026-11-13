# Team Guide — TekWissen CMS AI Service

> **Last updated:** 2026-11-12
> **Changed:** Added the service flow guide and clarified that the Intake Summary job path remains planned.

Welcome. Read this before writing any code.

> This repo is **only the AI service**: the agents, the model gateway, the job system and the `ai` database schema.
> The frontend and main backend belong to the backend team. They call us over HTTP; we never serve the frontend directly.

---

## What this service does (in 30 seconds)

- The backend sends a job (for example, "summarise intake X") to `POST /ai/v1/jobs` and gets a `job_id` back right away.
- A Celery worker loads the data into Redis and runs the agent (LangGraph steps).
- The agent calls **Qwen3.5-4B** through the model gateway, checks the output against a schema and rules, and saves a **draft** (`ai_draft`).
- The backend fetches the result. The user reviews and verifies it in the frontend, and the backend tells us with `/verified`. We save the verified version and record a learning event.

**AI proposes, people approve.** Nothing the AI makes is final until a user verifies it.

---

## Why this project is structured this way

AI coding agents forget everything between sessions.
New developers take days to get up to speed.
Both problems have the same solution: **structured, maintained documentation
that lives inside the repo.**

This project uses a three-layer system:

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1 — INSTRUCTIONS    AGENTS.md                     │
│  "How should the coding agent behave?"                   │
│  Loaded automatically by Kiro every session              │
├──────────────────────────────────────────────────────────┤
│  Layer 2 — KNOWLEDGE       agent-memory/                 │
│  "What does the AI service look like right now?"         │
│  Updated every time the code changes                     │
├──────────────────────────────────────────────────────────┤
│  Layer 3 — INTENT          spec/                         │
│  "Which agents and features are we building?"            │
│  Written before any implementation begins                │
└──────────────────────────────────────────────────────────┘
```

---

## Layer 1 — AGENTS.md

One file at the project root. It has a short list of rules that never change, plus four steps for the coding agent:
1. Read the knowledge base
2. Check the feature index
3. Update the knowledge base after every change
4. Run the tests (and the eval for agent changes) before closing

---

## Layer 2 — agent-memory/

Six markdown files. Each answers a different question:

| File | Question it answers |
|------|-------------------|
| `project-overview.md` | What is this project? Which model and stack? How do I run it? |
| `architecture.md` | What folders exist? How do the layers connect? What is the request flow? |
| `api-reference.md` | What endpoints exist? Which headers, request and response shapes, and error codes? |
| `database.md` | What tables, row-level security rules, queries and repository functions exist? |
| `flow.md` | How do requests, data and connections move through the service? |
| `conventions.md` | What rules must every developer follow? |

**Every file has a `Last updated` timestamp** so you can tell at a glance
whether the documentation is current.

**The golden rule:** when the code changes, the relevant `agent-memory/` file
changes too. Two automatic hooks enforce this. They remind the agent to sync
after every source file save and after every completed task.

---

## Layer 3 — spec/

Every feature gets a spec document written **before** implementation starts.

```
spec/
├── index.md
├── team-guide.md
└── specification/
    └── intake_agent.md
```

### spec/index.md

The feature register. One row per feature with a status:
- `📝 not-specced`: agreed in the plan, spec not written
- `📋 planned`: spec written, not started
- `🚧 in-progress`: being built
- `✅ done`: shipped and tested

### Writing a spec

Each spec document should cover:
1. **Overview**: what this feature does and why
2. **Current state**: what already exists that is relevant
3. **Endpoint / interface specification**: exact request and response shapes
4. **Agent design** (agent features only): steps, prompt version, output schema, rules, failure cases
5. **Database changes**: any new tables, migrations or queries
6. **Implementation checklist**: an ordered list of files to create or modify
7. **Test cases**: unit, API and repository tests, plus **eval samples** for agents
8. **Scope**: what is in and out of scope

See `spec/specification/intake_agent.md` for a complete example.

---

## Key rules for this AI service

| Rule | Why |
|------|-----|
| Only `app/gateway/` calls the model | One place for prompts, JSON forcing, retries and tracing |
| Model name comes from `LLM_MODEL` (Qwen3.5-4B) | It can be swapped without changing code |
| Every output is checked by a Pydantic schema, with one retry | A small model must return exact formats |
| Missing information goes in `gaps`, never guessed | Consultants must be able to trust the output |
| Agents save drafts only and never overwrite | Every version is kept for review and learning |
| Every query runs in `workspace_session` | One client's data never leaks into another |
| Intake text is data, never instructions | Protects against prompt injection |
| Prompts are versioned files (`name@vN.md`) | Changes can be tracked, tested and rolled back |
| Don't decide open questions alone | Leave a `TODO(open-question)` and add it to `spec/index.md` Open questions |

---

## Run it locally

```
cp .env.example .env          # fill in local values
docker compose up -d          # Redis, Postgres+pgvector, Ollama, Langfuse
ollama pull qwen3.5:4b        # first time only
uv sync                       # install dependencies
uv run alembic upgrade head   # create the ai schema
uv run uvicorn app.main:app --reload --port 8000   # API
uv run celery -A app.tasks.celery_app worker -l info   # worker
```

Check that everything is up: `GET http://localhost:8000/health`

---

## The developer workflow

Every feature follows this exact sequence, with no shortcuts:

```
1.  Write spec → spec/specification/<feature>.md
         ↓
2.  Add row to spec/index.md  (status: planned)
         ↓
3.  Change status to in-progress, start implementing
         ↓
4.  Update agent-memory/ files that were affected
         ↓
5.  Run ruff, mypy, pytest — all must pass
    (agent / prompt / schema change → also run the eval, score must not drop)
         ↓
6.  Update spec/index.md  (status: done, add date)
```

---

## Quick reference

| Situation | What to do |
|-----------|-----------|
| Starting a new feature | Write the spec first |
| Not sure what exists | Check `spec/index.md` |
| Not sure how something works | Read `agent-memory/` |
| Adding a new agent | Add a schema, prompt, rules, graph, registry entry and samples, then update `agent-memory/architecture.md` (Agents section) |
| Changing a prompt | Add a new version file, run the eval, update `agent-memory/architecture.md` (Agents section) |
| Changed an endpoint | Update `agent-memory/api-reference.md` |
| Changed the database | Add an Alembic migration and update `agent-memory/database.md` |
| Added a new file or folder | Update `agent-memory/architecture.md` |
| Added a dependency or env var | Update `agent-memory/project-overview.md` |
| Introduced a new pattern | Update `agent-memory/conventions.md` |
| Hit an undecided question | Add it to `spec/index.md` Open questions and don't guess |
| Finishing any task | Run the full test suite (+ eval for agent changes) |

---

## One sentence summary

> Write the spec, build the feature, update the memory, run the tests and the eval.