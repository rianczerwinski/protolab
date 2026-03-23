"""Tests for export adapters."""

from __future__ import annotations

from protolab.adapters.export import export_promptfoo, export_raw
from protolab.config import load_config


def test_export_raw(tmp_project):
    """export_raw writes protocol with metadata header."""
    config = load_config(tmp_project / "protolab.toml")
    out_path = tmp_project / "deploy" / "protocol.md"

    export_raw(config, "# My Protocol\n\nContent here.\n", out_path)

    assert out_path.exists()
    text = out_path.read_text()
    assert "<!-- protolab v" in text
    assert "# My Protocol" in text


def test_export_raw_creates_dirs(tmp_project):
    """export_raw creates parent directories."""
    config = load_config(tmp_project / "protolab.toml")
    out_path = tmp_project / "deep" / "nested" / "protocol.md"

    export_raw(config, "content", out_path)
    assert out_path.exists()


def test_export_promptfoo(tmp_project):
    """export_promptfoo generates valid YAML-like output."""
    config = load_config(tmp_project / "protolab.toml")
    result = export_promptfoo(config, "You are a classifier.\nClassify inputs.")

    assert "prompts:" in result
    assert "protolab-protocol" in result
    assert "You are a classifier." in result
    assert "raw: |" in result


def test_export_via_api(tmp_project):
    """Project.export() works for both formats."""
    from protolab.api import Project

    project = Project(tmp_project / "protolab.toml")

    # Promptfoo returns string
    result = project.export(fmt="promptfoo")
    assert result is not None
    assert "prompts:" in result

    # Raw writes to file
    out_path = tmp_project / "exported.md"
    result = project.export(fmt="raw", path=out_path)
    assert result is None
    assert out_path.exists()
