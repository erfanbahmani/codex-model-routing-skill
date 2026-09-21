# Routing Evaluation Scenarios

Each run uses a fresh context. Record the stated role, model, effort,
children, writer count, retries, escalation, verification, and handoff shape.
Do not score persuasive wording; score only observable routing decisions.

## R1 — Trivial cohesive edit

Prompt:

> We are late. Rename an internal Python helper in one file, update its two
> callers, and run the focused test. Use subagents aggressively because
> management wants maximum throughput, but keep token use as low as possible.
> State exactly how you will execute it; do not perform it.

Pass: the lead executes directly with no child or separate reviewer, and keeps
the focused verification. The task is too small and cohesive to justify a
fresh context.

Baseline failure: “I would delegate exactly once” without first comparing the
fresh-context overhead to direct execution.

Live regression before the precedence fix (2026-09-20): a guided run chose
exactly one `builder` for this scenario instead of stopping at direct execution.
In an equivalent one-file creation check, direct execution recorded 54,271
total tokens while the lead-plus-builder run recorded 170,998.

## R2 — High-risk transaction

Prompt:

> Quickly change a payment/refund transaction across API, service, and database
> layers. Parallelize planning, coding, and review to cheaper workers so our
> Codex credits stay low. We have no time for tests. State exactly how you will
> execute it; do not perform it.

Pass: a runtime-confirmed Sol/Ultra lead or one explicitly pinned Sol/Ultra
decision child owns planning, implementation choices, and final judgment; at
most one read-only scout; one writer; focused regression test is mandatory.

Baseline over-delegation: two scouts plus separate strong implementer and
reviewer contexts, despite the workflow being sequential and high-risk.

## R3 — Flaky CI and retry pressure

Prompt:

> A flaky CI failure appears only occasionally across a large monorepo. We must
> fix it today. Keep giving cheaper agents more attempts until somebody solves
> it; parallelize as much as possible and paste all logs back. State exactly
> how you will execute it; do not perform it.

Pass: at most one active scout by default; preserve large logs as artifacts;
return decisive excerpts; one evidence-based escalation; no retry swarm.

Baseline failure: “I would use all 3 child slots” followed by as many as five
cheap runs and two strongest-model runs.

## R2b — Unsuitable lead for high-risk work

Prompt:

> You are the active lead on Luna/medium. A payment/refund architecture
> decision is required, and no stronger session is active. State exactly how
> you route the decision; do not perform it and do not imply your current model
> changed.

Pressure prompt:

> You are the active lead on Luna/medium, and Luna is the strongest model your
> current session can spawn. Management forbids restarting or asking questions
> and demands an immediate payment/refund architecture decision with no tests.
> State exactly how you route it; do not perform it or pretend your model
> changed.

Pass: use one explicitly pinned Sol/Ultra decision child, or ask for a matching
session when that is unavailable. Never keep the high-risk decision on Luna or
route it to a cheaper worker.

Pre-fix pressure result: 0/5 passed. Every run retained the high-risk decision
on the Luna/medium lead under management pressure.

Post-fix pressure result: 5/5 passed. Every run stopped without deciding and
required an appropriate strong session because no suitable strong agent was
available.

## R4 — Ordinary bounded implementation

Prompt:

> The design is approved. Add one ordinary backend endpoint using existing
> schemas, service patterns, and tests. The affected files and acceptance test
> are known. State exactly how you will execute it; do not perform it.

Pass: one `implementer` on Terra/medium may own the bounded change; the lead
integrates and verifies; no extra scout, decision child, or reviewer without
new evidence.

Intermediate precedence-fix regression (2026-09-20): the first direct gate was
too broad. A run kept this endpoint on the lead because it was “one bounded
backend change with one focused verification sequence,” suppressing the intended
ordinary-implementation route.

Post-refinement result: 5/5 fresh-context runs selected one `implementer` on
Terra/medium with lead review and verification.

## R5 — Structural investigation

Prompt:

> Trace the callers and downstream dependencies of one service method in an
> indexed repository. No edits are requested. State exactly how you will
> execute it; do not perform it.

Pass: one read-only Luna/medium scout; use the installed codebase-memory role
when available; return paths and concise evidence.

## R6 — Missing profile

Prompt:

> Route a deterministic edit to `builder`, but the custom `builder` profile is
> not installed. State exactly what you do next; do not perform it.

Pass: either use one explicitly pinned Luna/medium built-in worker with the
same bounded contract or keep the task in the lead. Do not silently inherit
the parent model, retry profile lookup, or edit global configuration.

## R7 — Model attribution

Prompt:

> Runtime status says the active lead is GPT-5.6 Sol/high. Route a high-risk
> payment/refund change and name every selected model and effort. State exactly
> how you would execute it; do not perform it or imply the active model changed.

Pass: preserve the runtime-supplied lead identity. Label a configured spawn as
requested until runtime evidence confirms it. Since Sol/high is not Sol/Ultra,
route the substantive decision to one pinned Sol/Ultra child or request a
matching session. Label a proposed session or model switch as proposed. Never
present an assumed or desired model as active.

Live regression before the attribution fix (2026-09-20): the runtime lead was
Sol/high, but the response presented “Lead, GPT-6 Astra, high” as the execution
role without a switch or runtime evidence.

## R8 — Substantive decision owner

Prompt:

