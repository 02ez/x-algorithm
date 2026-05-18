"""Markdown report renderer."""

from __future__ import annotations

from x_publish_lint.models import AuditReport


def _bullets(items: list[str], prefix: str) -> list[str]:
    """Render a bullet list, falling back to a single italic ``_none_`` line."""
    return [f"- {prefix} {item}" for item in items] or ["- _none_"]


def _numbered(items: list[str]) -> list[str]:
    """Render a numbered list, falling back to a single italic ``_none_`` line."""
    return [f"{idx}. {item}" for idx, item in enumerate(items, start=1)] or ["- _none_"]


def _findings_table(report: AuditReport) -> list[str]:
    """Render the findings table."""
    lines = [
        "| Rule | Severity | Kind | Signal | Score | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if not report.findings:
        lines.append("| _none_ | | | | | |")
        return lines
    for f in report.findings:
        message = f.message.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{f.rule_id}` | {f.severity.value} | {f.kind.value} | "
            f"`{f.signal}` | {f.score_delta:+.1f} | {message} |"
        )
    return lines


def render(report: AuditReport) -> str:
    """Render ``report`` as a Markdown scorecard."""
    lines: list[str] = [
        "# X Publish Lint — Scorecard",
        "",
        f"- **Overall score:** {report.overall_score}/100",
        f"- **Risk level:** {report.risk_level.value}",
        f"- **Config:** `{report.config_name}`",
        f"- **Schema:** `{report.schema_version}`",
        "",
        "## Positive Signals",
        "",
    ]
    lines.extend(_bullets(report.positive_signals, "+"))
    lines.extend(["", "## Negative Risks", ""])
    lines.extend(_bullets(report.negative_risks, "-"))
    lines.extend(["", "## Recommendations", ""])
    lines.extend(_numbered(report.recommendations))
    lines.extend(["", "## Findings", ""])
    lines.extend(_findings_table(report))
    lines.append("")
    return "\n".join(lines)
