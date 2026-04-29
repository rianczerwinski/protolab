# Protolab — Implementation Spec

**Tagline:** *Your protocol gets shorter every time you fix it.*

**Description:** Error-driven compression for system prompts and protocol documents. Structured correction accumulation with compressive resynthesis.

**PyPI name:** `protolab`
**CLI commands:** `protolab` (primary), `plab` (alias)
**License:** MIT + TRADEMARK.md
**Python:** ≥3.10
**Config format:** TOML throughout (config, corrections, rules)

---

## File Tree

```
protolab/
├── README.md
├── LICENSE                              # MIT
├── TRADEMARK.md
├── pyproject.toml
├── src/protolab/
│   ├── __init__.py                      # version string
│   ├── cli.py                           # click group, all commands
│   ├── config.py                        # load/validate protolab.toml
│   ├── init_cmd.py                      # `protolab init`
│   ├── correct.py                       # `protolab correct`, `--batch`
│   ├── import_cmd.py                    # `protolab import`
│   ├── check.py                         # trigger evaluation
│   ├── analyze.py                       # cluster analysis
│   ├── resynthesis.py                   # prompt assembly + `--run`
│   ├── status.py                        # dashboard
│   ├── store.py                         # TOML read/write for corrections and rules
│   └── llm.py                           # Anthropic API wrapper (isolated)
├── tests/
│   ├── conftest.py
│   ├── test_store.py
│   ├── test_correct.py
│   ├── test_import.py
│   ├── test_check.py
│   ├── test_analyze.py
│   ├── test_resynthesis.py
│   ├── test_status.py
│   └── test_config.py
├── docs/
│   ├── concepts.md                      # Standalone essay: the compression insight
│   ├── configuration.md                 # Full config reference
│   ├── correction-schema.md             # Correction + rule schemas
│   ├── resynthesis.md                   # Prompt design, template customization
│   └── integration.md                   # Eval frameworks, CI/CD, team patterns
└── examples/
    ├── quickstart/
    │   ├── protolab.toml
    │   ├── protocol.md                  # Minimal system prompt example
    │   └── corrections.toml             # Empty
    ├── full-loop/
    │   ├── protolab.toml
    │   ├── protocol-v1.md               # System prompt with known issues
    │   ├── corrections.toml             # 8 corrections
    │   ├── rules.toml                   # Extracted rules
    │   ├── resynthesis-prompt.md        # Assembled prompt
    │   └── protocol-v2.md              # Resynthesized: shorter, sharper
    └── resynthesis-prompt-template.md   # Default Jinja2 template
```

---

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "protolab"
version = "0.1.0"
description = "Error-driven compression for system prompts and protocol documents"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [{ name = "Rían" }]
keywords = ["protocol", "refinement", "prompt-engineering", "compression", "human-in-the-loop", "cli"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Quality Assurance",
    "Typing :: Typed",
]
dependencies = [
    "click>=8.0",
    "jinja2>=3.0",
    "rich>=13.0",
    "tomli-w>=1.0",
    "tomli>=2.0; python_version < '3.11'",
]

[project.optional-dependencies]
ai = ["anthropic>=0.39.0"]
dev = ["pytest>=7.0", "pytest-tmp-files>=0.0.2"]

[project.scripts]
protolab = "protolab.cli:main"
plab = "protolab.cli:main"

[project.urls]
Homepage = "https://github.com/liquidprismata/protolab"
Documentation = "https://github.com/liquidprismata/protolab/tree/main/docs"
Issues = "https://github.com/liquidprismata/protolab/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/protolab"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## Config Schema — `protolab.toml`

