"""Tests for protolab.config — configuration loading and validation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from protolab.config import load_config, load_protocol_text


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
    (tmp_project / "protolab.toml").write_text('[protocol]\npath = "nonexistent.md"\n')
    with pytest.raises(FileNotFoundError, match="Protocol file not found"):
        load_config(tmp_project / "protolab.toml")


def test_invalid_toml(tmp_project):
    """Malformed TOML — raises ValueError (TOMLDecodeError is a ValueError subclass)."""
    (tmp_project / "protolab.toml").write_text("this is not [valid toml\n")
    with pytest.raises(ValueError):
        load_config(tmp_project / "protolab.toml")


def test_path_traversal_rejected(tmp_project):
    """Protocol path escaping project root is rejected."""
    (tmp_project / "protolab.toml").write_text(
        '[protocol]\npath = "../../etc/passwd"\n'
    )
    with pytest.raises(ValueError, match="escapes the project root"):
        load_config(tmp_project / "protolab.toml")


# --- Multi-file protocol assembly ---


def test_load_protocol_text_single_file(tmp_project):
    """Single-file config: load_protocol_text returns content with no markers."""
    config = load_config(tmp_project / "protolab.toml")
    text = load_protocol_text(config)
    assert text == "# Test Protocol\n\nThis is a test.\n"
    assert "<!-- file:" not in text


def test_load_protocol_text_multi_file(tmp_project):
    """Multi-file config: sections joined with --- separators and file headers."""
    (tmp_project / "part1.md").write_text("Part one content.\n")
    (tmp_project / "part2.md").write_text("Part two content.\n")
    (tmp_project / "protolab.toml").write_text(
        '[protocol]\npath = "protocol.md"\npaths = ["part1.md", "part2.md"]\n'
    )
    config = load_config(tmp_project / "protolab.toml")
    text = load_protocol_text(config)
    assert "<!-- file: part1.md -->" in text
    assert "<!-- file: part2.md -->" in text
    assert "---" in text
    assert "Part one content." in text
    assert "Part two content." in text


def test_load_protocol_text_glob(tmp_project):
    """Glob patterns expand to matching files, sorted for determinism."""
    (tmp_project / "aa.md").write_text("AA content.\n")
    (tmp_project / "bb.md").write_text("BB content.\n")
    (tmp_project / "protolab.toml").write_text(
        '[protocol]\npath = "protocol.md"\npaths = ["[ab]*.md"]\n'
    )
    config = load_config(tmp_project / "protolab.toml")
    text = load_protocol_text(config)
    assert text.index("<!-- file: aa.md -->") < text.index("<!-- file: bb.md -->")
    assert "AA content." in text
    assert "BB content." in text


def test_load_protocol_text_backward_compat(tmp_project):
    """path-only config still works: load_protocol_text uses protocol_path."""
    config = load_config(tmp_project / "protolab.toml")
    assert config.protocol_paths == []
    text = load_protocol_text(config)
    assert "# Test Protocol" in text
