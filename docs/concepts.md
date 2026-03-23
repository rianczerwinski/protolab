# Concepts

*Your protocol gets shorter every time you fix it.*

## The Accumulation Problem

Most protocol improvement is additive. You run your protocol, notice an error, add a rule. The document grows. Over time it becomes bloated, internally contradictory, and too long to follow. The corrections layer on top of each other without ever being integrated back into a coherent whole.

This is the default outcome of error-driven improvement: accumulation. Every correction-tracking system, every issue tracker, every "known issues" appendix follows the same pattern. Errors are discovered, patches are applied, and the document becomes its own archaeology — layers of sediment from different eras, each addressing a failure that may no longer be relevant, all of them adding length without adding clarity.

The problem isn't that corrections are wrong. The problem is that they never get digested. Ten corrections about the same decision point sit side by side in a log, each one independently valid, none of them synthesized into the single refined discriminator that would replace all ten. The protocol grows when it should be converging.

## The Compression Insight

Protolab inverts the default. Errors are logged as structured corrections — what the artifact produced, what was correct, and why. When enough corrections accumulate, they trigger resynthesis: the artifact plus all corrections are compressed into a new version that is shorter, clearer, and more precise. Ten corrections about the same decision point collapse into one refined discriminator. The artifact converges on fidelity through each cycle rather than growing unboundedly.

The key property is that resynthesis compresses. Each cycle increases the artifact's information density — more accurate guidance per unit of length. The correction history isn't deleted; it's digested. The artifact at version N contains the compressed wisdom of every error from versions 1 through N-1.

This is what distinguishes protolab from every other correction-tracking system: every other system produces growth. This one produces compression.

## The Refinement Cycle

The atomic unit of protolab is the refinement cycle: detect, investigate, diagnose, intervene, validate.

**Detection** is noticing that the artifact produced a wrong output. **Investigation** is figuring out why — examining traces, comparing working and failing cases, checking what changed since the last known good state. **Diagnosis** is constructing a structural hypothesis about what feature of the artifact caused the failure. **Intervention** is resynthesis — rewriting the artifact to address the diagnosed cause. **Validation** is confirming that the intervention actually eliminated the error class without introducing new ones.

The cycle runs regardless of who or what performs each step. A human can detect, investigate, diagnose, intervene, and validate manually. An LLM can do the same using traces, diffs, history, and search. A hybrid is possible: the system detects and investigates, the human confirms the diagnosis, the system intervenes, both validate. The cycle's structure is invariant; the participants are variable.

## Corrections and Rules

A correction is a structured record of a refinement event. It captures: what was being analyzed (the subject), which decision point failed (the step), what the artifact produced (the protocol output), what was actually correct (the correct output), and why (the reasoning). The reasoning field is the inquiry trace — the diagnostic content that makes the correction actionable rather than merely observational.

A rule is a crystallized discriminator extracted from one or more corrections. Where a correction says "this specific case was wrong," a rule says "here's the generalizable principle." Rules are the intermediate representation between raw corrections and the integrated artifact — the artifact's "case law," with corrections as the "case facts." Resynthesis is codification: integrating case law back into statute.

Rules carry confidence levels. **Structural** rules follow from the domain's axioms and won't change — resynthesis preserves them verbatim. **Strong patterns** are consistent across multiple cases — resynthesis integrates them. **Provisional** rules have been observed once and may not generalize — resynthesis includes them if consistent with other evidence, drops them if they conflict.

## Convergence and the Eigenform

The compression constraint is the convergence guarantee. Each refinement cycle must produce something shorter and validated — not just shorter. "Shorter" without validation can produce artifacts that are compressed but wrong in new ways, leading to oscillation rather than convergence.

The formal claim is that compression under validation converges. The artifact approaches an eigenform — a fixed point of its own refinement cycle. The eigenform is the version that, when subjected to use and correction, reproduces itself because it no longer produces errors that would drive further modification. It's never reached; it's approached asymptotically. Each cycle brings the artifact closer. The gap between the current version and the eigenform is measurable: it's the correction rate. When corrections approach zero, the artifact is approaching its eigenform.

## Domain Generality

Any document that guides decisions and produces assessable results can be placed in a correction-compression loop. System prompts. Style guides. Grading rubrics. Diagnostic criteria. Legal review checklists. Coding standards. Generation templates. If you can say "this artifact produced output X, but correct was Y, because Z," you can run the refinement loop.

The artifact doesn't need to be a text document. It needs to be a thing with evaluable outputs — something that acts, whose actions can be assessed, and whose structure can be revised. "Protocol refinement" is the entry point. The general principle is: any artifact with evaluable outputs can be treated as a function and placed in a correction-compression loop.

Self-application is the proof. Protolab's own resynthesis template is an artifact that produces outputs (resynthesized protocols). Those outputs can be evaluated. When the template produces a bad resynthesis, that's a correction against the template itself. The template goes through its own refinement cycle. The tool refines itself through the same loop it provides to others.

## The Elaboratorium

The name carries the architecture's central metaphor. Latin *elaborare*: to work out through effort, to purify through careful process. The elaboratorium is the alchemist's workshop where crude material is refined through cyclic processing — heated, compressed, reintegrated, each pass driving off impurities and increasing the substance's purity. The modern English sense of "elaborate" has inverted — it now means to add detail, to make more complex. The original sense is the opposite: to make more essential.

*Proto-* reads three ways simultaneously. Protocol — the tool's entry point. Prototype — the artifact is always becoming, always a draft of its next version. And the Greek *protos*, first — the primary thing, the thing being worked on, the substrate of the elaboration.

The lab is the ongoing workspace that's never finished. The refinement cycle doesn't terminate. The artifact is always in the lab. This is the correct framing for any living document, any maintained codebase, any evolving system. The eigenform is asymptotic. The work continues.
