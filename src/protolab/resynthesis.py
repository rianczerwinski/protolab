"""protolab resynthesis — prompt assembly and LLM execution."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import jinja2
import tomli_w

from .analyze import AnalysisResult
from .config import Config
from . import llm


def assemble_prompt(
    config: Config,
    protocol_content: str,
    corrections: list[dict],
    rules: list[dict],
    analysis: AnalysisResult,
) -> str:
    """Render Jinja2 template with all data. Return prompt string."""
    template_path = config.root / config.prompt_template_path
    if not template_path.exists():
        raise FileNotFoundError(
            f"Resynthesis template not found at '{template_path}'. "
            f"Run `protolab init` to create one, or set "
            f"`resynthesis.prompt_template` in protolab.toml."
        )
    template_text = template_path.read_text()

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
    """Send prompt to LLM via llm.py. Return response text."""
    api_key = os.environ.get(config.llm_api_key_env)
    if not api_key:
        raise RuntimeError(
            f"API key not found. Set the {config.llm_api_key_env} "
            f"environment variable."
        )
    return llm.call_anthropic(config.llm_model, api_key, prompt)


def stage_resynthesis(config: Config, new_protocol: str) -> Path:
    """Write to staging path. Return path."""
    staging_dir = config.root / config.resynthesis_output_path.parent
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_path = staging_dir / "staged-protocol.md"
    staging_path.write_text(new_protocol)
    return staging_path


def promote_resynthesis(config: Config, staged_path: Path, new_version: str) -> None:
    """Archive current, move staged to active, update config, clear logs.

    Operation order is designed so that the protocol file (the most visible
    artifact) is the last thing changed — if the process is interrupted,
    the worst case is stale correction logs, not a missing protocol.
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


def _update_config_toml(config: Config, new_version: str) -> None:
    """Update protolab.toml with new version and resynthesis date."""
    import sys
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    config_path = config.root / "protolab.toml"
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    # Update version
    if "protocol" not in data:
        data["protocol"] = {}
    data["protocol"]["version"] = new_version

    # Update resynthesis date
    if "resynthesis" not in data:
        data["resynthesis"] = {}
    data["resynthesis"]["last_resynthesis_date"] = datetime.now(timezone.utc)

    config_path.write_text(tomli_w.dumps(data))
