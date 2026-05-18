"""Funnel rule pack: detect call-to-action placement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from x_publish_lint.models import Draft, Finding, Severity, SignalKind
from x_publish_lint.rules.base import register

_CTA_TERMS: tuple[str, ...] = (
    "sign up",
    "subscribe",
    "book",
    "register",
    "join",
    "download",
    "try",
    "get started",
    "learn more",
)


def _first_cta_position(text: str) -> int | None:
    """Return the lowest character index where any CTA term appears, else None."""
    lowered = text.lower()
    positions = [lowered.find(term) for term in _CTA_TERMS]
    positions = [p for p in positions if p >= 0]
    return min(positions) if positions else None


@dataclass(frozen=True)
class CTAPlacementRule:
    """Reward CTAs placed in the final 40%; warn when they appear too early."""

    rule_id: ClassVar[str] = "funnel.cta_placement"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a finding describing the CTA's placement, if any CTA is present."""
        weight = float(config.get("weights", {}).get("cta_placement", 5))
        text = draft.full_text
        if not text:
            return []
        position = _first_cta_position(text)
        if position is None:
            return []
        ratio = position / max(len(text), 1)
        if ratio >= 0.6:
            return [
                Finding(
                    rule_id=self.rule_id,
                    kind=SignalKind.POSITIVE,
                    severity=Severity.INFO,
                    signal="cta_placement",
                    score_delta=weight,
                    message="CTA placed in the final 40% of the draft.",
                )
            ]
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.WARN,
                signal="cta_placement",
                score_delta=-min(weight, 5.0),
                message="CTA appears too early; readers may bounce before the hook lands.",
                recommendation="Move the CTA to the final paragraph or final post in the thread.",
            )
        ]


register(CTAPlacementRule())
