# Codex Model Routing

> The best subagent is sometimes no subagent.

**Codex Model Routing** is a small skill for deciding who should do the work: the current lead, a read-only scout, or one bounded implementation agent. It aims for *verified work per credit*, not the lowest-looking model name or the most parallel threads.

```text
Is it high risk?        → Keep the decision with a suitable strong lead.
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
| One independent research or code-tracing question | Read-only `scout` · Luna / medium |
| Substantial, fully specified repetitive edit | `builder` · Luna / medium |
| Approved ordinary implementation across known files or layers | `implementer` · Terra / medium |
| Payment, security, migrations, public contracts, and other high-risk decisions | Strongest suitable lead; at most one read-only scout |

The lead stays responsible for reviewing delegated work and running the relevant verification. A requested child model is **not** proof of the model that actually ran, and the skill cannot silently switch the active lead model. See the exact rules in [SKILL.md](SKILL.md).

## Get started

1. Follow [the setup guide](references/setup.md) to install the skill and its three custom-agent profiles. The source and profiles are separate; installation does not edit your existing Codex configuration.
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

This reads local Codex state in read-only mode. It reports usage, **not** money saved; compare complete runs before drawing a credit or latency conclusion.

The routing scenarios and observed results live in [evals/scenarios.md](evals/scenarios.md). In the latest checks, tiny edits stayed direct in 5/5 fresh runs, ordinary endpoint work selected one implementer in 5/5, and model attribution stayed accurate in 5/5. A separate real Codex CLI tiny-edit run created zero child threads. These are routing checks, not a promise of savings on every task.

## Project files

- [SKILL.md](SKILL.md) — routing policy and dispatch contract
- [agent-profiles/](agent-profiles/) — optional `scout`, `builder`, and `implementer` profiles
- [references/setup.md](references/setup.md) — installation and verification
- [evals/scenarios.md](evals/scenarios.md) — pressure tests and results
- [scripts/runtime_usage.py](scripts/runtime_usage.py) — local runtime-model and token audit

Run the small audit-script test with `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
