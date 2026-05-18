"""Media presence rule pack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from x_publish_lint.models import Draft, Finding, Severity, SignalKind
from x_publish_lint.rules.base import register


@dataclass(frozen=True)
class MediaPresenceRule:
    """Reward media-rich drafts; nudge text-only drafts to add media."""

    rule_id: ClassVar[str] = "media.presence"

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Emit a finding based on whether video, photo, or no media is attached."""
        weight = float(config.get("weights", {}).get("media_presence", 7))
        if draft.has_video:
            return [
                Finding(
                    rule_id=self.rule_id,
                    kind=SignalKind.POSITIVE,
                    severity=Severity.INFO,
                    signal="video_view_likelihood",
                    score_delta=weight,
                    message="Video attached: typically lifts view-through engagement.",
                )
            ]
        if draft.media_count > 0:
            return [
                Finding(
                    rule_id=self.rule_id,
                    kind=SignalKind.POSITIVE,
                    severity=Severity.INFO,
                    signal="photo_expand_likelihood",
                    score_delta=weight * 0.6,
                    message="Image attached: lifts photo-expand interactions.",
                )
            ]
        return [
            Finding(
                rule_id=self.rule_id,
                kind=SignalKind.NEGATIVE,
                severity=Severity.INFO,
                signal="media_presence",
                score_delta=-2.0,
                message="Text-only draft; consider adding an image or short video.",
                recommendation="Attach a relevant image or short clip to lift engagement.",
            )
        ]


register(MediaPresenceRule())
