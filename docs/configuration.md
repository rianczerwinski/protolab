# Configuration

All configuration lives in `protolab.toml` at the project root, created by
`protolab init`.

## Full Reference

```toml
# Protocol identity
[protocol]
name = "my-protocol"
version = "1.0.0"
path = "protocol.md"                # Path to the active protocol document

# Storage paths
[paths]
corrections = "corrections.toml"
rules = "rules.toml"
archive = "archive/"                # Archived protocols + correction logs
template = "templates/resynthesis.md.j2"  # Resynthesis prompt template

# Resynthesis trigger thresholds (any one met → resynthesis recommended)
[triggers]
total_corrections = 10              # Minimum corrections before recommending
cluster_threshold = 0.30            # Max concentration ratio (fraction on one step)
preventable_errors = 3              # Corrections on steps with existing rules
max_days_since_resynthesis = 30     # Calendar time trigger

# LLM settings (used by --run flag)
[llm]
model = "claude-sonnet-4-20250514"
max_tokens = 8192
```

## Field Details

### `[protocol]`

**name** — Human-readable identifier. Used in status output and archive
filenames. No constraints on format.

**version** — Semantic version string. Updated on each resynthesis promotion.
Protolab prompts for the new version number during promotion.

**path** — Relative path to the active protocol document. This is the file that
gets archived and replaced during resynthesis promotion.

### `[paths]`

**corrections** — TOML file where corrections accumulate. Reset to empty on
promotion. Default: `corrections.toml`.

**rules** — TOML file where extracted rules accumulate. Reset to empty on
promotion. Default: `rules.toml`.

**archive** — Directory for archived protocols, corrections, and rules from
previous versions. Each promotion writes three files:
`{version}.md`, `corrections-{version}.toml`, `rules-{version}.toml`.

**template** — Jinja2 template for the resynthesis prompt. See
[resynthesis.md](resynthesis.md) for template variables and customization.

### `[triggers]`

All triggers are OR'd: any single trigger being met causes `protolab check`
to recommend resynthesis.

**total_corrections** — Raw count threshold. When the number of active
corrections reaches this value, resynthesis is recommended. Default: 10.

**cluster_threshold** — Concentration ratio. If any single decision step
accounts for more than this fraction of all corrections, resynthesis is
recommended. Default: 0.30 (30%).

**preventable_errors** — Corrections that target decision points where an
extracted rule already exists. These indicate the protocol isn't integrating
its own learned rules effectively. Default: 3.

**max_days_since_resynthesis** — Calendar time since the last resynthesis (or
since project initialization, if no resynthesis has occurred). Catches protocols
that are being used without correction. Default: 30.

### `[llm]`

Only used when running `protolab resynthesis --run`. Requires
`pip install protolab[ai]` for the `anthropic` package.

**model** — Anthropic model ID. Default: `claude-sonnet-4-20250514`.

**max_tokens** — Output token ceiling for the resynthesis call. Default: 8192.
