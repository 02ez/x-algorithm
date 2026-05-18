"""Pydantic models for the calibration outcome dataset.

One :class:`OutcomeRow` represents the observed result of a single published
draft. The schema is deliberately flat and CSV-friendly so it can be produced
by spreadsheets, manual exports, or analytics pipelines without bespoke tooling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Canonical, ordered column names for the outcome CSV. The loader enforces
#: that every input file declares exactly this header (order-sensitive) so
#: downstream consumers can rely on a stable contract.
OUTCOME_COLUMNS: Final[tuple[str, ...]] = (
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


class OutcomeRow(BaseModel):
    """A single observed post-publish outcome for one draft.

    All count fields are non-negative integers. ``published_at`` is a
    timezone-aware ISO 8601 datetime. ``draft_id`` and ``client_id`` are
    required non-empty strings (use ``"default"`` for ``client_id`` when no
    client-specific config applies).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    draft_id: str = Field(min_length=1, description="Stable identifier for the draft.")
    client_id: str = Field(
        min_length=1,
        description="Client identifier; use 'default' when no override applies.",
    )
    published_at: datetime = Field(description="Timezone-aware publish timestamp.")
    impressions: int = Field(ge=0)
    likes: int = Field(ge=0)
    replies: int = Field(ge=0)
    reposts: int = Field(ge=0)
    quotes: int = Field(ge=0)
    profile_clicks: int = Field(ge=0)
    follows: int = Field(ge=0)
    not_interested: int = Field(ge=0)
    mutes: int = Field(ge=0)
    blocks: int = Field(ge=0)
    reports: int = Field(ge=0)
    dwell_ms: int = Field(ge=0, description="Aggregate dwell time in milliseconds.")

    @field_validator("published_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("published_at must be timezone-aware (include UTC offset)")
        return value
