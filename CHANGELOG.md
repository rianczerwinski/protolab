# Changelog

## [0.1.0] — 2026-03-23

### Added

- Core refinement loop: `correct`, `analyze`, `check`, `resynthesis`, `status`
- CLI with all commands (`protolab`, `plab` alias)
- TOML-based correction and rule storage with datetime roundtrip
- Cluster analysis with preventable error detection
- Configurable resynthesis triggers (total corrections, cluster threshold, preventable errors, days since last)
- Jinja2 template-based prompt assembly with customizable templates
- Anthropic API integration (`--run` flag) with staging, diff review, and promotion lifecycle
- Web dashboard with SSE live updates (`protolab serve`)
- Multi-file protocol support via glob patterns
- Adapter system with registry: Promptfoo, Braintrust, generic config-driven
- Custom import schemas in `protolab.toml` with dot-path field mapping and filtering
- Metadata passthrough on corrections (carried through the full pipeline)
- Metadata-based analysis grouping (`--group-by metadata.model`)
- Export adapters: raw and Promptfoo YAML formats (`protolab export`)
- Adapter discovery command (`protolab adapters`)
- Programmatic Python API (`from protolab import Project`)
- Bulk ingest HTTP endpoint and adapter-specific webhook ingestion
- Full documentation: concepts, configuration, correction schema, resynthesis, integration
- ruff linter + formatter, mypy strict type checking, pre-commit hooks
