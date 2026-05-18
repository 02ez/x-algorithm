"""Engagement rule pack."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar

from x_publish_lint.models import Draft, Finding, Severity, SignalKind
from x_publish_lint.rules.base import register

_QUESTION_WORDS = ("why", "how", "what", "which", "when")
_STAT_PATTERN = re.compile(r"(\d+\s*%|\b\d+x\b)", re.IGNORECASE)
_LIST_PATTERN = re.compile(r"(^|\n)\s*([-*\u2022]|\d+\.)\s+", re.MULTILINE)


def _has_open_question(text: str) -> bool:
    """Return True if ``text`` contains an open-ended question."""
    lowered = text.lower()
    if "?" not in lowered:
        return False
    return any(word in lowered for word in _QUESTION_WORDS)


@dataclass(frozen=True)
class ReplyHookRule:
    """Reward open-ended questions that invite replies."""

    rule_id: ClassVar[str] = "engagement.reply_hook"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a positive finding when a reply-hook question is present."""
        weight = float(config.get("weights", {}).get("reply_hook", 8))
        text = draft.full_text
        if _has_open_question(text):
            return [
                Finding(
                    rule_id=self.rule_id,
                    kind=SignalKind.POSITIVE,
                    severity=Severity.INFO,
                    signal="reply_likelihood",
                    score_delta=weight,
                    message="Draft contains an open-ended question that invites replies.",
                )
            ]
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.WARN,
                signal="reply_likelihood",
                score_delta=-min(weight, 6.0),
                message="No open-ended question detected.",
                recommendation=(
                    "Add a single open-ended question (why/how/what/which/when) to "
                    "invite replies."
                ),
            )
        ]


@dataclass(frozen=True)
class DwellLengthRule:
    """Reward drafts long enough to keep readers dwelling."""

    rule_id: ClassVar[str] = "engagement.dwell_length"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a positive finding for sufficient length or multi-post threads."""
        min_chars = int(config.get("dwell", {}).get("min_chars", 180))
        weight = float(config.get("weights", {}).get("dwell_length", 6))
        text = draft.full_text
        long_enough = len(text) >= min_chars
        threaded = len(draft.thread) >= 2
        if long_enough or threaded:
            return [
                Finding(
                    rule_id=self.rule_id,
                    kind=SignalKind.POSITIVE,
                    severity=Severity.INFO,
                    signal="dwell_likelihood",
                    score_delta=weight,
                    message="Draft length or thread depth supports dwell time.",
                )
            ]
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.INFO,
                signal="dwell_likelihood",
                score_delta=-3.0,
                message=f"Short single post (<{min_chars} chars) limits dwell time.",
                recommendation="Add a second paragraph or convert the draft into a 2-3 post thread.",
            )
        ]


@dataclass(frozen=True)
class ShareabilityRule:
    """Reward stat-like or list-like structures that improve shareability."""

    rule_id: ClassVar[str] = "engagement.shareability"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a positive finding when stats or list structure are present."""
        weight = float(config.get("weights", {}).get("shareability", 5))
        text = draft.full_text
        if _STAT_PATTERN.search(text) or _LIST_PATTERN.search(text):
            return [
                Finding(
                    rule_id=self.rule_id,
                    kind=SignalKind.POSITIVE,
                    severity=Severity.INFO,
                    signal="shareability",
                    score_delta=weight,
                    message="Draft contains list or stat patterns that improve shareability.",
                )
            ]
        return []


register(ReplyHookRule())
register(DwellLengthRule())
register(ShareabilityRule())
