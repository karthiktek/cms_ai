# CMS Onboarding Agent

A small project for cleaning onboarding responses, preparing summary datasets, and validating structured intake output.

## Folders

- `agent/shared/`: shared Pydantic schemas.
- `agent/onboarding_agent/`: onboarding samples, data, scripts, evaluation helpers, and local Ollama model files.
- `agent/intake_agent/`: reserved for intake-agent code.
- `backend/`, `cache_storage/`, `notebooks/`, `docs/`: reserved project areas. `docs/` receives the former `specs/` contents.
- `_to_delete/`: preserved files collected separately; not used by the scripts.

Onboarding data is divided into `data/source/`, `data/processed/`, and `data/gold/`.

## Setup and checks

Run these commands from the project root:

```powershell
python -m pip install -r requirements.txt
python -m compileall -q agent
python -m agent.onboarding_agent.scripts.check_gold
```

## Data preparation

Run from the project root. These commands read or write files under `agent/onboarding_agent/data/`:

```powershell
python -m agent.onboarding_agent.scripts.clean_input
python -m agent.onboarding_agent.scripts.build_rows
python -m agent.onboarding_agent.scripts.split_data
python -m agent.onboarding_agent.scripts.convert_chat
```

## Optional Ollama inference

The evaluation scripts make requests to the local Ollama API; do not run them for syntax or schema checks. To prepare the model, run from the project root:

```powershell
Push-Location agent/onboarding_agent/model
ollama create cms-summary-v2 -f Modelfile
Pop-Location
```

With Ollama available, inference can be started with:

```powershell
python -m agent.onboarding_agent.eval.ask_tuned
python -m agent.onboarding_agent.eval.check_train
```
