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

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

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
class ImportSchema:
    """A user-defined import adapter configuration.

    Dot-path fields (``subject``, ``protocol_output``, etc.) use ``"a.b.0.c"``
    syntax to traverse nested dicts and lists in source data. Literal strings
    that don't match any path resolve to themselves (e.g. ``"TODO"``).
    """

    format: str  # jsonl | csv | json
    subject: str  # dot-path into source row
    protocol_output: str  # dot-path
    step: str  # dot-path
    correct_output: str = "TODO"  # dot-path or literal default
    reasoning: str = "TODO"  # dot-path or literal default
    filter_field: str | None = None  # simple equality filter: field name
    filter_value: str | None = None  # simple equality filter: required value
    metadata_fields: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Protolab project configuration loaded from protolab.toml.

    ``root`` is derived at load time — it is never stored in the TOML file.
    All Path fields are relative to ``root``.
    """

    root: Path
    protocol_path: Path
    # glob patterns; takes precedence over protocol_path when non-empty
    protocol_paths: list[str] = field(default_factory=list)
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
    import_schemas: dict[str, ImportSchema] = field(default_factory=dict)


def load_config(path: Path | None = None) -> Config:
    """Load project configuration from a TOML file.

    If *path* is ``None``, searches the current directory for
    ``protolab.toml``. Applies dataclass defaults for any missing fields.

    Validates that the protocol file exists and that all configured paths
    stay within the project root (path traversal guard).
    """
    if path is None:
        path = Path.cwd() / CONFIG_FILENAME
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at '{path}'. Run `protolab init` to create one."
        )

    with path.open("rb") as f:
        data = tomllib.load(f)

    root = path.parent
    logger.debug("Loading config from %s (root: %s)", path, root)

    # Protocol section
    proto = data.get("protocol", {})
    protocol_path = Path(proto.get("path", "protocol.md"))
    protocol_version = proto.get("version", "v1.0")
    steps = proto.get("steps", [])
    protocol_paths = proto.get("paths", [])

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

    # Import schemas — user-defined adapters ([import.<name>] sections)
    import_schemas: dict[str, ImportSchema] = {}
    for name, schema_data in data.get("import", {}).items():
        if not isinstance(schema_data, dict):
            continue
        import_schemas[name] = ImportSchema(
            format=schema_data.get("format", "jsonl"),
            subject=schema_data["subject"],
            protocol_output=schema_data["protocol_output"],
            step=schema_data["step"],
            correct_output=schema_data.get("correct_output", "TODO"),
            reasoning=schema_data.get("reasoning", "TODO"),
            filter_field=schema_data.get("filter_field"),
            filter_value=schema_data.get("filter_value"),
            metadata_fields=schema_data.get("metadata_fields", []),
        )

    logger.debug(
        "Protocol: %s (version %s, paths: %s, import schemas: %s)",
        protocol_path,
        protocol_version,
        protocol_paths or "single-file",
        list(import_schemas) or "none",
    )

    return Config(
        root=root,
        protocol_path=protocol_path,
        protocol_paths=protocol_paths,
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
        import_schemas=import_schemas,
    )


def _resolve_protocol_paths(cfg: Config) -> list[Path]:
    """Resolve the effective list of protocol file paths.

    If ``protocol_paths`` glob patterns are configured, expands each
    relative to ``cfg.root`` (sorted for determinism). Falls back to
    the single ``protocol_path`` file.
    """
    if cfg.protocol_paths:
        files: list[Path] = []
        for pattern in cfg.protocol_paths:
            files.extend(sorted(cfg.root.glob(pattern)))
        return files
    return [cfg.root / cfg.protocol_path]


def load_protocol_text(cfg: Config) -> str:
    """Assemble protocol text from one or more files.

    Single-file configs return the file content unchanged (no markers).
    Multi-file configs join sections with ``---`` separators and
    ``<!-- file: {name} -->`` headers so the origin of each section is
    traceable in resynthesis output.
    """
    paths = _resolve_protocol_paths(cfg)
    if len(paths) == 1:
        return paths[0].read_text()
    sections = [f"<!-- file: {p.name} -->\n{p.read_text()}" for p in paths]
    logger.debug("Assembled %d protocol files", len(paths))
    return "\n\n---\n\n".join(sections)
