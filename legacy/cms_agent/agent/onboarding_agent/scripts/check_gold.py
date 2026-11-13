import json
from pathlib import Path

from agent.shared.schemas import IntakeAnalysis

gold_path = Path(__file__).resolve().parents[1] / "data" / "gold" / "example_01.json"
with gold_path.open(encoding="utf-8") as f:
    result = IntakeAnalysis.model_validate(json.load(f))

print("OK:", len(result.stakeholders_affected), "stakeholders")