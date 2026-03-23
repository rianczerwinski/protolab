"""Promptfoo eval output adapter.

Handles Promptfoo's JSON output format (``promptfoooutput.json``).
Filters to failed assertions by default and maps test variables,
model output, and grading results to correction stubs.

Promptfoo result structure (v0.80+)::

    {
      "results": [
        {
          "success": false,
          "response": {"output": "model response text"},
          "vars": {"input": "test input", ...},
          "test": {
            "description": "test case name",
            "assert": [{"type": "equals", "value": "expected"}]
          },
          "gradingResult": {
            "pass": false,
            "reason": "why it failed",
            "score": 0.0
          },
          "provider": {"id": "openai:gpt-4o", ...}
        }
      ]
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from . import register
from .base import BaseAdapter, CorrectionStub, resolve_path

logger = logging.getLogger(__name__)


@register("promptfoo")
class PromptfooAdapter(BaseAdapter):
    """Parse Promptfoo JSON output into correction stubs."""

    name = "promptfoo"
    formats = (".json",)

    def parse(self, path: Path) -> list[CorrectionStub]:
        with path.open() as f:
            data = json.load(f)

        # Results can be at top level or nested under "results"
        results = data if isinstance(data, list) else data.get("results", [])
        if isinstance(results, dict):
            results = results.get("results", [])

        stubs: list[CorrectionStub] = []
        for result in results:
            if not isinstance(result, dict):
                continue

            # Skip passing tests
            if result.get("success", True):
                continue

            subject = self._extract_subject(result)
            protocol_output = self._extract_output(result)
            step = self._extract_step(result)
            correct_output = self._extract_expected(result)
            reasoning = self._extract_reasoning(result)
            metadata = self._extract_metadata(result)

            if not subject or not protocol_output:
                logger.debug("Promptfoo result missing subject or output, skipping")
                continue

            stubs.append(
                CorrectionStub(
                    subject=str(subject),
                    step=step or "unspecified",
                    protocol_output=str(protocol_output),
                    correct_output=str(correct_output) if correct_output else "TODO",
                    reasoning=str(reasoning) if reasoning else "TODO",
                    metadata=metadata,
                )
            )

        logger.debug(
            "Promptfoo adapter: %d failures extracted from %s",
            len(stubs),
            path,
        )
        return stubs

    @staticmethod
    def _extract_subject(result: dict[str, Any]) -> Any:
        """Extract test subject from vars or test description."""
        # Try vars.input first (most common pattern)
        vars_ = result.get("vars", {})
        if isinstance(vars_, dict):
            for key in ("input", "query", "prompt", "question"):
                if key in vars_:
                    return vars_[key]
            # Fall back to first var value
            if vars_:
                return next(iter(vars_.values()))
        # Fall back to test description
        return resolve_path(result, "test.description")

    @staticmethod
    def _extract_output(result: dict[str, Any]) -> Any:
        """Extract model output."""
        # response.output is the standard location
        output = resolve_path(result, "response.output")
        if output is not None:
            return output
        # Flat "output" field (older format)
        return result.get("output")

    @staticmethod
    def _extract_step(result: dict[str, Any]) -> str | None:
        """Extract decision point / test category."""
        # test.description is the closest analog
        desc = resolve_path(result, "test.description")
        if desc:
            return str(desc)
        # Fall back to test.metadata.step or vars.category
        step = resolve_path(result, "test.metadata.step")
        if step:
            return str(step)
        cat = resolve_path(result, "vars.category")
        return str(cat) if cat else None

    @staticmethod
    def _extract_expected(result: dict[str, Any]) -> Any:
        """Extract expected output from assertions."""
        assertions = resolve_path(result, "test.assert") or []
        for assertion in assertions:
            if isinstance(assertion, dict) and "value" in assertion:
                return assertion["value"]
        return None

    @staticmethod
    def _extract_reasoning(result: dict[str, Any]) -> Any:
        """Extract grading reason."""
        return resolve_path(result, "gradingResult.reason")

    @staticmethod
    def _extract_metadata(result: dict[str, Any]) -> dict[str, Any]:
        """Collect useful metadata from the result."""
        meta: dict[str, Any] = {}
        score = resolve_path(result, "gradingResult.score")
        if score is not None:
            meta["score"] = score
        provider = resolve_path(result, "provider.id")
        if provider:
            meta["provider"] = provider
        prompt_label = resolve_path(result, "prompt.label")
        if prompt_label:
            meta["prompt_label"] = prompt_label
        tokens = resolve_path(result, "response.tokenUsage")
        if tokens:
            meta["token_usage"] = tokens
        return meta
