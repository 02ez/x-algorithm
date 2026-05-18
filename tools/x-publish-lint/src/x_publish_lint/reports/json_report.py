"""JSON report renderer."""

from __future__ import annotations

from x_publish_lint.models import AuditReport


def render(report: AuditReport) -> str:
    """Render ``report`` as indented JSON."""
    return report.model_dump_json(indent=2)
