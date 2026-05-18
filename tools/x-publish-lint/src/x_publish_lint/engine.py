"""Audit engine: run all registered rules and assemble the report."""

from __future__ import annotations

import logging
from typing import Any

import x_publish_lint.rules  # noqa: F401  (import to trigger rule registration)
from x_publish_lint.models import AuditReport, Draft, Finding, Severity, SignalKind
from x_publish_lint.rules.base import all_rules
from x_publish_lint.signals import aggregate

_logger = logging.getLogger(__name__)


def audit(
    draft: Draft,
    config: dict[str, Any],
    config_name: str = "default",
) -> AuditReport:
    """Run every registered rule against ``draft`` and return an :class:`AuditReport`.

    Rule execution is fail-closed: any rule that raises is converted into a
    BLOCK finding with signal ``rule_execution_error`` and score delta ``-50.0``.
    The error is logged with :py:meth:`logging.Logger.exception` so CI can
    surface it.

    Args:
        draft: The draft to evaluate.
        config: Parsed configuration dictionary.
        config_name: Identifier of the active config (e.g. ``"default"`` or
            ``"clients/acme"``).

    Returns:
        The aggregated :class:`AuditReport`.
    """
    findings: list[Finding] = []
    for rule in all_rules():
        try:
            findings.extend(rule.evaluate(draft, config))
        except Exception:
            _logger.exception("Rule %s raised during evaluation", rule.rule_id)
            findings.append(
                Finding(
                    rule_id=rule.rule_id,
                    kind=SignalKind.NEGATIVE,
                    severity=Severity.BLOCK,
                    signal="rule_execution_error",
                    score_delta=-50.0,
                    message=f"Rule execution failed: {rule.rule_id}",
                    recommendation=(
                        "Fix or disable the failing rule before trusting this audit."
                    ),
                )
            )

    score, risk, positives, negatives, recommendations = aggregate(findings)
    return AuditReport(
        overall_score=score,
        risk_level=risk,
        positive_signals=positives,
        negative_risks=negatives,
        recommendations=recommendations,
        findings=findings,
        draft=draft,
        config_name=config_name,
    )
