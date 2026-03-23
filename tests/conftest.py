"""Shared test fixtures for protolab."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from protolab.config import Config, load_config


RESYNTHESIS_TEMPLATE = """\
# Protocol Resynthesis

You are rewriting a protocol document.

## Current Protocol ({{ version }})

{{ protocol_content }}

## Corrections ({{ corrections | length }} total)

{% for c in corrections %}
### {{ c.id }}
{% endfor %}

## Rules ({{ rules | length }} total)

{% for r in rules %}
- [{{ r.decision_point }}] {{ r.rule }}
{% endfor %}

## Analysis

{{ analysis_summary }}
"""


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temp directory with minimal protolab.toml, empty protocol.md,
    empty correction/rule files. Returns the project root path."""
    # Config
    (tmp_path / "protolab.toml").write_text(
        '[protocol]\npath = "protocol.md"\n'
    )
    # Protocol file
    (tmp_path / "protocol.md").write_text("# Test Protocol\n\nThis is a test.\n")
    # Correction and rule files
    corrections_dir = tmp_path / "corrections"
    corrections_dir.mkdir()
    (corrections_dir / "correction-log.toml").write_text("# Protolab correction log\n")
    (corrections_dir / "rules.toml").write_text("# Protolab rules\n")
    # Template
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "resynthesis-prompt.md").write_text(RESYNTHESIS_TEMPLATE)
    return tmp_path


@pytest.fixture
def sample_corrections() -> list[dict]:
    """Return list of 10 correction dicts covering 3 different steps.

    Distribution: 5 classification, 3 severity_assessment, 2 differential.
    Dates span days 1-10. Rules added on day 3, so corrections on days 4+
    with matching step are 'preventable'.
    """
    base = datetime(2026, 3, 20, tzinfo=timezone.utc)

    def dt(day: int) -> datetime:
        return base.replace(day=base.day + day)

    return [
        # Classification: 5 corrections (days 1, 2, 4, 6, 8)
        {
            "id": "corr_001", "subject": "case_alpha", "date": dt(1),
            "protocol_version": "v1.0", "step": "classification",
            "protocol_output": "Type 4w5", "correct_output": "Type 5w4",
            "reasoning": "Withdrawal serves curiosity, not identity.",
            "rule": "When withdrawal serves curiosity, classify as 5 not 4.",
        },
        {
            "id": "corr_002", "subject": "case_beta", "date": dt(2),
            "protocol_version": "v1.0", "step": "classification",
            "protocol_output": "Type 9w1", "correct_output": "Type 6w5",
            "reasoning": "Apparent passivity is conflict avoidance from anxiety.",
        },
        {
            "id": "corr_003", "subject": "case_gamma", "date": dt(4),
            "protocol_version": "v1.0", "step": "classification",
            "protocol_output": "Type 3w2", "correct_output": "Type 7w6",
            "reasoning": "Achievement focus masks avoidance of pain.",
        },
        {
            "id": "corr_004", "subject": "case_delta", "date": dt(6),
            "protocol_version": "v1.0", "step": "classification",
            "protocol_output": "Type 1w9", "correct_output": "Type 6w5",
            "reasoning": "Rigidity is security-seeking, not perfection-seeking.",
        },
        {
            "id": "corr_005", "subject": "case_epsilon", "date": dt(8),
            "protocol_version": "v1.0", "step": "classification",
            "protocol_output": "Type 2w3", "correct_output": "Type 9w1",
            "reasoning": "Helpfulness is merging, not pride-driven.",
        },
        # Severity assessment: 3 corrections (days 2, 5, 7)
        {
            "id": "corr_006", "subject": "case_zeta", "date": dt(2),
            "protocol_version": "v1.0", "step": "severity_assessment",
            "protocol_output": "moderate", "correct_output": "high",
            "reasoning": "Compounding factors were missed.",
        },
        {
            "id": "corr_007", "subject": "case_eta", "date": dt(5),
            "protocol_version": "v1.0", "step": "severity_assessment",
            "protocol_output": "low", "correct_output": "moderate",
            "reasoning": "Subclinical pattern underestimated.",
        },
        {
            "id": "corr_008", "subject": "case_theta", "date": dt(7),
            "protocol_version": "v1.0", "step": "severity_assessment",
            "protocol_output": "moderate", "correct_output": "high",
            "reasoning": "Duration of pattern not weighted.",
        },
        # Differential: 2 corrections (days 3, 9)
        {
            "id": "corr_009", "subject": "case_iota", "date": dt(3),
            "protocol_version": "v1.0", "step": "differential",
            "protocol_output": "primary: anxiety", "correct_output": "primary: depression",
            "reasoning": "Anxiety is secondary to anhedonia.",
        },
        {
            "id": "corr_010", "subject": "case_kappa", "date": dt(9),
            "protocol_version": "v1.0", "step": "differential",
            "protocol_output": "primary: ADHD", "correct_output": "primary: trauma",
            "reasoning": "Attention deficit is trauma-driven hypervigilance.",
        },
    ]


@pytest.fixture
def sample_rules() -> list[dict]:
    """Return list of 3 rules at different confidence levels
    (provisional, strong_pattern, structural). All added on day 3."""
    day3 = datetime(2026, 3, 23, tzinfo=timezone.utc)
    return [
        {
            "id": "rule_001",
            "decision_point": "classification",
            "rule": "When withdrawal serves curiosity/competence, classify as 5 not 4.",
            "confidence": "provisional",
            "source": "corr_001",
            "date_added": day3,
        },
        {
            "id": "rule_002",
            "decision_point": "severity_assessment",
            "rule": "When multiple moderate factors co-occur, escalate to high.",
            "confidence": "strong_pattern",
            "source": "corr_006",
            "date_added": day3,
        },
        {
            "id": "rule_003",
            "decision_point": "differential",
            "rule": "Always assess for masked depression before diagnosing anxiety-primary.",
            "confidence": "structural",
            "source": "corr_009",
            "date_added": day3,
        },
    ]


@pytest.fixture
def sample_config(tmp_project: Path) -> Config:
    """Return Config object pointed at tmp_project."""
    return load_config(tmp_project / "protolab.toml")


@pytest.fixture
def api_client(tmp_project: Path):
    """Return a FastAPI TestClient pointed at a tmp_project."""
    fastapi = pytest.importorskip("fastapi")
    from protolab.serve import create_app
    from starlette.testclient import TestClient

    app = create_app(tmp_project / "protolab.toml")
    return TestClient(app)
