"""protolab correct — interactive and batch correction logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click

from .config import Config
from .store import load_corrections, load_rules, load_toml, next_id


def interactive_correct(config: Config) -> dict:
    """Prompt user for correction fields. Return correction dict."""
    existing = load_corrections(config)
    corr_id = next_id(existing, "corr")

    subject = click.prompt("Subject (what was being analyzed)")

    # Step with completion from registry and history
    used_steps = sorted({c["step"] for c in existing})
    if config.steps:
        step_hint = f" [{', '.join(config.steps)}]"
    elif used_steps:
        step_hint = f" (previous: {', '.join(used_steps)})"
    else:
        step_hint = ""
    step = click.prompt(f"Decision point (step){step_hint}")

    protocol_output = click.prompt("What the protocol produced")
    correct_output = click.prompt("What was actually correct")
    reasoning = click.prompt("Why the correction is right")

    correction: dict = {
        "id": corr_id,
        "subject": subject,
        "date": datetime.now(timezone.utc),
        "protocol_version": config.protocol_version,
        "step": step,
        "protocol_output": protocol_output,
        "correct_output": correct_output,
        "reasoning": reasoning,
    }

    if click.confirm("Extract a generalizable rule?", default=False):
        rule_text = click.prompt("Rule")
        correction["rule"] = rule_text

    return correction


def batch_correct(config: Config, path: Path) -> list[dict]:
    """Load corrections from JSON or TOML file. Validate. Return list."""
    existing = load_corrections(config)
    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path) as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError(f"Expected a JSON array in '{path}', got {type(raw).__name__}")
    elif suffix == ".toml":
        data = load_toml(path)
        raw = data.get("corrections", [])
    else:
        raise ValueError(f"Unsupported batch format '{suffix}'. Use .json or .toml.")

    required_fields = {"subject", "step", "protocol_output", "correct_output", "reasoning"}
    corrections: list[dict] = []
    for i, item in enumerate(raw):
        missing = required_fields - set(item.keys())
        if missing:
            raise ValueError(
                f"Correction at index {i} is missing required field(s): "
                f"{', '.join(sorted(missing))}"
            )
        corr_id = next_id(existing + corrections, "corr")
        date_val = item.get("date", datetime.now(timezone.utc))
        if isinstance(date_val, str):
            try:
                date_val = datetime.fromisoformat(date_val)
            except ValueError:
                raise ValueError(
                    f"Correction at index {i} has invalid date format: '{date_val}'. "
                    f"Use ISO 8601 (e.g. 2026-03-22T14:30:00Z)."
                )
        correction: dict = {
            "id": corr_id,
            "subject": item["subject"],
            "date": date_val,
            "protocol_version": config.protocol_version,
            "step": item["step"],
            "protocol_output": item["protocol_output"],
            "correct_output": item["correct_output"],
            "reasoning": item["reasoning"],
        }
        if "rule" in item:
            correction["rule"] = item["rule"]
        corrections.append(correction)

    return corrections


def extract_rule(correction: dict, config: Config) -> dict | None:
    """If correction has rule text, create rule dict with provisional confidence."""
    if "rule" not in correction:
        return None

    existing_rules = load_rules(config)
    rule_id = next_id(existing_rules, "rule")

    return {
        "id": rule_id,
        "decision_point": correction["step"],
        "rule": correction["rule"],
        "confidence": "provisional",
        "source": correction["id"],
        "date_added": correction["date"],
    }
