"""CSV report renderer."""

from __future__ import annotations

import csv
import io

from x_publish_lint.models import AuditReport


def render(report: AuditReport) -> str:
    """Render ``report`` as CSV, one row per finding."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "overall_score",
            "risk_level",
            "config_name",
            "rule_id",
            "kind",
            "severity",
            "signal",
            "score_delta",
            "message",
            "recommendation",
        ]
    )
    if not report.findings:
        writer.writerow(
            [
                report.overall_score,
                report.risk_level.value,
                report.config_name,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )
    else:
        for f in report.findings:
            writer.writerow(
                [
                    report.overall_score,
                    report.risk_level.value,
                    report.config_name,
                    f.rule_id,
                    f.kind.value,
                    f.severity.value,
                    f.signal,
                    f"{f.score_delta:.2f}",
                    f.message,
                    f.recommendation or "",
                ]
            )
    return buffer.getvalue()
