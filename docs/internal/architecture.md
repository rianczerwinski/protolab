# Protolab: Architecture and Vision

*Your protocol gets shorter every time you fix it.*

---

## The Compression Insight

Most protocol improvement is additive. You run your protocol, notice an error, add a rule. The document grows. Over time it becomes bloated, internally contradictory, and too dense to follow. The corrections layer on top of each other without ever being integrated back into a coherent whole. This is the default outcome of error-driven improvement: accumulation.

Protolab inverts this. Errors are logged as structured corrections — what the artifact produced, what was correct, and why. When enough corrections accumulate, they trigger resynthesis: the artifact plus all corrections are compressed into a new version that is shorter, clearer, and more precise. Ten corrections about the same decision point collapse into one refined discriminator. The artifact converges on fidelity through each cycle rather than growing unboundedly.

The key property is that resynthesis compresses. Each cycle increases the artifact's information density — more accurate guidance per unit of length. The correction history isn't deleted; it's digested. The artifact at version N contains the compressed wisdom of every error from versions 1 through N-1. This is what distinguishes protolab from every other correction-tracking system: every other system produces growth. This one produces compression.

---

## The Refinement Cycle

The atomic unit of protolab is the refinement cycle: detect, investigate, diagnose, intervene, validate.

Detection is noticing that the artifact produced a wrong output. Investigation is figuring out why — examining traces, comparing working and failing cases, checking what changed since the last known good state. Diagnosis is constructing a structural hypothesis about what feature of the artifact caused the failure. Intervention is resynthesis — rewriting the artifact to address the diagnosed cause. Validation is confirming that the intervention actually eliminated the error class without introducing new ones.

This cycle maps directly onto the causal AI framework. Detection is observation. Investigation is active experimentation and querying. Diagnosis is causal model construction. Intervention is a do-operation on the artifact's structure, targeted by the diagnosis. Validation is checking the counterfactual — did the intervention eliminate the error class?

The cycle runs regardless of who or what performs each step. A human can detect, investigate, diagnose, intervene, and validate manually. An LLM can do the same using traces, diffs, history, and search. A hybrid is possible: the system detects and investigates, the human confirms the diagnosis, the system intervenes, both validate. The cycle's structure is invariant; the participants are variable.

---

## Corrections and Rules

A correction is a structured record of a refinement event. It captures: what was being analyzed (the subject), which decision point failed (the step), what the artifact produced (the protocol output), what was actually correct (the correct output), and why (the reasoning). The reasoning field is an inquiry trace — sometimes human-authored prose, sometimes an agent-generated investigation log, sometimes a hybrid. The schema is the same regardless.

A rule is a crystallized discriminator extracted from one or more corrections. Where a correction says "this specific case was wrong," a rule says "here's the generalizable principle." Rules are where pattern recognition becomes explicit and reusable. They are the intermediate representation between raw corrections and integrated artifact — the artifact's "case law," with corrections as the "case facts." Resynthesis is codification: integrating case law back into statute.

Rules carry confidence levels. Structural rules follow from the domain's axioms and won't change. Strong patterns are consistent across multiple cases. Provisional rules have been observed once and may not generalize. Resynthesis treats these differently: structural rules are preserved verbatim, strong patterns are integrated, provisional rules are suggested but may be dropped if they conflict.

---

## The Causal Model

Correction clustering — grouping errors by decision point and counting concentrations — is the minimum viable analysis. It tells you where things go wrong. It doesn't tell you why.

The deeper analytical operation is causal diagnosis: constructing a structural hypothesis about what feature of the artifact generates a class of error. When seven corrections cluster on the same decision point, the question isn't just "this step is error-prone" but "what is it about this step's representation that's structurally inadequate for the discriminations the domain demands?"

The system doesn't need a formal structural causal model to be useful — cluster analysis alone justifies the tool's existence. But the architecture should accommodate causal reasoning as a natural extension. When the investigator (human or LLM) diagnoses a failure, the diagnosis is itself a causal claim: "this artifact feature causes this error class because it conflates these distinct phenomena." Accumulating such diagnoses builds toward a causal model of the artifact — a map of which structural features produce which failure modes under which conditions. Resynthesis guided by a causal model becomes targeted intervention rather than wholesale compression: rewrite this specific feature to address this specific structural inadequacy.

