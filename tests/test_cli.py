"""CLI integration tests via CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from protolab.cli import main


def _init_project(runner: CliRunner, tmp: Path) -> None:
    """Helper: create a minimal protolab project in tmp."""
    (tmp / "protocol.md").write_text("# Test Protocol\n")
    result = runner.invoke(main, ["init", "--bare"], catch_exceptions=False)
    assert result.exit_code == 0


def test_init_bare(tmp_path, monkeypatch):
    """init --bare creates protolab.toml, corrections/, templates/."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "protocol.md").write_text("# Test\n")
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--bare"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / "protolab.toml").exists()
    assert (tmp_path / "corrections" / "correction-log.toml").exists()
    assert (tmp_path / "corrections" / "rules.toml").exists()
    assert (tmp_path / "templates" / "resynthesis-prompt.md").exists()
    assert "Ready" in result.output


def test_correct_batch(tmp_path, monkeypatch):
    """correct --batch writes corrections to disk."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    batch = tmp_path / "batch.json"
    batch.write_text(
        json.dumps(
            [
                {
                    "subject": "x",
                    "step": "a",
                    "protocol_output": "b",
                    "correct_output": "c",
                    "reasoning": "d",
                },
            ]
        )
    )
    result = runner.invoke(
        main, ["correct", "--batch", str(batch)], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "1 correction" in result.output
    # Verify written to disk
    log = (tmp_path / "corrections" / "correction-log.toml").read_text()
    assert "corr_001" in log


def test_import_cmd(tmp_path, monkeypatch):
    """import adds stubs to correction log."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    jsonl = tmp_path / "evals.jsonl"
    jsonl.write_text('{"subject":"a","output":"b","step":"c"}\n')
    result = runner.invoke(
        main,
        ["import", str(jsonl)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "1 correction stub" in result.output


def test_check_no_triggers(tmp_path, monkeypatch):
    """check exits 0 when no triggers met."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    result = runner.invoke(main, ["check"])
    assert result.exit_code == 0


def test_check_triggers_met(tmp_path, monkeypatch):
    """check exits 1 when triggers are met."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    # Add enough corrections to trigger total_corrections (threshold=10)
    batch = tmp_path / "batch.json"
    corrections = [
        {
            "subject": f"s{i}",
            "step": "a",
            "protocol_output": "x",
            "correct_output": "y",
            "reasoning": "z",
        }
        for i in range(10)
    ]
    batch.write_text(json.dumps(corrections))
    runner.invoke(main, ["correct", "--batch", str(batch)], catch_exceptions=False)
    result = runner.invoke(main, ["check"])
    assert result.exit_code == 1
    assert "Resynthesis recommended" in result.output


def test_analyze_output(tmp_path, monkeypatch):
    """analyze shows cluster info."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    batch = tmp_path / "batch.json"
    batch.write_text(
        json.dumps(
            [
                {
                    "subject": "s1",
                    "step": "classification",
                    "protocol_output": "x",
                    "correct_output": "y",
                    "reasoning": "z",
                },
            ]
        )
    )
    runner.invoke(main, ["correct", "--batch", str(batch)], catch_exceptions=False)
    result = runner.invoke(main, ["analyze"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "classification" in result.output


def test_status_output(tmp_path, monkeypatch):
    """status shows protocol info."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    result = runner.invoke(main, ["status"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Protocol" in result.output


def test_resynthesis_prompt(tmp_path, monkeypatch):
    """resynthesis (without --run) writes prompt file."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    _init_project(runner, tmp_path)
    result = runner.invoke(main, ["resynthesis"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Resynthesis prompt written" in result.output
    assert (tmp_path / "resynthesis" / "output.md").exists()


def test_no_config_error(tmp_path, monkeypatch):
    """Commands fail with clear error when no protolab.toml exists."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert result.exit_code != 0
    assert "protolab init" in result.output
