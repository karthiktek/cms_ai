import json
from pathlib import Path


def looks_like_junk(text: str) -> bool:
    text = str(text).strip().lower()
    return len(text) < 4 or len(set(text)) <= 3


def clean_intake(raw: list[dict]) -> str:
    lines = []
    current_step = None

    for item in raw:
        step = item["step"]
        if step != current_step:
            if current_step is not None:
                lines.append("")
            lines.append(f"Step {step}:")
            current_step = step

        answer = item["answer"]
        if isinstance(answer, list):
            answer = "; ".join(answer)

        line = f"{item['question']}: {answer}"

        detail = item.get("otherDetail")
        if detail:
            flag = " [UNCLEAR]" if looks_like_junk(detail) else ""
            line += f" (detail: {detail}{flag})"

        lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parents[1] / "samples" / "onboarding_01.json"
    with sample_path.open(encoding="utf-8") as f:
        print(clean_intake(json.load(f)))