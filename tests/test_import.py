"""Tests for protolab.import_cmd — eval failure import."""

from __future__ import annotations

import warnings

from protolab.config import load_config

from protolab.import_cmd import import_eval_failures


def test_jsonl_import(tmp_project, sample_config):
    """JSONL with 5 lines — 5 correction stubs with TODO placeholders."""
    jsonl = tmp_project / "evals.jsonl"
    lines = []
    for i in range(5):
        lines.append(f'{{"subject": "case_{i}", "output": "wrong_{i}", "step": "step_{i}"}}')
    jsonl.write_text("\n".join(lines) + "\n")

    stubs, skipped = import_eval_failures(
        sample_config, jsonl,
        subject_field="subject", output_field="output", step_field="step",
    )
    assert len(stubs) == 5
    assert all(s["correct_output"] == "TODO" for s in stubs)
    assert all(s["reasoning"] == "TODO" for s in stubs)
    assert stubs[0]["protocol_output"] == "wrong_0"


def test_csv_import(tmp_project, sample_config):
    """CSV with header row — correct field mapping."""
    csv_file = tmp_project / "evals.csv"
    csv_file.write_text("subject,output,step\ncase_a,wrong_a,step_a\ncase_b,wrong_b,step_b\n")

    stubs, skipped = import_eval_failures(
        sample_config, csv_file,
        subject_field="subject", output_field="output", step_field="step",
    )
    assert len(stubs) == 2
    assert stubs[0]["subject"] == "case_a"
    assert stubs[1]["step"] == "step_b"


def test_custom_fields(tmp_project, sample_config):
    """--subject-field=input --output-field=expected — maps correctly."""
    jsonl = tmp_project / "custom.jsonl"
    jsonl.write_text('{"input": "hello", "expected": "world", "category": "greet"}\n')

    stubs, skipped = import_eval_failures(
        sample_config, jsonl,
        subject_field="input", output_field="expected", step_field="category",
    )
    assert len(stubs) == 1
    assert stubs[0]["subject"] == "hello"
    assert stubs[0]["protocol_output"] == "world"
    assert stubs[0]["step"] == "greet"


def test_missing_field(tmp_project, sample_config):
    """Row missing mapped field — skip with warning, not crash."""
    jsonl = tmp_project / "missing.jsonl"
    # First row has all fields, second is missing 'step'
    jsonl.write_text(
        '{"subject": "a", "output": "b", "step": "c"}\n'
        '{"subject": "d", "output": "e"}\n'
    )

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        stubs, skipped = import_eval_failures(
            sample_config, jsonl,
            subject_field="subject", output_field="output", step_field="step",
        )
    assert len(stubs) == 1  # Second row skipped
    assert skipped == 1
    assert len(w) == 1  # Warning emitted
    assert "missing field" in str(w[0].message).lower()


def test_configured_adapter_imports_nested_records(tmp_project):
    """A named TOML schema drives nested source ingestion end to end."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"
version = "v2.0"

[import.eval_lab]
format = "jsonl"
subject = "case.input"
protocol_output = "result.actual"
step = "case.step"
correct_output = "case.expected"
reasoning = "result.explanation"
filter_field = "result.status"
filter_value = "failed"
metadata_fields = ["result.score"]
""")
    source = tmp_project / "evals.jsonl"
    source.write_text(
        '{"case":{"input":"alpha","step":"classify","expected":"A"},'
        '"result":{"actual":"B","explanation":"wrong class",'
        '"status":"failed","score":0}}\n'
        '{"case":{"input":"beta","step":"classify","expected":"B"},'
        '"result":{"actual":"B","explanation":"correct",'
        '"status":"passed","score":1}}\n'
    )

    corrections, skipped = import_eval_failures(
        load_config(tmp_project / "protolab.toml"),
        source,
        adapter_name="eval_lab",
    )

    assert skipped == 0
    assert len(corrections) == 1
    assert corrections[0]["protocol_version"] == "v2.0"
    assert corrections[0]["subject"] == "alpha"
    assert corrections[0]["protocol_output"] == "B"
    assert corrections[0]["correct_output"] == "A"
    assert corrections[0]["reasoning"] == "wrong class"
    assert corrections[0]["metadata"] == {"score": 0}
