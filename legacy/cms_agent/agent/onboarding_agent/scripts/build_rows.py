import json
import re
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]

raw = (AGENT_DIR / "data" / "source" / "summaries_todo.txt").read_text(encoding="utf-8")
blocks = re.split(r"^### INPUT \d+\s*$", raw, flags=re.M)[1:]

rows = []
for block in blocks:
    text, _, summary = block.partition("### SUMMARY")
    text, summary = text.strip(), summary.strip()
    if text and summary:
        rows.append({"input": text, "output": summary})

out = AGENT_DIR / "data" / "source" / "train_summary.jsonl"
with open(out, "w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")

print(f"Wrote {len(rows)} filled examples to {out}")