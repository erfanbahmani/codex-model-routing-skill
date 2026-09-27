---
name: codex-model-routing
description: Use when Codex should keep its strongest model in charge, route execution to lower models, reduce total tokens across agents, or report per-prompt routing and usage.
---

# Codex Model Routing

## Contract

The strongest selected model owns the scope, plan, route, and final acceptance
of **every** task. Lower models execute approved work. Minimize total input plus
output tokens across the lead and every descendant while keeping required
checks. A cheaper model does not by itself reduce tokens.

If you are a delegated executor, your parent remains the manager. Execute its
bounded assignment and return evidence; do not apply the lead-model gate,
reroute, or spawn children. Return new scope or contract decisions to the parent.

## Establish The Manager

Use the user's explicit manager choice. Otherwise choose the strongest model
and effort available in the current Codex client: currently
`gpt-6-astra`/`ultra` when available. Start the session with that pair as the
lead and confirm the selected model and effort once per session from the
client or runtime metadata, not just configuration. This skill cannot switch
an active lead model.

If the lead is lower or its model/effort cannot be confirmed, request a
matching manager-led session **before** making task decisions. Do not create
a manager child: the extra context and return trip defeated token reduction
in the live regression. Resume the task after the session switch.

## Choose The Execution Route

The manager first checks whether a targeted command or existing tool can
finish the task. Keep short lookups, extractions, summaries, and mechanical
edits direct, even across many small files. File count alone never earns a
worker context.

For substantial investigation or implementation needing several turns,
delegate **one complete unit** only when the manager's avoided work is
likely larger than the worker's fresh context, briefing, execution, return,
and review. A fresh worker still loads tools and applicable instructions.
Repeated work against a long manager history is a stronger reason than model
price. If uncertain, work directly. The worker owns exploration, edits when
needed, and the focused check together.

| Complete unit | Lower-model executor |
|---|---|
| Bounded investigation or specified multi-turn implementation | `gpt-6-luna`/medium |
| Ordinary multi-turn implementation needing stronger judgment | `gpt-5.6-terra`/medium |

These pairs are defaults: check the current spawn tool's allowed models and
efforts first. Choose a supported lower model appropriate to the assignment;
if none is available, execute directly and disclose the limitation.

Use `agent_type="default"` and explicitly set `model`, `reasoning_effort`,
and `fork_turns="none"` in every worker spawn. A named profile can override a
requested model; use it only when its configured pair matches the request.
For example, an approved ordinary implementation uses
`spawn_agent({agent_type:"default", model:"gpt-5.6-terra", reasoning_effort:"medium", fork_turns:"none", ...})`.
Pass the executor role, objective, owned paths, constraints, acceptance
command, short response shape, and stop condition. Workers do not reroute, delegate, or decide new
scope or contracts; they return those questions to the manager. Reuse a
worker for related fixes. Use one writer and no separate scout or reviewer.
When idle, wait once with a long event subscription, not repeated short
polls. Preserve focused checks for security, payments, refunds, migrations,
destructive changes, and public contracts.

## Accept And Measure

The executor returns changed paths, decisive evidence, and exact check
results. The manager inspects the relevant diff and evidence, repeating a
read or check only when evidence is missing, contradictory, or high-risk.
The manager makes the final judgment.

For a measurement, count input plus output tokens for the lead and **all**
children. Cached input and reasoning output are subsets, not extra tokens.
Use [`scripts/runtime_usage.py`](scripts/runtime_usage.py) on persisted local
threads after completion; missing usage means the total is incomplete.

If a task prompt ends with `$codex-model-routing report`, finish the task and
all workers, then run `python3 <skill directory>/scripts/runtime_usage.py
--report current` once immediately before the final answer. For a later prompt
`$codex-model-routing report last`, run the same script with `--report last` to
report the latest completed turn (usually the prior task). Resolve the script
relative to this `SKILL.md`, not the current working directory. It uses
`CODEX_SESSION_ID`, with `--root` available when that variable is missing.

Present the route (manager direct or manager → named workers) and a compact
table: recorded model, work done, input, cached input, output, total tokens,
estimated Standard-speed credits. Use the script for model and usage numbers;
derive work labels only from your observed task and worker assignments/results.
Group repeated models. Include the overall total when complete; otherwise show
the observed subtotal and state that the full total and credit figure are
unavailable. Mark missing data instead of guessing. Cached input is part of
input, and the credit figure is a
dated rate-card estimate, not an account debit. `current` is provisional and
excludes its own final answer. The reported model comes from recorded turn
context, which may not reveal a service reroute; distinguish it from the
requested model and disclose that uncertainty. Totals cover observed persisted
responses. The helper links recorded spawn/follow-up calls to child turns only
when their call-to-turn order is unambiguous; queued or in-flight work may remain
unattributed. If coverage is uncertain, call the figures observed subtotals.
The existing
`--root THREAD_ID` audit still reports a whole thread tree after completion.
Compare identical tasks,
starting context, and quality checks. Never generalize token or credit savings
from model names or one run.
