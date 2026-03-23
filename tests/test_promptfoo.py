"""Tests for the Promptfoo adapter."""

from __future__ import annotations

import json

from protolab.adapters.promptfoo import PromptfooAdapter


def test_parse_failures_only(tmp_path):
    """Only failed results are imported."""
    data = {
        "results": [
            {
                "success": True,
                "response": {"output": "correct answer"},
                "vars": {"input": "q1"},
                "test": {"description": "passing test"},
            },
            {
                "success": False,
                "response": {"output": "wrong answer"},
                "vars": {"input": "q2"},
                "test": {
                    "description": "failing test",
                    "assert": [{"type": "equals", "value": "right answer"}],
                },
                "gradingResult": {
                    "pass": False,
                    "reason": "Output did not match expected",
                    "score": 0.0,
                },
            },
        ]
    }
    f = tmp_path / "results.json"
    f.write_text(json.dumps(data))

    adapter = PromptfooAdapter()
    stubs = adapter.parse(f)

    assert len(stubs) == 1
    assert stubs[0].subject == "q2"
    assert stubs[0].protocol_output == "wrong answer"
    assert stubs[0].correct_output == "right answer"
    assert stubs[0].reasoning == "Output did not match expected"
    assert stubs[0].step == "failing test"


def test_metadata_extraction(tmp_path):
    """Score and provider are carried as metadata."""
    data = {
        "results": [
            {
                "success": False,
                "response": {"output": "bad"},
                "vars": {"input": "test"},
                "test": {"description": "step_a"},
                "gradingResult": {"score": 0.3, "reason": "low quality"},
                "provider": {"id": "anthropic:claude-sonnet"},
            }
        ]
    }
    f = tmp_path / "results.json"
    f.write_text(json.dumps(data))

    stubs = PromptfooAdapter().parse(f)
    assert len(stubs) == 1
    assert stubs[0].metadata["score"] == 0.3
    assert stubs[0].metadata["provider"] == "anthropic:claude-sonnet"


def test_missing_vars_uses_description(tmp_path):
    """When vars is empty, test.description becomes the subject."""
    data = {
        "results": [
            {
                "success": False,
                "response": {"output": "output"},
                "vars": {},
                "test": {"description": "my test case"},
            }
        ]
    }
    f = tmp_path / "results.json"
    f.write_text(json.dumps(data))

    stubs = PromptfooAdapter().parse(f)
    assert len(stubs) == 1
    assert stubs[0].subject == "my test case"


def test_empty_results(tmp_path):
    """Empty results array produces no stubs."""
    f = tmp_path / "results.json"
    f.write_text(json.dumps({"results": []}))

    stubs = PromptfooAdapter().parse(f)
    assert stubs == []


def test_all_passing(tmp_path):
    """All-passing results produce no stubs."""
    data = {
        "results": [
            {
                "success": True,
                "response": {"output": "good"},
                "vars": {"input": "q"},
                "test": {"description": "t"},
            }
        ]
    }
    f = tmp_path / "results.json"
    f.write_text(json.dumps(data))

    stubs = PromptfooAdapter().parse(f)
    assert stubs == []
