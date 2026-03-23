# Configuration

Full reference for `protolab.toml` — the project configuration file created by `protolab init`.

All paths are relative to the directory containing `protolab.toml`. Path traversal outside the project root (e.g. `../../etc/passwd`) is rejected at load time.

## Minimal Config

```toml
[protocol]
path = "protocol.md"
```

Everything else falls back to defaults. This is what `protolab init --bare` creates.

## Full Config

```toml
[protocol]
path = "protocol.md"
version = "v1.0"
steps = ["classification", "severity"]
paths = ["instructions/*.md", "system-prompt.md"]

[corrections]
path = "corrections/correction-log.toml"
rules_path = "corrections/rules.toml"

[resynthesis]
prompt_template = "templates/resynthesis-prompt.md"
output_path = "resynthesis/output.md"
last_resynthesis_date = 2026-03-01T00:00:00Z

[resynthesis.triggers]
total_corrections = 10
cluster_threshold = 0.30
preventable_errors = 3
max_days_since_resynthesis = 30

[archive]
versions_path = "protocol/versions/"

[llm]
provider = "anthropic"
model = "claude-sonnet-4-20250514"
api_key_env = "ANTHROPIC_API_KEY"

[import.my_eval_system]
format = "jsonl"
subject = "test_case.input"
protocol_output = "test_case.output"
step = "test_case.category"
correct_output = "annotations.gold"
reasoning = "annotations.notes"
filter_field = "status"
filter_value = "failed"
metadata_fields = ["model", "latency_ms"]
```

## Field Reference

### `[protocol]`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | `"protocol.md"` | Path to the active protocol document. Required to exist at load time. |
| `version` | string | `"v1.0"` | Current version label. Updated automatically after resynthesis promotion. |
| `steps` | array of strings | `[]` | Valid decision point names. Used for tab-completion in `protolab correct`. When empty, any step name is accepted. |
| `paths` | array of strings | `[]` | Glob patterns for multi-file protocol assembly. When non-empty, files are concatenated with `<!-- file: name -->` markers. |

### `[corrections]`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | `"corrections/correction-log.toml"` | Path to the correction log file. Created automatically on first correction. |
| `rules_path` | string | `"corrections/rules.toml"` | Path to the extracted rules file. |

### `[resynthesis]`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt_template` | string | `"templates/resynthesis-prompt.md"` | Path to the Jinja2 template for prompt assembly. |
| `output_path` | string | `"resynthesis/output.md"` | Where the assembled resynthesis prompt is written. |
| `last_resynthesis_date` | datetime | *omitted* | Updated automatically after promotion. Omit if no resynthesis has occurred. |

### `[resynthesis.triggers]`

Triggers determine when `protolab check` recommends resynthesis. All thresholds are configurable; any single trigger being met is sufficient.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `total_corrections` | integer | `10` | Resynthesis recommended when this many corrections have accumulated. |
| `cluster_threshold` | float | `0.30` | Resynthesis recommended when the top cluster contains this fraction of all corrections (0.0–1.0). |
| `preventable_errors` | integer | `3` | Resynthesis recommended when this many corrections occurred on steps that already have rules. |
| `max_days_since_resynthesis` | integer | `30` | Resynthesis recommended when this many days have passed since the last resynthesis. Skipped if no previous resynthesis. |

### `[archive]`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `versions_path` | string | `"protocol/versions/"` | Directory where previous protocol versions are archived after promotion. |

### `[llm]`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | string | `"anthropic"` | LLM provider. Currently only `"anthropic"` is supported. |
| `model` | string | `"claude-sonnet-4-20250514"` | Model identifier passed to the provider API. |
| `api_key_env` | string | `"ANTHROPIC_API_KEY"` | Name of the environment variable containing the API key. The key itself is never stored in the config file. |

### `[import.<name>]` — Custom Import Schemas

Define custom adapters for your own data formats. Each `[import.<name>]` section creates an adapter accessible via `protolab import --from <name>`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `format` | string | `"jsonl"` | File format: `"jsonl"`, `"csv"`, or `"json"`. |
| `subject` | string | *required* | Dot-path to the subject field in source data (e.g. `"test_case.input"`). |
| `protocol_output` | string | *required* | Dot-path to the protocol output field. |
| `step` | string | *required* | Dot-path to the decision point / category field. |
| `correct_output` | string | `"TODO"` | Dot-path to the expected output, or literal default. |
| `reasoning` | string | `"TODO"` | Dot-path to the reasoning/explanation field, or literal default. |
| `filter_field` | string | *omitted* | Field name for simple equality filtering. |
| `filter_value` | string | *omitted* | Required value for the filter field. Only rows where `filter_field == filter_value` are imported. |
| `metadata_fields` | array of strings | `[]` | Dot-paths to fields that should be preserved as correction metadata. |

Dot-path syntax: `"a.b.0.c"` traverses `obj["a"]["b"][0]["c"]`. Numeric segments index into arrays.
