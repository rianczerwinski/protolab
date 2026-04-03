"""Tests for protolab.correct — interactive and batch correction logging."""

from __future__ import annotations

import json

import pytest
import tomli_w

from protolab.correct import batch_correct, extract_rule
from protolab.store import load_toml, save_corrections, save_toml


def test_batch_json(tmp_project, sample_config):
    """Load batch from JSON array — correct count, all fields populated."""
    batch_file = tmp_project / "batch.json"
    batch_file.write_text(json.dumps([
        {
            "subject": "case_a", "step": "classification",
            "protocol_output": "X", "correct_output": "Y",
            "reasoning": "Because Z",
        },
        {
            "subject": "case_b", "step": "severity",
            "protocol_output": "low", "correct_output": "high",
            "reasoning": "Missed factors",
        },
    ]))
    result = batch_correct(sample_config, batch_file)
    assert len(result) == 2
    assert result[0]["id"] == "corr_001"
    assert result[1]["id"] == "corr_002"
    assert result[0]["subject"] == "case_a"
    assert result[1]["reasoning"] == "Missed factors"


def test_batch_toml(tmp_project, sample_config):
    """Load batch from TOML — correct count, all fields populated."""
    batch_file = tmp_project / "batch.toml"
    batch_file.write_text(tomli_w.dumps({
        "corrections": [
            {
                "subject": "case_a", "step": "classification",
                "protocol_output": "X", "correct_output": "Y",
                "reasoning": "Because Z",
            },
        ]
    }))
    result = batch_correct(sample_config, batch_file)
    assert len(result) == 1
    assert result[0]["step"] == "classification"


def test_batch_validates(tmp_project, sample_config):
    """Batch with missing required field — raises with informative error."""
    batch_file = tmp_project / "bad.json"
    batch_file.write_text(json.dumps([
        {"subject": "case_a", "step": "classification"}
        # missing: protocol_output, correct_output, reasoning
    ]))
    with pytest.raises(ValueError, match="missing required field"):
        batch_correct(sample_config, batch_file)


def test_rule_extraction(tmp_project, sample_config):
    """Correction with rule text — rule file updated, source references correction id."""
    correction = {
        "id": "corr_001",
        "subject": "case_a",
        "date": sample_config.last_resynthesis_date or __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        "protocol_version": "v1.0",
        "step": "classification",
        "protocol_output": "X",
        "correct_output": "Y",
        "reasoning": "Z",
        "rule": "When A, prefer B over C.",
    }
    rule = extract_rule(correction, sample_config)
    assert rule is not None
    assert rule["id"] == "rule_001"
    assert rule["decision_point"] == "classification"
    assert rule["rule"] == "When A, prefer B over C."
    assert rule["confidence"] == "provisional"
    assert rule["source"] == "corr_001"


def test_batch_string_date_parsed(tmp_project, sample_config):
    """String date in JSON batch is parsed to datetime."""
    batch_file = tmp_project / "dated.json"
    batch_file.write_text(json.dumps([
        {
            "subject": "x", "step": "a",
            "protocol_output": "b", "correct_output": "c",
            "reasoning": "d",
            "date": "2026-03-22T14:30:00+00:00",
        },
    ]))
    result = batch_correct(sample_config, batch_file)
    from datetime import datetime
    assert isinstance(result[0]["date"], datetime)


def test_version_stamped(tmp_project, sample_config):
    """Correction auto-populated with current protocol version from config."""
    batch_file = tmp_project / "batch.json"
    batch_file.write_text(json.dumps([
        {
            "subject": "x", "step": "a",
            "protocol_output": "b", "correct_output": "c",
            "reasoning": "d",
        },
    ]))
    result = batch_correct(sample_config, batch_file)
    assert result[0]["protocol_version"] == sample_config.protocol_version


def test_optional_rule_absent(tmp_project, sample_config):
    """Correction without rule — no rule field in output TOML."""
    corrections = [{
        "id": "corr_001",
        "subject": "case_a",
        "step": "classification",
        "protocol_output": "X",
        "correct_output": "Y",
        "reasoning": "Z",
        "protocol_version": "v1.0",
        "date": __import__("datetime").datetime(2026, 3, 22, tzinfo=__import__("datetime").timezone.utc),
    }]
    save_corrections(sample_config, corrections)
    # Reload the raw TOML to check field presence
    path = sample_config.root / sample_config.corrections_path
    data = load_toml(path)
    assert "rule" not in data["corrections"][0]
