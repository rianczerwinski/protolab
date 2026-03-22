"""Load and validate protolab.toml configuration.

The Config dataclass carries all project settings. All paths are stored
relative to the project root (the directory containing protolab.toml);
the ``root`` field provides the anchor for resolution.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILENAME = "protolab.toml"
DEFAULT_LLM_MODEL = "claude-sonnet-4-20250514"


@dataclass
class TriggerConfig:
    """Thresholds that determine when resynthesis is recommended."""

    total_corrections: int = 10
    cluster_threshold: float = 0.30
    preventable_errors: int = 3
    max_days_since_resynthesis: int | None = 30


@dataclass
class Config:
    """Protolab project configuration loaded from protolab.toml.

    ``root`` is derived at load time — it is never stored in the TOML file.
    All Path fields are relative to ``root``.
    """

    root: Path
    protocol_path: Path
    protocol_version: str = "v1.0"
    steps: list[str] = field(default_factory=list)
    corrections_path: Path = Path("corrections/correction-log.toml")
    rules_path: Path = Path("corrections/rules.toml")
    triggers: TriggerConfig = field(default_factory=TriggerConfig)
    prompt_template_path: Path = Path("templates/resynthesis-prompt.md")
    resynthesis_output_path: Path = Path("resynthesis/output.md")
    last_resynthesis_date: datetime | None = None
    archive_versions_path: Path = Path("protocol/versions/")
    llm_provider: str = "anthropic"
    llm_model: str = DEFAULT_LLM_MODEL
    llm_api_key_env: str = "ANTHROPIC_API_KEY"


def load_config(path: Path | None = None) -> Config:
    """Load project configuration from a TOML file.

    If *path* is ``None``, searches the current directory for
    ``protolab.toml``. Applies dataclass defaults for any missing fields.

    Validates that the protocol file exists and that all configured paths
    stay within the project root (path traversal guard).
    """
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    if path is None:
        path = Path.cwd() / CONFIG_FILENAME
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at '{path}'. "
            "Run `protolab init` to create one."
        )

    with open(path, "rb") as f:
        data = tomllib.load(f)

    root = path.parent
    logger.debug("Loading config from %s (root: %s)", path, root)

    # Protocol section
    proto = data.get("protocol", {})
    protocol_path = Path(proto.get("path", "protocol.md"))
    protocol_version = proto.get("version", "v1.0")
    steps = proto.get("steps", [])

    # Path traversal guard — all configured paths must resolve inside root.
    # Without this, a malicious protolab.toml could read arbitrary files
    # (e.g. protocol.path = "../../etc/passwd").
    resolved_protocol = (root / protocol_path).resolve()
    if not resolved_protocol.is_relative_to(root.resolve()):
        raise ValueError(
            f"Protocol path '{protocol_path}' escapes the project root. "
            f"Paths must stay within the directory containing {CONFIG_FILENAME}."
        )
    if not resolved_protocol.exists():
        raise FileNotFoundError(
            f"Protocol file not found at '{resolved_protocol}'. "
            f"Create it or update `protocol.path` in '{path}'."
        )

    # Corrections section
    corr = data.get("corrections", {})
    corrections_path = Path(corr.get("path", "corrections/correction-log.toml"))
    rules_path = Path(corr.get("rules_path", "corrections/rules.toml"))

    # Resynthesis section
    resynth = data.get("resynthesis", {})
    prompt_template_path = Path(
        resynth.get("prompt_template", "templates/resynthesis-prompt.md")
    )
    resynthesis_output_path = Path(resynth.get("output_path", "resynthesis/output.md"))
    last_resynthesis_date = resynth.get("last_resynthesis_date", None)

    # Triggers subsection
    trig = resynth.get("triggers", {})
    triggers = TriggerConfig(
        total_corrections=trig.get("total_corrections", 10),
        cluster_threshold=trig.get("cluster_threshold", 0.30),
        preventable_errors=trig.get("preventable_errors", 3),
        max_days_since_resynthesis=trig.get("max_days_since_resynthesis", 30),
    )

    # Archive section
    archive = data.get("archive", {})
    archive_versions_path = Path(archive.get("versions_path", "protocol/versions/"))

    # LLM section
    llm = data.get("llm", {})
    llm_provider = llm.get("provider", "anthropic")
    llm_model = llm.get("model", DEFAULT_LLM_MODEL)
    llm_api_key_env = llm.get("api_key_env", "ANTHROPIC_API_KEY")

    logger.debug("Protocol: %s (version %s)", protocol_path, protocol_version)

    return Config(
        root=root,
        protocol_path=protocol_path,
        protocol_version=protocol_version,
        steps=steps,
        corrections_path=corrections_path,
        rules_path=rules_path,
        triggers=triggers,
        prompt_template_path=prompt_template_path,
        resynthesis_output_path=resynthesis_output_path,
        last_resynthesis_date=last_resynthesis_date,
        archive_versions_path=archive_versions_path,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key_env=llm_api_key_env,
    )
