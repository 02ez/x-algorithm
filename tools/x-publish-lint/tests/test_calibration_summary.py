"""Tests for the calibration outcome summary aggregator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from x_publish_lint.calibration import (
    ZERO_DIVISION_RATE,
    OutcomeRow,
    OutcomeSummary,
    load_outcomes,
    summarize_outcomes,
)

REPO_TOOL_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = REPO_TOOL_ROOT / "examples" / "calibration" / "sample_outcomes.csv"


def _row(
    *,
    draft_id: str = "d-1",
    client_id: str = "default",
    published_at: datetime | None = None,
    impressions: int = 1000,
    likes: int = 0,
    replies: int = 0,
    reposts: int = 0,
    quotes: int = 0,
    profile_clicks: int = 0,
    follows: int = 0,
    not_interested: int = 0,
    mutes: int = 0,
    blocks: int = 0,
    reports: int = 0,
    dwell_ms: int = 0,
) -> OutcomeRow:
    return OutcomeRow(
        schema_version="1",
        draft_id=draft_id,
        client_id=client_id,
        published_at=published_at or datetime(2026, 5, 1, tzinfo=UTC),
        impressions=impressions,
        likes=likes,
        replies=replies,
        reposts=reposts,
        quotes=quotes,
        profile_clicks=profile_clicks,
        follows=follows,
        not_interested=not_interested,
        mutes=mutes,
        blocks=blocks,
        reports=reports,
        dwell_ms=dwell_ms,
    )


def test_empty_sequence_raises() -> None:
    with pytest.raises(ValueError, match="at least one row"):
        summarize_outcomes([])


def test_single_row_summary() -> None:
    row = _row(
        impressions=1000,
        likes=100,
        replies=50,
        reposts=20,
        quotes=5,
        profile_clicks=30,
        follows=10,
        not_interested=4,
        mutes=2,
        blocks=1,
        reports=3,
        dwell_ms=180_000,
    )
    summary = summarize_outcomes([row])

    assert summary.row_count == 1
    assert summary.client_ids == ("default",)
    assert summary.published_at_min == row.published_at
    assert summary.published_at_max == row.published_at
    assert summary.total_impressions == 1000
    assert summary.total_likes == 100
    assert summary.total_replies == 50
    assert summary.total_reposts == 20
    assert summary.total_quotes == 5
    assert summary.total_profile_clicks == 30
    assert summary.total_follows == 10
    assert summary.total_not_interested == 4
    assert summary.total_mutes == 2
    assert summary.total_blocks == 1
    assert summary.total_reports == 3
    assert summary.avg_dwell_ms == 180_000.0
    assert summary.reply_rate == pytest.approx(0.05)
    assert summary.repost_rate == pytest.approx(0.02)
    assert summary.follow_rate == pytest.approx(0.01)
    # negative = 4+2+1+3 = 10 / 1000
    assert summary.negative_action_rate == pytest.approx(0.01)


def test_multi_row_totals_and_bounds() -> None:
    t0 = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    rows = [
        _row(draft_id="d-1", client_id="acme", published_at=t0, impressions=1000, replies=10),
        _row(
            draft_id="d-2",
            client_id="default",
            published_at=t0 + timedelta(days=2),
            impressions=2000,
            replies=20,
        ),
        _row(
            draft_id="d-3",
            client_id="acme",
            published_at=t0 - timedelta(days=1),
            impressions=3000,
            replies=30,
        ),
    ]
    summary = summarize_outcomes(rows)

    assert summary.row_count == 3
    assert summary.client_ids == ("acme", "default")
    assert summary.published_at_min == t0 - timedelta(days=1)
    assert summary.published_at_max == t0 + timedelta(days=2)
    assert summary.total_impressions == 6000
    assert summary.total_replies == 60
    assert summary.reply_rate == pytest.approx(60 / 6000)


def test_zero_impressions_yields_zero_rates() -> None:
    rows = [_row(impressions=0, replies=0, reposts=0, follows=0, not_interested=0)]
    summary = summarize_outcomes(rows)

    assert summary.total_impressions == 0
    assert summary.reply_rate == ZERO_DIVISION_RATE
    assert summary.repost_rate == ZERO_DIVISION_RATE
    assert summary.follow_rate == ZERO_DIVISION_RATE
    assert summary.negative_action_rate == ZERO_DIVISION_RATE


def test_negative_action_rate_aggregates_all_four_signals() -> None:
    row = _row(
        impressions=1000,
        not_interested=10,
        mutes=20,
        blocks=30,
        reports=40,
    )
    summary = summarize_outcomes([row])
    # (10 + 20 + 30 + 40) / 1000 = 0.1
    assert summary.negative_action_rate == pytest.approx(0.1)


def test_rates_may_exceed_one() -> None:
    # Rates are action-per-impression, not probabilities. Multiple negative
    # actions per impression must be representable, not clamped away.
    row = _row(
        impressions=10,
        not_interested=5,
        mutes=5,
        blocks=5,
        reports=5,
        replies=15,
    )
    summary = summarize_outcomes([row])
    assert summary.negative_action_rate == pytest.approx(2.0)
    assert summary.reply_rate == pytest.approx(1.5)


def test_avg_dwell_ms_is_mean_across_rows() -> None:
    rows = [
        _row(draft_id="d-1", dwell_ms=100_000),
        _row(draft_id="d-2", dwell_ms=200_000),
        _row(draft_id="d-3", dwell_ms=300_000),
    ]
    summary = summarize_outcomes(rows)
    assert summary.avg_dwell_ms == pytest.approx(200_000.0)


def test_summary_is_frozen() -> None:
    summary = summarize_outcomes([_row()])
    with pytest.raises(ValidationError):
        summary.row_count = 99  # type: ignore[misc]


def test_summarize_sample_csv_end_to_end() -> None:
    rows = load_outcomes(SAMPLE_CSV)
    summary = summarize_outcomes(rows)

    assert summary.row_count == 5
    assert summary.client_ids == ("acme", "default")
    # Totals match the fixture by hand: impressions = 12450+8730+21800+4520+15670
    assert summary.total_impressions == 63170
    assert summary.total_likes == 312 + 198 + 544 + 87 + 402
    assert summary.reply_rate >= 0.0
    assert summary.negative_action_rate >= 0.0
    assert summary.published_at_min == datetime(2026, 5, 1, 14, 30, tzinfo=UTC)
    assert summary.published_at_max == datetime(2026, 5, 5, 20, 10, tzinfo=UTC)


def test_summary_returns_outcome_summary_type() -> None:
    summary = summarize_outcomes([_row()])
    assert isinstance(summary, OutcomeSummary)