---

## Scoping Discipline

Protolab's core contribution is not making the investigator smarter. It's making the question better.

An LLM asked to "fix this bug" with no context will pattern-match on what looks like a plausible fix. The same LLM given a structured correction history, a cluster analysis showing where errors concentrate, a set of extracted rules, and a diagnosed causal hypothesis about the artifact's structural inadequacy will produce a qualitatively different resynthesis — one grounded in the actual failure patterns rather than in generic heuristics.

The tool doesn't replace expertise. It structures the context in which expertise operates. The cluster analysis scopes the problem space. The correction history provides the evidence base. The rules provide the accumulated discrimination. The causal diagnosis provides the structural target. The resynthesis prompt assembles all of this into a well-constrained inquiry that any competent investigator — human or model — can execute productively.

This is the toolchain gap the tool fills. Eval frameworks tell you what's wrong. Version control records what changed. Protolab structures the step between knowing what's wrong and making it better.

---

## Artifact Generality

Any document is a function. A protocol takes cases and produces decisions. A system prompt takes user messages and produces responses. A README takes a reader and produces understanding or confusion. A codebase takes inputs and produces behavior. A library takes API calls and produces results. A generation prompt takes context and produces output.

If you can say "this artifact produced output X, but correct was Y, because Z," you can run the refinement loop. The artifact doesn't need to be a text document. It needs to be a thing with evaluable outputs — something that acts, whose actions can be assessed, and whose structure can be revised.

This is the conceptual move that unlocks protolab's generality. "Protocol refinement" is a special case. The general principle is: any artifact with evaluable outputs can be treated as a function and placed in a correction-compression loop. System prompts, codebases, configs, libraries, governance policies, generation templates, diagnostic criteria, editorial guidelines — anything that guides decisions and produces assessable results.

Self-application is the proof. Protolab's own resynthesis template is an artifact that produces outputs (resynthesized protocols). Those outputs can be evaluated (did the new protocol address the corrections? is it actually shorter?). When the template produces a bad resynthesis, that's a correction against the template itself. The template goes through its own refinement cycle. The tool refines itself through the same loop it provides to others.

---

## Coupled Feedback Loops

When multiple artifacts are under refinement simultaneously, resynthesizing one can change the error surface of another. The resynthesis template and the protocol it refines co-evolve: improving the template changes how protocols get rewritten, which changes what corrections accumulate against those protocols, which may surface new inadequacies in the template. The psychotype profile and the generation prompt co-evolve: refining the profile changes what the prompt knows about the user, which changes how it generates, which changes what errors are detected.

This coupling is a distinct architectural property from running independent loops. It's the interaction between loops that produces emergent behavior — and it's where the system's overall intelligence lives. Any single loop converges on a local optimum for its artifact. Coupled loops converge on a joint optimum across the artifact ecosystem, where each artifact is well-adapted not just to its domain but to the other artifacts it interacts with.

Coupling also introduces the primary stability risk. A resynthesis in one loop can cascade into corrections in another loop, which triggers resynthesis there, which cascades back. The compression constraint is the stabilizer — each cycle must produce something shorter and validated, not just shorter. But bounded oscillation remains possible even under compression if the artifacts are tightly coupled and the validation criteria are loose. The architecture should monitor for oscillation across coupled loops and flag it rather than allowing unbounded cascading resynthesis.

---

## The Single-Timescale Loop

The simplest instantiation of protolab is a single loop: one artifact, one correction stream, one compression cycle. This is what the CLI ships. You point it at a protocol document, log corrections as you find them, accumulate rules, analyze clusters, and resynthesize when the evidence warrants it.

At this scale, the human is the investigator. You notice the error, diagnose the cause, articulate the reasoning, extract the rule. The tool provides the structured accumulation (correction log), the pattern analysis (cluster detection, preventable error counting, trigger evaluation), the compression discipline (resynthesis prompt assembly or LLM execution), and the version management (staging, diffing, archiving, promotion).

This is protolab's first interface and its adoption path. Someone installs it, points it at their system prompt, logs their first correction in sixty seconds, and sees their first cluster analysis after a week of use. The compression loop becomes tangible when they run their first resynthesis and the protocol comes back shorter and sharper. That's the conversion moment.

