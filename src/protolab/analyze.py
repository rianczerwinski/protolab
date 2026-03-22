"""protolab analyze — cluster analysis of accumulated corrections."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class StepCluster:
    """Correction cluster for a single decision point."""

    step: str
    count: int
    percentage: float
    corrections: list[dict]
    rules: list[dict]
    preventable_count: int


@dataclass
class AnalysisResult:
    """Aggregate analysis across all corrections."""

    total_corrections: int
    unique_steps: int
    clusters: list[StepCluster]  # sorted by count desc
    concentration_ratio: float  # top cluster / total


def analyze_corrections(
    corrections: list[dict],
    rules: list[dict],
) -> AnalysisResult:
    """Cluster corrections by step, compute diagnostics."""
    total = len(corrections)

    if total == 0:
        return AnalysisResult(
            total_corrections=0,
            unique_steps=0,
            clusters=[],
            concentration_ratio=0.0,
        )

    # Group corrections by step, skip malformed entries
    by_step: dict[str, list[dict]] = defaultdict(list)
    for corr in corrections:
        if "step" not in corr:
            continue
        by_step[corr["step"]].append(corr)

    # Build clusters
    clusters: list[StepCluster] = []
    for step, step_corrections in by_step.items():
        step_rules = [
            r for r in rules
            if r.get("decision_point") == step
        ]

        # Count preventable: corrections after any matching rule was added
        preventable = 0
        for corr in step_corrections:
            if "date" not in corr:
                continue
            for rule in step_rules:
                if "date_added" not in rule:
                    continue
                if rule["date_added"] <= corr["date"]:
                    preventable += 1
                    break

        clusters.append(StepCluster(
            step=step,
            count=len(step_corrections),
            percentage=len(step_corrections) / total * 100,
            corrections=step_corrections,
            rules=step_rules,
            preventable_count=preventable,
        ))

    # Sort by count descending
    clusters.sort(key=lambda c: c.count, reverse=True)

    return AnalysisResult(
        total_corrections=total,
        unique_steps=len(clusters),
        clusters=clusters,
        concentration_ratio=clusters[0].count / total,
    )
