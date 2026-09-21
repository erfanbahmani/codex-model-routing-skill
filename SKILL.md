---
name: codex-model-routing
description: Use when a Codex task raises model, reasoning effort, subagent, delegation, token, credit, latency, or cost-per-result choices.
---

# Codex Model Routing

## Principle

Optimize verified work per credit. A cheaper child can reduce expensive-model
work while increasing total tokens. Delegate only when a bounded unit earns its
fresh context; never spawn solely to reduce tokens.

## Decide In Order

1. **Decision gate.** Substantive architecture and planning decisions,
   high-risk implementation choices, and final judgments on those decisions belong to
   `gpt-5.6-sol`/`ultra`. A runtime-confirmed Sol/Ultra lead decides directly;
   otherwise use one pinned `default` decision child with
   `fork_turns="none"`, instructed to make decisions only, never edit or
   delegate; use a read-only sandbox when available. Reuse it for final
   judgment. If Sol/Ultra is unavailable, request a matching session and stop
   decision work. Do not substitute `max` or imply the lead changed models.
   Approved ordinary implementation and tiny edits need no new decision owner.
2. **Safety gate.** Security, authentication, payments, refunds, migrations,
   concurrency, destructive operations, and public contracts require that
   decision owner, one writer, and focused checks. One read-only scout may
   gather evidence before the decision.
3. **Direct gate.** The lead executes and stops routing only when all work is a
   small local change, adds no cross-file or cross-layer behavior, needs no
   independent research, and has one focused check. This wins even when the edit
   is deterministic. Renaming one helper and its callers is direct work.
4. **Delegation gate.** Delegate only a unit that is independent of the lead and
   substantial enough to amortize a fresh context.

| Remaining task shape | Route |
|---|---|
| One independent read-heavy question | `scout`: Luna, medium, read-only |
| Substantial repetitive edit with a complete specification and objective check | `builder`: Luna, medium |
| Approved ordinary behavior spanning known files or layers | `implementer`: Terra, medium |
| No row clearly fits | Lead executes directly |

For structural repository exploration, use the installed codebase-memory role
when available and explicitly select Luna/medium; do not let it inherit an
expensive parent by accident.

## Dispatch Contract

Each child receives: objective; owned paths; constraints and evidence;
acceptance command; response shape; stop condition.

- Default to zero children, at most one active child, and one writer. Children
  never delegate. Aggressive delegation requests bypass no gate.
- Use `fork_turns="none"` for decision children. For other model/effort
  overrides, use `none` or the smallest bounded fork; full history inherits the parent.
- Reuse a child for a closely related follow-up.
- Retry one transient failure. After one substantive failure, add evidence and
  escalate one tier once; then the lead owns execution. Decision work still
  obeys the decision gate.
- For non-decision work, if a named profile is unavailable, use one explicitly
  pinned equivalent or keep the task in the lead. Never edit configuration
  during the task.
- Store authorized large logs as artifacts; return decisive excerpts and paths.
- Never remove tests, validation, or safety checks to save tokens or credits.

## Completion

The lead inspects delegated work and verifies execution. For work crossing the
decision gate, its Sol/Ultra owner makes the final substantive judgment;
routine implementation review stays with the lead. Report the route, exact checks,
and requested child model/effort. Call a model or effort actual only when runtime
metadata confirms it; otherwise write `actual model/effort: unverified`. A
desired switch remains `proposed`. Never infer the lead model from “strongest,”
a profile, or the catalog. Separate credits from total tokens; infer neither.
For persisted local threads, verify with
[`scripts/runtime_usage.py`](scripts/runtime_usage.py).
