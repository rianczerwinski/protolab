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
    """Only corrections at or after a matching rule are preventable."""
    result = analyze_corrections(sample_corrections, sample_rules)
    severity = next(c for c in result.clusters if c.step == "severity_assessment")
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


def test_group_by_nested_metadata():
    """Dot-path grouping exposes API analysis dimensions beyond step."""
    corrections = [
        {"id": "corr_001", "step": "classify", "metadata": {"model": "a"}},
        {"id": "corr_002", "step": "classify", "metadata": {"model": "b"}},
        {"id": "corr_003", "step": "classify", "metadata": {"model": "a"}},
    ]

    result = analyze_corrections(corrections, [], group_by="metadata.model")

    assert [cluster.step for cluster in result.clusters] == ["a", "b"]
    assert [cluster.count for cluster in result.clusters] == [2, 1]
    assert result.concentration_ratio == 2 / 3


def test_group_by_missing_from_every_record():
    """An absent grouping dimension produces an empty result, not a crash."""
    corrections = [
        {"id": "corr_001", "step": "classify"},
        {"id": "corr_002", "step": "classify"},
    ]

    result = analyze_corrections(corrections, [], group_by="metadata.model")

    assert result.total_corrections == 2
    assert result.unique_steps == 0
    assert result.clusters == []
    assert result.concentration_ratio == 0.0
