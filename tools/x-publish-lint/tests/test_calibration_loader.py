"""Tests for the calibration outcome dataset loader and models."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from x_publish_lint.calibration import (
    OUTCOME_COLUMNS,
    CalibrationFormatError,
    OutcomeRow,
    iter_outcomes,
    load_outcomes,
)

REPO_TOOL_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = REPO_TOOL_ROOT / "examples" / "calibration" / "sample_outcomes.csv"

_HEADER = ",".join(OUTCOME_COLUMNS)


def _write_csv(tmp_path: Path, *body_rows: str) -> Path:
    path = tmp_path / "outcomes.csv"
    path.write_text("\n".join((_HEADER, *body_rows)) + "\n", encoding="utf-8")
    return path


def test_outcome_columns_are_stable() -> None:
    # Locking the canonical column order is part of the contract; failing this
    # test is a deliberate signal that downstream consumers must be updated.
    assert OUTCOME_COLUMNS == (
        "draft_id",
        "client_id",
        "published_at",
        "impressions",
        "likes",
        "replies",
        "reposts",
        "quotes",
        "profile_clicks",
        "follows",
        "not_interested",
        "mutes",
        "blocks",
        "reports",
        "dwell_ms",
    )


def test_sample_csv_loads_cleanly() -> None:
    rows = load_outcomes(SAMPLE_CSV)
    assert len(rows) == 5
    assert rows[0].draft_id == "d-0001"
    assert rows[0].client_id == "default"
    assert rows[0].impressions == 12450
    assert rows[0].dwell_ms == 182000
    assert rows[0].published_at == datetime(2026, 5, 1, 14, 30, tzinfo=UTC)


def test_iter_outcomes_streams_in_source_order(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        "d-1,default,2026-01-01T00:00:00+00:00,1,0,0,0,0,0,0,0,0,0,0,0",
        "d-2,default,2026-01-02T00:00:00+00:00,2,0,0,0,0,0,0,0,0,0,0,0",
    )
    ids = [row.draft_id for row in iter_outcomes(path)]
    assert ids == ["d-1", "d-2"]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_outcomes(tmp_path / "nope.csv")


def test_empty_file_raises_format_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(CalibrationFormatError, match="empty"):
        load_outcomes(path)


def test_wrong_header_raises_format_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("draft_id,client_id\nd-1,default\n", encoding="utf-8")
    with pytest.raises(CalibrationFormatError, match="header mismatch"):
        load_outcomes(path)


def test_reordered_header_raises_format_error(tmp_path: Path) -> None:
    cols = list(OUTCOME_COLUMNS)
    cols[0], cols[1] = cols[1], cols[0]
    path = tmp_path / "reordered.csv"
    path.write_text(",".join(cols) + "\n", encoding="utf-8")
    with pytest.raises(CalibrationFormatError, match="header mismatch"):
        load_outcomes(path)


def test_wrong_field_count_raises(tmp_path: Path) -> None:
    path = _write_csv(tmp_path, "d-1,default,2026-01-01T00:00:00+00:00,1,2,3")
    with pytest.raises(CalibrationFormatError, match=r":2: expected 15 fields, got 6"):
        load_outcomes(path)


def test_negative_count_raises(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        "d-1,default,2026-01-01T00:00:00+00:00,1,-1,0,0,0,0,0,0,0,0,0,0",
    )
    with pytest.raises(CalibrationFormatError, match=r":2: invalid outcome row"):
        load_outcomes(path)


def test_naive_timestamp_rejected(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        "d-1,default,2026-01-01T00:00:00,1,0,0,0,0,0,0,0,0,0,0,0",
    )
    with pytest.raises(CalibrationFormatError, match="timezone-aware"):
        load_outcomes(path)


def test_empty_draft_id_rejected(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        ",default,2026-01-01T00:00:00+00:00,1,0,0,0,0,0,0,0,0,0,0,0",
    )
    with pytest.raises(CalibrationFormatError, match=r":2: invalid outcome row"):
        load_outcomes(path)


def test_outcome_row_is_frozen() -> None:
    row = OutcomeRow(
        draft_id="d-1",
        client_id="default",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        impressions=10,
        likes=1,
        replies=0,
        reposts=0,
        quotes=0,
        profile_clicks=0,
        follows=0,
        not_interested=0,
        mutes=0,
        blocks=0,
        reports=0,
        dwell_ms=0,
    )
    with pytest.raises(ValidationError):
        row.impressions = 999  # type: ignore[misc]


def test_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        OutcomeRow(
            draft_id="d-1",
            client_id="default",
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
            impressions=0,
            likes=0,
            replies=0,
            reposts=0,
            quotes=0,
            profile_clicks=0,
            follows=0,
            not_interested=0,
            mutes=0,
            blocks=0,
            reports=0,
            dwell_ms=0,
            extra_column="boom",  # type: ignore[call-arg]
        )
