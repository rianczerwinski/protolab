"""Tests for protolab.status — dashboard rendering."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from protolab.status import render_status
from protolab.store import save_corrections, save_rules


def test_smoke_empty(sample_config):
    """Render status with no corrections — doesn't crash."""
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    render_status(sample_config, console=console)
    text = output.getvalue()
    assert "Protocol" in text
    assert "Corrections" in text
    assert "never" in text


def test_smoke_with_data(sample_config, sample_corrections, sample_rules):
    """Render status with corrections and rules — includes expected sections."""
    save_corrections(sample_config, sample_corrections)
    save_rules(sample_config, sample_rules)
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    render_status(sample_config, console=console)
    text = output.getvalue()
    assert "classification" in text
    assert "Triggers" in text
