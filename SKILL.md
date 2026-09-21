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

1. **Safety gate.** Security, authentication, payments, refunds, migrations,
   concurrency, destructive operations, and public contracts stay with the
   strongest suitable lead. One independent read-only scout may gather evidence.
2. **Direct gate.** The lead executes and stops routing only when all work is a
   small local change, adds no cross-file or cross-layer behavior, needs no
   independent research, and has one focused check. This wins even when the edit
   is deterministic. Renaming one helper and its callers is direct work.
3. **Delegation gate.** Delegate only a unit that is independent of the lead and
   substantial enough to amortize a fresh context.

| Remaining task shape | Route |
|---|---|
| One independent read-heavy question | `scout`: Luna, medium, read-only |
| Substantial repetitive edit with a complete specification and objective check | `builder`: Luna, medium |
| Approved ordinary behavior spanning known files or layers | `implementer`: Terra, medium |
| No row clearly fits | Lead executes directly |

If the lead is unsuitable for a high-risk decision, use one pinned suitable
strong agent or request a stronger session. Never leave the decision with an
unsuitable lead or imply that its model changed.

For structural repository exploration, use the installed codebase-memory role
when available and explicitly select Luna/medium; do not let it inherit an
expensive parent by accident.

## Dispatch Contract

Each child receives: objective; owned paths; constraints and evidence;
acceptance command; response shape; stop condition.

- Default to zero children, at most one active child, and one writer. Children
  never delegate. Aggressive delegation requests bypass no gate.
- Use `fork_turns="none"` or the smallest bounded fork when overriding model or
  effort; a full-history fork inherits the parent.
- Reuse a child for a closely related follow-up.
- Retry one transient failure. After one substantive failure, add evidence and
  escalate one tier once; then the lead owns it.
- If a named profile is unavailable, use one explicitly pinned equivalent or
  keep the task in the lead. Never edit configuration during the task.
- Store authorized large logs as artifacts; return decisive excerpts and paths.
- Never remove tests, validation, or safety checks to save tokens or credits.

## Completion

The lead inspects delegated work and verifies it. Report the route, exact checks,
and requested child model/effort. Call a model or effort actual only when runtime
metadata confirms it; otherwise write `actual model/effort: unverified`. A
desired switch remains `proposed`. Never infer the lead model from “strongest,”
a profile, or the catalog. Separate credits from total tokens; infer neither.
For persisted local threads, verify with
[`scripts/runtime_usage.py`](scripts/runtime_usage.py).