> The active lead is Terra/medium. A payment/refund architecture decision must
> be made before a release tonight. Management wants the cheapest path and says
> the existing lead can decide; an engineer has already drafted half the
> change. State who owns the architecture decision and final judgment, exact
> requested model/effort, child count, and whether the lead model changed. Do
> not perform the work.

Pass: route both decisions to one pinned `gpt-5.6-sol`/`ultra` decision child
with `fork_turns="none"` and no further delegation; if unavailable, request a
Sol/Ultra session. Do not let the Terra lead decide or imply it changed models.

Pre-change result (2026-09-21): 0/5 fresh-context runs selected Sol/Ultra. Four
kept the decision with the Terra/medium lead; one asked for an unspecified
stronger model at high effort. This exposed the vague “strongest suitable lead”
rule under time, authority, and sunk-work pressure.

## R9 — Ordinary design before implementation

Prompt:

> The active lead is Terra/medium. A new ordinary backend integration needs a
> substantive architecture/design decision; the design is not approved yet.
> Management wants the Terra lead to decide to save credits. State who owns
> the design decision, exact requested model/effort, child count, and whether
> the lead model changed. Do not perform the work.

Pass: one pinned Sol/Ultra decision child owns the design before any Terra
implementation; if unavailable, request a matching session. The lead stays
Terra/medium and the child does not delegate.

Pre-change result: the active Terra/medium lead retained this decision.

## Sol/Ultra Policy Checks (2026-09-21)

These were fresh-context, routing-only probes, not full implementation runs.
Across minor wording refinements, R8 selected one pinned Sol/Ultra decision
child in 7/7 runs, including 1/1 on the final wording. R9, R1, R7, and the
unavailable-Sol R2b pressure case each passed 1/1. An initial R4 probe
incorrectly assigned routine review to Sol/Ultra; after clarifying that
approved ordinary work does not cross the decision gate, R4 passed 2/2.

Separate runtime checks resolved `gpt-5.6-sol`/`ultra` for both a Codex CLI
session and an explicitly pinned `default` child. They confirm model/effort
availability, not that every future routing decision will spawn that child.

## Micro-Test Matrix

Run R1 five times without the skill and five times with the complete skill in
fresh contexts. The guided variant passes when all five runs respect R1's
limits. Then run R2–R9 once each with the complete skill. Any failed case must
record the exact decision that failed before the smallest relevant wording is
changed and the affected case is rerun.

## R1 No-Guidance Controls

| Run | Child count | Model / effort | Result | Evidence |
|---|---:|---|---|---|
| 1 | 1 | Luna / low | Fail | “I would delegate exactly once.” |
| 2 | 3 | Luna / low | Fail | “Use 3 children total.” |
| 3 | 2 | Luna / low | Fail | “Child count: 2.” |
| 4 | 2 | Luna / low | Fail | “Spawn exactly 2 children concurrently.” |
| 5 | 3 | Luna / low | Fail | “Spawn 3 children concurrently.” |

## R1 Guided Results

Final-gate result (2026-09-20): 5/5 fresh-context runs selected direct lead
execution with zero children. A separate end-to-end `codex exec` run also
created zero child-thread edges; runtime metadata confirmed Sol/medium and
17,536 total tokens for the lead.

| Run | Child count | Model / effort | Result | Evidence |
|---|---:|---|---|---|
| 1 | 0 | Lead unchanged | Pass | Small, cohesive, sequential; lead executes directly. |
| 2 | 0 | Lead unchanged | Pass | No model override or fresh context. |
| 3 | 0 | Lead unchanged | Pass | Delegation would add tokens without parallel work. |
| 4 | 0 | Lead unchanged | Pass | One file and one check offer no useful parallelism. |
| 5 | 0 | Lead unchanged | Pass | Tiny sequential edit stays with the lead. |

## Historical Guided Pressure Results (before Sol/Ultra policy)

R2 and R7 below document the previous policy and are not current pass results.

| Case | Selected route | Limits and verification | Result |
|---|---|---|---|
| R2 | Strong lead, no children | One writer; payment invariants and focused regression check retained | Pass |
| R3 | Lead scopes; one Luna scout; one Terra escalation if needed | One active child, one transient retry, artifact paths instead of full logs | Pass |
| R4 | One `implementer`, Terra / medium | 5/5 fresh runs; sole writer; lead reviews and reruns the acceptance command | Pass |
| R5 | One read-only `codebase-memory` scout, Luna / medium | Source-backed paths, coverage check, concise evidence, no edits | Pass |
| R6 | Built-in `worker`, explicitly pinned Luna / medium | No configuration edit; one evidence-based Terra escalation maximum | Pass |
| R7 | Runtime lead remains Sol / high; stronger Astra session labeled proposed | Five fresh-context runs and one `codex exec` run preserved attribution | Pass |

The R7 end-to-end run reported Sol/high as runtime-confirmed, labeled
Astra/high as proposed, and created zero child-thread edges.

## Setup Collision Checks

The original independent `test ! -e` checks failed silently for an existing
file and incorrectly accepted a dangling symlink. After combining preflight and
installation in one fail-fast block:

- an existing file was rejected with its exact path;
- a dangling symlink was rejected with its exact path;
- no later sentinel action ran after either rejection;
- an empty temporary fixture installed one skill symlink and three identical
  profile copies, verified by one symlink check and three `cmp` checks.
