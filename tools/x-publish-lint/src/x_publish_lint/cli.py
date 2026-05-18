"""Typer CLI entry point for x-publish-lint."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import typer

from x_publish_lint.engine import audit as run_audit
from x_publish_lint.loader import load_config, load_draft
from x_publish_lint.models import AuditReport, RiskLevel
from x_publish_lint.reports import RENDERERS
from x_publish_lint.reports.markdown import render as render_markdown
from x_publish_lint.rules.base import all_rules

app = typer.Typer(
    help="Deterministic, rules-based X/Twitter draft auditor (advisory only).",
    no_args_is_help=True,
    add_completion=False,
)

_RISK_ORDER: dict[str, int] = {
    "none": -1,
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}

_RISK_LEVEL_RANK: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def _resolve_root() -> Path | None:
    """Locate a tool root containing ``configs/default.toml``, or ``None``.

    Resolution order:
        1. ``X_PUBLISH_LINT_ROOT`` environment variable, if set.
        2. ``<cwd>/tools/x-publish-lint`` when ``configs/default.toml`` exists there.
        3. ``Path(__file__).resolve().parents[2]`` (editable monorepo layout) when
           ``configs/default.toml`` exists there.
        4. ``None`` — the loader will fall back to the packaged default that ships
           inside the wheel.

    Returns:
        A resolved tool root :class:`Path`, or ``None`` to indicate the loader
        should use its packaged default.
    """
    env_root = os.getenv("X_PUBLISH_LINT_ROOT")
    if env_root:
        return Path(env_root)

    cwd_candidate = Path.cwd() / "tools" / "x-publish-lint"
    if (cwd_candidate / "configs" / "default.toml").exists():
        return cwd_candidate

    install_candidate = Path(__file__).resolve().parents[2]
    if (install_candidate / "configs" / "default.toml").exists():
        return install_candidate

    return None


def _emit(text: str) -> None:
    """Write ``text`` to stdout without a trailing newline."""
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def _run(draft_path: Path, client: str | None) -> AuditReport:
    """Load configuration + draft and run the audit engine."""
    root = _resolve_root()
    config_name, config = load_config(client, root)
    draft = load_draft(draft_path)
    if client and not draft.client_id:
        draft = draft.model_copy(update={"client_id": client})
    return run_audit(draft, config, config_name=config_name)


@app.command()
def audit(
    draft_path: Path = typer.Argument(..., exists=False, help="Path to the draft file."),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json | markdown | md | csv.",
    ),
    client: str | None = typer.Option(
        None, "--client", "-c", help="Client identifier for config override."
    ),
    fail_on: str = typer.Option(
        "critical",
        "--fail-on",
        help="Exit non-zero when risk level meets/exceeds threshold "
        "(low|medium|high|critical|none).",
    ),
) -> None:
    """Audit a draft and emit a report in the requested format."""
    fmt = format.lower()
    if fmt not in RENDERERS:
        typer.echo(
            f"Unknown format: {format!r}. Expected one of: {sorted(RENDERERS)}",
            err=True,
        )
        raise typer.Exit(code=2)

    threshold_key = fail_on.lower()
    if threshold_key not in _RISK_ORDER:
        typer.echo(
            f"Unknown --fail-on value: {fail_on!r}. "
            f"Expected one of: {sorted(_RISK_ORDER)}",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        report = _run(draft_path, client)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    rendered = RENDERERS[fmt](report)
    _emit(rendered)

    if threshold_key == "none":
        return
    threshold_rank = _RISK_ORDER[threshold_key]
    report_rank = _RISK_LEVEL_RANK[report.risk_level]
    if report_rank >= threshold_rank:
        raise typer.Exit(code=1)


@app.command()
def scorecard(
    draft_path: Path = typer.Argument(..., help="Path to the draft file."),
    client: str | None = typer.Option(None, "--client", "-c", help="Client identifier."),
    out: Path | None = typer.Option(
        None, "--out", "-o", help="Optional output file (parents auto-created)."
    ),
) -> None:
    """Render a Markdown scorecard for ``draft_path``."""
    try:
        report = _run(draft_path, client)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    rendered = render_markdown(report)
    if out is None:
        _emit(rendered)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")


@app.command("list-rules")
def list_rules() -> None:
    """Print every registered rule ID, sorted."""
    for rule_id in sorted(rule.rule_id for rule in all_rules()):
        _emit(rule_id)
