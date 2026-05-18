"""Bundled rule packs.

Importing this package triggers registration of every rule via its module's
top-level ``register(...)`` call.
"""

from x_publish_lint.rules import (  # noqa: F401
    engagement,
    funnel,
    media,
    negative_signals,
    safety,
)
