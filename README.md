# Codex Model Routing

> The best subagent is sometimes no subagent.

**Codex Model Routing** is a small skill for deciding who should do the work: the current lead, a read-only scout, or one bounded implementation agent. It aims for *verified work per credit*, not the lowest-looking model name or the most parallel threads.

```text
Substantive decision?   → Sol / Ultra lead or one pinned decision child.
Is it high risk?        → One writer and focused checks.
Is it small and local?  → Do it directly. Zero children.
Is there a bounded, independent unit?
                       → Delegate once, then verify in the lead.
Otherwise              → Keep it in the lead.
```

## Why it exists

A cheaper child starts with a fresh context. For a tiny edit, that overhead can cost more tokens than doing the edit directly. This skill makes **direct execution the default**, reserves delegation for work that earns its context, and keeps safety checks in place even under “move fast” pressure.

| Work | Route |
| --- | --- |
| One small local edit and a focused check | Lead, no child |
| Substantive architecture, planning, or final judgment | Sol / Ultra lead, or one pinned non-writing `gpt-5.6-sol` / `ultra` decision child |
| One independent research or code-tracing question | Read-only `scout` · Luna / medium |
| Substantial, fully specified repetitive edit | `builder` · Luna / medium |
| Approved ordinary implementation across known files or layers | `implementer` · Terra / medium |
| Payment, security, migrations, public contracts, and other high-risk work | Sol / Ultra owns decisions; one writer and focused checks |

The lead reviews execution and runs the relevant verification; Sol / Ultra makes final judgments on substantive decisions, not routine reviews of approved implementation. A requested child model is **not** proof of the model that actually ran, and the skill cannot silently switch the active lead model. If Sol / Ultra is unavailable, decision work waits for a matching session; `max` is not a substitute for `ultra`. See the exact rules in [SKILL.md](SKILL.md).

## Requirements

- A current, signed-in [Codex client](https://learn.chatgpt.com/docs/codex/cli) with skills and subagents available. Access to `gpt-5.6-sol` at `ultra` is required for substantive decisions; the optional profiles use `gpt-5.6-luna` and `gpt-5.6-terra`. Model access depends on your account and client and cannot be installed by this repository. See the [Codex model guide](https://learn.chatgpt.com/docs/models) and [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- No pip, npm, or MCP dependency for core routing. `codebase-memory` is used only when already available. The optional local usage audit and tests need Python 3.10+ and only its standard library.
- The setup commands use a POSIX shell (Linux, macOS, or WSL).

## Get started

1. Follow [the setup guide](references/setup.md) to install the skill. Its three custom-agent profiles are optional; installation does not edit your existing Codex configuration.
2. Reload Codex, then invoke it explicitly in a Codex session:

   ```text
   Use $codex-model-routing to route this task. Explain whether you will work directly or delegate, and how you will verify the result.
   ```

Codex can also select a skill when a task matches its description. The [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills) explains skill discovery and `$` invocation; its [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents) covers custom agent files and model settings.

## Check what actually happened

For a persisted local Codex thread, inspect the resolved lead and direct-child models, reasoning effort, and total tokens:

```bash
python3 scripts/runtime_usage.py --root YOUR_THREAD_ID
```

This optional command reads local Codex SQLite state in read-only mode. It uses `CODEX_SQLITE_HOME` or `CODEX_HOME` when set; for a custom `sqlite_home` configuration, pass `--db /path/to/state_N.sqlite`. If Codex has no persisted local state, there is nothing to audit. It reports usage, **not** money saved; compare complete runs before drawing a credit or latency conclusion.

The routing scenarios and observed results live in [evals/scenarios.md](evals/scenarios.md). The Sol / Ultra decision policy passed seven fresh payment/refund routing probes across wording refinements; final wording also kept approved endpoint work on the ordinary Terra route and stopped a high-risk decision when Sol / Ultra was unavailable. Separate runtime checks confirmed the exact model/effort in a Codex session and a pinned child. These checks are not a promise of savings or automatic model selection on every task.

## Project files

- [SKILL.md](SKILL.md) — routing policy and dispatch contract
- [agent-profiles/](agent-profiles/) — optional `scout`, `builder`, and `implementer` profiles
- [references/setup.md](references/setup.md) — installation and verification
- [evals/scenarios.md](evals/scenarios.md) — pressure tests and results
- [scripts/runtime_usage.py](scripts/runtime_usage.py) — local runtime-model and token audit

Run the small audit-script test with `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
