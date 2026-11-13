import json
import sys
import requests

from agent.onboarding_agent.scripts.clean_input import clean_intake

MODEL = "cms-summary-v2"
SYSTEM = "Summarize the onboarding answers."


def summarize(raw):
    text = clean_intake(raw)
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
            ],
            "options": {"temperature": 0, "num_predict": 300},
        },
        timeout=120,
    )
    return r.json()["message"]["content"].strip()


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(summarize(json.load(f)))