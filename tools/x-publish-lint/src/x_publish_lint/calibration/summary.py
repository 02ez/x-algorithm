"""Aggregate summary over a collection of :class:`OutcomeRow` instances.

This module is deliberately small and pure. It does not persist, fetch, or
mutate anything; it just folds a sequence of validated outcome rows into a
single :class:`OutcomeSummary` with totals, time bounds, and a handful of
transparent per-impression rates.

No weight tuning, no scoring side-effects, no network I/O. Weight tuning
arrives in a later version.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from x_publish_lint.calibration.models import OutcomeRow

#: Sentinel returned by every rate field when ``total_impressions == 0``.
#: Centralised so callers can compare against it cheaply if they want to.
ZERO_DIVISION_RATE: Final[float] = 0.0


class OutcomeSummary(BaseModel):
    """Aggregate view over a non-empty sequence of :class:`OutcomeRow`.

    All ``total_*`` fields are non-negative integers. ``avg_dwell_ms`` is a
    non-negative float (mean across rows). All ``*_rate`` fields are floats
    in ``[0.0, 1.0]`` computed as ``total / total_impressions`` and clamped
    to :data:`ZERO_DIVISION_RATE` when ``total_impressions`` is zero.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    row_count: int = Field(ge=1)
    client_ids: tuple[str, ...] = Field(
        description="Distinct client_ids present in the input, sorted ascending.",
    )
    published_at_min: datetime
    published_at_max: datetime

    total_impressions: int = Field(ge=0)
    total_likes: int = Field(ge=0)
    total_replies: int = Field(ge=0)
    total_reposts: int = Field(ge=0)
    total_quotes: int = Field(ge=0)
    total_profile_clicks: int = Field(ge=0)
    total_follows: int = Field(ge=0)
    total_not_interested: int = Field(ge=0)
    total_mutes: int = Field(ge=0)
    total_blocks: int = Field(ge=0)
    total_reports: int = Field(ge=0)

    avg_dwell_ms: float = Field(ge=0.0)

    reply_rate: float = Field(ge=0.0, le=1.0)
    repost_rate: float = Field(ge=0.0, le=1.0)
    follow_rate: float = Field(ge=0.0, le=1.0)
    negative_action_rate: float = Field(ge=0.0, le=1.0)


def _safe_rate(numerator: int, denominator: int) -> float:
    """Return ``numerator / denominator`` or :data:`ZERO_DIVISION_RATE`.

    Division by zero is a normal case (e.g. a draft published but never
    surfaced) and must not raise.
    """
    if denominator == 0:
        return ZERO_DIVISION_RATE
    return numerator / denominator


def summarize_outcomes(rows: Sequence[OutcomeRow]) -> OutcomeSummary:
    """Fold ``rows`` into a single :class:`OutcomeSummary`.

    Args:
        rows: A non-empty sequence of validated outcome rows.

    Returns:
        An :class:`OutcomeSummary` with totals, time bounds, average dwell,
        and the four documented per-impression rates.

    Raises:
        ValueError: If ``rows`` is empty. Summarising an empty sequence has
            no meaningful interpretation (no time bounds, no client set),
            so it is rejected explicitly rather than returning sentinel
            values.
    """
    if len(rows) == 0:
        raise ValueError("summarize_outcomes requires at least one row")

    total_impressions = 0
    total_likes = 0
    total_replies = 0
    total_reposts = 0
    total_quotes = 0
    total_profile_clicks = 0
    total_follows = 0
    total_not_interested = 0
    total_mutes = 0
    total_blocks = 0
    total_reports = 0
    total_dwell_ms = 0

    client_id_set: set[str] = set()
    published_at_min = rows[0].published_at
    published_at_max = rows[0].published_at

    for row in rows:
        total_impressions += row.impressions
        total_likes += row.likes
        total_replies += row.replies
        total_reposts += row.reposts
        total_quotes += row.quotes
        total_profile_clicks += row.profile_clicks
        total_follows += row.follows
        total_not_interested += row.not_interested
        total_mutes += row.mutes
        total_blocks += row.blocks
        total_reports += row.reports
        total_dwell_ms += row.dwell_ms

        client_id_set.add(row.client_id)

        if row.published_at < published_at_min:
            published_at_min = row.published_at
        if row.published_at > published_at_max:
            published_at_max = row.published_at

    total_negative = total_not_interested + total_mutes + total_blocks + total_reports

    return OutcomeSummary(
        row_count=len(rows),
        client_ids=tuple(sorted(client_id_set)),
        published_at_min=published_at_min,
        published_at_max=published_at_max,
        total_impressions=total_impressions,
        total_likes=total_likes,
        total_replies=total_replies,
        total_reposts=total_reposts,
        total_quotes=total_quotes,
        total_profile_clicks=total_profile_clicks,
        total_follows=total_follows,
        total_not_interested=total_not_interested,
        total_mutes=total_mutes,
        total_blocks=total_blocks,
        total_reports=total_reports,
        avg_dwell_ms=total_dwell_ms / len(rows),
        reply_rate=_safe_rate(total_replies, total_impressions),
        repost_rate=_safe_rate(total_reposts, total_impressions),
        follow_rate=_safe_rate(total_follows, total_impressions),
        negative_action_rate=_safe_rate(total_negative, total_impressions),
    )
