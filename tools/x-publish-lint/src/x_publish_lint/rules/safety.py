"""Brand-safety rule pack.

This is a coarse lexical lint, not a moderation system. It scans the draft for
configured blocked terms and emits a BLOCK finding when any are present.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from x_publish_lint.models import Draft, Finding, Severity, SignalKind
from x_publish_lint.rules.base import register


@dataclass(frozen=True)
class BrandSafetyRule:
    """Lexical brand-safety check against configured blocked terms."""

    rule_id: ClassVar[str] = "safety.brand_safety"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a BLOCK finding when any blocked term appears in the draft."""
        terms = config.get("safety", {}).get("blocked_terms", [])
        if not terms:
            return []
        lowered = draft.full_text.lower()
        hits = sorted({term for term in terms if str(term).lower() in lowered})
        if not hits:
            return []
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.BLOCK,
                signal="brand_safety_violation",
                score_delta=-40.0,
                message=f"Blocked terms detected: {', '.join(hits)}",
                recommendation="Remove or rephrase the flagged terms before publishing.",
            )
        ]


register(BrandSafetyRule())
