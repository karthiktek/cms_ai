# Merge Plan: CMS Model Agent into `cms_ai`

**Status:** Proposal only. No project files have been moved, copied, deleted, or pushed. The only change made for this request is this plan file.

## Current Model Project Structure

Generated items such as `.git`, `.venv`, and `__pycache__` are omitted below. The root Git repository has no commits or remotes. There is no root `.env` or `.env.example`.

```text
cms_agent/
├── agent/
│   ├── intake_agent/                 (empty placeholder)
│   ├── onboarding_agent/
│   │   ├── data/
│   │   │   ├── gold/                 example_01.json, knowledge.json
│   │   │   ├── processed/            train/test JSONL and chat JSONL
│   │   │   └── source/               summaries_todo.txt, train_summary.jsonl
│   │   ├── eval/                     ask_tuned.py, check_train.py
│   │   ├── model/                    Modelfile, cms-summary-q4_k_m.gguf (~2.5 GB)
│   │   ├── samples/                  onboarding_01.json
│   │   ├── scripts/                  build_rows, check_gold, clean_input,
│   │   │                             convert_chat, split_data
│   │   └── run_summary.py
│   └── shared/                       schemas.py
├── backend/                          (empty placeholder)
├── cache_storage/                    (empty placeholder)
├── data/gold/                        (empty)
├── docs/                             (empty)
├── notebooks/                        (empty)
├── scripts/                          (empty)
├── specs/                            (empty)
├── .gitignore
├── README.md
└── requirements.txt
```

## What the Model Code Does

- **Entry point:** `agent/onboarding_agent/run_summary.py` accepts a JSON file path as its first command-line argument, loads the list of intake answers, calls `clean_intake`, and prints the response. The input path is currently interpreted relative to the shell's working directory.
- **Input cleanup:** `scripts/clean_input.py` groups answers by step, joins list answers, formats question/answer lines, and marks short or low-variety `otherDetail` values as `[UNCLEAR]`.
- **Model call:** the runner sends one synchronous `POST` to `http://localhost:11434/api/chat` via `requests`, using model `cms-summary-v2`, temperature 0, and a 300-token output limit. It does not call `raise_for_status`, configure the endpoint/model through environment settings, retry, or validate the returned text.
- **Prompt:** the system prompt is the inline text `Summarize the onboarding answers.` The Ollama `Modelfile` also defines a template, temperature/stop settings, and a local GGUF base model.
- **Output:** the entry point prints raw assistant text; it does not save a result. `schemas.py` defines `IntakeAnalysis` plus nested stakeholder/gap/question types, but `run_summary.py` does not use those schemas. `check_gold.py` separately validates `data/gold/example_01.json` against `IntakeAnalysis`.
- **Dataset scripts:** `build_rows.py` extracts completed INPUT/SUMMARY blocks; `split_data.py` makes a seeded train/test split; `convert_chat.py` converts rows into chat-message JSONL. `ask_tuned.py` and `check_train.py` call Ollama for evaluation and therefore make real model calls.
- **Dependencies:** Python standard library, `requests`, and Pydantic v2 (`model_validate`). The current `requirements.txt` contains only `requests` and `pydantic`.

## Backend Rules and Current State

Read `AGENTS.md`, all six `agent-memory/` knowledge files, `spec/index.md`, `spec/team-guide.md`, and `spec/specification/intake_agent.md` from the supplied skeleton.

Key rules for any future implementation:

- Only `app/gateway/` may call a model. Model name and endpoint come from configuration; do not hard-code them.
- Validate every model output with a Pydantic schema and deterministic rules; retry invalid output once. Missing information belongs in gaps, never guessed.
- Treat intake text as untrusted data, not instructions. Save AI drafts only; do not publish or overwrite verified results.
- Keep prompts versioned in `app/prompts/` and add a new version instead of editing released prompts.
- Follow the feature-first workflow: update/write the spec and index before implementation, update relevant `agent-memory/` docs, then run tests and evaluation.
- Preserve the open questions in `spec/index.md`; notably backend data access, result delivery, and final category values are not decided.

The backend skeleton's Git remote is `https://github.com/karthiktek/cms_ai.git`; branch `main` is clean and matches `origin/main` at `e7d7d83` (`chore: add Flower + see-it-running guide`). It has eight commits. The model workspace's Git repo has no commits and no remote.

The skeleton's actual tree contains `app/` (FastAPI app, config, health route, database probe, Doctor, Celery setup, and empty feature package placeholders), `tests/`, `migrations/`, `agent-memory/`, `spec/`, `scripts/`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `uv.lock`, `alembic.ini`, `.env.example`, and `.githooks/`. Its documentation describes future `app/gateway/`, job routes, agent registry, and Intake Summary implementation, but these are not present yet. `spec/index.md` marks Feature #6 Intake Summary as planned; Features #2–#5 are prerequisites and the job/model call path has not been implemented.

## Proposed Single-Project Layout

Use the backend skeleton as the root project and keep the current model project intact under `legacy/cms_agent/` until Feature #6 is specified and implemented. The legacy area would retain the current `agent/` tree, its `README.md`, and its `requirements.txt`; keep generated caches and virtual environments out of the merge. Preserve the existing empty placeholders (`backend/`, `cache_storage/`, `data/gold/`, `docs/`, `notebooks/`, `scripts/`, and `specs/`) unless a later approved cleanup explicitly addresses them.

