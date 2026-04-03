# Concepts

## The Accumulation Problem

Most protocol improvement is additive. You notice an error, you add a rule. You
find an edge case, you add a caveat. The document grows monotonically — it
becomes its own archaeology. Eventually it's too long to fit in a context
window, too dense to be actionable, and full of redundant or contradictory
rules that nobody can hold in their head simultaneously.

This is the default trajectory for any document that guides decisions: system
prompts, style guides, diagnostic criteria, grading rubrics, review checklists.
The failure mode isn't neglect — it's diligent maintenance that adds without
removing. The document becomes a sedimentary record of every mistake ever made,
rather than a distilled expression of what the current best practice is.

## The Compression Insight

Structured error accumulation + periodic resynthesis = convergence.

Instead of adding rules when you find errors, you log corrections systematically
and periodically rewrite the protocol from scratch, collapsing all accumulated
learning into a version that is **shorter and more powerful** than the previous
version plus its corrections.

Ten corrections about the same decision point collapse into one refined
discriminator. Contradictions are resolved. Redundancies merge. Preventable
errors — things the existing rules should have caught — trigger reorganization
rather than more rules. The protocol evolves like a codebase (refactored toward
clarity) rather than a wiki page (growing toward completeness).

Information density increases per cycle. The protocol converges on precision.

## The Refinement Cycle

The unit of improvement is the cycle, not the individual correction.

```
Protocol(v) + Corrections(v) → Resynthesis → Protocol(v+1)
```

Each cycle is a compression event. The inner loop (use the protocol, log
corrections) accumulates feedstock. The outer loop (analyze patterns, check
triggers, resynthesize) consumes it. After resynthesis, corrections are archived
and the counter resets.

**Inner loop** — per use:
1. Use the protocol to guide a decision
2. Note where the output was wrong
3. Log the correction: what was produced, what was correct, why
4. Optionally extract a generalizable discriminator rule

**Outer loop** — periodic:
1. Analyze correction distribution — where do errors cluster?
2. Check triggers — enough corrections to justify resynthesis?
3. Assemble the resynthesis prompt (current protocol + all corrections + rules)
4. Resynthesize — produce a new protocol version
5. Review, promote, archive

## Error as Feedstock

Corrections aren't problems to fix. They're the energy source for refinement.
Without errors, the protocol stagnates. A protocol that never produces
correctable output has either converged to its eigenform or isn't being used
critically enough.

The tool reframes failure as fuel. Every correction carries structured
information: what decision point failed, what the correct output was, and why
the protocol's logic was wrong. This structure enables pattern mining — the
`analyze` command finds where corrections cluster, revealing which parts of the
protocol are weakest.

## Rules as Crystallized Pattern

Rules are the intermediate representation between raw corrections and
integrated protocol. Corrections say "this was wrong in this case." Rules
say "here's the generalizable discriminator."

Not every correction yields a rule. Some errors are one-off noise. But when a
correction reveals a structural principle — a pattern that would prevent a
class of errors, not just a single instance — that principle crystallizes into
a rule with an explicit confidence level:

- **structural** — follows from the domain's logic, unlikely to be revised
- **strong_pattern** — observed multiple times, could have edge cases
- **provisional** — observed once but plausible as general rule, needs confirmation

Rules travel into the resynthesis prompt alongside raw corrections, giving the
rewrite process both the raw material and the analyst's pattern recognition.

## Convergence and the Eigenform

The protocol approaches a fixed point: the version that no longer produces
errors driving further modification. Never reached; asymptotically approached.
Each cycle compresses the distance between what the protocol says and what the
domain actually requires.

The measure of progress isn't fewer corrections per se — it's that corrections
shift from revealing structural gaps (the protocol doesn't address this case) to
revealing edge precision (the protocol's rule is almost right but needs a
conditional). The character of errors changes even when the count doesn't.

## Domain Generality

The compression insight applies to any decision-guiding document:

- **System prompts** — the original use case. Prompt engineering as iterative
  compression.
- **Style guides** — editorial standards that sharpen through error correction.
- **Grading rubrics** — evaluation criteria that discriminate better each cycle.
- **Diagnostic criteria** — clinical or technical decision trees refined through
  use.
- **Legal review checklists** — compliance criteria compressed through case law.
- **Coding standards** — conventions that crystallize from code review patterns.

The pattern is the same: a document guides decisions, decisions produce errors,
errors are logged structurally, and periodic resynthesis compresses everything
into a more precise document. Protolab structures this process regardless of
domain.
