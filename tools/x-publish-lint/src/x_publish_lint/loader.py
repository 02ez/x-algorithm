"""Draft and configuration loaders.

Loading is intentionally stdlib-only: ``tomllib`` parses configs, and drafts
arrive either as JSON (validated into :class:`Draft`) or as plain markdown/text.
"""

from __future__ import annotations

import json
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

from x_publish_lint.models import Draft

_TEXT_SUFFIXES = {".md", ".txt"}
_PACKAGED_DEFAULT_NAME = "default (packaged)"


def load_draft(path: Path) -> Draft:
    """Load a draft from disk.

    Args:
        path: Path to a ``.json``, ``.md``, or ``.txt`` draft file.

    Returns:
        Parsed :class:`Draft` instance.

    Raises:
        FileNotFoundError: When ``path`` does not exist.
        ValueError: When the file extension is not supported.
    """
    if not path.exists():
        raise FileNotFoundError(f"Draft file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return Draft.model_validate(data)
    if suffix in _TEXT_SUFFIXES:
        return Draft(text=path.read_text(encoding="utf-8").strip())
    raise ValueError(
        f"Unsupported draft extension {suffix!r}. Expected .json, .md, or .txt."
    )


def _load_packaged_default() -> tuple[str, dict[str, Any]]:
    """Load the default config that ships inside the wheel as package data."""
    resource = resources.files("x_publish_lint.configs").joinpath("default.toml")
    with resource.open("rb") as handle:
        return _PACKAGED_DEFAULT_NAME, tomllib.load(handle)


def load_config(
    client: str | None, search_root: Path | None = None
) -> tuple[str, dict[str, Any]]:
    """Load a TOML configuration, preferring a client override.

    Resolution order:
        1. ``<search_root>/configs/clients/<client>.toml`` (when ``client`` is set).
        2. ``<search_root>/configs/default.toml`` (when ``search_root`` is set).
        3. Packaged ``x_publish_lint.configs.default.toml`` (ships in the wheel).

    Args:
        client: Optional client identifier. When set, ``configs/clients/<client>.toml``
            takes priority if present in ``search_root``.
        search_root: Optional root directory containing a ``configs/`` folder. When
            ``None`` (e.g. non-editable install with no override), the loader falls
            back to the packaged default that ships inside the distribution.

    Returns:
        Tuple ``(config_name, config_dict)``. ``config_name`` is ``"default"``,
        ``"default (packaged)"``, or ``f"clients/{client}"``.

    Raises:
        FileNotFoundError: When ``client`` is requested but the client config is
            not found and no ``search_root`` fallback exists.
    """
    if search_root is not None:
        configs_dir = search_root / "configs"
        if client:
            client_path = configs_dir / "clients" / f"{client}.toml"
            if client_path.exists():
                with client_path.open("rb") as handle:
                    return f"clients/{client}", tomllib.load(handle)

        default_path = configs_dir / "default.toml"
        if default_path.exists():
            with default_path.open("rb") as handle:
                return "default", tomllib.load(handle)

    if client:
        raise FileNotFoundError(
            f"Client config {client!r} not found. Set X_PUBLISH_LINT_ROOT to a "
            "directory containing configs/clients/<client>.toml, or omit --client "
            "to use the packaged default."
        )

    return _load_packaged_default()
