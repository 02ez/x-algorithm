"""Engine-level tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from x_publish_lint.engine import audit
from x_publish_lint.loader import load_config, load_draft
from x_publish_lint.models import Draft, Finding, RiskLevel, Severity, SignalKind
from x_publish_lint.rules.base import all_rules, register


def _audit_fixture(name: str, tool_root: Path, fixtures_dir: Path):
    config_name, config = load_config(None, tool_root)
    draft = load_draft(fixtures_dir / name)
    return audit(draft, config, config_name=config_name)


def test_good_draft_is_low_or_medium(tool_root: Path, fixtures_dir: Path) -> None:
    report = _audit_fixture("draft_good.md", tool_root, fixtures_dir)
    assert report.overall_score >= 70
    assert report.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
    assert "reply_likelihood" in report.positive_signals


def test_bad_draft_is_high_or_critical(tool_root: Path, fixtures_dir: Path) -> None:
    report = _audit_fixture("draft_bad.md", tool_root, fixtures_dir)
    assert report.overall_score < 70
    assert "rage_bait_risk" in report.negative_risks


@dataclass(frozen=True)
class _BoomRule:
    rule_id: ClassVar[str] = "test.boom"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        raise RuntimeError("boom")


def test_rule_failure_is_fail_closed(tool_root: Path) -> None:
    register(_BoomRule())
    assert any(r.rule_id == "test.boom" for r in all_rules())
    _, config = load_config(None, tool_root)
    report = audit(Draft(text="Hello world"), config)
    boom = [f for f in report.findings if f.rule_id == "test.boom"]
    assert boom, "expected fail-closed finding for failing rule"
    assert boom[0].severity is Severity.BLOCK
    assert boom[0].kind is SignalKind.NEGATIVE
    assert boom[0].signal == "rule_execution_error"
    assert report.risk_level is RiskLevel.CRITICAL
