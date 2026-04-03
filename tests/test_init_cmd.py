"""Tests for protolab.init_cmd — project scaffolding."""

from __future__ import annotations

from pathlib import Path

from protolab.init_cmd import scaffold_project


def test_bare_creates_structure(tmp_path, monkeypatch):
    """Bare mode creates protolab.toml, corrections/, templates/."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "protocol.md").write_text("# Test\n")
    scaffold_project(bare=True)
    assert (tmp_path / "protolab.toml").exists()
    assert (tmp_path / "corrections" / "correction-log.toml").exists()
    assert (tmp_path / "corrections" / "rules.toml").exists()
    assert (tmp_path / "templates" / "resynthesis-prompt.md").exists()


def test_bare_no_protocol_check(tmp_path, monkeypatch):
    """Bare mode doesn't fail if protocol.md is missing."""
    monkeypatch.chdir(tmp_path)
    # protocol.md does NOT exist — init should still succeed
    scaffold_project(bare=True)
    assert (tmp_path / "protolab.toml").exists()


def test_existing_files_overwritten(tmp_path, monkeypatch):
    """Re-running init overwrites protolab.toml."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "protocol.md").write_text("# Test\n")
    (tmp_path / "protolab.toml").write_text("# old content\n")
    scaffold_project(bare=True)
    content = (tmp_path / "protolab.toml").read_text()
    assert "protocol.md" in content  # overwritten with new content
    assert "old content" not in content
