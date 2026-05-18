"""Negative-signal rule pack: rage bait, mute-risk keywords, overposting."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar

from x_publish_lint.models import Draft, Finding, Severity, SignalKind
from x_publish_lint.rules.base import register

_RAGE_TERMS: tuple[str, ...] = (
    "outrageous",
    "disgrace",
    "destroy",
    "cancel",
    "expose",
    "shameful",
    "disaster",
    "breaking",
)


def _count_term_hits(text: str, terms: tuple[str, ...]) -> list[str]:
    """Return the sorted unique list of terms that appear in ``text``."""
    lowered = text.lower()
    hits: set[str] = set()
    for term in terms:
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, lowered):
            hits.add(term)
    return sorted(hits)


@dataclass(frozen=True)
class RageBaitRule:
    """Flag drafts that stack adversarial language likely to attract rage bait."""

    rule_id: ClassVar[str] = "negative.rage_bait"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a negative finding when at least two rage-bait terms appear."""
        weight = float(config.get("weights", {}).get("rage_bait", 8))
        hits = _count_term_hits(draft.full_text, _RAGE_TERMS)
        if len(hits) < 2:
            return []
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.WARN,
                signal="rage_bait_risk",
                score_delta=-weight,
                message=f"Stacked adversarial language detected: {', '.join(hits)}",
                recommendation="Rework wording to argue from substance rather than outrage.",
            )
        ]


@dataclass(frozen=True)
class MuteKeywordRule:
    """Flag terms that commonly appear on users' mute lists."""

    rule_id: ClassVar[str] = "negative.mute_keyword"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a negative finding when configured mute-risk terms are present."""
        terms = tuple(
            str(t) for t in config.get("safety", {}).get("mute_risk_terms", [])
        )
        weight = float(config.get("weights", {}).get("mute_keyword", 5))
        if not terms:
            return []
        hits = _count_term_hits(draft.full_text, terms)
        if not hits:
            return []
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.WARN,
                signal="mute_keyword_risk",
                score_delta=-weight,
                message=f"Mute-risk terms detected: {', '.join(hits)}",
                recommendation="Reframe to avoid words commonly muted by your audience.",
            )
        ]


@dataclass(frozen=True)
class OverpostingRule:
    """Flag threads long enough to risk follower fatigue."""

    rule_id: ClassVar[str] = "negative.overposting"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a negative finding when the thread has 8 or more replies."""
        weight = float(config.get("weights", {}).get("overposting", 4))
        if len(draft.thread) < 8:
            return []
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.WARN,
                signal="overposting_risk",
                score_delta=-weight,
                message=f"Thread has {len(draft.thread)} replies; risk of follower fatigue.",
                recommendation="Split into a separate post or condense the thread.",
            )
        ]


register(RageBaitRule())
register(MuteKeywordRule())
register(OverpostingRule())
