"""Packaged default configuration for x-publish-lint.

This sub-package ships ``default.toml`` as importable package data so the CLI
works after a non-editable install (e.g. ``pip install dist/*.whl``) without
requiring the ``X_PUBLISH_LINT_ROOT`` environment variable. Repo-level
``tools/x-publish-lint/configs/`` files still take priority during development.
"""