```text
cms_ai/                             (backend repository root)
├── AGENTS.md
├── agent-memory/
├── app/
├── migrations/
├── spec/
├── tests/
├── scripts/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── .env.example
├── Dockerfile / docker-compose.yml / .githooks/
└── legacy/
    └── cms_agent/
        ├── agent/                  (existing model project tree, unchanged initially)
        ├── README.md               (preserved model-project guide)
        └── requirements.txt        (legacy-only dependency record)
```

The backend's root `README.md`, `.gitignore`, `pyproject.toml`, and lockfile remain authoritative. Preserve the model workspace's `data/raw/` ignore rule when reconciling `.gitignore`; do not replace backend ignore/security rules.

## Later Feature #6 Reuse Map

Reuse as reference material, not as a direct drop-in implementation. Feature #6 has a different specified output (`summary`, `problem_category`, `key_points`, `gaps`) and must follow the backend's gateway, rule, persistence, and job contracts.

| Current model asset | Possible future home | Required adaptation |
|---|---|---|
| `run_summary.py` orchestration | `app/agents/intake_summary/` (`state.py`, `nodes.py`, `graph.py`) | Replace direct HTTP request with the shared gateway and implement the specified LangGraph stages/job flow. |
| Inline system text and `Modelfile` prompt/template | `app/prompts/intake_summary@v1.md` | Create a versioned, grounded prompt using an explicit data block; model serving/template details stay in the gateway/deployment configuration. |
| `agent/shared/schemas.py` | `app/schemas/intake.py` | Use as type-design reference only. `IntakeAnalysis` does not match the Feature #6 `IntakeSummary` contract; define and validate the specified fields. |
| `clean_input.py` normalization and junk heuristic | `app/rules/intake_summary.py` | Review and test deterministic behavior against `IntakeInput`; do not assume the current `[UNCLEAR]` heuristic is the feature's gap policy. |
| `samples/`, `data/gold/`, source and processed JSONL | `tests/samples/intake_summary/` and evaluation inputs | Review privacy and convert inputs/expected outputs to the feature's exact schemas; current gold output is a different contract. |
| `build_rows.py`, `split_data.py`, `convert_chat.py`, evaluation scripts | Development/evaluation tooling, if still needed | Keep outside request-time app code; tests must use a fake gateway, and any real-model eval must use the backend's configured gateway. |

## Dependency and Runtime Compatibility

- **Pydantic:** no conflict identified. Backend requires `pydantic>=2.8.0`; the model code uses the Pydantic v2 `model_validate` API.
- **Requests:** not listed in backend `pyproject.toml`. This is a missing direct dependency only if legacy scripts are run in the backend environment, not a version conflict. Prefer keeping it in the legacy requirements while the code remains isolated. Do not add a direct `requests` model call to `app/`; the backend requires model access through its gateway (which uses the backend's HTTP client stack).
- **Python:** backend requires Python 3.12+. The model code's syntax is compatible with that minimum.
- **Runtime model mismatch:** legacy scripts use Ollama model `cms-summary-v2`; backend configuration defaults to `LLM_MODEL=qwen3.5:4b`. The legacy model name, raw-text output, and broad `IntakeAnalysis` schema are not interchangeable with Feature #6's configured model and `IntakeSummary` contract.

## Secrets and Environment

The model workspace currently has no `.env`. The backend checkout has a local `.env` that is ignored by Git and is not tracked; its values were not read or included here. After the merge is approved, manually transfer only the needed local values into the final root `.env`, using the backend `.env.example` variable names as the guide. Keep `.env` ignored, never stage or commit it, and verify with `git status` before commit/push. Do not put secret values in this plan or documentation.

## Merge and Git Sequence (After Approval Only)

1. Confirm this plan and the target merge/push branch with the user. No merge or push is authorized by this plan alone.
2. Make and verify a separate backup of the current model project, including its approximately 2.5 GB GGUF file and data. Do not rely on Git to back up untracked assets.
3. Use a clean staging clone of `karthiktek/cms_ai` at its current `main` as the base so its complete backend `.git` history is retained. Do not nest `.git` directories or copy the skeleton's `.git` into the existing repository. The current model repo has no commits to preserve.
4. Place the existing model project under `legacy/cms_agent/` without editing its code or data. Preserve its README and requirements under that legacy directory; reconcile ignore rules without dropping either project's rules. Leave the backend's `AGENTS.md`, `agent-memory/`, `spec/`, `app/`, `tests/`, `migrations/`, `pyproject.toml`, `alembic.ini`, `.env.example`, and supporting files at the root.
5. Manually configure the final root `.env`; do not copy secret values through Git or add `.env` to the index.
6. Review the staged diff and file inventory, run the backend's Ruff, mypy, and pytest checks, and run any approved non-model legacy checks. Do not run real-model evaluation without explicit approval; Feature #6 evaluation must follow backend rules.
7. Commit the integration on a clearly named branch based on backend `main`, push that branch to the same `origin` repository, and open a PR for review before merging to `main`.

**Approval gate:** Stop here and wait for the user's explicit OK before performing any merge, file movement/copying, environment transfer, commit, or push.
