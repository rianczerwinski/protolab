"""Tests for adapter infrastructure — base utilities and registry."""

from __future__ import annotations

import pytest

from protolab.adapters import get_adapter, list_adapters
from protolab.adapters.base import CorrectionStub, read_file, resolve_path

# ---------------------------------------------------------------------------
# resolve_path
# ---------------------------------------------------------------------------


def test_resolve_path_flat():
    """Simple key lookup."""
    assert resolve_path({"a": 1}, "a") == 1


def test_resolve_path_nested():
    """Dot-separated nested traversal."""
    obj = {"a": {"b": {"c": 42}}}
    assert resolve_path(obj, "a.b.c") == 42


def test_resolve_path_list_index():
    """Numeric segment indexes into lists."""
    obj = {"items": [{"name": "first"}, {"name": "second"}]}
    assert resolve_path(obj, "items.1.name") == "second"


def test_resolve_path_missing_key():
    """Missing intermediate key returns None."""
    assert resolve_path({"a": 1}, "b.c") is None


def test_resolve_path_missing_index():
    """Out-of-range list index returns None."""
    assert resolve_path({"items": [1]}, "items.5") is None


def test_resolve_path_none_input():
    """None input returns None."""
    assert resolve_path(None, "a") is None


def test_resolve_path_empty_dict():
    """Empty dict, any path returns None."""
    assert resolve_path({}, "a.b") is None


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------


def test_read_jsonl(tmp_path):
    """JSONL with 3 lines."""
    f = tmp_path / "data.jsonl"
    f.write_text('{"a": 1}\n{"a": 2}\n{"a": 3}\n')
    rows = read_file(f)
    assert len(rows) == 3
    assert rows[0]["a"] == 1


def test_read_csv(tmp_path):
    """CSV with header row."""
    f = tmp_path / "data.csv"
    f.write_text("name,value\nalpha,1\nbeta,2\n")
    rows = read_file(f)
    assert len(rows) == 2
    assert rows[0]["name"] == "alpha"


def test_read_json_array(tmp_path):
    """JSON top-level array."""
    f = tmp_path / "data.json"
    f.write_text('[{"a": 1}, {"a": 2}]')
    rows = read_file(f)
    assert len(rows) == 2


def test_read_json_nested_results(tmp_path):
    """JSON with results nested under 'results' key."""
    f = tmp_path / "data.json"
    f.write_text('{"results": [{"a": 1}], "meta": "ignored"}')
    rows = read_file(f)
    assert len(rows) == 1
    assert rows[0]["a"] == 1


def test_read_unsupported_format(tmp_path):
    """Unsupported extension raises ValueError."""
    f = tmp_path / "data.xml"
    f.write_text("<data/>")
    with pytest.raises(ValueError, match="Unsupported"):
        read_file(f)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_list_adapters_includes_builtins():
    """Built-in adapters are registered."""
    adapters = list_adapters()
    assert "promptfoo" in adapters
    assert "braintrust" in adapters


def test_get_adapter_builtin():
    """get_adapter resolves built-in by name."""
    adapter = get_adapter("promptfoo")
    assert adapter.name == "promptfoo"


def test_get_adapter_unknown_raises():
    """Unknown adapter name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown adapter"):
        get_adapter("nonexistent_adapter_xyz")


def test_get_adapter_custom_schema(tmp_project, sample_config):
    """Custom import schema in config is resolvable."""
    from protolab.config import ImportSchema

    sample_config.import_schemas["my_eval"] = ImportSchema(
        format="jsonl",
        subject="input",
        protocol_output="output",
        step="category",
    )
    adapter = get_adapter("my_eval", sample_config)
    assert adapter.name == "generic"


# ---------------------------------------------------------------------------
# CorrectionStub
# ---------------------------------------------------------------------------


def test_correction_stub_defaults():
    """CorrectionStub has TODO defaults for optional fields."""
    stub = CorrectionStub(subject="x", step="y", protocol_output="z")
    assert stub.correct_output == "TODO"
    assert stub.reasoning == "TODO"
    assert stub.metadata == {}
