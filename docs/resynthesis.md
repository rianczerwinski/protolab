# Resynthesis

## What Resynthesis Does

Resynthesis is the compression event. The current protocol plus all accumulated
corrections and extracted rules are assembled into a single prompt. An LLM (or
human editor) rewrites the protocol from scratch — not patching, not appending,
but producing a complete new version that absorbs all learning and is shorter
and more precise than what it replaces.

The resynthesis prompt is the most important artifact in the system. It carries
the instructions for how compression should happen.

## The Default Template

`protolab init` creates a resynthesis template at `templates/resynthesis.md.j2`.
It uses Jinja2 for variable injection and contains five process steps:

### 1. Identify Redundancies
Multiple rules or corrections that are specific instances of the same general
principle. Collapse them into the principle, retaining specific cases as
illustrative examples only if needed.

### 2. Identify Contradictions
Rules that conflict. Resolve by:
- Determining which correction was wrong (rare — remove it)
- Adding a conditional: "this rule holds except when [condition]"
- Recognizing they operate at different levels and don't actually conflict

### 3. Identify Gaps
Patterns in corrections that no existing rule covers. Generate candidate rules
to fill the gap, flagged as provisional until confirmed by future analyses.

### 4. Identify Preventable Errors
Corrections targeting errors that the current protocol's rules should have
caught. This means the rules need reorganization or emphasis, not more rules.
Preventable errors are the strongest signal that the protocol's structure —
not its content — needs work.

### 5. Rewrite
Produce the complete new protocol. The output must be:
- **Standalone** — readable without reference to corrections or prior versions
- **Shorter** — or at most the same length, with higher information density
- **More discriminating** — edge cases the old version got wrong should now be
  covered by the integrated logic, not by appended patches

## Template Variables

The Jinja2 template receives these variables:

| Variable | Content |
|----------|---------|
| `protocol_version` | Current version string |
| `protocol_content` | Full text of the current protocol |
| `corrections` | All corrections since last resynthesis (list of dicts) |
| `rules` | All extracted rules (list of dicts) |
| `analysis_summary` | Output of `protolab analyze` — cluster distribution, concentration ratio, preventable error count |

## Customizing the Template

Edit `templates/resynthesis.md.j2` to change the resynthesis instructions.
Common customizations:

- **Domain-specific guidance** — "preserve the structural rules in section 3
  verbatim; only rewrite the discriminator rules"
- **Output format constraints** — "the protocol must fit in 4000 tokens"
- **Confidence integration** — "only promote provisional rules to strong_pattern
  if three or more corrections support them"
- **Changelog requirement** — "append a changelog entry listing what changed"

The default template works well for most cases. Customize when your domain
has structural constraints the generic instructions don't capture.

## Manual vs Automated Workflow

**Manual (default):**
```bash
protolab resynthesis          # Assembles prompt, outputs to stdout
protolab resynthesis > prompt.md  # Save to file
# Paste into your AI system, review output, save as staged protocol
```

**Automated:**
```bash
protolab resynthesis --run    # Assembles AND executes via Anthropic API
# Output written to staged-protocol.md for review
```

The `--run` flag requires `pip install protolab[ai]` and a configured API key.
Both workflows produce a staged output that must be explicitly promoted.

## Reviewing Staged Output

After resynthesis (manual or automated), the new protocol sits in
`staged-protocol.md`. Before promoting:

1. **Diff against current** — what changed? Is the compression real or cosmetic?
2. **Check for dropped rules** — did any structural rules disappear? This is
   usually an error.
3. **Check for hallucinated rules** — did the rewrite introduce rules that no
   correction supports? Remove them.
4. **Test against known cases** — mentally run the new protocol against the
   subjects that produced the most corrections. Would it get them right?
5. **Check length** — is it actually shorter? If not, the resynthesis didn't
   compress and should be re-run with stronger instructions.

## Promotion

```bash
protolab resynthesis --promote
```

Promotion:
1. Archives the old protocol as `archive/{old_version}.md`
2. Archives corrections and rules as `archive/corrections-{old_version}.toml`
   and `archive/rules-{old_version}.toml`
3. Moves staged protocol to active
4. Resets corrections and rules to empty
5. Updates `protolab.toml` with new version and resynthesis timestamp

The correction counter resets. The next cycle begins.
