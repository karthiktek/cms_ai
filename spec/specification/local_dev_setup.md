# Local Dev Setup (no Docker) — Specification

> **Last updated:** 2026-11-11
> **Changed:** First version.

## Overview
Developers on company laptops have no Docker. Local dev uses the Ollama Windows app (model), Supabase (Postgres) and Upstash (Redis). This feature adds a `doctor` command that checks `.env` and every service connection, prints clear fixes, and never prints secrets.

## Current State
- Feature #1 (skeleton) is done. `/health` exists.
- `.env` must be filled by hand; wrong URLs give unclear errors (for example, "Could not parse SQLAlchemy URL").

## Interface
Command: `uv run python -m app.doctor`

Checks, in order. Each prints `OK` / `FAIL` + a one-line fix:

| # | Check | FAIL message example |
|---|-------|----------------------|
| 1 | `.env` file exists | ".env missing — run: copy .env.example .env" |
| 2 | All required vars set and not placeholders (`<`, `>`, `[`, `]`, `YOUR-`, empty) | "DATABASE_URL still has a placeholder" |
| 3 | `DATABASE_URL` parses and starts with `postgresql+asyncpg://` | "Use postgresql+asyncpg:// not postgresql://" |
| 4 | Password chars `@ # / :` are URL-encoded | "Password has '@' — replace with %40" |
| 5 | Supabase uses the session pooler (port 5432, `pooler.supabase.com`) | "Use the Session pooler URL, not direct/transaction" |
| 6 | Redis URLs start with `rediss://` for Upstash; Celery URLs have `ssl_cert_reqs` | "Add ?ssl_cert_reqs=required to CELERY_BROKER_URL" |
| 7 | Database connects (`SELECT 1`, 5 s) | "Cannot reach database: <short reason>" |
| 8 | Redis connects (`PING`, 5 s) | "Cannot reach Redis: <short reason>" |
| 9 | Ollama reachable and `LLM_MODEL` pulled | "Run: ollama pull qwen3.5:4b" |
| 10 | `LLM_THINK` is false | "Set LLM_THINK=false" |

Rules:
- Secrets are always masked as `****` in output.
- Exit code 0 if all OK, 1 if any FAIL.
- Checks 1–6 run even if nothing is reachable (offline checks).

## Database Changes
None.

## Implementation Checklist
| File | Change |
|------|--------|
| `app/doctor.py` | Create — the 10 checks, masked output, exit code |
| `.env.example` | Add comments: Supabase session pooler and Upstash examples, how to encode passwords |
| `tests/test_doctor.py` | Create — test cases below (no network; mock connections) |
| `agent-memory/project-overview.md` | Add "Local dev without Docker" section + doctor command |
| `spec/index.md` | Add row #1b, Decision: "Dev without Docker: Ollama app + Supabase + Upstash" |

## Test Cases
| # | Description | Expected |
|---|-------------|----------|
| 1 | No `.env` | FAIL check 1 |
| 2 | Placeholder in DATABASE_URL | FAIL check 2 |
| 3 | `postgresql://` prefix | FAIL check 3 with fix |
| 4 | Unencoded `@` in password | FAIL check 4 |
| 5 | Direct Supabase host | FAIL check 5 |
| 6 | Celery URL without ssl_cert_reqs | FAIL check 6 |
| 7 | Password never appears in output | output has `****` only |
| 8 | All mocked OK | exit code 0 |

## Scope
In: doctor command, `.env.example` comments, docs.
Out: creating Supabase/Upstash accounts, writing real secrets, Docker.

## Current stage
Spec written. Ready to implement.