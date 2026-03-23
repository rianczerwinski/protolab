"""Tests for protolab.store — TOML read/write for corrections and rules."""

from __future__ import annotations

from datetime import datetime

from protolab.store import (
    load_corrections,
    load_toml,
    next_id,
    save_corrections,
    save_toml,
)


def test_roundtrip(sample_config, sample_corrections):
    """Write corrections then load them back — data is identical."""
    save_corrections(sample_config, sample_corrections)
    loaded = load_corrections(sample_config)
    assert len(loaded) == len(sample_corrections)
    for orig, loaded_item in zip(sample_corrections, loaded, strict=True):
        assert orig["id"] == loaded_item["id"]
        assert orig["subject"] == loaded_item["subject"]
        assert orig["step"] == loaded_item["step"]
        assert orig["reasoning"] == loaded_item["reasoning"]
        assert orig["protocol_output"] == loaded_item["protocol_output"]
        assert orig["correct_output"] == loaded_item["correct_output"]
        assert orig["protocol_version"] == loaded_item["protocol_version"]
        assert isinstance(loaded_item["date"], datetime)


def test_empty_file(sample_config):
    """Load from file with no [[corrections]] array — returns empty list."""
    result = load_corrections(sample_config)
    assert result == []


def test_empty_file_comment_only(tmp_project):
    """Load from file with only comments — returns empty list."""
    comment_file = tmp_project / "comment_only.toml"
    comment_file.write_text("# This is just a comment\n# Another comment\n")
    data = load_toml(comment_file)
    assert data == {}


def test_next_id():
    """Given [corr_001, corr_003] returns corr_004."""
    existing = [{"id": "corr_001"}, {"id": "corr_003"}]
    assert next_id(existing, "corr") == "corr_004"


def test_next_id_empty():
    """Given [] returns corr_001."""
    assert next_id([], "corr") == "corr_001"


def test_save_creates_dirs(tmp_path):
    """Save to nested/path/file.toml — creates directories."""
    nested = tmp_path / "a" / "b" / "file.toml"
    save_toml(nested, {"key": "value"})
    assert nested.exists()
    data = load_toml(nested)
    assert data["key"] == "value"


def test_datetime_roundtrip(sample_config, sample_corrections):
    """Datetime objects survive write/read cycle as native TOML datetimes."""
    save_corrections(sample_config, sample_corrections[:1])
    loaded = load_corrections(sample_config)
    assert len(loaded) == 1
    assert isinstance(loaded[0]["date"], datetime)
    assert loaded[0]["date"] == sample_corrections[0]["date"]


def test_malformed_toml_raises(tmp_path):
    """Non-empty file with invalid TOML raises ValueError."""
    bad_file = tmp_path / "bad.toml"
    bad_file.write_text("this is not [valid toml\n")
    import pytest

    with pytest.raises(ValueError, match="Failed to parse TOML"):
        load_toml(bad_file)


def test_next_id_with_non_numeric():
    """IDs with non-numeric suffixes are skipped; no collision."""
    existing = [
        {"id": "corr_001"},
        {"id": "corr_abc"},  # non-numeric
        {"id": "corr_002"},
    ]
    assert next_id(existing, "corr") == "corr_003"
