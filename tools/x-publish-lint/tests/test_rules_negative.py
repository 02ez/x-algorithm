"""Tests for the negative-signal rule pack."""

from __future__ import annotations

from x_publish_lint.models import Draft
from x_publish_lint.rules.negative_signals import (
    MuteKeywordRule,
    OverpostingRule,
    RageBaitRule,
)


def _config() -> dict:
    return {
        "weights": {"rage_bait": 8, "mute_keyword": 5, "overposting": 4},
        "safety": {"mute_risk_terms": ["politics", "election"]},
    }


def test_rage_bait_requires_two_terms() -> None:
    cfg = _config()
    one = RageBaitRule().evaluate(Draft(text="This is a disaster."), cfg)
    assert one == []
    two = RageBaitRule().evaluate(
        Draft(text="A disaster and a disgrace, breaking everything."), cfg
    )
    assert two and two[0].signal == "rage_bait_risk"


def test_mute_keyword_hits_configured_terms() -> None:
    findings = MuteKeywordRule().evaluate(
        Draft(text="Today in politics, the election heats up."), _config()
    )
    assert findings and findings[0].signal == "mute_keyword_risk"


def test_overposting_triggers_on_long_thread() -> None:
    findings = OverpostingRule().evaluate(
        Draft(text="hello", thread=["a"] * 8), _config()
    )
    assert findings and findings[0].signal == "overposting_risk"


def test_overposting_silent_on_short_thread() -> None:
    findings = OverpostingRule().evaluate(
        Draft(text="hello", thread=["a", "b"]), _config()
    )
    assert findings == []
