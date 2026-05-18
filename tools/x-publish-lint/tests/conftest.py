"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

# Import the package eagerly so all bundled rules are registered exactly once.
import x_publish_lint.rules  # noqa: F401
from x_publish_lint.rules import base as _rules_base

TOOL_ROOT = Path(__file__).resolve().parents[1]

# Snapshot bundled rules so individual tests that call ``register`` can be
# rolled back without disturbing other tests.
_BUNDLED_RULES = tuple(_rules_base._REGISTRY)


@pytest.fixture(autouse=True)
def _set_env_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the CLI/loader at this tool root for every test."""
    monkeypatch.setenv("X_PUBLISH_LINT_ROOT", str(TOOL_ROOT))


@pytest.fixture(autouse=True)
def _restore_registry():
    """Restore the bundled rule registry after each test."""
    yield
    _rules_base._REGISTRY[:] = list(_BUNDLED_RULES)


@pytest.fixture
def tool_root() -> Path:
    """Return the path to the x-publish-lint tool root."""
    return TOOL_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the directory containing draft fixtures."""
    return TOOL_ROOT / "tests" / "fixtures"
