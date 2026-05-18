"""Report renderers for x-publish-lint."""

from __future__ import annotations

from collections.abc import Callable

from x_publish_lint.models import AuditReport
from x_publish_lint.reports import csv_report, json_report, markdown

RENDERERS: dict[str, Callable[[AuditReport], str]] = {
    "json": json_report.render,
    "markdown": markdown.render,
    "md": markdown.render,
    "csv": csv_report.render,
}

__all__ = ["RENDERERS"]
