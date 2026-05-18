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
from x_publish_lint.calibration.models import (
    CURRENT_SCHEMA_VERSION,
    OUTCOME_COLUMNS,
    OutcomeRow,
)
from x_publish_lint.calibration.summary import (
    ZERO_DIVISION_RATE,
    OutcomeSummary,
    summarize_outcomes,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "OUTCOME_COLUMNS",
    "ZERO_DIVISION_RATE",
    "CalibrationFormatError",
    "OutcomeRow",
    "OutcomeSummary",
    "iter_outcomes",
    "load_outcomes",
    "summarize_outcomes",
]
