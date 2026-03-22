"""TOML read/write for corrections and rules."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from .config import Config


def load_toml(path: Path) -> dict:
    """Load TOML file. Return dict (may be empty if file has no arrays)."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError:
        # Empty files (0 bytes) are expected — return empty dict.
        # Non-empty files that fail to parse are real errors.
        if path.stat().st_size == 0:
            return {}
        raise ValueError(
            f"Failed to parse TOML file '{path}'. "
            f"Check for syntax errors."
        )


def save_toml(path: Path, data: dict) -> None:
    """Write TOML with clean formatting via tomli_w."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(data))


def load_corrections(config: Config) -> list[dict]:
    """Load correction log. Return data.get('corrections', [])."""
    path = config.root / config.corrections_path
    if not path.exists():
        return []
    data = load_toml(path)
    return data.get("corrections", [])


def save_corrections(config: Config, corrections: list[dict]) -> None:
    """Write corrections as {'corrections': corrections} to TOML."""
    path = config.root / config.corrections_path
    save_toml(path, {"corrections": corrections})


def load_rules(config: Config) -> list[dict]:
    """Load rules. Return data.get('rules', [])."""
    path = config.root / config.rules_path
    if not path.exists():
        return []
    data = load_toml(path)
    return data.get("rules", [])


def save_rules(config: Config, rules: list[dict]) -> None:
    """Write rules as {'rules': rules} to TOML."""
    path = config.root / config.rules_path
    save_toml(path, {"rules": rules})


def next_id(existing: list[dict], prefix: str) -> str:
    """Generate next sequential ID: prefix_NNN."""
    existing_ids = {item.get("id", "") for item in existing}
    if not existing:
        return f"{prefix}_001"
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
                continue
    # Verify no collision, increment if needed
    candidate = f"{prefix}_{max_num + 1:03d}"
    while candidate in existing_ids:
        max_num += 1
        candidate = f"{prefix}_{max_num + 1:03d}"
    return candidate
