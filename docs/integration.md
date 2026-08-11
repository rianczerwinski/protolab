# Integration

## Eval Framework Integration

Protolab imports failure records from eval frameworks as correction stubs. A stub has the structural fields populated but `correct_output` and `reasoning` set to `TODO` unless the adapter can recover them from the source.

### Promptfoo

```bash
protolab import results.json --adapter promptfoo
```

Parses Promptfoo JSON output. Extracts the subject from `vars`, protocol output from `response.output`, expected output from assertions, and the grading reason. Metadata includes scores, providers, and token counts.

### Braintrust

```bash
protolab import experiments.jsonl --adapter braintrust
```

Parses Braintrust JSONL or JSON exports. Filters to failures with a score below 1.0 and retains scores and source metadata.

### Config-Driven Adapters

For another eval framework, define a named import schema in `protolab.toml`:

```toml
[import.my_framework]
format = "jsonl"
subject = "input.case_id"
protocol_output = "response.text"
step = "grading.category"
correct_output = "expected"
reasoning = "grading.reason"
filter_field = "result"
filter_value = "fail"
metadata_fields = ["score", "model", "latency"]
```

`format` accepts `jsonl`, `csv`, or `json`. Field mappings use dot paths into each source record. `correct_output` and `reasoning` are optional and default to the literal `TODO`; `filter_field` and `filter_value` are optional but must be declared together.

Import with the schema name:

```bash
protolab import results.jsonl --adapter my_framework
```

The older `--from my_framework` spelling remains an alias for scripted callers.

### Direct Field Mapping

Flat JSONL, CSV, or JSON records need no custom schema. Auto-detection falls back to the legacy field mapper, whose field names can be overridden directly:

```bash
protolab import results.jsonl \
  --subject-field=input \
  --output-field=expected \
  --step-field=category
```

## Webhook Ingestion

The web server accepts POST requests for automated ingestion:

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '[{"subject": "case_1", "step": "classify", "protocol_output": "X", "correct_output": "TODO", "reasoning": "TODO"}]'

curl -X POST http://localhost:8000/api/ingest/promptfoo \
  -H "Content-Type: application/json" \
  -d @promptfoo-results.json
```

## Git Workflow

Protolab stores everything in plain TOML and Markdown files. Corrections accumulate append-only, resynthesized protocols should be committed as discrete versioned events, and archived protocol versions remain unchanged as reference material.

## CI/CD

`protolab check` returns exit code 1 when any trigger is met, so CI can flag when resynthesis is overdue:

```yaml
- name: Check protocol freshness
  run: protolab check
```

## Team Usage

Multiple team members can log corrections against the same protocol. Since corrections are append-only TOML records, concurrent changes can retain both entries when merged.

For larger teams, the web server provides a shared dashboard with SSE live updates so corrections logged by one team member appear immediately for others.

## Multi-Protocol Setups

Each protocol gets its own `protolab.toml`. When a repository manages multiple protocols, give each one a directory:

```
protocols/
├── classification/
│   ├── protolab.toml
│   ├── protocol.md
│   └── corrections.toml
└── grading/
    ├── protolab.toml
    ├── protocol.md
    └── corrections.toml
```

Run Protolab from the directory of the protocol you want to manage.

## Export

### Raw Protocol Export

```bash
protolab export raw --output protocol-with-metadata.md
```

Outputs the protocol with a metadata header containing its version and source path.

### Promptfoo Config Export

```bash
protolab export promptfoo --output promptfoo-snippet.yaml
```

Generates a YAML snippet for `promptfooconfig.yaml` that uses the current protocol as the system prompt.
