"""protolab resynthesis — prompt assembly and LLM execution.

Handles the full resynthesis lifecycle: assembling the Jinja2 prompt,
sending it to an LLM, staging the result, and promoting it to the
active protocol (with archiving and config updates).
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import jinja2
import tomli_w

from .analyze import AnalysisResult
from .config import Config
from .types import Correction, Rule
from . import llm

logger = logging.getLogger(__name__)


def assemble_prompt(
    config: Config,
    protocol_content: str,
    corrections: list[Correction],
    rules: list[Rule],
    analysis: AnalysisResult,
) -> str:
    """Render the Jinja2 resynthesis template with all accumulated data.

    Raises ``FileNotFoundError`` if the configured template file is missing.
    """
    template_path = config.root / config.prompt_template_path
    if not template_path.exists():
        raise FileNotFoundError(
            f"Resynthesis template not found at '{template_path}'. "
            f"Run `protolab init` to create one, or set "
            f"`resynthesis.prompt_template` in protolab.toml."
        )
    template_text = template_path.read_text()
    logger.debug("Loaded template from %s", template_path)

    # Build analysis summary string
    lines = [
        f"Total corrections: {analysis.total_corrections}",
        f"Unique decision points: {analysis.unique_steps}",
    ]
    if analysis.clusters:
        top = analysis.clusters[0]
        lines.append(
            f"Top cluster: '{top.step}' with {top.count} corrections "
            f"({top.percentage:.0f}%)"
        )
        if top.preventable_count > 0:
            lines.append(
                f"  {top.preventable_count} occurred after rules were "
                f"established for this step"
            )
    lines.append(
        f"Concentration ratio: {analysis.concentration_ratio:.2f}"
    )
    analysis_summary = "\n".join(lines)

    env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        undefined=jinja2.StrictUndefined,
    )
    template = env.from_string(template_text)
    return template.render(
        version=config.protocol_version,
        protocol_content=protocol_content,
        corrections=corrections,
        rules=rules,
        analysis_summary=analysis_summary,
    )


def run_resynthesis(config: Config, prompt: str) -> str:
    """Send the assembled prompt to the configured LLM and return its response."""
    api_key = os.environ.get(config.llm_api_key_env)
    if not api_key:
        raise RuntimeError(
            f"API key not found. Set the {config.llm_api_key_env} "
            f"environment variable."
        )
    return llm.call_anthropic(config.llm_model, api_key, prompt)


def stage_resynthesis(config: Config, new_protocol: str) -> Path:
    """Write the LLM's output to a staging path (not the active protocol)."""
    staging_dir = config.root / config.resynthesis_output_path.parent
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_path = staging_dir / "staged-protocol.md"
    staging_path.write_text(new_protocol)
    logger.debug("Staged resynthesis at %s", staging_path)
    return staging_path


def promote_resynthesis(config: Config, staged_path: Path, new_version: str) -> None:
    """Promote a staged resynthesis to the active protocol.

    Operation order minimizes corruption risk if the process is
    interrupted: archive first, clear logs, then move the protocol
    file last (the visible "commit"). Config update is final.
    """
    archive_dir = config.root / config.archive_versions_path
    archive_dir.mkdir(parents=True, exist_ok=True)
    current_protocol = config.root / config.protocol_path
    corr_path = config.root / config.corrections_path
    rules_path = config.root / config.rules_path

    # 1. Archive current protocol
    shutil.copy2(current_protocol, archive_dir / f"{config.protocol_version}.md")

    # 2. Archive corrections and rules
    if corr_path.exists():
        shutil.copy2(
            corr_path,
            archive_dir / f"corrections-{config.protocol_version}.toml",
        )
    if rules_path.exists():
        shutil.copy2(
            rules_path,
            archive_dir / f"rules-{config.protocol_version}.toml",
        )

    # 3. Reset data files to empty
    corr_path.write_text("# Protolab correction log\n")
    rules_path.write_text("# Protolab rules\n")

    # 4. Move staged to active (the "commit" — last visible change)
    shutil.move(str(staged_path), str(current_protocol))

    # 5. Update config file
    _update_config_toml(config, new_version)

    logger.info(
        "Promoted %s -> %s (archived to %s)",
        config.protocol_version, new_version, archive_dir,
    )


def _update_config_toml(config: Config, new_version: str) -> None:
    """Update protolab.toml with new version and resynthesis timestamp."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    config_path = config.root / "protolab.toml"
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    if "protocol" not in data:
        data["protocol"] = {}
    data["protocol"]["version"] = new_version

    if "resynthesis" not in data:
        data["resynthesis"] = {}
    data["resynthesis"]["last_resynthesis_date"] = datetime.now(timezone.utc)

    config_path.write_text(tomli_w.dumps(data))
