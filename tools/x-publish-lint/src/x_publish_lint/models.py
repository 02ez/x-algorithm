"""Domain models for x-publish-lint.

All models use Pydantic v2. Models are intentionally small and pure: they
describe drafts, individual rule findings, and the aggregated audit report.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Coarse risk classification for a complete audit report."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Severity(str, Enum):
    """Per-finding severity emitted by a single rule."""

    INFO = "INFO"
    WARN = "WARN"
    BLOCK = "BLOCK"


class SignalKind(str, Enum):
    """Whether a finding represents a positive or negative signal."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class Draft(BaseModel):
    """A draft post (or post + thread) to audit before publication.

    Attributes:
        text: Body text of the root post.
        thread: Ordered list of reply texts that follow the root post.
        media_count: Number of attached media items.
        has_video: True when the draft attaches a video.
        has_link: True when the draft contains an outbound link.
        surface: Where the draft will be posted (post/reply/quote).
        client_id: Optional client identifier for client-specific configs.
    """

    text: str
    thread: list[str] = Field(default_factory=list)
    media_count: int = 0
    has_video: bool = False
    has_link: bool = False
    surface: Literal["post", "reply", "quote"] = "post"
    client_id: str | None = None

    @property
    def full_text(self) -> str:
        """Return the combined text of the root post and any thread replies."""
        return "\n\n".join([self.text, *self.thread]).strip()


class Finding(BaseModel):
    """A single deterministic observation emitted by a rule."""

    rule_id: str
    kind: SignalKind
    severity: Severity
    signal: str
    score_delta: float
    message: str
    recommendation: str | None = None


class AuditReport(BaseModel):
    """Aggregated audit report for a single draft."""

    overall_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    positive_signals: list[str]
    negative_risks: list[str]
    recommendations: list[str]
    findings: list[Finding]
    draft: Draft
    config_name: str
    schema_version: str = "1.0.0"