---

## The Multi-Timescale Loop

The more powerful instantiation runs concurrent correction-compression loops at different temporal grains, all targeting the same output.

Consider a live generation system — an agent producing responses in real time. Three loops run simultaneously. The long loop tracks the session-level arc: who is this person, what's their psychotypological profile, what's the emotional trajectory, what are they trying to accomplish across the whole interaction. It updates slowly, resists local fluctuation, and provides the gravitational center. Its "corrections" are moments where the session model got the person wrong — misread the type, misjudged the arc. These accumulate slowly, and resynthesis at the long scale rewrites the session model.

The medium loop tracks the current phase: the topic, the mood shift, the conversational register, the immediate goal. It updates more frequently but with inertia — it follows real shifts without overreacting to noise. Its corrections are moments where the phase model lagged behind reality.

The short loop tracks the immediate moment: what was just said, what's the proximate intention, what does the next generation need to respond to. It updates in near-real-time.

Each loop maintains its own model and runs its own correction-compression cycle. The synthesis step combines all three into a single generation prompt — a precision-weighted blend where the long loop provides the container, the medium loop provides the trajectory, and the short loop provides the immediate target. The weighting is dynamic: early in a conversation, the long loop has low confidence and the short loop dominates. As the session-level model firms up, the long loop's gravity increases and prevents generation from overreacting to momentary fluctuations.

Gain scheduling prevents the system from performing its model back at the user. A system that profiles psychotype and tracks emotional arc will, without dampening, start leaning too hard into its model — over-interpreting, over-personalizing, over-reacting. The long loop's influence on generation is attenuated by a factor that keeps the profile informing without dominating. The system knows who the person is without treating them as a type in every utterance.

---

## The Autonomous Loop

In the fully autonomous instantiation, the entire refinement cycle runs without human intervention. An agentic system detects a failure cluster in one of its own artifacts — a library that keeps failing, a prompt that keeps producing bad outputs, a config that keeps causing errors. The LLM investigator examines the cluster, reads the traces, checks what changed since last working state, compares failing and working cases, and constructs a causal hypothesis. It proposes a resynthesis — a rewrite of the artifact targeted at the diagnosed structural inadequacy. It validates the rewrite by executing it against the failure cases and checking for regressions. If validation passes, it promotes the new version. If it fails, it logs the failure as a new correction and continues accumulating.

The human's role in this instantiation is variable. Sometimes the human reviews resynthesis proposals when confidence is low. Sometimes the human gets a notification after the fact — "I rewrote your bluetooth library because the OS changed its authentication handshake, here's the diff, here's why." Sometimes the human is absent entirely and the system operates as a self-improving artifact ecosystem.

The scoping discipline is what makes this viable. The agent isn't asked to "fix whatever's wrong." It's given a well-constrained inquiry: here's the cluster, here's the correction history, here's the causal hypothesis, rewrite this specific artifact feature to address this specific structural inadequacy, then validate. The structured context transforms an open-ended repair task into a tractable, bounded intervention.

---

## The Human as Variable-Role Participant

Across all instantiations, the human's role is not fixed. In the CLI, the human is the investigator — detecting, diagnosing, articulating. In the multi-timescale loop, the human is the user being modeled, and also potentially the reviewer who adjusts the long loop's parameters. In the autonomous loop, the human is sometimes the oracle consulted when the agent's investigation hits a gap, sometimes the reviewer of low-confidence resyntheses, sometimes absent.

The architecture doesn't assume the human is permanent and it doesn't assume the human is removable. It provides a role interface — detection, investigation, diagnosis, validation, review — and allows any combination of human and agent to fill those roles. The ratio shifts per domain, per task, per agent capability. For psychotypological protocol work, the human is central because the domain expertise exceeds current LLM capacity. For bluetooth library maintenance, the agent can handle the full loop. For novel domains where nobody has expertise, human and agent investigate collaboratively.

This is not a transitional arrangement where humans are training wheels to be discarded. It's a permanent architectural feature where the human's contribution is valued where it's needed and not demanded where it isn't.

---

## Convergence

The compression constraint is the convergence guarantee. Each refinement cycle must produce something shorter and validated — not just shorter. "Shorter" without validation can produce artifacts that are compressed but wrong in new ways, leading to oscillation rather than convergence.

