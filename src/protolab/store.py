"""TOML read/write for corrections and rules.

All file I/O for correction logs and rule files is routed through this
module. Callers never open TOML files directly — this keeps the storage
format isolated and swappable.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from .config import Config
from .types import Correction, Rule

logger = logging.getLogger(__name__)

ID_PAD_WIDTH = 3  # zero-pad width for generated IDs (corr_001, rule_042)


def load_toml(path: Path) -> dict:
    """Load a TOML file and return its contents as a dict.

    Empty files (0 bytes) return ``{}``. Non-empty files that fail to parse
    raise ``ValueError`` with the file path for diagnostics.
    """
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        logger.debug("Loaded %s (%d top-level keys)", path, len(data))
        return data
    except tomllib.TOMLDecodeError:
        if path.stat().st_size == 0:
            logger.debug("Empty file %s — returning {}", path)
            return {}
        raise ValueError(
            f"Failed to parse TOML file '{path}'. "
            f"Check for syntax errors."
        )


def save_toml(path: Path, data: dict) -> None:
    """Write a dict to a TOML file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(data))
    logger.debug("Wrote %s", path)


def load_corrections(config: Config) -> list[Correction]:
    """Load the correction log. Returns ``[]`` if the file is missing or empty."""
    path = config.root / config.corrections_path
    if not path.exists():
        return []
    data = load_toml(path)
    return data.get("corrections", [])


def save_corrections(config: Config, corrections: list[Correction]) -> None:
    """Write the full correction list to the correction log."""
    path = config.root / config.corrections_path
    save_toml(path, {"corrections": corrections})


def load_rules(config: Config) -> list[Rule]:
    """Load the rules file. Returns ``[]`` if the file is missing or empty."""
    path = config.root / config.rules_path
    if not path.exists():
        return []
    data = load_toml(path)
    return data.get("rules", [])


def save_rules(config: Config, rules: list[Rule]) -> None:
    """Write the full rule list to the rules file."""
    path = config.root / config.rules_path
    save_toml(path, {"rules": rules})


def next_id(existing: list[dict], prefix: str) -> str:
    """Generate the next sequential ID (e.g. ``corr_001``, ``rule_042``).

    Scans existing items for the highest numeric suffix and increments.
    Non-numeric suffixes (e.g. manually inserted IDs) are skipped.
    A collision check ensures the generated ID is unique even if manual
    entries occupy the next slot.
    """
    existing_ids = {item.get("id", "") for item in existing}
    if not existing:
        candidate = f"{prefix}_{'1':0>{ID_PAD_WIDTH}}"
        logger.debug("Generated first ID: %s", candidate)
        return candidate

    max_num = 0
    for item in existing:
        item_id = item.get("id", "")
        parts = item_id.rsplit("_", 1)
        if len(parts) == 2:
            try:
                num = int(parts[1])
                if num > max_num:
                    max_num = num
            except ValueError:
                # Non-numeric suffix (e.g. manual ID) — skip
                continue

    # Collision guard: if a manual entry occupies the next slot, keep incrementing
    candidate = f"{prefix}_{max_num + 1:0{ID_PAD_WIDTH}d}"
    while candidate in existing_ids:
        max_num += 1
        candidate = f"{prefix}_{max_num + 1:0{ID_PAD_WIDTH}d}"

    logger.debug("Generated ID: %s", candidate)
    return candidate
