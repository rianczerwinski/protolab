# Correction and Rule Schemas

Field reference for the TOML data files that store corrections and extracted rules.

## Corrections

Corrections live in the file specified by `corrections.path` in `protolab.toml` (default: `corrections/correction-log.toml`). Each correction is a `[[corrections]]` entry in the TOML array.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | auto | Sequential identifier (`corr_001`, `corr_002`, ...). Generated automatically — never set this manually. |
| `subject` | string | yes | What was being analyzed when the error occurred. A case name, test input, document identifier — whatever identifies the instance. |
| `date` | datetime | auto | When the correction was logged. Native TOML datetime, populated automatically. |
| `protocol_version` | string | auto | Which version of the protocol produced the error. Populated from `protocol.version` in config. |
| `step` | string | yes | The decision point where the error occurred. This is the primary grouping key for cluster analysis. Use consistent names — `"classification"`, `"severity_assessment"`, etc. |
| `protocol_output` | string | yes | What the protocol produced. The wrong answer, the incorrect classification, the misguided recommendation. |
| `correct_output` | string | yes | What should have been produced. The ground truth for this case. |
| `reasoning` | string | yes | Why the correction is right. This is the diagnostic content — the structural explanation of what went wrong and what the correct discriminator is. The richer this field, the better resynthesis can integrate the correction. |
| `rule` | string | optional | A generalizable discriminator extracted from this correction. When present, protolab creates a corresponding rule entry automatically. Omit entirely if no generalizable rule applies. |
| `metadata` | table | optional | Arbitrary key-value pairs carried through the pipeline. Populated by adapters (e.g. model name, scores, provider). Preserved in the correction log and available in resynthesis templates. |

### Example

```toml
[[corrections]]
id = "corr_001"
subject = "case_alpha"
date = 2026-03-22T14:30:00Z
protocol_version = "v1.0"
step = "classification"
protocol_output = "Type 4w5"
correct_output = "Type 5w4"
reasoning = "Withdrawal pattern is information-gathering (5), not identity-seeking (4). The aesthetic sensitivity is wing, not core."
rule = "When withdrawal serves curiosity/competence rather than identity/authenticity, classify as 5 not 4."

[[corrections]]
id = "corr_002"
subject = "case_beta"
date = 2026-03-22T15:00:00Z
protocol_version = "v1.0"
step = "severity_assessment"
protocol_output = "moderate"
correct_output = "high"
reasoning = "Compounding factors were missed."
```

The `rule` field is optional. When absent, omit it entirely — TOML has no null, so absence is the convention.

### Empty Correction Log

A fresh correction log contains only a comment:

```toml
# Protolab correction log
```

`load_corrections()` returns an empty list when no `[[corrections]]` array exists.

## Rules

Rules live in the file specified by `corrections.rules_path` in `protolab.toml` (default: `corrections/rules.toml`). Each rule is a `[[rules]]` entry.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | auto | Sequential identifier (`rule_001`, `rule_002`, ...). Generated automatically. |
| `decision_point` | string | auto | The step this rule applies to. Copied from the source correction's `step` field. |
| `rule` | string | auto | The generalizable discriminator text. Copied from the source correction's `rule` field. |
| `confidence` | string | auto | How established this rule is. See confidence levels below. New rules start as `"provisional"`. |
| `source` | string | auto | The correction ID this rule was extracted from (e.g. `"corr_001"`). |
| `date_added` | datetime | auto | When the rule was created. Used to determine which corrections are "preventable" (occurred after a rule was established). |

### Confidence Levels

Rules carry one of three confidence levels, which affect how resynthesis treats them:

**`provisional`** — Observed in one correction. May not generalize. Resynthesis integrates the rule if consistent with other evidence; drops it if conflicting. This is the default for newly extracted rules.

**`strong_pattern`** — Consistent across multiple cases. Resynthesis integrates this into the protocol text. Upgrading from provisional to strong_pattern is a manual judgment call — when you've seen the pattern hold across enough cases, edit the rule's confidence field.

**`structural`** — Follows from the domain's axioms. Won't change regardless of new evidence. Resynthesis preserves structural rules verbatim unless a correction explicitly overrides one. Reserve this level for rules that are definitional, not empirical.

### Example

```toml
[[rules]]
id = "rule_001"
decision_point = "classification"
rule = "When withdrawal serves curiosity/competence rather than identity/authenticity, classify as 5 not 4."
confidence = "provisional"
source = "corr_001"
date_added = 2026-03-22T14:30:00Z

[[rules]]
id = "rule_002"
decision_point = "severity_assessment"
rule = "When multiple moderate factors co-occur, escalate to high."
confidence = "strong_pattern"
source = "corr_002"
date_added = 2026-03-22T15:00:00Z
```

## Preventable Errors

A correction is "preventable" if it occurred on a step that already had an established rule at the time of the correction. Specifically: if any rule exists for the same `decision_point` with a `date_added` at or before the correction's `date`, that correction counts as preventable.

The preventable error count is a key resynthesis trigger — it measures how many errors the protocol is still producing despite having rules that should address them. A high preventable count indicates the rules aren't being integrated into the protocol effectively, which is exactly what resynthesis fixes.
