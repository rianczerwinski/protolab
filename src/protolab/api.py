"""Public Python API for protolab.

Provides a ``Project`` class for programmatic access to all protolab
operations — correction management, analysis, trigger checking, and
resynthesis — without routing through the CLI or HTTP server.

Usage::

    from protolab import Project

    project = Project("./protolab.toml")
    project.ingest("evals.jsonl", adapter="braintrust")
    analysis = project.analyze()
    if any(t.met for t in project.check()):
        prompt = project.assemble_prompt()
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyze import AnalysisResult, analyze_corrections
from .check import TriggerResult, evaluate_triggers
from .config import load_config, load_protocol_text
from .correct import extract_rule
from .import_cmd import import_eval_failures
from .resynthesis import assemble_prompt, run_resynthesis
from .store import (
    load_corrections,
    load_rules,
    next_id,
    save_corrections,
    save_rules,
)
from .types import Correction, Rule


class Project:
    """Programmatic interface to a protolab project.

    All operations read/write the same TOML files as the CLI.
    """

    def __init__(self, config_path: Path | str | None = None) -> None:
        if config_path is not None:
            config_path = Path(config_path)
        self.config = load_config(config_path)

    # --- Read ---

    def corrections(self) -> list[Correction]:
        """Load all corrections from the correction log."""
        return load_corrections(self.config)

    def rules(self) -> list[Rule]:
        """Load all rules from the rules file."""
        return load_rules(self.config)

    # --- Ingest ---

    def ingest(
        self,
        path: Path | str,
        adapter: str = "auto",
        **field_overrides: str,
    ) -> tuple[list[Correction], int]:
        """Import eval failures from a file using the named adapter.

        Returns ``(corrections, skipped)``. Corrections are persisted
        immediately — no separate save step needed.
        """
        stubs, skipped = import_eval_failures(
            self.config,
            Path(path),
            adapter_name=adapter,
            subject_field=field_overrides.get("subject_field", "subject"),
            output_field=field_overrides.get("output_field", "output"),
            step_field=field_overrides.get("step_field", "step"),
        )
        existing = load_corrections(self.config)
        existing.extend(stubs)
        save_corrections(self.config, existing)
        return stubs, skipped

    def add_correction(self, **fields: Any) -> Correction:
        """Create and persist a single correction.

        Required fields: ``subject``, ``step``, ``protocol_output``,
        ``correct_output``, ``reasoning``. Optional: ``rule``, ``metadata``.
        """
        existing = load_corrections(self.config)
        corr_id = next_id(existing, "corr")

        correction: dict[str, Any] = {
            "id": corr_id,
            "date": datetime.now(timezone.utc),
            "protocol_version": self.config.protocol_version,
            "subject": fields["subject"],
            "step": fields["step"],
            "protocol_output": fields["protocol_output"],
            "correct_output": fields["correct_output"],
            "reasoning": fields["reasoning"],
        }
        if "rule" in fields:
            correction["rule"] = fields["rule"]
        if "metadata" in fields:
            correction["metadata"] = fields["metadata"]

        existing.append(correction)  # type: ignore[arg-type]
        save_corrections(self.config, existing)

        # Extract rule if present
        rule = extract_rule(correction, self.config)  # type: ignore[arg-type]
        if rule is not None:
            existing_rules = load_rules(self.config)
            existing_rules.append(rule)
            save_rules(self.config, existing_rules)

        return correction  # type: ignore[return-value]

    # --- Analysis ---

    def analyze(self, group_by: str = "step") -> AnalysisResult:
        """Run cluster analysis on accumulated corrections.

        *group_by* defaults to ``"step"``. Use dot-path syntax for
        metadata fields, e.g. ``"metadata.model"``.
        """
        return analyze_corrections(self.corrections(), self.rules(), group_by=group_by)

    def check(self) -> list[TriggerResult]:
        """Evaluate all resynthesis triggers."""
        return evaluate_triggers(self.config, self.corrections(), self.rules())

    # --- Resynthesis ---

    def assemble_prompt(self) -> str:
        """Assemble the resynthesis prompt from corrections, rules, and analysis."""
        corrections = self.corrections()
        rules = self.rules()
        analysis = analyze_corrections(corrections, rules)
        protocol_content = load_protocol_text(self.config)
        return assemble_prompt(
            self.config, protocol_content, corrections, rules, analysis
        )

    def run_resynthesis(self) -> str:
        """Assemble the prompt and send to the configured LLM.

        Returns the LLM's response text. Raises ``RuntimeError`` if the
        API key is not set, ``ImportError`` if the provider package is
        missing.
        """
        prompt = self.assemble_prompt()
        return run_resynthesis(self.config, prompt)

    # --- Export ---

    def export(self, fmt: str = "raw", path: Path | str | None = None) -> str | None:
        """Export the current protocol in a framework-friendly format.

        Returns the formatted text for ``"promptfoo"`` format, or writes
        to *path* for ``"raw"`` format and returns ``None``.
        """
        from .adapters.export import export_promptfoo, export_raw

        protocol_text = load_protocol_text(self.config)
        if fmt == "promptfoo":
            return export_promptfoo(self.config, protocol_text)
        out_path = Path(path) if path else self.config.root / "deploy" / "protocol.md"
        export_raw(self.config, protocol_text, out_path)
        return None
