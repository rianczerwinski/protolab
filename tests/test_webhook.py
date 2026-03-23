"""Tests for bulk ingest and webhook endpoints."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")

from protolab.config import load_config  # noqa: E402
from protolab.store import load_corrections  # noqa: E402


def test_bulk_ingest(api_client, tmp_project):
    """POST /api/ingest accepts array of correction dicts."""
    res = api_client.post(
        "/api/ingest",
        json=[
            {
                "subject": "case_1",
                "step": "classification",
                "protocol_output": "Type 4",
                "correct_output": "Type 5",
                "reasoning": "Domain-exhaustion.",
            },
            {
                "subject": "case_2",
                "step": "severity",
                "protocol_output": "low",
                "correct_output": "high",
                "reasoning": "Compounding factors.",
            },
        ],
    )
    assert res.status_code == 201
    data = res.json()
    assert len(data) == 2
    assert data[0]["id"] == "corr_001"
    assert data[1]["id"] == "corr_002"

    # Verify persisted
    config = load_config(tmp_project / "protolab.toml")
    corrections = load_corrections(config)
    assert len(corrections) == 2


def test_bulk_ingest_with_metadata(api_client, tmp_project):
    """Bulk ingest preserves metadata."""
    res = api_client.post(
        "/api/ingest",
        json=[
            {
                "subject": "test",
                "step": "step",
                "protocol_output": "out",
                "metadata": {"model": "gpt-4o", "score": 0.5},
            },
        ],
    )
    assert res.status_code == 201
    data = res.json()
    assert data[0]["metadata"] == {"model": "gpt-4o", "score": 0.5}


def test_bulk_ingest_empty(api_client):
    """Empty array returns empty result."""
    res = api_client.post("/api/ingest", json=[])
    assert res.status_code == 201
    assert res.json() == []


def test_bulk_ingest_defaults(api_client, tmp_project):
    """Missing optional fields get defaults."""
    res = api_client.post(
        "/api/ingest",
        json=[{"subject": "test"}],
    )
    assert res.status_code == 201
    data = res.json()
    assert data[0]["correct_output"] == "TODO"
    assert data[0]["reasoning"] == "TODO"
    assert data[0]["step"] == "unspecified"


def test_webhook_unknown_adapter(api_client):
    """POST /api/ingest/{name} with unknown adapter returns 400."""
    res = api_client.post("/api/ingest/nonexistent_xyz")
    assert res.status_code == 400
    assert "Unknown adapter" in res.json()["detail"]


def test_webhook_known_adapter(api_client):
    """POST /api/ingest/{name} with known adapter returns info."""
    res = api_client.post("/api/ingest/promptfoo")
    assert res.status_code == 201
    data = res.json()
    assert data["adapter"] == "promptfoo"
    assert data["status"] == "adapter_available"