```toml
[protocol]
path = "protocol/current.md"            # Path to active protocol document
version = "v1.0"                         # Current version label
steps = []                               # Optional: valid decision point names

[corrections]
path = "corrections/correction-log.toml"
rules_path = "corrections/rules.toml"

[resynthesis]
prompt_template = "templates/resynthesis-prompt.md"
output_path = "resynthesis/output.md"
last_resynthesis_date = 2026-01-01T00:00:00Z  # Updated automatically; omit if never resynthesized

[resynthesis.triggers]
total_corrections = 10                   # N corrections accumulated
cluster_threshold = 0.30                 # M% of corrections on same step
preventable_errors = 3                   # K errors on steps with existing rules
max_days_since_resynthesis = 30          # Days since last resynthesis

[archive]
versions_path = "protocol/versions/"

[llm]
provider = "anthropic"                   # v1: anthropic only. Future: LLM-agnostic
model = "claude-sonnet-4-20250514"
api_key_env = "ANTHROPIC_API_KEY"
```

Defaults: `config.py` provides defaults for every field so a minimal config works:

```toml
[protocol]
path = "protocol.md"
```

Everything else falls back to defaults.

---

## Data Schemas

### Correction — `corrections.toml`

```toml
[[corrections]]
id = "corr_001"
subject = "case_identifier"
date = 2026-03-22T14:30:00Z
protocol_version = "v1.0"
step = "classification"
protocol_output = "Type 4w5"
correct_output = "Type 5w4"
reasoning = "Withdrawal pattern is information-gathering (5), not identity-seeking (4). The aesthetic sensitivity is wing, not core."
rule = "When withdrawal serves curiosity/competence rather than identity/authenticity, classify as 5 not 4."

[[corrections]]
id = "corr_002"
subject = "another_case"
date = 2026-03-22T15:00:00Z
protocol_version = "v1.0"
step = "severity_assessment"
protocol_output = "moderate"
correct_output = "high"
reasoning = "Compounding factors were missed."
```

The `rule` field is optional. When absent, omit it entirely (TOML has no null — absence is the convention).

### Rule — `rules.toml`

