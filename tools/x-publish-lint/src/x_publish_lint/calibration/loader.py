"""CSV loader for the calibration outcome dataset.

Reads a UTF-8 CSV file whose header exactly matches
:data:`x_publish_lint.calibration.models.OUTCOME_COLUMNS` and validates every
row via :class:`~x_publish_lint.calibration.models.OutcomeRow`.

Failures are reported with the 1-based source row number so a human can
quickly locate the bad cell. No network I/O, no mutation, no side-effects.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from x_publish_lint.calibration.models import OUTCOME_COLUMNS, OutcomeRow


class CalibrationFormatError(ValueError):
    """Raised when an outcome CSV does not match the documented contract."""


def iter_outcomes(path: Path) -> Iterator[OutcomeRow]:
    """Yield :class:`OutcomeRow` instances from ``path`` one at a time.

    Args:
        path: Path to a UTF-8 CSV file with the canonical header.

    Yields:
        Validated :class:`OutcomeRow` instances in source order.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        CalibrationFormatError: If the header is wrong or any row fails
            validation. The error message includes the 1-based source row
            number (header counts as row 1).
    """
    if not path.exists():
        raise FileNotFoundError(f"Calibration CSV not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            raise CalibrationFormatError(f"{path}: file is empty") from None

        actual = tuple(name.strip() for name in header)
        if actual != OUTCOME_COLUMNS:
            raise CalibrationFormatError(
                f"{path}: header mismatch. "
                f"expected {list(OUTCOME_COLUMNS)}, got {list(actual)}"
            )

        for source_row, row in enumerate(reader, start=2):
            if len(row) != len(OUTCOME_COLUMNS):
                raise CalibrationFormatError(
                    f"{path}:{source_row}: expected {len(OUTCOME_COLUMNS)} "
                    f"fields, got {len(row)}"
                )
            data = dict(zip(OUTCOME_COLUMNS, row, strict=True))
            try:
                yield OutcomeRow.model_validate(data)
            except ValidationError as exc:
                raise CalibrationFormatError(
                    f"{path}:{source_row}: invalid outcome row: {exc}"
                ) from exc


def load_outcomes(path: Path) -> list[OutcomeRow]:
    """Load and validate an entire outcome CSV into memory.

    Convenience wrapper around :func:`iter_outcomes` for callers that want
    the full list. For large files prefer :func:`iter_outcomes` to stream.
    """
    return list(iter_outcomes(path))
