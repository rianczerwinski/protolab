"""Tests for protolab.check — resynthesis trigger evaluation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from protolab.check import evaluate_triggers


def _find(results, name):
    return next(r for r in results if r.name == name)


def test_total_met(sample_config, sample_corrections):
    """10 corrections, threshold 10 — trigger met."""
    results = evaluate_triggers(sample_config, sample_corrections, [])
    assert _find(results, "total_corrections").met is True


def test_total_unmet(sample_config):
    """9 corrections, threshold 10 — trigger unmet."""
    corrections = [{"id": f"corr_{i:03d}", "step": "a"} for i in range(1, 10)]
    results = evaluate_triggers(sample_config, corrections, [])
    assert _find(results, "total_corrections").met is False


def test_cluster_met(sample_config, sample_corrections):
    """5/10 corrections on classification step, threshold 0.30 — met."""
    results = evaluate_triggers(sample_config, sample_corrections, [])
    trigger = _find(results, "cluster_threshold")
    assert trigger.met is True
    assert trigger.current_value == 0.5


def test_cluster_unmet(sample_config):
    """2/10 on same step, threshold 0.30 — unmet."""
    # 10 corrections spread evenly across 5 steps (2 each = 0.20)
    corrections = [
        {"id": f"corr_{i:03d}", "step": f"step_{i % 5}"} for i in range(1, 11)
    ]
    results = evaluate_triggers(sample_config, corrections, [])
    assert _find(results, "cluster_threshold").met is False


def test_preventable_met(sample_config, sample_corrections, sample_rules):
    """3 corrections on step with existing rule, threshold 3 — met."""
    results = evaluate_triggers(sample_config, sample_corrections, sample_rules)
    trigger = _find(results, "preventable_errors")
    # Rules added day 3. Post-rule corrections:
    # classification: corr_003 (day 4), corr_004 (day 6), corr_005 (day 8) = 3
    # severity_assessment: corr_007 (day 5), corr_008 (day 7) = 2
    # differential: corr_010 (day 9) = 1
    # Total preventable = 6
    assert trigger.met is True
    assert trigger.current_value >= 3


def test_days_met(sample_config):
    """Last resynthesis 31 days ago, threshold 30 — met."""
    sample_config.last_resynthesis_date = datetime.now(timezone.utc) - timedelta(
        days=31
    )
    results = evaluate_triggers(sample_config, [], [])
    assert _find(results, "max_days_since_resynthesis").met is True


def test_days_null(sample_config):
    """No previous resynthesis — trigger not evaluated (skip, don't trigger)."""
    sample_config.last_resynthesis_date = None
    results = evaluate_triggers(sample_config, [], [])
    assert _find(results, "max_days_since_resynthesis").met is False


def test_exit_code(sample_config, sample_corrections):
    """Any trigger met — exit code 1 (represented by any(.met))."""
    results = evaluate_triggers(sample_config, sample_corrections, [])
    assert any(r.met for r in results)


def test_malformed_correction_skipped(sample_config):
    """Corrections missing 'step' or 'date' are skipped, not KeyError."""
    corrections = [
        {"id": "corr_001"},  # missing step and date
        {"id": "corr_002", "step": "a"},  # missing date
        {
            "id": "corr_003",
            "step": "a",
            "date": datetime(2026, 3, 22, tzinfo=timezone.utc),
        },
    ]
    rules = [
        {
            "decision_point": "a",
            "date_added": datetime(2026, 3, 20, tzinfo=timezone.utc),
        },
    ]
    results = evaluate_triggers(sample_config, corrections, rules)
    # Should not crash — preventable count should only count corr_003
    trigger = _find(results, "preventable_errors")
    assert trigger.current_value == 1
