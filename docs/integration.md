# Integration

How to connect protolab to your existing tools — assessment frameworks, CI/CD pipelines, and team workflows.

## Built-In Adapters

Protolab ships with adapters for common assessment frameworks. Use `--from` to select one:

```bash
protolab import results.json --from promptfoo
protolab import export.jsonl --from braintrust
```

Without `--from`, protolab auto-detects the format by examining file structure. Auto-detection checks for Promptfoo's `results` key and Braintrust's `scores` key, falling back to flat field mapping for unrecognized formats.

### Promptfoo

Parses Promptfoo's JSON output (`promptfoooutput.json`). Filters to failed test cases by default.

**Field mapping:**
- `vars.input` (or first var value) → subject
- `response.output` → protocol_output
- `test.assert[].value` → correct_output (when available)
- `test.description` → step
- `gradingResult.reason` → reasoning

**Metadata carried:** `score`, `provider`, `prompt_label`, `token_usage`

```bash
# After running promptfoo eval
protolab import output/latest.json --from promptfoo
```

### Braintrust

Parses Braintrust JSONL experiment exports. Filters to rows where any score is below 1.0.

**Field mapping:**
- `input` → subject (stringified if dict)
- `output` → protocol_output
- `expected` → correct_output
- `metadata.category` or `tags[0]` → step

**Metadata carried:** `scores`, all `metadata` fields, `braintrust_id`

```bash
# After exporting from Braintrust
protolab import experiment-results.jsonl --from braintrust
```

### Discovering Adapters

List all available adapters (built-in and custom):

```bash
protolab adapters
```

## Custom Import Schemas

For data formats not covered by built-in adapters, define a custom schema in `protolab.toml`:

```toml
[import.my_framework]
format = "jsonl"
subject = "test_case.input"
protocol_output = "test_case.output"
step = "test_case.category"
correct_output = "annotations.gold"
reasoning = "annotations.notes"
filter_field = "status"
filter_value = "failed"
metadata_fields = ["model", "latency_ms", "tags"]
```

Then import using your schema name:

```bash
protolab import results.jsonl --from my_framework
```

### Dot-Path Syntax

Field values use dot-path syntax to traverse nested structures. `"test_case.input"` resolves to `row["test_case"]["input"]`. Numeric segments index into arrays: `"results.0.output"` resolves to `row["results"][0]["output"]`.

### Filtering

`filter_field` and `filter_value` implement simple equality filtering. Only rows where the filter field equals the filter value are imported. This covers the most common case — importing only failures from a mixed results file.

### Metadata Fields

Fields listed in `metadata_fields` are extracted from each row and stored in the correction's `metadata` dict. Use dot-paths for nested fields. The last segment of the path becomes the metadata key: `"info.model"` stores as `metadata.model`.

## Legacy Field Mapping

The original import interface with `--subject-field`, `--output-field`, and `--step-field` flags still works for flat JSONL and CSV files:

```bash
protolab import evals.jsonl --subject-field=input --output-field=expected
```

This is equivalent to a custom schema with flat field names. For nested structures or metadata, use the adapter system.

## Programmatic API

For scripts, notebooks, and CI pipelines, use the Python API directly:

```python
from protolab import Project

project = Project("./protolab.toml")

# Import from a file
stubs, skipped = project.ingest("results.jsonl", adapter="braintrust")

# Add a single correction programmatically
project.add_correction(
    subject="test_case_42",
    step="classification",
    protocol_output="Type 4",
    correct_output="Type 5",
    reasoning="Domain-exhaustion, not trust-failure.",
    metadata={"model": "claude-sonnet", "score": 0.2},
)

# Check triggers
triggers = project.check()
if any(t.met for t in triggers):
    prompt = project.assemble_prompt()
    # Feed to your preferred LLM, or:
    # response = project.run_resynthesis()

# Analysis with custom grouping
by_model = project.analyze(group_by="metadata.model")
by_step = project.analyze()  # default: group by step
```

## CI/CD Integration

### Exit Codes

`protolab check` returns exit code 1 when any trigger is met, exit code 0 otherwise. Use this in CI to flag when resynthesis is due:

```yaml
# GitHub Actions example
- name: Check resynthesis triggers
  run: protolab check
  continue-on-error: true

- name: Warn if resynthesis needed
  if: failure()
  run: echo "::warning::Resynthesis triggers met. Run protolab resynthesis."
```

### Automated Import

After running your assessment suite in CI, import failures automatically:

```yaml
- name: Run assessments
  run: promptfoo eval --output results.json

- name: Import failures
  run: protolab import results.json --from promptfoo

- name: Commit corrections
  run: |
    git add corrections/
    git diff --cached --quiet || git commit -m "Import assessment failures"
```

## Export

After resynthesis, export the updated protocol in framework-specific format:

```bash
# Raw export with metadata header
protolab export --format raw --output deploy/system-prompt.md

# Promptfoo YAML config snippet
protolab export --format promptfoo --output promptfoo-prompt.yaml
```

Or via the API:

```python
project = Project("./protolab.toml")
yaml_config = project.export(fmt="promptfoo")
project.export(fmt="raw", path="deploy/system-prompt.md")
```

## HTTP API / Webhooks

The web server (`protolab serve`) provides endpoints for programmatic ingestion:

```bash
# Bulk correction import (JSON array)
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -d '[{"subject": "test", "step": "classify", "protocol_output": "wrong"}]'

# Adapter-specific webhook (raw framework output)
curl -X POST http://localhost:8080/api/ingest/promptfoo \
  -H "Content-Type: application/octet-stream" \
  --data-binary @results.json
```

## Git Workflow

Protolab's TOML files are designed to be version-controlled. A recommended git workflow:

1. **Commit corrections as they accumulate.** Each `protolab correct` session produces a change to `corrections/correction-log.toml`. Commit these regularly.
2. **Commit resynthesis as a milestone.** After accepting a resynthesis, commit the new protocol, the archived corrections, and the config update as a single commit. The diff shows exactly what changed and why.
3. **Use branches for experimental resyntheses.** If you want to try a resynthesis without committing to it, create a branch, run `protolab resynthesis --run`, and review the result before merging.

## Team Usage

For teams sharing a protocol:

- **Shared correction log:** Multiple people log corrections to the same file. Git merge handles concurrent edits since TOML arrays append cleanly.
- **Review before promotion:** Use `protolab resynthesis` (without `--run`) to generate the prompt, share it for review, then promote the accepted version.
- **Role separation:** Domain experts log corrections and extract rules. A designated reviewer runs resynthesis and validates the output. The tool supports this workflow without enforcing it.