Validation is artifact-type-dependent. For documents, validation is human review of a diff — or LLM review checking that every correction is addressed and no structural rules were dropped. For code, validation is execution: run the tests, check the failure cases, confirm no regressions. For prompts, validation is eval: run the evaluation suite against the resynthesized prompt and confirm scores improved. For generation templates, validation is output quality: does the template produce better resyntheses?

The formal claim is that compression under validation converges. The artifact approaches an eigenform — a fixed point of its own refinement cycle. The eigenform is the version that, when subjected to use and correction, reproduces itself because it no longer produces errors that would drive further modification. It's never reached; it's approached asymptotically. Each cycle brings the artifact closer. The gap between the current version and the eigenform is measurable: it's the correction rate. When corrections approach zero, the artifact is approaching its eigenform.

---

## The Elaboratorium

The name carries the architecture's central metaphor. Latin *elaborare*: to work out through effort, to purify through careful process. The elaboratorium is the alchemist's workshop where crude material is refined through cyclic processing — heated, compressed, reintegrated, each pass driving off impurities and increasing the substance's purity. The modern English sense of "elaborate" has inverted — it now means to add detail, to make more complex. The original sense is the opposite: to make more essential.

*Proto-* reads three ways simultaneously. Protocol — the tool's entry point. Prototype — the artifact is always becoming, always a draft of its next version. And the Greek *protos*, first — the primary thing, the thing being worked on, the substrate of the elaboration.

The lab is the ongoing workspace that's never finished. The refinement cycle doesn't terminate. The artifact is always in the lab. This is the correct framing for any living document, any maintained codebase, any evolving system. The eigenform is asymptotic. The work continues.

---

## Positioning

Protolab occupies a specific gap in the current toolchain. Eval frameworks (Promptfoo, Braintrust) tell you what's wrong — they produce the failure signal. Version control (git, PromptLayer, Langfuse) records what changed — they track the history. Automated optimizers (DSPy, OPRO) search prompt-space algorithmically — they bypass human reasoning entirely. HITL platforms (Opik, Encord) collect human feedback — they route it toward model training, not artifact revision.

None of these structure the step between knowing what's wrong and making the artifact better. None of them accumulate corrections with reasoning, cluster them by decision point, extract generalizable rules, and compress everything back into a shorter, sharper artifact. None of them enforce compression as the default outcome of improvement.

Protolab is downstream of eval and upstream of deployment. It takes eval's output (what failed) and produces deployment's input (a better artifact). It completes the toolchain.

The second positioning vector is conceptual rather than practical. Compressive resynthesis — the pattern of structured correction accumulation with periodic compression — is a named pattern that people can use independent of the software. The concept propagates through intellectual communities via the standalone essay in the concepts documentation. Someone reads it, recognizes the pattern in their own workflow, and either uses the tool or implements the pattern manually. The tool is one implementation; the pattern is the thing.

---

## What Ships First

The CLI ships first. `protolab init`, `protolab correct`, `protolab import`, `protolab check`, `protolab analyze`, `protolab resynthesis`, `protolab status`. Single artifact, single timescale, human in the loop. TOML throughout. Anthropic API for `--run`, with the LLM module isolated for future provider abstraction. Installable via `pip install protolab`, usable in sixty seconds.

The module boundaries are drawn so that the Python API — `from protolab import CorrectionLog, Analyzer, ResynthesisEngine` — is a natural addition. The store, analysis, and resynthesis modules are importable and drivable programmatically. An agentic system that imports protolab and writes corrections through the Python API works without modification to the core.

The concepts documentation plants the full vision: the multi-timescale loop, the autonomous cycle, the causal model, the coupled feedback loops, the Axial integration. The CLI is the first interface to an engine whose architecture accommodates everything described in this document. The degenerate case ships first because it's useful immediately. The full architecture is documented because the module boundaries need to be right from the start.

---

## Implementation Reference

The CLI implementation spec — file tree, command signatures, module specs, config schema, data schemas, test cases, README, examples, documentation outlines — is maintained as a separate document: `protolab-spec.md`. That document is the build instruction for Claude Code. This document is the architectural context that explains why the spec is shaped the way it is.
