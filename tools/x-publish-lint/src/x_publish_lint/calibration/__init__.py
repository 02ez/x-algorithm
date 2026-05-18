"""Calibration dataset format for observed post-publish outcomes.

This subpackage defines the *durable contract* for outcome data that the
linter can later be calibrated against. It is intentionally read-only and
boring:

- :mod:`x_publish_lint.calibration.models` — Pydantic models for one outcome row.
- :mod:`x_publish_lint.calibration.loader` — Stdlib-CSV reader that validates
  every row into :class:`~x_publish_lint.calibration.models.OutcomeRow`.

No weight tuning, no scoring side-effects, no network I/O. Weight tuning
arrives in a later version.
"""

from x_publish_lint.calibration.loader import (
    CalibrationFormatError,
    iter_outcomes,
    load_outcomes,
)
from x_publish_lint.calibration.models import OUTCOME_COLUMNS, OutcomeRow

__all__ = [
    "OUTCOME_COLUMNS",
    "CalibrationFormatError",
    "OutcomeRow",
    "iter_outcomes",
    "load_outcomes",
]