```toml
[[rules]]
id = "rule_001"
decision_point = "classification"
rule = "When withdrawal serves curiosity/competence rather than identity/authenticity, classify as 5 not 4."
confidence = "provisional"               # provisional | strong_pattern | structural
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

### Empty data files

```toml
# Protolab correction log
```

```toml
# Protolab rules
```

`store.py` returns empty list when no `[[corrections]]` or `[[rules]]` array exists.

---

## Command Specs

### `protolab init`

Interactive scaffolding. Creates `protolab.toml`, empty correction log, empty rules file, template directory.

Behavior:
1. Glob for likely protocol files (`*.md`, `system-prompt.*`, `prompt.*`, `protocol.*`) in cwd
2. If found, offer as default path; otherwise prompt for path
3. Create `protolab.toml` with that path + all defaults
4. Create empty `corrections/correction-log.toml`
5. Create empty `corrections/rules.toml`
6. Create `templates/resynthesis-prompt.md` from bundled default template
7. Print: "Ready. Log your first correction with `protolab correct`"

Flag: `--bare` — skip interactive prompts, use all defaults, assume `protocol.md` exists.

### `protolab correct`

Interactive correction logging.

Behavior:
1. Load config, load correction log
2. Prompt for fields in order: subject, step (with tab-completion from step registry if defined, and from previously-used steps), protocol_output, correct_output, reasoning
3. Ask: "Extract a generalizable rule? [y/N]" — if yes, prompt for rule text
4. Generate ID (next sequential `corr_NNN`)
5. Auto-populate date, protocol_version
6. Append to correction log
7. If rule provided: generate rule ID, append to rules file with confidence `provisional` and source reference
8. Print summary with rich formatting

Flag: `--batch PATH` — read JSON or TOML file containing array of correction objects. Validate each, append all, report count. Skip interactive prompts.

### `protolab import`

Import eval failures as correction stubs.

Behavior:
1. Read JSONL or CSV file (auto-detect by extension)
2. Map fields to correction schema. Configurable field mapping via flags:
   - `--subject-field` (default: `subject` or `input`)
   - `--output-field` (default: `output` or `expected`)
   - `--step-field` (default: `step` or `category`)
3. For each row: create correction stub with protocol_output populated, correct_output and reasoning set to `"TODO"` placeholder
4. Append all to correction log
5. Print: "Imported N correction stubs. Run `protolab correct` to fill in reasoning."

This is the eval-framework integration point. Stubs pre-populate the structured part; human fills in the semantic part.

### `protolab check`

Evaluate resynthesis triggers.

Behavior:
1. Load config, corrections, rules
2. Evaluate each trigger:
   - `total_corrections`: len(corrections) >= threshold
   - `cluster_threshold`: max(corrections_per_step) / len(corrections) >= threshold
   - `preventable_errors`: count corrections where step has existing rule >= threshold
   - `max_days_since_resynthesis`: days since last_resynthesis_date >= threshold (skip if no previous resynthesis)
3. Print each trigger with status (met/unmet) and current value vs threshold
4. If any trigger met: "Resynthesis recommended. Run `protolab resynthesis`"
5. Exit code: 0 if no triggers met, 1 if any met (for CI scripting)

### `protolab analyze`

Cluster analysis of accumulated corrections.

Behavior:
1. Load corrections and rules
2. Group corrections by step
3. For each step, report:
   - Count and percentage of total
   - List of corrections (brief: id, subject, one-line summary of reasoning)
   - Whether rules exist for this step
   - If rules exist: how many corrections postdate those rules (= preventable errors)
4. Sort steps by correction count descending
5. Identify the top cluster and print a summary: "N corrections (M%) target step '{step}'. {K} occurred after rules were established for this step."
6. Print overall: total corrections, unique steps, concentration ratio (top step / total)
7. Rich table output

This command uses no AI. Pure data analysis on the correction log.

### `protolab resynthesis`

Assemble resynthesis prompt, optionally execute via LLM.

Behavior (prompt assembly, default):
1. Load config, protocol, corrections, rules
2. Render Jinja2 template with:
   - `version`: current protocol version
   - `protocol_content`: full text of protocol file
   - `corrections_formatted`: all corrections, formatted readably
   - `rules_formatted`: all rules, grouped by confidence level
   - `analysis_summary`: output of analyze (cluster info, preventable error count)
3. Write rendered prompt to `resynthesis.output_path`
4. Print: "Resynthesis prompt written to {path}. Feed to your preferred LLM."

Behavior with `--run`:
1. Do everything above
2. Check for `anthropic` package (error with install instructions if missing)
3. Read API key from env var specified in config
4. Send prompt to Anthropic API
5. Write response to staging path: `resynthesis/staged-protocol.md`
6. Print diff (current protocol vs staged) using rich diff formatting
7. Prompt: "Accept this resynthesis? [y/N]"
8. If yes:
   - Copy current protocol to `archive/versions_path/{version}.md`
   - Move staged protocol to protocol path
   - Auto-increment version in config (v1.0 → v1.1, or prompt for label)
   - Update `last_resynthesis_date` in config
   - Archive correction log to `archive/corrections-{version}.toml`
   - Archive rules to `archive/rules-{version}.toml`
   - Reset correction and rule files to empty
   - Print: "Protocol updated to {new_version}. Corrections archived."

### `protolab status`

Dashboard.

Behavior:
1. Load everything
2. Rich-formatted output:
   - Protocol: path, version, last modified date
   - Corrections: count, oldest, newest
   - Corrections per step: table (step | count | has_rules)
   - Rules: count by confidence level
   - Triggers: status of each (same as `check` but embedded in dashboard)
   - Last resynthesis: date or "never"

---

## Module Specs

### `store.py`

```python
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

def load_toml(path: Path) -> dict:
    """Load TOML file. Return dict (may be empty if file has no arrays)."""

def save_toml(path: Path, data: dict) -> None:
    """Write TOML with clean formatting via tomli_w."""

def load_corrections(config: Config) -> list[dict]:
    """Load correction log. Return data.get('corrections', [])."""

def save_corrections(config: Config, corrections: list[dict]) -> None:
    """Write corrections as {'corrections': corrections} to TOML."""

