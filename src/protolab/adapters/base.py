"""Base adapter protocol and shared utilities.

All adapters convert eval framework output into ``CorrectionStub`` objects —
a normalized intermediate form that ``import_cmd`` converts into full
``Correction`` dicts with IDs, timestamps, and protocol version.
"""

from __future__ import annotations

import csv
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CorrectionStub:
    """Normalized correction data extracted by an adapter.

    Fields mirror the Correction TypedDict but without system-generated
    values (id, date, protocol_version) which are added during import.
    """

    subject: str
    step: str
    protocol_output: str
    correct_output: str = "TODO"
    reasoning: str = "TODO"
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """Abstract base for eval framework adapters."""

    name: str
    formats: tuple[str, ...]  # supported file extensions

    @abstractmethod
    def parse(self, path: Path) -> list[CorrectionStub]:
        """Parse a source file into correction stubs.

        Adapters should filter to failures/errors by default — callers
        expect only actionable items, not the full eval result set.
        """


def resolve_path(obj: Any, dot_path: str) -> Any:
    """Traverse nested dicts/lists via dot-path notation.

    ``"a.b.0.c"`` resolves to ``obj["a"]["b"][0]["c"]``.
    Returns ``None`` if any segment is missing or the path is invalid.
    """
    current = obj
    for segment in dot_path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, (list, tuple)):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def read_file(path: Path) -> list[dict[str, Any]]:
    """Read a data file, dispatching by extension.

    Supports ``.jsonl`` (one JSON object per line), ``.csv`` (header row),
    and ``.json`` (top-level array or object with a results array).
    """
    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        return _read_jsonl(path)
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".json":
        return _read_json(path)

    raise ValueError(f"Unsupported file format '{suffix}'. Use .jsonl, .csv, or .json.")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _read_json(path: Path) -> list[dict[str, Any]]:
    with path.open() as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Common pattern: results nested under a key
        for key in ("results", "data", "items", "rows"):
            if key in data and isinstance(data[key], list):
                return data[key]  # type: ignore[no-any-return]
        # Single object — wrap in list
        return [data]
    return []
