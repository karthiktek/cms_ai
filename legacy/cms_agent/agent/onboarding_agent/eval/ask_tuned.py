import json
import time
from pathlib import Path

import requests

AGENT_DIR = Path(__file__).resolve().parents[1]
MODEL = "cms-summary-v2"
SYSTEM = "Summarize the onboarding answers."


def ask(text: str) -> str:
    body = {
        "model": MODEL,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 300},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text},
        ],
    }
    r = requests.post("http://localhost:11434/api/chat", json=body, timeout=1800)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


if __name__ == "__main__":
    lines = (AGENT_DIR / "data" / "processed" / "test.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]

    for i, row in enumerate(rows, start=1):
        start = time.time()
        answer = ask(row["input"])
        print(f"===== TEST {i} ({time.time() - start:.0f} seconds) =====")
        print("TUNED:    ", answer)
        print("YOUR TEXT:", row["output"])
        print()