# Resynthesis

Resynthesis is the compression event at the heart of protolab. It takes the current protocol, all accumulated corrections, all extracted rules, and a cluster analysis — and produces a new version that is shorter, clearer, and more precise.

## What Resynthesis Does

The `protolab resynthesis` command assembles a structured prompt from four sources:

1. **The current protocol** — the full text of your protocol document
2. **Corrections** — every structured error record since the last resynthesis
3. **Rules** — generalizable discriminators extracted from corrections, grouped by confidence level
4. **Analysis** — cluster summary showing where corrections concentrate and which errors are preventable

These are rendered into a Jinja2 template that instructs the reader (human or LLM) to produce a new protocol version that integrates all corrections while being shorter than the current version.

The output is a prompt, not a protocol. By default, protolab writes the assembled prompt to a file for you to feed to your preferred LLM or human editor. With `--run`, it sends the prompt directly to the Anthropic API and stages the response for review.

## The Default Template

The template created by `protolab init` has these sections:

### Protocol Section
The full text of the current protocol, labeled with its version number. This is what the resynthesizer is rewriting.

### Corrections Section
Every correction since the last resynthesis, formatted with ID, step, subject, protocol output, correct output, reasoning, and metadata (if present). Each correction is a discrete error to address.

### Rules Section
Rules grouped by confidence level:
- **Structural** rules are labeled "preserve verbatim unless a correction explicitly overrides"
- **Strong pattern** rules are presented for integration
- **Provisional** rules are presented with the caveat "integrate if consistent with other evidence; drop if conflicting"

### Analysis Section
The cluster analysis summary: total corrections, unique decision points, top cluster identification, concentration ratio. This scopes the problem — it tells the resynthesizer where to focus.

### Instructions
Seven numbered directives that enforce the compression discipline:
1. Integrate all corrections
2. Synthesize clustered corrections into single discriminators
3. Remove redundant guidance
4. Preserve structural rules
5. Produce a self-contained document
6. Be shorter than the current version
7. Output only the protocol — no commentary

## Customizing the Template

The template is a standard Jinja2 file. You can edit it at the path specified by `resynthesis.prompt_template` in your config.

### Available Variables

| Variable | Type | Description |
|----------|------|-------------|
| `version` | string | Current protocol version label |
| `protocol_content` | string | Full text of the protocol |
| `corrections` | list of dicts | All corrections (each has `id`, `subject`, `step`, `protocol_output`, `correct_output`, `reasoning`, optional `metadata`) |
| `rules` | list of dicts | All rules (each has `id`, `decision_point`, `rule`, `confidence`, `source`, `date_added`) |
| `analysis_summary` | string | Pre-formatted analysis text |

### Domain-Specific Modifications

The default template is domain-agnostic. For specific domains, consider:

- **System prompts**: Add an instruction to preserve the prompt's persona and tone while compressing the decision logic
- **Grading rubrics**: Add an instruction to maintain scoring ranges and boundary definitions
- **Diagnostic criteria**: Add an instruction to preserve hierarchical exclusion logic (diagnose A before considering B)
- **Coding standards**: Add an instruction to keep code examples updated with the new rules

### Metadata in Templates

Corrections imported via adapters may carry metadata (model name, scores, provider info). The default template renders metadata when present:

```jinja2
{% if c.metadata %}- **Metadata:** {{ c.metadata }}
{% endif %}
```

You can access specific metadata fields: `{{ c.metadata.model }}`, `{{ c.metadata.score }}`, etc.

## Manual vs Automated Resynthesis

### Manual Workflow

```bash
protolab resynthesis
# Writes prompt to resynthesis/output.md
# Copy the content, paste into your preferred LLM
# Review the output, make edits
# Save as the new protocol version
```

This is the default and recommended starting point. You maintain full control over what the protocol becomes.

### Automated Workflow

```bash
protolab resynthesis --run
# Sends prompt to Anthropic API
# Shows diff: current protocol vs proposed
# Prompts: "Accept this resynthesis? [y/N]"
# If accepted: archives current, promotes new, resets logs
```

The `--run` flag requires:
- The `anthropic` package installed (`pip install protolab[ai]`)
- The API key set in the environment variable specified by `llm.api_key_env`

Even with `--run`, you review and explicitly accept before anything changes.

## The Promotion Lifecycle

When a resynthesis is accepted (whether manual or via `--run`), promotion follows a specific order designed to minimize corruption if the process is interrupted:

1. **Archive** the current protocol to `archive/versions/{version}.md`
2. **Archive** the correction log and rules file alongside it
3. **Reset** the correction and rule files to empty
4. **Move** the new protocol to the active path
5. **Update** `protocol.version` and `last_resynthesis_date` in the config

The active protocol file is updated last — it's the visible "commit." If the process is interrupted at any earlier step, the current protocol is still intact.

After promotion, the correction log starts fresh. The archived corrections remain accessible in the versions directory for historical reference. The protocol version auto-increments (v1.0 → v1.1) or you can specify a custom version label.

## Reviewing Resynthesis Output

Before accepting a resynthesis, check:

- **Every correction is addressed.** The new protocol should handle each error case correctly. If a correction is dropped, that's a signal the resynthesis missed something.
- **Structural rules are preserved.** Unless a correction explicitly overrides one, structural rules should appear verbatim in the new version.
- **It's actually shorter.** Measure in lines or characters. If the new version is longer, the resynthesis failed its primary objective — reject and re-run, possibly with a more constrained template.
- **No new ambiguities.** Compression can introduce vagueness if discriminators are merged too aggressively. Read the new version as if you'd never seen the corrections — does it still make the right decisions?
