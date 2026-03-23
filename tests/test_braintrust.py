"""Tests for the Braintrust adapter."""

from __future__ import annotations

import json

from protolab.adapters.braintrust import BraintrustAdapter


def test_parse_failures_only(tmp_path):
    """Only rows with scores < 1.0 are imported."""
    lines = [
        json.dumps({"input": "q1", "output": "correct", "scores": {"accuracy": 1.0}}),
        json.dumps(
            {
                "input": "q2",
                "output": "wrong",
                "expected": "right",
                "scores": {"accuracy": 0.0},
                "metadata": {"model": "gpt-4o"},
            }
        ),
    ]
    f = tmp_path / "export.jsonl"
    f.write_text("\n".join(lines) + "\n")

    stubs = BraintrustAdapter().parse(f)

    assert len(stubs) == 1
    assert stubs[0].subject == "q2"
    assert stubs[0].protocol_output == "wrong"
    assert stubs[0].correct_output == "right"
    assert stubs[0].metadata["scores"] == {"accuracy": 0.0}
    assert stubs[0].metadata["model"] == "gpt-4o"


def test_dict_input_stringified(tmp_path):
    """Dict input is stringified using a known key if available."""
    line = json.dumps(
        {
            "input": {"query": "what is 2+2?", "context": "math"},
            "output": "5",
            "scores": {"accuracy": 0.0},
        }
    )
    f = tmp_path / "export.jsonl"
    f.write_text(line + "\n")

    stubs = BraintrustAdapter().parse(f)
    assert len(stubs) == 1
    assert stubs[0].subject == "what is 2+2?"


def test_step_from_metadata(tmp_path):
    """Step is extracted from metadata.category."""
    line = json.dumps(
        {
            "input": "test",
            "output": "bad",
            "scores": {"x": 0.5},
            "metadata": {"category": "billing"},
        }
    )
    f = tmp_path / "export.jsonl"
    f.write_text(line + "\n")

    stubs = BraintrustAdapter().parse(f)
    assert stubs[0].step == "billing"


def test_step_from_tags(tmp_path):
    """Step falls back to first tag if no metadata.step."""
    line = json.dumps(
        {
            "input": "test",
            "output": "bad",
            "scores": {"x": 0.5},
            "tags": ["classification", "hard"],
        }
    )
    f = tmp_path / "export.jsonl"
    f.write_text(line + "\n")

    stubs = BraintrustAdapter().parse(f)
    assert stubs[0].step == "classification"


def test_no_scores_includes_row(tmp_path):
    """Rows without scores are included (no filtering basis)."""
    line = json.dumps({"input": "test", "output": "result"})
    f = tmp_path / "export.jsonl"
    f.write_text(line + "\n")

    stubs = BraintrustAdapter().parse(f)
    assert len(stubs) == 1


def test_empty_file(tmp_path):
    """Empty JSONL produces no stubs."""
    f = tmp_path / "export.jsonl"
    f.write_text("")

    stubs = BraintrustAdapter().parse(f)
    assert stubs == []


def test_braintrust_id_in_metadata(tmp_path):
    """Braintrust row ID is preserved in metadata."""
    line = json.dumps(
        {
            "id": "bt_abc123",
            "input": "test",
            "output": "bad",
            "scores": {"x": 0.5},
        }
    )
    f = tmp_path / "export.jsonl"
    f.write_text(line + "\n")

    stubs = BraintrustAdapter().parse(f)
    assert stubs[0].metadata["braintrust_id"] == "bt_abc123"
