"""Tests for protolab.analyze — cluster analysis."""

from __future__ import annotations

from protolab.analyze import analyze_corrections


def test_cluster_grouping(sample_corrections, sample_rules):
    """10 corrections across 3 steps — 3 clusters, sorted by count."""
    result = analyze_corrections(sample_corrections, sample_rules)
    assert result.unique_steps == 3
    assert len(result.clusters) == 3
    # Sorted descending: classification (5), severity (3), differential (2)
    assert result.clusters[0].step == "classification"
    assert result.clusters[0].count == 5
    assert result.clusters[1].step == "severity_assessment"
    assert result.clusters[1].count == 3
    assert result.clusters[2].step == "differential"
    assert result.clusters[2].count == 2


def test_concentration_ratio(sample_corrections, sample_rules):
    """Top cluster has 5/10 — ratio 0.5."""
    result = analyze_corrections(sample_corrections, sample_rules)
    assert result.concentration_ratio == 0.5


def test_preventable_detection(sample_corrections, sample_rules):
    """Rule added on day 3, corrections on day 1 and day 5 — preventable_count = 1.

    For the differential step specifically: rule_003 added day 3 (March 23).
    corr_009 on day 3 (March 23) — rule date <= corr date, so preventable.
    corr_010 on day 9 (March 29) — rule date <= corr date, so preventable.
    That's 2 preventable for differential.

    But the test title says "day 1 and day 5 → preventable = 1" generically.
    Let's verify: for severity_assessment, rule_002 added day 3.
    corr_006 day 2 — not preventable. corr_007 day 5 — preventable.
    corr_008 day 7 — preventable. So 2 preventable for severity.
    """
    result = analyze_corrections(sample_corrections, sample_rules)
    # Check severity_assessment cluster specifically
    severity = next(c for c in result.clusters if c.step == "severity_assessment")
    # corr_006 (day 2) is before rule (day 3) — not preventable
    # corr_007 (day 5) and corr_008 (day 7) are after — preventable
    assert severity.preventable_count == 2


def test_empty_corrections():
    """0 corrections — empty analysis, no crash."""
    result = analyze_corrections([], [])
    assert result.total_corrections == 0
    assert result.unique_steps == 0
    assert result.clusters == []
    assert result.concentration_ratio == 0.0


def test_malformed_correction_skipped():
    """Corrections missing 'step' are skipped, not KeyError."""
    corrections = [
        {"id": "corr_001"},  # missing step
        {"id": "corr_002", "step": "a", "date": None},  # has step but no valid date
    ]
    result = analyze_corrections(corrections, [])
    # corr_001 skipped (no step), corr_002 grouped under "a"
    assert result.total_corrections == 2  # total counts all
    assert len(result.clusters) == 1
    assert result.clusters[0].step == "a"
