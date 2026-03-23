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
