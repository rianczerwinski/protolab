"""Tests for protolab serve — the HTTP API and dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from protolab.store import save_corrections, save_rules
from protolab.config import load_config


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


def test_get_status_empty(api_client):
    """Fresh project returns valid status JSON with zero counts."""
    res = api_client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["corrections"]["total"] == 0
    assert data["clusters"] == []
    assert data["rules"]["total"] == 0
    assert isinstance(data["triggers"], list)
    assert data["protocol"]["version"] == "v1.0"


def test_get_status_with_data(api_client, tmp_project, sample_corrections, sample_rules):
    """With corrections and rules, all fields are populated."""
    config = load_config(tmp_project / "protolab.toml")
    save_corrections(config, sample_corrections)
    save_rules(config, sample_rules)

    res = api_client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["corrections"]["total"] == 10
    assert len(data["clusters"]) == 3
    assert data["rules"]["total"] == 3
    assert data["rules"]["by_confidence"]["provisional"] == 1
    assert data["rules"]["by_confidence"]["structural"] == 1


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------


def test_list_corrections_empty(api_client):
    """Empty project returns empty corrections list."""
    res = api_client.get("/api/corrections")
    assert res.status_code == 200
    assert res.json() == []


def test_list_corrections_with_data(api_client, tmp_project, sample_corrections):
    """Returns all corrections."""
    config = load_config(tmp_project / "protolab.toml")
    save_corrections(config, sample_corrections)

    res = api_client.get("/api/corrections")
    assert res.status_code == 200
    assert len(res.json()) == 10


def test_list_corrections_filter_step(api_client, tmp_project, sample_corrections):
    """Filtering by step returns only matching corrections."""
    config = load_config(tmp_project / "protolab.toml")
    save_corrections(config, sample_corrections)

    res = api_client.get("/api/corrections?step=classification")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert all(c["step"] == "classification" for c in data)


def test_get_correction_by_id(api_client, tmp_project, sample_corrections):
    """GET /api/corrections/{id} returns the correction."""
    config = load_config(tmp_project / "protolab.toml")
    save_corrections(config, sample_corrections)

    res = api_client.get("/api/corrections/corr_001")
    assert res.status_code == 200
    assert res.json()["subject"] == "case_alpha"


def test_get_correction_not_found(api_client):
    """GET /api/corrections/{id} returns 404 for missing ID."""
    res = api_client.get("/api/corrections/corr_999")
    assert res.status_code == 404


def test_post_correction(api_client, tmp_project):
    """POST /api/corrections creates a correction with auto-assigned ID."""
    res = api_client.post("/api/corrections", json={
        "subject": "test_case",
        "step": "classification",
        "protocol_output": "Type 4",
        "correct_output": "Type 5",
        "reasoning": "Domain-exhaustion, not trust-failure.",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == "corr_001"
    assert data["subject"] == "test_case"
    assert data["protocol_version"] == "v1.0"

    # Verify persisted
    res2 = api_client.get("/api/corrections")
    assert len(res2.json()) == 1


def test_post_correction_with_rule(api_client, tmp_project):
    """POST with rule field extracts and persists the rule."""
    res = api_client.post("/api/corrections", json={
        "subject": "test_case",
        "step": "classification",
        "protocol_output": "Type 4",
        "correct_output": "Type 5",
        "reasoning": "Domain-exhaustion, not trust-failure.",
        "rule": "Serial disenchantment as domain-exhaustion points to 5.",
    })
    assert res.status_code == 201

    # Check rule was created
    config = load_config(tmp_project / "protolab.toml")
    from protolab.store import load_rules as _load_rules
    rules = _load_rules(config)
    assert len(rules) == 1
    assert rules[0]["rule"] == "Serial disenchantment as domain-exhaustion points to 5."


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------


def test_get_triggers(api_client):
    """GET /api/triggers returns list of trigger results."""
    res = api_client.get("/api/triggers")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert all("name" in t and "met" in t for t in data)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


def test_get_protocol_file(api_client):
    """GET /api/protocol returns file content for single-file protocol."""
    res = api_client.get("/api/protocol")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "file"
    assert "Test Protocol" in data["content"]


def test_get_protocol_directory(api_client, tmp_project):
    """GET /api/protocol returns module list for directory protocol."""
    # Convert to directory-based protocol
    proto_dir = tmp_project / "protocol-modules"
    proto_dir.mkdir()
    (proto_dir / "01-stage.md").write_text("# Stage 1\n")
    (proto_dir / "02-stage.md").write_text("# Stage 2\n")

    # Update config to point at directory
    (tmp_project / "protolab.toml").write_text(
        '[protocol]\npath = "protocol-modules"\n'
    )

    res = api_client.get("/api/protocol")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "directory"
    assert len(data["modules"]) == 2
    assert data["modules"][0]["name"] == "01-stage.md"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_patch_config(api_client, tmp_project):
    """PATCH /api/config updates trigger thresholds in protolab.toml."""
    res = api_client.patch("/api/config", json={
        "total_corrections": 20,
        "cluster_threshold": 0.5,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_corrections"] == 20
    assert data["cluster_threshold"] == 0.5

    # Verify persisted
    config = load_config(tmp_project / "protolab.toml")
    assert config.triggers.total_corrections == 20
    assert config.triggers.cluster_threshold == 0.5


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


def test_dashboard_html(api_client):
    """GET / returns HTML with expected elements."""
    res = api_client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "protolab" in res.text.lower()
    assert "corrections" in res.text.lower()


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


def test_cors_headers(api_client):
    """CORS headers are present on responses."""
    res = api_client.get(
        "/api/status",
        headers={"Origin": "http://localhost:9000"},
    )
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers
