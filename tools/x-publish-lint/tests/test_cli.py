"""CLI tests using Typer's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from x_publish_lint.cli import app

runner = CliRunner()


def _env(tool_root: Path) -> dict[str, str]:
    return {"X_PUBLISH_LINT_ROOT": str(tool_root)}


def test_list_rules_shows_all_nine(tool_root: Path) -> None:
    result = runner.invoke(app, ["list-rules"], env=_env(tool_root))
    assert result.exit_code == 0, result.output
    lines = [ln for ln in result.output.splitlines() if ln.strip()]
    assert len(lines) == 9
    assert "engagement.reply_hook" in lines


def test_audit_good_json_parses(tool_root: Path, fixtures_dir: Path) -> None:
    result = runner.invoke(
        app,
        ["audit", str(fixtures_dir / "draft_good.md"), "-f", "json"],
        env=_env(tool_root),
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "overall_score" in payload
    assert "risk_level" in payload


def test_audit_bad_markdown_fail_on_high_exits_one(
    tool_root: Path, fixtures_dir: Path
) -> None:
    result = runner.invoke(
        app,
        [
            "audit",
            str(fixtures_dir / "draft_bad.md"),
            "-f",
            "markdown",
            "--fail-on",
            "high",
        ],
        env=_env(tool_root),
    )
    assert result.exit_code == 1, result.output
    assert "# X Publish Lint" in result.output


def test_scorecard_out_creates_parents(
    tool_root: Path, fixtures_dir: Path, tmp_path: Path
) -> None:
    out = tmp_path / "nested" / "deeper" / "scorecard.md"
    result = runner.invoke(
        app,
        ["scorecard", str(fixtures_dir / "draft_good.md"), "--out", str(out)],
        env=_env(tool_root),
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "# X Publish Lint" in out.read_text(encoding="utf-8")


def test_audit_unknown_format_exits_two(tool_root: Path, fixtures_dir: Path) -> None:
    result = runner.invoke(
        app,
        ["audit", str(fixtures_dir / "draft_good.md"), "-f", "xml"],
        env=_env(tool_root),
    )
    assert result.exit_code == 2
