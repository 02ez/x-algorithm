"""Signal aggregation: convert a list of findings into a final report."""

from __future__ import annotations

from x_publish_lint.models import Finding, RiskLevel, Severity, SignalKind

_BASELINE = 70


def _risk_from(score: int, findings: list[Finding]) -> RiskLevel:
    """Classify risk from score plus the presence of BLOCK findings."""
    if any(f.severity is Severity.BLOCK for f in findings):
        return RiskLevel.CRITICAL
    if score < 40:
        return RiskLevel.HIGH
    if score < 70:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _sorted_unique(values: list[str]) -> list[str]:
    """Return a sorted, de-duplicated copy of ``values``."""
    return sorted(set(values))


def aggregate(
    findings: list[Finding],
) -> tuple[int, RiskLevel, list[str], list[str], list[str]]:
    """Aggregate findings into ``(score, risk, positives, negatives, recommendations)``.

    Args:
        findings: Findings emitted by the rule pipeline.

    Returns:
        Tuple of overall score (clamped to ``[0, 100]``), risk level, sorted-unique
        positive signal names, sorted-unique negative signal names, and an
        order-preserving list of non-empty recommendations.
    """
    raw = _BASELINE + sum(f.score_delta for f in findings)
    score = max(0, min(100, round(raw)))
    risk = _risk_from(score, findings)
    positives = _sorted_unique(
        [f.signal for f in findings if f.kind is SignalKind.POSITIVE]
    )
    negatives = _sorted_unique(
        [f.signal for f in findings if f.kind is SignalKind.NEGATIVE]
    )
    recommendations = [f.recommendation for f in findings if f.recommendation]
    return score, risk, positives, negatives, recommendations
