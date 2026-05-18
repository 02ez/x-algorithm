"""Rule protocol and module-level registry."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from x_publish_lint.models import Draft, Finding


@runtime_checkable
class Rule(Protocol):
    """Protocol implemented by all deterministic rules."""

    rule_id: str

    def evaluate(self, draft: Draft, config: dict[str, Any]) -> list[Finding]:
        """Evaluate ``draft`` against ``config`` and return findings."""
        ...


_REGISTRY: list[Rule] = []


def register(rule: Rule) -> Rule:
    """Register ``rule`` in the global registry.

    Args:
        rule: A :class:`Rule` instance to add.

    Returns:
        The same rule instance, for fluent registration.
    """
    _REGISTRY.append(rule)
    return rule


def all_rules() -> tuple[Rule, ...]:
    """Return an immutable snapshot of every registered rule."""
    return tuple(_REGISTRY)