def load_rules(config: Config) -> list[dict]:
    """Load rules. Return data.get('rules', [])."""

def save_rules(config: Config, rules: list[dict]) -> None:
    """Write rules as {'rules': rules} to TOML."""

def next_id(existing: list[dict], prefix: str) -> str:
    """Generate next sequential ID: prefix_NNN."""
```

`tomli_w` handles `[[array]]` syntax natively when given `{"corrections": [list of dicts]}`. Datetime objects written as native TOML datetimes.

### `config.py`

```python
@dataclass
class TriggerConfig:
    total_corrections: int = 10
    cluster_threshold: float = 0.30
    preventable_errors: int = 3
    max_days_since_resynthesis: int | None = 30

@dataclass
class Config:
    protocol_path: Path
    protocol_version: str = "v1.0"
    steps: list[str] = field(default_factory=list)
    corrections_path: Path = Path("corrections/correction-log.toml")
    rules_path: Path = Path("corrections/rules.toml")
    triggers: TriggerConfig = field(default_factory=TriggerConfig)
    prompt_template_path: Path = Path("templates/resynthesis-prompt.md")
    resynthesis_output_path: Path = Path("resynthesis/output.md")
    last_resynthesis_date: datetime | None = None
    archive_versions_path: Path = Path("protocol/versions/")
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key_env: str = "ANTHROPIC_API_KEY"

def load_config(path: Path | None = None) -> Config:
    """
    Load protolab.toml from given path or search cwd.
    Apply defaults for all missing fields.
    Validate paths exist where required (protocol file).
    """
```

### `correct.py`

```python
def interactive_correct(config: Config) -> dict:
    """Prompt user for correction fields. Return correction dict."""

def batch_correct(config: Config, path: Path) -> list[dict]:
    """Load corrections from JSON or TOML file. Validate. Return list."""

def extract_rule(correction: dict, config: Config) -> dict | None:
    """If correction has rule text, create rule dict with provisional confidence."""
```

### `import_cmd.py`

```python
def import_eval_failures(
    config: Config,
    path: Path,
    subject_field: str,
    output_field: str,
    step_field: str,
) -> list[dict]:
    """
    Read JSONL or CSV. Map fields to correction schema.
    Set correct_output and reasoning to 'TODO'.
    Return list of correction stubs.
    """
```

### `check.py`

```python
@dataclass
class TriggerResult:
    name: str
    met: bool
    current_value: float | int
    threshold: float | int

def evaluate_triggers(
    config: Config,
    corrections: list[dict],
    rules: list[dict],
) -> list[TriggerResult]:
    """Evaluate all configured triggers. Return results."""
```

### `analyze.py`

```python
@dataclass
class StepCluster:
    step: str
    count: int
    percentage: float
    corrections: list[dict]
    rules: list[dict]
    preventable_count: int

@dataclass
class AnalysisResult:
    total_corrections: int
    unique_steps: int
    clusters: list[StepCluster]          # sorted by count desc
    concentration_ratio: float

def analyze_corrections(
    corrections: list[dict],
    rules: list[dict],
) -> AnalysisResult:
    """Cluster corrections by step, compute diagnostics."""
```

### `resynthesis.py`

```python
def assemble_prompt(
    config: Config,
    protocol_content: str,
    corrections: list[dict],
    rules: list[dict],
    analysis: AnalysisResult,
) -> str:
    """Render Jinja2 template with all data. Return prompt string."""

def run_resynthesis(config: Config, prompt: str) -> str:
    """Send prompt to LLM via llm.py. Return response text."""

def stage_resynthesis(config: Config, new_protocol: str) -> Path:
    """Write to staging path. Return path."""

def promote_resynthesis(config: Config, staged_path: Path, new_version: str) -> None:
    """Archive current, move staged to active, update config, clear logs."""
