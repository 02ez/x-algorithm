"""Draft and configuration loaders.

Loading is intentionally stdlib-only: ``tomllib`` parses configs, and drafts
arrive either as JSON (validated into :class:`Draft`) or as plain markdown/text.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from x_publish_lint.models import Draft

_TEXT_SUFFIXES = {".md", ".txt"}


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


def load_config(client: str | None, search_root: Path) -> tuple[str, dict[str, Any]]:
    """Load a TOML configuration, preferring a client override.

    Args:
        client: Optional client identifier. When set, ``configs/clients/<client>.toml``
            takes priority if present.
        search_root: Root directory containing the ``configs/`` folder.

    Returns:
        Tuple ``(config_name, config_dict)``. ``config_name`` is ``"default"`` or
        ``f"clients/{client}"``.

    Raises:
        FileNotFoundError: When the requested config (or default fallback) is missing.
    """
    configs_dir = search_root / "configs"
    if client:
        client_path = configs_dir / "clients" / f"{client}.toml"
        if client_path.exists():
            with client_path.open("rb") as handle:
                return f"clients/{client}", tomllib.load(handle)

    default_path = configs_dir / "default.toml"
    if not default_path.exists():
        raise FileNotFoundError(f"Default config not found: {default_path}")
    with default_path.open("rb") as handle:
        return "default", tomllib.load(handle)
