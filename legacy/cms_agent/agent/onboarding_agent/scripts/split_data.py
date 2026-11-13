import json
import random
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]

source_dir = AGENT_DIR / "data" / "source"
processed_dir = AGENT_DIR / "data" / "processed"
lines = (source_dir / "train_summary.jsonl").read_text(encoding="utf-8").splitlines()
rows = [json.loads(line) for line in lines if line.strip()]

random.Random(42).shuffle(rows)
test, train = rows[:4], rows[4:]


def save(name, items):
    with open(processed_dir / name, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")


save("train.jsonl", train)
save("test.jsonl", test)
print(f"train: {len(train)}  test: {len(test)}")