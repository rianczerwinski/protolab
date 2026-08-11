"""Import eval failures through built-in, custom, or legacy adapters."""

from __future__ import annotations

import json
import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path

from .adapters import get_adapter
from .adapters.base import CorrectionStub, read_file
from .config import Config
from .store import load_corrections, next_id
from .types import Correction

logger = logging.getLogger(__name__)


def import_eval_failures(
    config: Config,
    path: Path,
    subject_field: str = "subject",
    output_field: str = "output",
    step_field: str = "step",
    *,
    adapter_name: str = "auto",
) -> tuple[list[Correction], int]:
    """Import eval failures and return ``(corrections, skipped_rows)``.

    ``auto`` recognizes built-in formats and otherwise preserves the original
    flat JSONL/CSV mapping. A named adapter resolves either a built-in parser or
    an ``[import.<name>]`` schema from the project configuration.
    """
    if adapter_name == "auto":
        adapter_name = _detect_adapter(path)

    if adapter_name == "legacy":
        return _legacy_import(
            config, path, subject_field, output_field, step_field
        )

    adapter = get_adapter(adapter_name, config)
    suffix = path.suffix.lower()
    if suffix not in adapter.formats:
        supported = ", ".join(adapter.formats)
        raise ValueError(
            f"Adapter '{adapter_name}' does not accept '{suffix or 'files without an extension'}'. "
            f"Supported: {supported}."
        )
    return _stubs_to_corrections(config, adapter.parse(path))


def _detect_adapter(path: Path) -> str:
    """Detect known eval exports, falling back to the legacy field mapper."""
    suffix = path.suffix.lower()

    if suffix == ".json":
        try:
            with path.open(encoding="utf-8") as source:
                data = json.load(source)
            if isinstance(data, dict):
                results = data.get("results")
                if isinstance(results, list) and results:
                    first = results[0]
                    if isinstance(first, dict) and (
                        "success" in first or "gradingResult" in first
                    ):
                        return "promptfoo"
        except (json.JSONDecodeError, OSError):
            pass

    if suffix == ".jsonl":
        try:
            with path.open(encoding="utf-8") as source:
                first_line = source.readline().strip()
            if first_line:
                row = json.loads(first_line)
                if isinstance(row, dict) and "scores" in row:
                    return "braintrust"
        except (json.JSONDecodeError, OSError):
            pass

    return "legacy"


def _stubs_to_corrections(
    config: Config, stubs: list[CorrectionStub]
) -> tuple[list[Correction], int]:
    """Add generated IDs, timestamps, and protocol versions to adapter rows."""
    existing = load_corrections(config)
    corrections: list[Correction] = []

    for stub in stubs:
        correction: Correction = {
            "id": next_id(existing + corrections, "corr"),
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
        corrections.append(correction)

    return corrections, 0


def _legacy_import(
    config: Config,
    path: Path,
    subject_field: str,
    output_field: str,
    step_field: str,
) -> tuple[list[Correction], int]:
    """Map flat JSONL, CSV, or JSON rows using the original field contract."""
    rows = read_file(path)
    existing = load_corrections(config)
    corrections: list[Correction] = []
    skipped = 0
    field_map = {
        "subject": [subject_field, "subject", "input"],
        "protocol_output": [output_field, "output", "expected"],
        "step": [step_field, "step", "category"],
    }

    for index, row in enumerate(rows):
        mapped: dict[str, str] = {}
        for target, candidates in field_map.items():
            value = next((row[key] for key in candidates if key in row), None)
            if value is None:
                warnings.warn(
                    f"Row {index}: missing field for '{target}' "
                    f"(tried: {', '.join(candidates)}). Skipping.",
                    stacklevel=2,
                )
                skipped += 1
                break
            mapped[target] = str(value)
        else:
            corrections.append(
                {
                    "id": next_id(existing + corrections, "corr"),
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
        "Legacy import: %d corrections, %d skipped from %s",
        len(corrections),
        skipped,
        path,
    )
    return corrections, skipped
