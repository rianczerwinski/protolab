"""protolab init — interactive project scaffolding."""

from __future__ import annotations

import glob
from pathlib import Path

import click
import tomli_w


DEFAULT_TEMPLATE = """\
# Protocol Resynthesis

You are rewriting a protocol document. Your goal is to produce a new version that is
**shorter, clearer, and more precise** than the current version — not longer.

## Current Protocol ({{ version }})

{{ protocol_content }}

## Corrections Since Last Resynthesis ({{ corrections | length }} total)

{% for c in corrections %}
### {{ c.id }} — {{ c.step }}
- **Subject:** {{ c.subject }}
- **Protocol said:** {{ c.protocol_output }}
- **Correct:** {{ c.correct_output }}
- **Reasoning:** {{ c.reasoning }}
{% endfor %}

## Extracted Rules ({{ rules | length }} total)

### Structural (preserve verbatim unless a correction explicitly overrides)
{% for r in rules if r.confidence == "structural" %}
- [{{ r.decision_point }}] {{ r.rule }}
{% endfor %}

### Strong Pattern
{% for r in rules if r.confidence == "strong_pattern" %}
- [{{ r.decision_point }}] {{ r.rule }}
{% endfor %}

### Provisional (integrate if consistent with other evidence; drop if conflicting)
{% for r in rules if r.confidence == "provisional" %}
- [{{ r.decision_point }}] {{ r.rule }}
{% endfor %}

## Cluster Analysis

{{ analysis_summary }}

## Instructions

1. Integrate all corrections into the protocol text.
2. Where multiple corrections cluster on the same decision point, synthesize into a single clearer discriminator.
3. Remove redundant or contradictory guidance that corrections have superseded.
4. Preserve structural rules verbatim unless explicitly overridden.
5. The new protocol must be **self-contained** — no references to this correction log.
6. The new protocol must be **shorter** than the current version. Measure in lines. If you cannot make it shorter, explain why in a comment block at the top.
7. Output ONLY the new protocol document. No commentary, no changelog.
"""


def scaffold_project(bare: bool = False) -> None:
    """Create protolab.toml, empty correction/rule files, and template directory.

    If bare=False, globs for likely protocol files and offers interactive selection.
    If bare=True, uses all defaults and assumes protocol.md exists.
    """
    cwd = Path.cwd()

    if bare:
        protocol_path = "protocol.md"
        if not (cwd / protocol_path).exists():
            click.echo(
                f"Warning: '{protocol_path}' does not exist yet. "
                f"Create it before running other commands."
            )
    else:
        # Glob for likely protocol files
        candidates = []
        for pattern in ["*.md", "system-prompt.*", "prompt.*", "protocol.*"]:
            candidates.extend(glob.glob(pattern))
        # Deduplicate and sort
        candidates = sorted(set(candidates))

        if candidates:
            click.echo("Found potential protocol files:")
            for i, c in enumerate(candidates, 1):
                click.echo(f"  {i}. {c}")
            protocol_path = click.prompt(
                "Protocol file path",
                default=candidates[0],
            )
        else:
            protocol_path = click.prompt(
                "Protocol file path",
                default="protocol.md",
            )

    # Write protolab.toml
    config_data = {
        "protocol": {
            "path": protocol_path,
            "version": "v1.0",
        },
    }
    (cwd / "protolab.toml").write_text(tomli_w.dumps(config_data))

    # Create empty correction/rule files
    corrections_dir = cwd / "corrections"
    corrections_dir.mkdir(exist_ok=True)
    (corrections_dir / "correction-log.toml").write_text("# Protolab correction log\n")
    (corrections_dir / "rules.toml").write_text("# Protolab rules\n")

    # Create template
    templates_dir = cwd / "templates"
    templates_dir.mkdir(exist_ok=True)
    (templates_dir / "resynthesis-prompt.md").write_text(DEFAULT_TEMPLATE)

    click.echo("Ready. Log your first correction with `protolab correct`")
