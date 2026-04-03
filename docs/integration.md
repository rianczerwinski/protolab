# Integration

## Eval Framework Integration

Protolab imports failure records from eval frameworks as correction stubs.
A stub has the structural fields populated but `correct_output` and `reasoning`
set to `TODO` — the human analyst fills these in via `protolab correct`.

### Promptfoo

```bash
protolab import results.json --adapter promptfoo
```

Parses Promptfoo JSON output. Extracts subject from `vars`, protocol output
from `response.output`, expected output from `assertions`, and grading reason.
Metadata includes score, provider, and token counts.

### Braintrust

```bash
protolab import experiments.jsonl --adapter braintrust
```

Parses Braintrust JSONL export. Filters to failures (scores < 1.0). Collects
scores and source metadata.

### Generic (Config-Driven)

For custom eval frameworks, define an import schema in `protolab.toml`:

```toml
[import.my_framework]
format = "jsonl"                    # jsonl | csv | json
subject_field = "input.case_id"     # Dot-path into each record
output_field = "response.text"
expected_field = "expected"
reason_field = "grading.reason"     # Optional
filter = "result == 'fail'"         # Optional filter expression
metadata_fields = ["score", "model", "latency"]
```

Then:
```bash
protolab import results.jsonl --adapter my_framework
```

### Field Mapping

```bash
# Direct field mapping without config
protolab import results.jsonl \
  --subject-field=input \
  --output-field=expected \
  --reason-field=grading_notes
```

## Webhook Ingestion

The web server accepts POST requests for automated ingestion:

```bash
# Generic ingestion
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '[{"subject": "case_1", "step": "classify", "protocol_output": "X", "correct_output": "TODO", "reasoning": "TODO"}]'

# Adapter-based webhook
curl -X POST http://localhost:8000/api/ingest/promptfoo \
  -H "Content-Type: application/json" \
  -d @promptfoo-results.json
```

## Git Workflow

Protolab stores everything in plain files (TOML + markdown). Recommended git
practices:

- **Commit corrections as they accumulate** — they're append-only, merge
  conflicts are rare
- **Commit resynthesized protocols as discrete events** — the version bump in
  `protolab.toml` makes each resynthesis a clear point in history
- **Archive directory grows monotonically** — old versions are reference
  material, never modified

## CI/CD

`protolab check` returns exit code 1 when any trigger is met. Use it in CI
to flag when resynthesis is overdue:

```yaml
# GitHub Actions example
- name: Check protocol freshness
  run: protolab check --exit-code
```

## Team Usage

Multiple team members can log corrections against the same protocol. Since
corrections are append-only TOML, concurrent commits produce trivially
resolvable merge conflicts (just keep both entries).

For larger teams, the web server provides a shared dashboard with SSE live
updates — corrections logged by one team member appear immediately for others.

## Multi-Protocol Setups

Each protocol gets its own `protolab.toml`. If you manage multiple protocols
in the same repository, use directory structure:

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

Run protolab from each directory, or use `--config` to point at a specific
config file.

## Export

### Raw Protocol Export

```bash
protolab export raw > protocol-with-metadata.md
```

Outputs the protocol with a metadata header (version, correction count,
last resynthesis date).

### Promptfoo Config Export

```bash
protolab export promptfoo > promptfoo-snippet.yaml
```

Generates a YAML snippet for `promptfooconfig.yaml` that uses the current
protocol as the system prompt.
