"""protolab check — evaluate resynthesis triggers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import Config


@dataclass
class TriggerResult:
    """Result of evaluating a single resynthesis trigger."""

    name: str
    met: bool
    current_value: float | int
    threshold: float | int


def evaluate_triggers(
    config: Config,
    corrections: list[dict],
    rules: list[dict],
) -> list[TriggerResult]:
    """Evaluate all configured triggers. Return results."""
    results: list[TriggerResult] = []
    total = len(corrections)

    # 1. Total corrections
    results.append(TriggerResult(
        name="total_corrections",
        met=total >= config.triggers.total_corrections,
        current_value=total,
        threshold=config.triggers.total_corrections,
    ))

    # 2. Cluster threshold
    if total > 0:
        valid = [c for c in corrections if "step" in c]
        step_counts = Counter(c["step"] for c in valid)
        max_count = max(step_counts.values()) if step_counts else 0
        ratio = max_count / total
    else:
        ratio = 0.0
    results.append(TriggerResult(
        name="cluster_threshold",
        met=ratio >= config.triggers.cluster_threshold,
        current_value=round(ratio, 3),
        threshold=config.triggers.cluster_threshold,
    ))

    # 3. Preventable errors
    preventable = 0
    for corr in corrections:
        if "step" not in corr or "date" not in corr:
            continue
        for rule in rules:
            if ("decision_point" not in rule or "date_added" not in rule):
                continue
            if (rule["decision_point"] == corr["step"]
                    and rule["date_added"] <= corr["date"]):
                preventable += 1
                break
    results.append(TriggerResult(
        name="preventable_errors",
        met=preventable >= config.triggers.preventable_errors,
        current_value=preventable,
        threshold=config.triggers.preventable_errors,
    ))

    # 4. Days since last resynthesis
    if config.triggers.max_days_since_resynthesis is not None:
        if config.last_resynthesis_date is None:
            # No previous resynthesis — don't trigger
            results.append(TriggerResult(
                name="max_days_since_resynthesis",
                met=False,
                current_value=0,
                threshold=config.triggers.max_days_since_resynthesis,
            ))
        else:
            days = (datetime.now(timezone.utc) - config.last_resynthesis_date).days
            results.append(TriggerResult(
                name="max_days_since_resynthesis",
                met=days >= config.triggers.max_days_since_resynthesis,
                current_value=days,
                threshold=config.triggers.max_days_since_resynthesis,
            ))

    return results