```

### `llm.py`

```python
def call_anthropic(model: str, api_key: str, prompt: str) -> str:
    """
    Call Anthropic messages API. Return response text.
    Raise clear error if anthropic package not installed.
    Isolated module: only dependency on anthropic SDK.
    Future: add providers here for LLM-agnostic support.
    """
```

### `cli.py`

```python
import click

@click.group()
def main():
    """Protolab: error-driven compression for protocol documents."""

@main.command()
@click.option("--bare", is_flag=True, help="Non-interactive, all defaults")
def init(bare): ...

@main.command()
@click.option("--batch", type=click.Path(exists=True), help="Import corrections from file")
def correct(batch): ...

@main.command("import")
@click.argument("path", type=click.Path(exists=True))
@click.option("--subject-field", default="subject")
@click.option("--output-field", default="output")
@click.option("--step-field", default="step")
def import_cmd(path, subject_field, output_field, step_field): ...

@main.command()
def check(): ...

@main.command()
def analyze(): ...

@main.command()
@click.option("--run", is_flag=True, help="Execute via LLM API")
def resynthesis(run): ...

@main.command()
def status(): ...
```

---

## Default Resynthesis Template

`templates/resynthesis-prompt.md`:

```markdown
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
```

---

## Test Cases

### `test_store.py`

- **roundtrip**: write corrections → load corrections → identical data
- **empty_file**: load from file with no `[[corrections]]` array → empty list
- **empty_file_comment_only**: load from file with only comments → empty list
- **next_id**: given `[corr_001, corr_003]` → returns `corr_004`
- **next_id_empty**: given `[]` → returns `corr_001`
- **save_creates_dirs**: save to `nested/path/file.toml` → creates directories
- **datetime_roundtrip**: datetime objects survive write → read cycle as native TOML datetimes

### `test_correct.py`

- **batch_json**: load batch from JSON array → correct count, all fields populated
- **batch_toml**: load batch from TOML → same
- **batch_validates**: batch with missing required field → raises with informative error
- **rule_extraction**: correction with rule text → rule file updated, source references correction id
- **version_stamped**: correction auto-populated with current protocol version from config
- **optional_rule_absent**: correction without rule → no rule field in output TOML

### `test_import.py`

- **jsonl_import**: JSONL with 5 lines → 5 correction stubs with `TODO` placeholders
- **csv_import**: CSV with header row → correct field mapping
- **custom_fields**: `--subject-field=input --output-field=expected` → maps correctly
- **missing_field**: row missing mapped field → skip with warning, not crash

### `test_check.py`

- **total_met**: 10 corrections, threshold 10 → trigger met
- **total_unmet**: 9 corrections, threshold 10 → trigger unmet
- **cluster_met**: 4/10 corrections on same step, threshold 0.30 → met
- **cluster_unmet**: 2/10 on same step, threshold 0.30 → unmet
- **preventable_met**: 3 corrections on step with existing rule, threshold 3 → met
- **days_met**: last resynthesis 31 days ago, threshold 30 → met
- **days_null**: no previous resynthesis → trigger not evaluated (skip, don't trigger)
- **exit_code**: any trigger met → exit code 1

### `test_analyze.py`

- **cluster_grouping**: 10 corrections across 3 steps → 3 clusters, sorted by count
- **concentration_ratio**: top cluster has 5/10 → ratio 0.5
- **preventable_detection**: rule added on day 3, corrections on day 1 and day 5 → preventable_count = 1
- **empty_corrections**: 0 corrections → empty analysis, no crash

### `test_resynthesis.py`

- **template_renders**: template + corrections + rules → output contains protocol content, all correction IDs, all rule texts
- **rules_grouped**: structural rules in structural section, provisional in provisional section
- **analysis_included**: analysis summary appears in rendered prompt
- **staging**: resynthesis writes to staging path, not active protocol path

### `test_config.py`

- **defaults**: minimal config (just protocol path) → all other fields populated with defaults
- **full_config**: all fields specified → all loaded correctly
- **missing_protocol**: protocol file doesn't exist → clear error
- **invalid_toml**: malformed TOML → clear error

### `conftest.py`

Shared fixtures:
- `tmp_project`: creates a temp directory with minimal `protolab.toml`, empty `protocol.md`, empty correction/rule files
- `sample_corrections`: returns list of 10 correction dicts covering 3 different steps
- `sample_rules`: returns list of 3 rules at different confidence levels
- `sample_config`: returns Config object pointed at tmp_project

---

## Examples Content

### `examples/quickstart/protolab.toml`

```toml
[protocol]
path = "protocol.md"
version = "v1.0"
```

### `examples/quickstart/protocol.md`

```markdown
# Customer Support Classifier

