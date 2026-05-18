"""Tests for the engagement rule pack."""

from __future__ import annotations

from x_publish_lint.models import Draft, SignalKind
from x_publish_lint.rules.engagement import (
    DwellLengthRule,
    ReplyHookRule,
    ShareabilityRule,
)


def _config() -> dict:
    return {
        "weights": {"reply_hook": 8, "dwell_length": 6, "shareability": 5},
        "dwell": {"min_chars": 180},
    }


def test_reply_hook_positive_on_open_question() -> None:
    findings = ReplyHookRule().evaluate(
        Draft(text="Why does this approach actually work in practice?"), _config()
    )
    assert findings and findings[0].kind is SignalKind.POSITIVE
    assert findings[0].signal == "reply_likelihood"


def test_reply_hook_negative_without_question() -> None:
    findings = ReplyHookRule().evaluate(Draft(text="This is a statement."), _config())
    assert findings and findings[0].kind is SignalKind.NEGATIVE


def test_dwell_length_positive_on_long_text() -> None:
    long_text = "x" * 200
    findings = DwellLengthRule().evaluate(Draft(text=long_text), _config())
    assert findings and findings[0].kind is SignalKind.POSITIVE


def test_dwell_length_positive_on_thread() -> None:
    findings = DwellLengthRule().evaluate(
        Draft(text="short", thread=["a", "b"]), _config()
    )
    assert findings and findings[0].kind is SignalKind.POSITIVE


def test_shareability_positive_on_stat() -> None:
    findings = ShareabilityRule().evaluate(
        Draft(text="We saw a 42% lift in conversions."), _config()
    )
    assert findings and findings[0].kind is SignalKind.POSITIVE
