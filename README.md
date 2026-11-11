# TekWissen CMS – AI Service · SDD Setup

> **Last updated:** 2026-11-11
> **Changed:** Aligned docs with sdd-template folder structure

**Spec-driven development for the AI backend.** This folder setup keeps AI coding agents and new developers up to date with the AI service from day one: the agents, the model gateway, the job flow and the `ai` schema.

> Scope: only the AI side. The frontend and main backend are owned by the backend team and documented in their own repos.

---

## What's included

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
└── agent-memory/
    ├── project-overview.md
    ├── architecture.md
    ├── api-reference.md
    ├── database.md
    └── conventions.md
```

---

## How to use

Clone the repo. The three layers are already in the project root:
```
AGENTS.md
spec/
agent-memory/
```

The coding agent (Kiro) loads `AGENTS.md` automatically and reads `agent-memory/` before writing code.
Developers start with `spec/team-guide.md`.

---

## Setup status

1. `AGENTS.md`: project rules and workflow are filled ✅
2. `agent-memory/project-overview.md`: stack, model, environment variables and scripts are filled ✅
3. `agent-memory/architecture.md`: folder map, agent details and request flow are filled ✅
4. `agent-memory/api-reference.md`: V1 job endpoints are filled ✅
5. `agent-memory/database.md`: AI schema and repository guidance are filled ✅
6. `agent-memory/conventions.md`: coding and workflow rules are filled ✅
7. `spec/index.md`: feature register, open questions and decisions are filled ✅
8. `spec/team-guide.md`: developer onboarding is filled ✅
9. `spec/specification/intake_agent.md`: Intake Summary Agent specification is filled ✅

---

## The Three Layers

| Layer | File/Folder | Purpose | Audience |
|-------|------------|---------|----------|
| 1 — Instructions | `AGENTS.md` | How the coding agent behaves, plus the rules that never change | AI coding agent |
| 2 — Knowledge | `agent-memory/` | Current state of the AI service | AI coding agent + developers |
| 3 — Intent | `spec/` | Which agents and features are planned, in progress or done | Developers + AI coding agent |

---

## The workflow

```
Write the spec  →  Build the feature  →  Update the memory  →  Run the tests + eval
```

Every feature. Every time. No exceptions.

For the pre-commit hook to run locally once, run:

```
git config core.hooksPath .githooks
```

For any change to an agent, prompt or schema, also run the eval (`tests/eval.py`). The score must not drop.

---

## Feature order

| Phase | Feature | Status |
|-------|---------|--------|
| V1 | Intake Summary Agent | planned |
| V2 | Project Understanding (merge intakes, facts, gaps, conflicts) | planned |
| V2 | Change Assessment analyses (stakeholder + RACI, current/future, impact, dependency, risk) | planned |
| V3 | Workspace Agent (ask, explain, edit, update-from-notes) | planned |
| Later | Learning Agent (uses verified versions) | planned |

---

## The golden rule

> `agent-memory/` must always reflect the actual code.
> If the code changes, the relevant file in `agent-memory/` changes too.
> A prompt, schema or model change without updated memory and a passing eval does not count as done.