You are a customer support routing system. Classify incoming messages into one of these categories:

## Categories

- **billing**: Payment issues, subscription changes, refund requests
- **technical**: Product bugs, integration problems, API errors
- **general**: Feature requests, how-to questions, feedback

## Rules

1. If the message mentions money, payment, charge, or subscription → billing
2. If the message mentions error, bug, crash, or API → technical
3. Everything else → general
4. If ambiguous between two categories, prefer the more specific one
```

### `examples/quickstart/corrections.toml`

```toml
# Protolab correction log
```

### `examples/full-loop/protolab.toml`

```toml
[protocol]
path = "protocol-v1.md"
version = "v1.0"

[corrections]
path = "corrections.toml"
rules_path = "rules.toml"

[resynthesis]
prompt_template = "../../resynthesis-prompt-template.md"
output_path = "resynthesis-prompt.md"

[resynthesis.triggers]
total_corrections = 8

[archive]
versions_path = "versions/"
```

### `examples/full-loop/protocol-v1.md`

A system prompt (~40 lines) for the customer support classifier, with known weaknesses in edge cases around billing-vs-technical overlap, multi-intent messages, and emotional tone affecting classification.

### `examples/full-loop/corrections.toml`

8 corrections as `[[corrections]]` entries:
- 3 on billing/technical overlap (failed payments caused by API errors)
- 2 on multi-intent messages (billing question + feature request in same message)
- 2 on tone misclassification (angry messages routed to billing regardless of content)
- 1 on genuine edge case (pricing page broken = technical, not billing)

### `examples/full-loop/rules.toml`

3 rules as `[[rules]]` entries:
- "When a payment failure is caused by a system/API error, classify as technical not billing" (strong_pattern)
- "Multi-intent messages: classify by the actionable intent, not the secondary mention" (provisional)
- "Emotional tone (anger, frustration) is not a classification signal" (structural)

### `examples/full-loop/protocol-v2.md`

Resynthesized protocol: shorter than v1 (~30 lines), with billing/technical discriminator sharpened, multi-intent rule added, tone-independence stated explicitly. Verbose category descriptions compressed.

---

## README.md

```markdown
# Protolab

Your protocol gets shorter every time you fix it.

Protolab structures the loop between finding errors in a protocol document and making
the document better. Log corrections, track patterns, and periodically compress
everything back into a sharper, shorter protocol through resynthesis.

## Install

\`\`\`bash
pip install protolab
\`\`\`

## Quick Start

\`\`\`bash
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
\`\`\`

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

\`\`\`bash
protolab import eval-results.jsonl --subject-field=input --output-field=expected
\`\`\`

Then fill in the reasoning with `protolab correct`.

## Docs

- [Concepts](docs/concepts.md) — The compression insight and refinement methodology
- [Configuration](docs/configuration.md) — Full `protolab.toml` reference
- [Correction Schema](docs/correction-schema.md) — Correction and rule field reference
- [Resynthesis](docs/resynthesis.md) — Prompt design and template customization
- [Integration](docs/integration.md) — Eval frameworks, CI/CD, team workflows

## License

MIT. See [TRADEMARK.md](TRADEMARK.md) for trademark notice.
\`\`\`

---

## TRADEMARK.md

```markdown
# Trademark Notice

"Typology Institute" and "TI" are trademarks of Rían.

