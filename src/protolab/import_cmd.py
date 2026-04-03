"""protolab import — import eval failures as correction stubs."""

from __future__ import annotations

import csv
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .store import load_corrections, next_id


def import_eval_failures(
    config: Config,
    path: Path,
    subject_field: str,
    output_field: str,
    step_field: str,
) -> list[dict]:
    """Read JSONL or CSV. Map fields to correction schema.

    Set correct_output and reasoning to 'TODO'.
    Return list of correction stubs.
    """
    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        rows = _read_jsonl(path)
    elif suffix == ".csv":
        rows = _read_csv(path)
    else:
        raise ValueError(
            f"Unsupported import format '{suffix}'. Use .jsonl or .csv."
        )

    existing = load_corrections(config)
    stubs: list[dict] = []
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
        stubs.append({
            "id": corr_id,
            "subject": mapped["subject"],
            "date": datetime.now(timezone.utc),
            "protocol_version": config.protocol_version,
            "step": mapped["step"],
            "protocol_output": mapped["protocol_output"],
            "correct_output": "TODO",
            "reasoning": "TODO",
        })

    return stubs, skipped


def _read_jsonl(path: Path) -> list[dict]:
    """Read JSONL file, one JSON object per line."""
    rows: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _read_csv(path: Path) -> list[dict]:
    """Read CSV file with header row."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)
