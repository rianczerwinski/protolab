# Protolab

Your protocol gets shorter every time you fix it.

Protolab structures the loop between finding errors in a protocol document and making
the document better. Log corrections, track patterns, and periodically compress
everything back into a sharper, shorter protocol through resynthesis.

## Install

```bash
pip install protolab
```

## Quick Start

```bash
# Point protolab at your protocol (system prompt, style guide, diagnostic criteria — any decision document)
protolab init

# When your protocol produces a wrong output, log it
protolab correct

# Check if it's time for resynthesis
protolab check

# See where corrections cluster
protolab analyze

# Compress corrections back into the protocol
protolab resynthesis
# or execute directly via Anthropic API:
protolab resynthesis --run
```

## How It Works

Most protocol improvement is additive. You notice an error, you add a rule. The document
grows. Over time it becomes bloated, internally contradictory, and too long to follow.

Protolab inverts this. You log structured corrections — what the protocol said, what was
correct, and why. When enough corrections accumulate, you trigger **resynthesis**: the
current protocol plus all corrections are fed to an LLM (or human editor) with a single
instruction: produce a new version that is **shorter and more precise**, not longer.

Ten corrections about the same decision point collapse into one refined discriminator.
The protocol converges on clarity through each cycle rather than growing unboundedly.

## The Loop

1. **Use** your protocol
2. **Correct** errors with `protolab correct` (structured: what, why, generalizable rule)
3. **Analyze** patterns with `protolab analyze` (where do corrections cluster?)
4. **Check** triggers with `protolab check` (enough corrections to justify resynthesis?)
5. **Resynthesize** with `protolab resynthesis` (compress everything into a shorter, sharper protocol)
6. **Repeat**

## Works With Any Protocol

System prompts. Style guides. Grading rubrics. Diagnostic criteria. Legal review
checklists. Coding standards. If you have a document that guides decisions and you
want to improve it systematically, protolab structures that process.

## Importing From Eval Frameworks

If you use an eval framework (Promptfoo, Braintrust, or custom), import failures as
correction stubs:

```bash
protolab import eval-results.jsonl --subject-field=input --output-field=expected
```

Then fill in the reasoning with `protolab correct`.

## Web Dashboard

Protolab includes an optional HTTP server with a live-updating dashboard and JSON API.

```bash
pip install protolab[serve]
protolab serve              # http://localhost:8080
protolab serve --port 9090  # custom port
```

The dashboard shows correction stream, trigger gauges, cluster analysis, and
editable configuration — all live-updating via SSE when corrections are added
(from the CLI or via the API).

**API endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Full status (corrections, clusters, rules, triggers) |
| GET | `/api/corrections` | List corrections (`?step=`, `?since=`) |
| POST | `/api/corrections` | Log a correction via JSON |
| GET | `/api/triggers` | Trigger evaluation results |
| GET | `/api/protocol` | Protocol content (file or module directory) |
| POST | `/api/resynthesis` | Assemble prompt (`?run=true` to execute) |
| PATCH | `/api/config` | Update trigger thresholds |
| GET | `/api/events` | SSE stream (live updates) |

## Docs

- [Concepts](docs/concepts.md) — The compression insight and refinement methodology
- [Configuration](docs/configuration.md) — Full `protolab.toml` reference
- [Correction Schema](docs/correction-schema.md) — Correction and rule field reference
- [Resynthesis](docs/resynthesis.md) — Prompt design and template customization
- [Integration](docs/integration.md) — Eval frameworks, CI/CD, team workflows

## License

MIT. See [TRADEMARK.md](TRADEMARK.md) for trademark notice.
