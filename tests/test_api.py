"""Tests for the Project programmatic API."""

from __future__ import annotations

import json

from protolab.api import Project
from protolab.config import load_config


def test_project_init(tmp_project):
    """Project loads config from path."""
    project = Project(tmp_project / "protolab.toml")
    assert project.config.root == tmp_project


def test_corrections_empty(tmp_project):
    """Fresh project has no corrections."""
    project = Project(tmp_project / "protolab.toml")
    assert project.corrections() == []


def test_add_correction(tmp_project):
    """add_correction persists and returns the correction."""
    project = Project(tmp_project / "protolab.toml")
    corr = project.add_correction(
        subject="test_case",
        step="classification",
        protocol_output="Type 4",
        correct_output="Type 5",
        reasoning="Domain-exhaustion, not trust-failure.",
    )
    assert corr["id"] == "corr_001"
    assert corr["subject"] == "test_case"

    # Persisted
    loaded = project.corrections()
    assert len(loaded) == 1
    assert loaded[0]["id"] == "corr_001"


def test_add_correction_with_metadata(tmp_project):
    """Metadata is carried through."""
    project = Project(tmp_project / "protolab.toml")
    corr = project.add_correction(
        subject="test",
        step="step",
        protocol_output="a",
        correct_output="b",
        reasoning="c",
        metadata={"model": "gpt-4o", "score": 0.3},
    )
    assert corr["metadata"]["model"] == "gpt-4o"


def test_add_correction_with_rule(tmp_project):
    """Rule text triggers rule extraction."""
    project = Project(tmp_project / "protolab.toml")
    project.add_correction(
        subject="test",
        step="step",
        protocol_output="a",
        correct_output="b",
        reasoning="c",
        rule="When X, classify as Y.",
    )
    rules = project.rules()
    assert len(rules) == 1
    assert rules[0]["rule"] == "When X, classify as Y."


def test_ingest_legacy(tmp_project):
    """ingest with legacy adapter imports JSONL."""
    project = Project(tmp_project / "protolab.toml")

    f = tmp_project / "evals.jsonl"
    lines = [
        json.dumps({"subject": f"case_{i}", "output": f"out_{i}", "step": f"step_{i}"})
        for i in range(3)
    ]
    f.write_text("\n".join(lines) + "\n")

    stubs, skipped = project.ingest(f, adapter="legacy")
    assert len(stubs) == 3
    assert skipped == 0
    assert len(project.corrections()) == 3


def test_analyze_empty(tmp_project):
    """Analyze on empty project returns zero totals."""
    project = Project(tmp_project / "protolab.toml")
    result = project.analyze()
    assert result.total_corrections == 0


def test_check_returns_triggers(tmp_project):
    """Check returns trigger results."""
    project = Project(tmp_project / "protolab.toml")
    results = project.check()
    assert isinstance(results, list)
    assert all(hasattr(r, "met") for r in results)


def test_assemble_prompt(tmp_project, sample_corrections):
    """assemble_prompt produces a string containing protocol content."""
    config = load_config(tmp_project / "protolab.toml")
    from protolab.store import save_corrections

    save_corrections(config, sample_corrections)

    project = Project(tmp_project / "protolab.toml")
    prompt = project.assemble_prompt()
    assert "Test Protocol" in prompt
    assert "corr_001" in prompt
