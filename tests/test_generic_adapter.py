"""Tests for the generic (config-driven) adapter."""

from __future__ import annotations

import json

from protolab.adapters.generic import GenericAdapter
from protolab.config import ImportSchema


def _schema(**overrides) -> ImportSchema:
    """Create an ImportSchema with sensible defaults."""
    defaults = {
        "format": "jsonl",
        "subject": "input",
        "protocol_output": "output",
        "step": "category",
    }
    defaults.update(overrides)
    return ImportSchema(**defaults)


def test_flat_fields(tmp_path):
    """Simple flat field mapping."""
    f = tmp_path / "data.jsonl"
    f.write_text(
        json.dumps({"input": "hello", "output": "world", "category": "greet"}) + "\n"
    )

    adapter = GenericAdapter(_schema())
    stubs = adapter.parse(f)

    assert len(stubs) == 1
    assert stubs[0].subject == "hello"
    assert stubs[0].protocol_output == "world"
    assert stubs[0].step == "greet"
    assert stubs[0].correct_output == "TODO"
    assert stubs[0].reasoning == "TODO"


def test_dot_path_nested(tmp_path):
    """Dot-path traversal into nested objects."""
    row = {
        "test_case": {"input": "deep value", "output": "deep out"},
        "meta": {"category": "deep_cat"},
    }
    f = tmp_path / "data.jsonl"
    f.write_text(json.dumps(row) + "\n")

    schema = _schema(
        subject="test_case.input",
        protocol_output="test_case.output",
        step="meta.category",
    )
    stubs = GenericAdapter(schema).parse(f)

    assert len(stubs) == 1
    assert stubs[0].subject == "deep value"
    assert stubs[0].step == "deep_cat"


def test_filter(tmp_path):
    """filter_field + filter_value only includes matching rows."""
    lines = [
        json.dumps({"input": "a", "output": "b", "category": "c", "status": "passed"}),
        json.dumps({"input": "d", "output": "e", "category": "f", "status": "failed"}),
        json.dumps({"input": "g", "output": "h", "category": "i", "status": "failed"}),
    ]
    f = tmp_path / "data.jsonl"
    f.write_text("\n".join(lines) + "\n")

    schema = _schema(filter_field="status", filter_value="failed")
    stubs = GenericAdapter(schema).parse(f)

    assert len(stubs) == 2
    assert stubs[0].subject == "d"
    assert stubs[1].subject == "g"


def test_metadata_fields(tmp_path):
    """metadata_fields are collected from source rows."""
    row = {
        "input": "x",
        "output": "y",
        "category": "z",
        "model": "gpt-4o",
        "latency": 1200,
    }
    f = tmp_path / "data.jsonl"
    f.write_text(json.dumps(row) + "\n")

    schema = _schema(metadata_fields=["model", "latency"])
    stubs = GenericAdapter(schema).parse(f)

    assert stubs[0].metadata == {"model": "gpt-4o", "latency": 1200}


def test_nested_metadata_fields(tmp_path):
    """Metadata fields can use dot-paths."""
    row = {"input": "x", "output": "y", "category": "z", "info": {"model": "gpt-4o"}}
    f = tmp_path / "data.jsonl"
    f.write_text(json.dumps(row) + "\n")

    schema = _schema(metadata_fields=["info.model"])
    stubs = GenericAdapter(schema).parse(f)

    assert stubs[0].metadata == {"model": "gpt-4o"}


def test_missing_required_field_skips(tmp_path):
    """Rows missing required fields are skipped."""
    lines = [
        json.dumps({"input": "a", "output": "b", "category": "c"}),
        json.dumps({"input": "d"}),  # missing output and category
    ]
    f = tmp_path / "data.jsonl"
    f.write_text("\n".join(lines) + "\n")

    stubs = GenericAdapter(_schema()).parse(f)
    assert len(stubs) == 1


def test_correct_output_from_path(tmp_path):
    """correct_output and reasoning can be mapped from source fields."""
    row = {
        "input": "x",
        "output": "y",
        "category": "z",
        "gold": "correct_value",
        "explanation": "why it's correct",
    }
    f = tmp_path / "data.jsonl"
    f.write_text(json.dumps(row) + "\n")

    schema = _schema(correct_output="gold", reasoning="explanation")
    stubs = GenericAdapter(schema).parse(f)

    assert stubs[0].correct_output == "correct_value"
    assert stubs[0].reasoning == "why it's correct"


def test_csv_format(tmp_path):
    """Generic adapter works with CSV files."""
    f = tmp_path / "data.csv"
    f.write_text("input,output,category\nhello,world,greet\n")

    schema = _schema(format="csv")
    stubs = GenericAdapter(schema).parse(f)

    assert len(stubs) == 1
    assert stubs[0].subject == "hello"
