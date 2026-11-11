from __future__ import annotations

import subprocess
from pathlib import Path

START_MARKER = "<!-- WORKLOG:START -->"
END_MARKER = "<!-- WORKLOG:END -->"
HEADER_LINE = "| Date | Commit message | Commit |"
SEPARATOR_LINE = "|------|----------------|--------|"


def git_log_lines(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "log", "--date=short", "--pretty=format:%ad|%s"],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def parse_git_log(lines: list[str]) -> list[str]:
    rows: list[str] = []
    seen: set[tuple[str, str]] = set()
    for entry in lines:
        if "|" not in entry:
            continue
        date, message = entry.split("|", 1)
        date = date.strip()
        message = message.strip()
        if not date or not message:
            continue
        key = (date, message)
        if key in seen:
            continue
        seen.add(key)
        rows.append(f"| {date} | {message} | {message} |")
    return rows


def parse_existing_rows(block: str) -> list[str]:
    rows: list[str] = []
    for line in block.splitlines():
        value = line.strip()
        if not value.startswith("|"):
            continue
        cells = [cell.strip() for cell in value.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "date":
            continue
        rows.append(value)
    return rows


def merge_worklog(existing_block: str, commit_rows: list[str]) -> str:
    existing_rows = parse_existing_rows(existing_block)
    seen: set[str] = set()
    merged_rows: list[str] = []

    for row in existing_rows + commit_rows:
        clean = row.strip()
        if not clean:
            continue
        if clean in seen:
            continue
        seen.add(clean)
        merged_rows.append(clean)

    table_lines = [HEADER_LINE, SEPARATOR_LINE, *merged_rows]
    return "\n".join(table_lines) + "\n"


def update_worklog(path: Path, git_log_output: str | None = None) -> None:
    path = path.resolve()
    content = path.read_text(encoding="utf-8")

    start_index = content.find(START_MARKER)
    end_index = content.find(END_MARKER)
    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError(f"Missing WORKLOG markers in {path}")

    before = content[: start_index + len(START_MARKER)]
    after = content[end_index:]
    existing_block = content[start_index + len(START_MARKER) : end_index]

    if git_log_output is None:
        git_log_output = "\n".join(git_log_lines(path.parent.parent))

    commit_rows = parse_git_log(git_log_output.splitlines())
    new_block = merge_worklog(existing_block, commit_rows)
    path.write_text(before + "\n" + new_block + "\n" + after, encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    worklog_path = repo_root / "spec" / "index.md"
    update_worklog(worklog_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
