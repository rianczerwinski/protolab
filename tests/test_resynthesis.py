"""Tests for protolab.resynthesis — prompt assembly and staging."""

from __future__ import annotations

import sys

from protolab.analyze import analyze_corrections
from protolab.config import load_config
from protolab.resynthesis import assemble_prompt, promote_resynthesis, stage_resynthesis
from protolab.store import load_corrections, load_rules, save_corrections, save_rules


def test_template_renders(tmp_project, sample_config, sample_corrections, sample_rules):
    """Template + corrections + rules — output contains protocol content,
    all correction IDs, all rule texts."""
    protocol_content = (sample_config.root / sample_config.protocol_path).read_text()
    analysis = analyze_corrections(sample_corrections, sample_rules)
    result = assemble_prompt(
        sample_config, protocol_content, sample_corrections, sample_rules, analysis
    )
    # Protocol content present
    assert "Test Protocol" in result
    # All correction IDs present
    for corr in sample_corrections:
        assert corr["id"] in result
    # All rule texts present
    for rule in sample_rules:
        assert rule["rule"] in result


def test_rules_grouped(tmp_project, sample_config, sample_corrections, sample_rules):
    """Structural rules in structural section, provisional in provisional section."""
    # Use the full resynthesis template from examples for this test
    template_path = sample_config.root / sample_config.prompt_template_path
    template_path.write_text("""\
### Structural
{% for r in rules if r.confidence == "structural" %}
- STRUCT: {{ r.rule }}
{% endfor %}

### Provisional
{% for r in rules if r.confidence == "provisional" %}
- PROV: {{ r.rule }}
{% endfor %}

### Strong Pattern
{% for r in rules if r.confidence == "strong_pattern" %}
- STRONG: {{ r.rule }}
{% endfor %}
""")
    protocol_content = "test"
    analysis = analyze_corrections(sample_corrections, sample_rules)
    result = assemble_prompt(
        sample_config, protocol_content, sample_corrections, sample_rules, analysis
    )
    # Structural rule in structural section
    structural_rule = next(r for r in sample_rules if r["confidence"] == "structural")
    assert f"STRUCT: {structural_rule['rule']}" in result
    # Provisional rule in provisional section
    provisional_rule = next(r for r in sample_rules if r["confidence"] == "provisional")
    assert f"PROV: {provisional_rule['rule']}" in result
    # Strong pattern in strong section
    strong_rule = next(r for r in sample_rules if r["confidence"] == "strong_pattern")
    assert f"STRONG: {strong_rule['rule']}" in result


def test_analysis_included(tmp_project, sample_config, sample_corrections, sample_rules):
    """Analysis summary appears in rendered prompt."""
    protocol_content = "test"
    analysis = analyze_corrections(sample_corrections, sample_rules)
    result = assemble_prompt(
        sample_config, protocol_content, sample_corrections, sample_rules, analysis
    )
    assert "Total corrections: 10" in result
    assert "Unique decision points: 3" in result
    assert "Concentration ratio:" in result


def test_staging(tmp_project, sample_config):
    """Resynthesis writes to staging path, not active protocol path."""
    new_protocol = "# New Protocol\n\nBetter version.\n"
    staged = stage_resynthesis(sample_config, new_protocol)
    assert staged.exists()
    assert staged.name == "staged-protocol.md"
    assert staged.read_text() == new_protocol
    # Original protocol unchanged
    original = (sample_config.root / sample_config.protocol_path).read_text()
    assert "Test Protocol" in original


def test_promote_archives_protocol(tmp_project, sample_config, sample_corrections, sample_rules):
    """After promote, archive contains old version."""
    save_corrections(sample_config, sample_corrections)
    save_rules(sample_config, sample_rules)
    staged = stage_resynthesis(sample_config, "# New Protocol v1.1\n")
    promote_resynthesis(sample_config, staged, "v1.1")
    archive = sample_config.root / sample_config.archive_versions_path / "v1.0.md"
    assert archive.exists()
    assert "Test Protocol" in archive.read_text()


def test_promote_clears_logs(tmp_project, sample_config, sample_corrections, sample_rules):
    """Correction and rule files reset to empty after promote."""
    save_corrections(sample_config, sample_corrections)
    save_rules(sample_config, sample_rules)
    staged = stage_resynthesis(sample_config, "# New\n")
    promote_resynthesis(sample_config, staged, "v1.1")
    assert load_corrections(sample_config) == []
    assert load_rules(sample_config) == []


def test_promote_updates_config(tmp_project, sample_config, sample_corrections):
    """protolab.toml has new version and last_resynthesis_date after promote."""
    save_corrections(sample_config, sample_corrections)
    staged = stage_resynthesis(sample_config, "# New\n")
    promote_resynthesis(sample_config, staged, "v1.1")
    reloaded = load_config(sample_config.root / "protolab.toml")
    assert reloaded.protocol_version == "v1.1"
    assert reloaded.last_resynthesis_date is not None


def test_promote_version_collision(tmp_project, sample_config, sample_corrections):
    """Archive already has file — overwrites without error."""
    archive_dir = sample_config.root / sample_config.archive_versions_path
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "v1.0.md").write_text("# Old archive\n")
    save_corrections(sample_config, sample_corrections)
    staged = stage_resynthesis(sample_config, "# New\n")
    promote_resynthesis(sample_config, staged, "v1.1")
    assert "Test Protocol" in (archive_dir / "v1.0.md").read_text()
