"""Tests for protolab.config — configuration loading and validation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from protolab.config import Config, TriggerConfig, load_config, load_protocol_text


def test_defaults(tmp_project):
    """Minimal config (just protocol path) — all other fields populated with defaults."""
    config = load_config(tmp_project / "protolab.toml")
    assert config.root == tmp_project
    assert config.protocol_path == Path("protocol.md")
    assert config.protocol_version == "v1.0"
    assert config.steps == []
    assert config.corrections_path == Path("corrections/correction-log.toml")
    assert config.rules_path == Path("corrections/rules.toml")
    assert config.triggers.total_corrections == 10
    assert config.triggers.cluster_threshold == 0.30
    assert config.triggers.preventable_errors == 3
    assert config.triggers.max_days_since_resynthesis == 30
    assert config.last_resynthesis_date is None
    assert config.llm_provider == "anthropic"
    assert config.llm_model == "claude-sonnet-4-20250514"
    assert config.import_schemas == {}


def test_full_config(tmp_project):
    """All fields specified — all loaded correctly."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"
version = "v2.1"
steps = ["classification", "severity"]

[corrections]
path = "data/corrections.toml"
rules_path = "data/rules.toml"

[resynthesis]
prompt_template = "my-template.md"
output_path = "out/resynthesis.md"
last_resynthesis_date = 2026-03-01T00:00:00Z

[resynthesis.triggers]
total_corrections = 5
cluster_threshold = 0.50
preventable_errors = 2
max_days_since_resynthesis = 14

[archive]
versions_path = "archive/versions/"

[llm]
provider = "anthropic"
model = "claude-opus-4-20250514"
api_key_env = "MY_KEY"
""")
    config = load_config(tmp_project / "protolab.toml")
    assert config.protocol_version == "v2.1"
    assert config.steps == ["classification", "severity"]
    assert config.corrections_path == Path("data/corrections.toml")
    assert config.rules_path == Path("data/rules.toml")
    assert config.triggers.total_corrections == 5
    assert config.triggers.cluster_threshold == 0.50
    assert config.triggers.preventable_errors == 2
    assert config.triggers.max_days_since_resynthesis == 14
    assert config.prompt_template_path == Path("my-template.md")
    assert config.resynthesis_output_path == Path("out/resynthesis.md")
    assert isinstance(config.last_resynthesis_date, datetime)
    assert config.archive_versions_path == Path("archive/versions/")
    assert config.llm_model == "claude-opus-4-20250514"
    assert config.llm_api_key_env == "MY_KEY"


def test_missing_protocol(tmp_project):
    """Protocol file doesn't exist — clear error."""
    (tmp_project / "protolab.toml").write_text(
        '[protocol]\npath = "nonexistent.md"\n'
    )
    with pytest.raises(FileNotFoundError, match="Protocol file not found"):
        load_config(tmp_project / "protolab.toml")


def test_invalid_toml(tmp_project):
    """Malformed TOML — clear error."""
    (tmp_project / "protolab.toml").write_text("this is not [valid toml\n")
    with pytest.raises(Exception):
        load_config(tmp_project / "protolab.toml")


def test_path_traversal_rejected(tmp_project):
    """Protocol path escaping project root is rejected."""
    (tmp_project / "protolab.toml").write_text(
        '[protocol]\npath = "../../etc/passwd"\n'
    )
    with pytest.raises(ValueError, match="escapes the project root"):
        load_config(tmp_project / "protolab.toml")


def test_custom_import_schema(tmp_project):
    """A complete custom schema is loaded as an executable contract."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"

[import.regression_suite]
format = "json"
subject = "case.input"
protocol_output = "result.output"
step = "case.category"
correct_output = "case.expected"
reasoning = "result.reason"
filter_field = "result.status"
filter_value = "failed"
metadata_fields = ["result.score", "model"]
""")

    schema = load_config(tmp_project / "protolab.toml").import_schemas[
        "regression_suite"
    ]
    assert schema.format == "json"
    assert schema.subject == "case.input"
    assert schema.correct_output == "case.expected"
    assert schema.filter_field == "result.status"
    assert schema.filter_value == "failed"
    assert schema.metadata_fields == ["result.score", "model"]


def test_import_schema_requires_all_structural_fields(tmp_project):
    """Malformed adapter declarations fail at the configuration boundary."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"

[import.incomplete]
subject = "input"
protocol_output = "output"
""")

    with pytest.raises(ValueError, match=r"\[import\.incomplete\]\.step"):
        load_config(tmp_project / "protolab.toml")


def test_import_schema_filter_is_a_complete_pair(tmp_project):
    """A filter cannot silently become inactive because half is missing."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"

[import.incomplete_filter]
subject = "input"
protocol_output = "output"
step = "step"
filter_field = "status"
""")

    with pytest.raises(ValueError, match="must be set together"):
        load_config(tmp_project / "protolab.toml")


def test_import_schema_rejects_unknown_format(tmp_project):
    """The configured source format must name a parser Protolab provides."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"

[import.xml_feed]
format = "xml"
subject = "input"
protocol_output = "output"
step = "step"
""")

    with pytest.raises(ValueError, match="jsonl, csv, json"):
        load_config(tmp_project / "protolab.toml")


def test_import_schema_rejects_reserved_name(tmp_project):
    """A custom schema cannot be declared under an unreachable built-in name."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"

[import.promptfoo]
subject = "input"
protocol_output = "output"
step = "step"
""")

    with pytest.raises(ValueError, match="reserved adapter name 'promptfoo'"):
        load_config(tmp_project / "protolab.toml")


def test_import_schema_rejects_unknown_fields(tmp_project):
    """Schema typos fail visibly instead of becoming decorative configuration."""
    (tmp_project / "protolab.toml").write_text("""\
[protocol]
path = "protocol.md"

[import.typo]
subject = "input"
protocol_output = "output"
step = "step"
filter = "status == 'failed'"
""")

    with pytest.raises(ValueError, match=r"unknown field\(s\): filter"):
        load_config(tmp_project / "protolab.toml")


def test_load_protocol_text_preserves_utf8(tmp_project):
    """The shared protocol loader returns exact UTF-8 source text."""
    expected = "# Prötocol\n\nDecide with care: λ.\n"
    (tmp_project / "protocol.md").write_text(expected, encoding="utf-8")

    config = load_config(tmp_project / "protolab.toml")

    assert load_protocol_text(config) == expected
