import json
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = AGENT_DIR / "data" / "processed"

SYSTEM = "Summarize the onboarding answers."


def convert(src, dst):
    lines = (PROCESSED_DIR / src).read_text(encoding="utf-8").splitlines()
    with open(PROCESSED_DIR / dst, "w", encoding="utf-8") as f:
        for line in lines:
            if not line.strip():
                continue
            row = json.loads(line)
            chat = {
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": row["input"]},
                    {"role": "assistant", "content": row["output"]},
                ]
            }
            f.write(json.dumps(chat) + "\n")


convert("train.jsonl", "train_chat.jsonl")
convert("test.jsonl", "test_chat.jsonl")
print("Wrote train_chat.jsonl and test_chat.jsonl")