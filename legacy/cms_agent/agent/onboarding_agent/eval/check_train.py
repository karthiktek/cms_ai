import json
from pathlib import Path

from agent.onboarding_agent.eval.ask_tuned import ask

AGENT_DIR = Path(__file__).resolve().parents[1]
lines = (AGENT_DIR / "data" / "processed" / "train.jsonl").read_text(encoding="utf-8").splitlines()
row = json.loads(lines[0])

print("MODEL:       ", ask(row["input"]))
print()
print("TRAIN TARGET:", row["output"])