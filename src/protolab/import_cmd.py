"""protolab import — import eval failures as correction stubs.

Supports two modes:
- **Adapter mode** (``--from <name>``): uses a registered or config-defined
  adapter to parse eval framework output with full schema mapping.
- **Legacy mode** (``--subject-field``, ``--output-field``, ``--step-field``):
  flat field mapping on JSONL/CSV, backward-compatible with v0.1.
"""

from __future__ import annotations

import json
import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import get_adapter
from .adapters.base import CorrectionStub, read_file
from .config import Config
from .store import load_corrections, next_id
from .types import Correction

logger = logging.getLogger(__name__)


def import_eval_failures(
    config: Config,
    path: Path,
    adapter_name: str = "auto",
    subject_field: str = "subject",
    output_field: str = "output",
    step_field: str = "step",
) -> tuple[list[Correction], int]:
    """Import eval failures as correction stubs.

    When *adapter_name* is ``"auto"``, attempts to detect the source format.
    When set to ``"legacy"``, uses the flat field-mapping path.
    Otherwise, resolves the named adapter from the registry or config.

    Returns ``(stubs, skipped)`` — the list of created correction dicts
    and the count of rows that were skipped due to missing fields.
    """
    if adapter_name == "auto":
        adapter_name = _detect_adapter(path)

    if adapter_name == "legacy":
        return _legacy_import(config, path, subject_field, output_field, step_field)

    # Adapter-based import
    adapter = get_adapter(adapter_name, config)
    correction_stubs = adapter.parse(path)
    return _stubs_to_corrections(config, correction_stubs)


def _detect_adapter(path: Path) -> str:
    """Guess the adapter from file content structure.

    Checks for known patterns (Promptfoo's ``results`` key, Braintrust's
    ``scores`` key). Falls back to ``"legacy"`` for unrecognized formats.
    """
    suffix = path.suffix.lower()

    if suffix == ".json":
        try:
            with path.open() as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Promptfoo: has "results" key with nested structure
                results = data.get("results")
                if isinstance(results, list) and results:
                    first = results[0]
                    if isinstance(first, dict) and (
                        "success" in first or "gradingResult" in first
                    ):
                        logger.debug("Auto-detected Promptfoo format")
                        return "promptfoo"
        except (json.JSONDecodeError, OSError):
            pass

    if suffix == ".jsonl":
        try:
            with path.open() as f:
                first_line = f.readline().strip()
            if first_line:
                row = json.loads(first_line)
                if isinstance(row, dict) and "scores" in row:
                    logger.debug("Auto-detected Braintrust format")
                    return "braintrust"
        except (json.JSONDecodeError, OSError):
            pass

    return "legacy"


def _stubs_to_corrections(
    config: Config, stubs: list[CorrectionStub]
) -> tuple[list[Correction], int]:
    """Convert adapter stubs to full Correction dicts with IDs and timestamps."""
    existing = load_corrections(config)
    corrections: list[Correction] = []

    for stub in stubs:
        corr_id = next_id(existing + corrections, "corr")
        correction: dict[str, Any] = {
            "id": corr_id,
            "subject": stub.subject,
            "date": datetime.now(timezone.utc),
            "protocol_version": config.protocol_version,
            "step": stub.step,
            "protocol_output": stub.protocol_output,
            "correct_output": stub.correct_output,
            "reasoning": stub.reasoning,
        }
        if stub.metadata:
            correction["metadata"] = stub.metadata
        corrections.append(correction)  # type: ignore[arg-type]

    logger.debug("Converted %d stubs to corrections", len(corrections))
    return corrections, 0


def _legacy_import(
    config: Config,
    path: Path,
    subject_field: str,
    output_field: str,
    step_field: str,
) -> tuple[list[Correction], int]:
    """Original flat field-mapping import (v0.1 behavior).

    Each target field tries candidates in order: the user-specified name
    first, then common defaults. First match wins.
    """
    rows = read_file(path)
    existing = load_corrections(config)
    stubs: list[Correction] = []
    skipped = 0

    field_map = {
        "subject": [subject_field, "subject", "input"],
        "protocol_output": [output_field, "output", "expected"],
        "step": [step_field, "step", "category"],
    }

    for i, row in enumerate(rows):
        mapped: dict[str, str] = {}
        skip = False
        for target, candidates in field_map.items():
            value = None
            for candidate in candidates:
                if candidate in row:
                    value = row[candidate]
                    break
            if value is None:
                warnings.warn(
                    f"Row {i}: missing field for '{target}' "
                    f"(tried: {', '.join(candidates)}). Skipping.",
                    stacklevel=2,
                )
                skip = True
                break
            mapped[target] = value

        if skip:
            skipped += 1
            continue

        corr_id = next_id(existing + stubs, "corr")
        stubs.append(
            {
                "id": corr_id,
                "subject": mapped["subject"],
                "date": datetime.now(timezone.utc),
                "protocol_version": config.protocol_version,
                "step": mapped["step"],
                "protocol_output": mapped["protocol_output"],
                "correct_output": "TODO",
                "reasoning": "TODO",
            }
        )

    logger.debug(
        "Legacy import: %d stubs, %d skipped from %s", len(stubs), skipped, path
    )
    return stubs, skipped
