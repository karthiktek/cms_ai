from __future__ import annotations

from pathlib import Path

from scripts.update_worklog import update_worklog


def test_update_worklog_appends_missing_git_commits(tmp_path: Path) -> None:
    worklog_path = tmp_path / "spec" / "index.md"
    worklog_path.parent.mkdir(parents=True, exist_ok=True)
    worklog_path.write_text(
        "# Sample\n\n"
        "## Work log\n"
        "<!-- WORKLOG:START -->\n"
        "| Date | Commit message | Commit |\n"
        "|------|----------------|--------|\n"
        "| 2026-11-10 | Keep manual row | Keep manual row |\n"
        "<!-- WORKLOG:END -->\n",
        encoding="utf-8",
    )

    git_output = "2026-11-11|Add automatic worklog\n2026-11-10|Keep manual row\n"
    update_worklog(worklog_path, git_log_output=git_output)

    updated = worklog_path.read_text(encoding="utf-8")
    assert "<!-- WORKLOG:START -->" in updated
    assert "<!-- WORKLOG:END -->" in updated
    assert "| 2026-11-10 | Keep manual row | Keep manual row |" in updated
    assert "| 2026-11-11 | Add automatic worklog | Add automatic worklog |" in updated
    assert updated.count("Add automatic worklog") == 2


def test_update_worklog_preserves_manual_rows_and_rewrites_only_marker_block(tmp_path: Path) -> None:
    worklog_path = tmp_path / "spec" / "index.md"
    worklog_path.parent.mkdir(parents=True, exist_ok=True)
    worklog_path.write_text(
        "# Sample\n\n"
        "before\n"
        "<!-- WORKLOG:START -->\n"
        "| Date | Commit message | Commit |\n"
        "|------|----------------|--------|\n"
        "| 2026-11-09 | manual | manual |\n"
        "<!-- WORKLOG:END -->\n"
        "after\n",
        encoding="utf-8",
    )

    git_output = "2026-11-11|New commit\n2026-11-09|manual\n"
    update_worklog(worklog_path, git_log_output=git_output)

    updated = worklog_path.read_text(encoding="utf-8")
    assert updated.index("<!-- WORKLOG:START -->") < updated.index("<!-- WORKLOG:END -->")
    assert "before\n" in updated
    assert "after\n" in updated
    assert "| 2026-11-09 | manual | manual |" in updated
    assert "| 2026-11-11 | New commit | New commit |" in updated
