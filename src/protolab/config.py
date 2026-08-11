"""Load and validate protolab.toml configuration."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

RESERVED_IMPORT_SCHEMA_NAMES = frozenset({"auto", "legacy", "promptfoo", "braintrust"})
IMPORT_SCHEMA_KEYS = frozenset(
    {
        "format",
        "subject",
        "protocol_output",
        "step",
        "correct_output",
        "reasoning",
        "filter_field",
        "filter_value",
        "metadata_fields",
    }
)


@dataclass
class TriggerConfig:
    """Thresholds that determine when resynthesis is recommended."""

    total_corrections: int = 10
    cluster_threshold: float = 0.30
    preventable_errors: int = 3
    max_days_since_resynthesis: int | None = 30


@dataclass
class ImportSchema:
    """Field mappings for a config-defined import adapter.

    Mapping values use dot paths such as ``result.output.text``. Bare values
    for ``correct_output`` and ``reasoning`` also act as literal defaults when
    the source row has no field with that name.
    """

    format: str
    subject: str
    protocol_output: str
    step: str
    correct_output: str = "TODO"
    reasoning: str = "TODO"
    filter_field: str | None = None
    filter_value: str | None = None
    metadata_fields: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Protolab project configuration loaded from protolab.toml."""

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
    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key_env: str = "ANTHROPIC_API_KEY"
    import_schemas: dict[str, ImportSchema] = field(default_factory=dict)


def load_config(path: Path | None = None) -> Config:
    """Load protolab.toml from given path or search cwd.

    Apply defaults for all missing fields.
    Validate paths exist where required (protocol file).
    """
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    if path is None:
        path = Path.cwd() / "protolab.toml"
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at '{path}'. "
            "Run `protolab init` to create one."
        )

    with open(path, "rb") as f:
        data = tomllib.load(f)

    root = path.parent

    # Protocol section
    proto = data.get("protocol", {})
    protocol_path = Path(proto.get("path", "protocol.md"))
    protocol_version = proto.get("version", "v1.0")
    steps = proto.get("steps", [])

    # Validate protocol file exists and is within project root
    resolved_protocol = (root / protocol_path).resolve()
    if not resolved_protocol.is_relative_to(root.resolve()):
        raise ValueError(
            f"Protocol path '{protocol_path}' escapes the project root. "
            f"Paths must stay within the directory containing protolab.toml."
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
    llm_model = llm.get("model", "claude-sonnet-4-20250514")
    llm_api_key_env = llm.get("api_key_env", "ANTHROPIC_API_KEY")

    import_schemas = _load_import_schemas(data.get("import", {}))

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
        import_schemas=import_schemas,
    )


def _load_import_schemas(raw_schemas: object) -> dict[str, ImportSchema]:
    """Validate and load ``[import.<name>]`` adapter declarations."""
    if not isinstance(raw_schemas, dict):
        raise ValueError("[import] must be a table of named adapter schemas.")

    schemas: dict[str, ImportSchema] = {}
    for name, raw_schema in raw_schemas.items():
        section = f"[import.{name}]"
        if not name.strip():
            raise ValueError("Import adapter names must be non-empty strings.")
        if name in RESERVED_IMPORT_SCHEMA_NAMES:
            raise ValueError(
                f"{section} uses reserved adapter name '{name}'."
            )
        if not isinstance(raw_schema, dict):
            raise ValueError(f"{section} must be a table.")
        unknown_keys = sorted(set(raw_schema) - IMPORT_SCHEMA_KEYS)
        if unknown_keys:
            raise ValueError(
                f"{section} has unknown field(s): {', '.join(unknown_keys)}."
            )

        required: dict[str, str] = {}
        for key in ("subject", "protocol_output", "step"):
            value = raw_schema.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{section}.{key} must be a non-empty string.")
            required[key] = value

        source_format = raw_schema.get("format", "jsonl")
        if not isinstance(source_format, str) or source_format not in {
            "jsonl",
            "csv",
            "json",
        }:
            raise ValueError(
                f"{section}.format must be one of: jsonl, csv, json."
            )

        optional_strings: dict[str, str | None] = {}
        for key, default in (
            ("correct_output", "TODO"),
            ("reasoning", "TODO"),
            ("filter_field", None),
            ("filter_value", None),
        ):
            value = raw_schema.get(key, default)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(
                    f"{section}.{key} must be a non-empty string when set."
                )
            optional_strings[key] = value

        filter_field = optional_strings["filter_field"]
        filter_value = optional_strings["filter_value"]
        if (filter_field is None) != (filter_value is None):
            raise ValueError(
                f"{section}.filter_field and filter_value must be set together."
            )

        metadata_fields = raw_schema.get("metadata_fields", [])
        if not isinstance(metadata_fields, list) or not all(
            isinstance(value, str) and value.strip() for value in metadata_fields
        ):
            raise ValueError(
                f"{section}.metadata_fields must be a list of non-empty strings."
            )

        schemas[name] = ImportSchema(
            format=source_format,
            subject=required["subject"],
            protocol_output=required["protocol_output"],
            step=required["step"],
            correct_output=optional_strings["correct_output"] or "TODO",
            reasoning=optional_strings["reasoning"] or "TODO",
            filter_field=filter_field,
            filter_value=filter_value,
            metadata_fields=metadata_fields,
        )

    return schemas


def load_protocol_text(config: Config) -> str:
    """Read the configured protocol as UTF-8 text."""
    return (config.root / config.protocol_path).read_text(encoding="utf-8")