This project is released under the MIT License. You are free to use, modify, and
distribute the code. However, the Typology Institute name and marks may not be used
to endorse or promote derivative works without written permission.

Forks and derivative works should use their own branding.
```

---

## Docs Outlines

### `docs/concepts.md`

Standalone essay. Linkable independently of the tool.

1. **The accumulation problem** — Why protocol improvement defaults to growth. Every correction adds a rule; no process removes them. The document becomes its own archaeology.
2. **The compression insight** — Structured error accumulation + periodic resynthesis = convergence. The protocol gets denser, not longer. Information density increases per cycle.
3. **The refinement cycle** — Formal description: Protocol(v) + Corrections(v) → Resynthesis → Protocol(v+1). Each cycle is a compression event. The cycle is the unit of improvement, not the individual correction.
4. **Error as feedstock** — Corrections aren't problems to fix. They're the energy source for refinement. Without errors, the protocol stagnates. The tool reframes failure as fuel.
5. **Rules as crystallized pattern** — The intermediate representation between raw corrections and integrated protocol. Rules are where pattern recognition becomes explicit. Corrections say "this was wrong"; rules say "here's the generalizable discriminator."
6. **Convergence and the eigenform** — The protocol approaches a fixed point: the version that no longer produces errors driving further modification. Never reached; asymptotically approached. Brief nod to von Foerster, accessible register.
7. **The elaboratorium** — Etymology of protolab. The archaic sense of "elaborate" as purification through careful process. The lab as ongoing workspace, never finished.
8. **Domain generality** — Why this works for any decision-guiding document. Prompt engineering as entry point; the general pattern as depth.

### `docs/configuration.md`

Reference document. Every field in `protolab.toml`, type, default value, description. Annotated example config.

### `docs/correction-schema.md`

Reference document. Every field in correction and rule schemas. Field-by-field descriptions. Valid values for confidence levels with guidance on when to use each. Examples in TOML.

### `docs/resynthesis.md`

1. What resynthesis does and why compression is the goal
2. The default template: walkthrough of each section
3. Customizing the template: Jinja2 variables available, domain-specific modifications
4. Manual workflow (prompt assembly) vs automated (`--run`)
5. Reviewing resynthesis output: what to check, when to reject and re-run

### `docs/integration.md`

1. Eval framework integration: Promptfoo, Braintrust, custom scripts → `protolab import`
2. Git workflow: committing corrections and resynthesized protocols
3. CI/CD: using `protolab check` exit codes to flag when resynthesis is due
4. Team usage: shared correction logs, review processes
5. Multi-protocol setups

---

## Design Notes for Implementer

**Dependencies are minimal.** `click` for CLI, `tomli`/`tomllib` + `tomli_w` for data, `jinja2` for templates, `rich` for terminal formatting. `anthropic` is optional (extras install). No other dependencies.

**All state lives in TOML files.** No database, no hidden state directory. Everything is in the project directory, version-controllable with git.

**Interactive prompts use `click.prompt()` and `rich`** for formatting. Keep them fast — the interactive `correct` flow should take under 60 seconds.

**The `analyze` command uses no AI.** Pure data analysis: grouping, counting, sorting.

**Error messages must be actionable.** Example: "Protocol file not found at `protocol.md`. Run `protolab init` or set `protocol.path` in `protolab.toml`." Not "FileNotFoundError."

**The `llm.py` module is deliberately isolated.** All Anthropic-specific code lives here. When LLM-agnostic support is added later, this module grows a provider abstraction; nothing else changes.

**Version auto-increment:** Split on `.`, increment last segment. `v1.0` → `v1.1`. `v2.3.1` → `v2.3.2`. If version doesn't match this pattern, prompt user for new version label.

**TOML writing convention:** Use `tomli_w.dumps()` for all output. The library handles `[[array_of_tables]]` syntax, native datetimes, and clean formatting. For empty data files, write a comment header and no arrays — `store.py` returns empty list when no array key is found.
