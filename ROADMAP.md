# Protolab Roadmap

## v0.1.x — Current

Multi-file protocol support via flat assembly: glob patterns, ordered
concatenation, section markers. Single-file configs remain unchanged.

Config:
```toml
[protocol]
paths = ["instructions/*.md", "system-prompt.md"]
```

## Future

### Agentic CAPA — cross-agent failure learning

Generalize Protolab from manual correction-compression for one protocol into a provider-neutral corrective and preventive action loop for agentic systems. Conversation and execution records from Claude Code, Codex, ChatGPT, Antigravity, and future harnesses become evidence for recurring friction, mistakes, and failure modes; independent reviewers annotate that evidence; clusters become candidate systemic causes; and validated interventions improve the control surfaces that produced the failures.

This is a design program, not an implementation commitment yet. Gate zero is the unfinished prior-art synthesis and advisory-panel verdict: reconcile quality-management CAPA, incident/postmortem systems, LLM observability and evaluation, trajectory analysis, prompt/program optimization, reflection/self-improvement research, and conversation-memory systems by mechanism rather than terminology. Record what Protolab should extend, compose, or deliberately supersede.

Candidate acceptance criteria to adjudicate during that design pass:

- Preserve raw source records immutably and normalize them into a versioned provider-neutral event model without treating lossy summaries as evidence.
- Make every annotation append-only and provenance-bearing: reviewer/model identity, prompt and rubric version, cited event spans, confidence, competing hypotheses, and review disposition.
- Separate symptom, failure mode, contributing condition, root-cause hypothesis, corrective action, preventive action, and validation result instead of collapsing them into one free-form “lesson.”
- Use cross-provider review to reduce self-rationalization, while measuring reviewer agreement, correlated model blind spots, and contamination from shared prompts or training lineage.
- Cluster only after preserving case-level evidence; support taxonomy-first, embedding-assisted, and causal/structural views without allowing any clusterer to become the sole authority on what a failure means.
- Promote interventions through an explicit control loop: proposal → scoped target → independent evaluation → deliberately false mutation/regression challenge → canary or reversible rollout → measured effect → retain, revise, or revert.
- Route interventions to the right control surface—skill, rule, prompt, hook, tool, code, documentation, or model choice—and prevent an annotation store from becoming another additive rule graveyard.
- Keep privacy, secrets, personal-data boundaries, retention, redaction, and local-versus-remote model execution visible in the data model rather than bolted on after ingestion.
- Define success in observable terms: lower recurrence and friction on held-out future work without merely shortening prompts, increasing reviewer agreement, or optimizing the same model that proposed the intervention.

Open architecture forks for the advisory pass:

- The primary unit of analysis: whole conversation, task/episode, tool-action trajectory, failure event, or a layered model that preserves all four.
- The review topology: every model reviews every other model, sampled reciprocal review, specialist judges, or ensemble review triggered by risk and novelty.
- The canonical store boundary: Protolab-owned event and CAPA storage versus an analytical layer over Octopus's conversation archive and provenance spine.
- The intervention authority boundary: advisory-only proposals, automatic low-risk changes with rollback, or risk-tiered promotion requiring human approval for durable behavioral changes.
- The synthesis target: repair individual protocols, improve shared skills/rules, modify tools and code, or maintain a causal portfolio spanning all of them.

Closure evidence for this track must come from a replayable corpus with known seeded failure classes, held-out future sessions, cross-review agreement and disagreement records, intervention diffs, recurrence measurements, rollback proof, and adversarial mutations that the evaluator rejects. A self-authored retrospective or a shorter prompt is not closure evidence.

### Protocol manifest / module graph

A top-level manifest declares protocol modules, their roles (core /
extension / override), and relationships between them. Corrections and
rules carry module attribution. Resynthesis can propagate changes across
linked modules.

Motivation: as protocols grow, isolation between subjects breaks down.
A rule in `auth.md` may govern behavior described in `session.md`. The
graph model makes those relationships explicit and queryable.

Design entry point: `PROTOCOL.toml` at repo root with `[[modules]]`
entries declaring roles and inter-module links.
