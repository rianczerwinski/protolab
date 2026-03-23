"""Braintrust experiment export adapter.

Handles Braintrust's JSONL export format. Each line represents one
experiment result with input, output, expected, scores, and metadata.

Braintrust row structure::

    {
      "id": "...",
      "input": "test input" | {"query": "...", ...},
      "output": "model output" | {"result": "...", ...},
      "expected": "expected output" | {"answer": "...", ...},
      "scores": {"accuracy": 0.0, "relevance": 0.5, ...},
      "metadata": {"model": "gpt-4o", "experiment": "v2", ...}
    }
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from . import register
from .base import BaseAdapter, CorrectionStub, read_file

logger = logging.getLogger(__name__)


@register("braintrust")
class BraintrustAdapter(BaseAdapter):
    """Parse Braintrust JSONL exports into correction stubs."""

    name = "braintrust"
    formats = (".jsonl", ".json")

    def parse(self, path: Path) -> list[CorrectionStub]:
        rows = read_file(path)
        stubs: list[CorrectionStub] = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            # Filter to failures: any score < 1.0 (or no scores = include)
            scores = row.get("scores", {})
            if (
                isinstance(scores, dict)
                and scores
                and all(
                    v >= 1.0 for v in scores.values() if isinstance(v, (int, float))
                )
            ):
                continue

            subject = self._stringify(row.get("input", ""))
            output = self._stringify(row.get("output", ""))
            expected = self._stringify(row.get("expected"))
            step = self._extract_step(row)

            if not subject or not output:
                logger.debug("Braintrust row missing input or output, skipping")
                continue

            # Build metadata from scores + source metadata
            metadata: dict[str, Any] = {}
            if scores and isinstance(scores, dict):
                metadata["scores"] = scores
            source_meta = row.get("metadata", {})
            if isinstance(source_meta, dict):
                metadata.update(source_meta)
            row_id = row.get("id")
            if row_id:
                metadata["braintrust_id"] = row_id

            stubs.append(
                CorrectionStub(
                    subject=subject,
                    step=step or "unspecified",
                    protocol_output=output,
                    correct_output=expected if expected else "TODO",
                    reasoning="TODO",
                    metadata=metadata,
                )
            )

        logger.debug(
            "Braintrust adapter: %d failures extracted from %s", len(stubs), path
        )
        return stubs

    @staticmethod
    def _stringify(value: Any) -> str:
        """Convert a value to string, handling dicts and None."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            # Try common single-value keys first
            for key in ("text", "result", "answer", "query", "content"):
                if key in value:
                    return str(value[key])
            # Fall back to compact JSON
            import json

            return json.dumps(value, ensure_ascii=False)
        return str(value)

    @staticmethod
    def _extract_step(row: dict[str, Any]) -> str | None:
        """Extract decision point from metadata or tags."""
        meta = row.get("metadata", {})
        if isinstance(meta, dict):
            for key in ("step", "category", "test_suite", "experiment"):
                if key in meta:
                    return str(meta[key])
        tags = row.get("tags")
        if isinstance(tags, list) and tags:
            return str(tags[0])
        return None
