# Codex Model Routing

> Strong decisions. Selective handoffs. Measured outcomes.

**Codex Model Routing** keeps the strongest available model in charge of every task and gives bounded execution to a lower model only when the handoff is likely to reduce **total tokens**. The default manager is `gpt-6-astra` at `ultra`; you can choose a different manager pair for your account.

```text
Manager lead?          → Own scope, route, and final acceptance.
Lower-model lead?      → Switch to the manager model before task decisions.
One command or tiny edit? → Manager handles it directly.
Substantial multi-turn work? → Delegate one complete unit only when the handoff is justified.
After the handoff      → Manager reads decisive evidence and accepts the result.
```

## Why it exists

A child starts a fresh context. Early tests exposed over-delegation and model-pinning failures. This revision requires a strongest-model lead, sends only complete jobs to one lower worker when the handoff is justified, and keeps short work direct. The current benchmark results below show why a cheaper worker does not automatically mean fewer tokens or equivalent quality.

| Work | Route |
| --- | --- |
| Scope, plan, route, final acceptance | Astra / Ultra manager, or your selected strongest available pair |
| One small cohesive action | Manager directly; no worker context |
| Short lookup, extraction, summary, or mechanical edit | Manager uses a targeted tool directly |
| Substantial bounded investigation | Luna / medium worker when a fresh context is expected to reduce total tokens |
| Complete, specified multi-turn implementation | Luna / medium worker when delegation is justified |
| Complete ordinary implementation needing more judgment | Terra / medium worker when delegation is justified |
| High-risk work | Manager decides; one writer and focused checks |

The manager must be the lead. A lower-model lead must switch before decisions; delegated workers execute under their parent's management and do not repeat this gate. The skill cannot silently switch the active model. Worker spawns use the built-in `default` role with explicit model and effort chosen from the active tool's supported models, avoiding conflicting custom-profile settings. A requested worker model is **not** proof of the model that actually ran. See [SKILL.md](SKILL.md).

## Requirements

- A current, signed-in [Codex client](https://learn.chatgpt.com/docs/codex/cli) with skills and subagents available. Access to `gpt-6-astra` at `ultra` is needed for the default manager; if unavailable, select the strongest pair your account supports. The optional profiles use `gpt-6-luna` and `gpt-5.6-terra`; adjust them to supported models before installation. Model access depends on your account and client. See the [Codex model guide](https://learn.chatgpt.com/docs/models) and [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- No pip, npm, or MCP dependency for core routing. `codebase-memory` is used only when already available. The optional local usage audit and tests need Python 3.10+ and only its standard library.
- The setup commands use a POSIX shell (Linux, macOS, or WSL).

## Get started

1. Follow [the setup guide](references/setup.md) to install the skill. Its three custom-agent profiles are optional; installation does not edit your existing Codex configuration.
2. In Codex or Zed, select `gpt-6-astra` / `ultra` as the lead when available. If you choose a lower lead, the skill will ask for a matching manager-led session before decisions.
3. Reload Codex, then invoke it explicitly in a Codex session:

   ```text
   Use $codex-model-routing for this task. Keep the strongest model in charge, and choose the route with the fewest expected total tokens that preserves verification.
   ```

Codex can also select a skill when a task matches its description. The [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills) explains skill discovery and `$` invocation; its [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents) covers custom agent files and model settings.

## Check what actually happened

After a local Codex run finishes, inspect the lead and every descendant's persisted model, reasoning effort, and total tokens:

```bash
python3 scripts/runtime_usage.py --root YOUR_THREAD_ID
```

This optional command reads local Codex SQLite state in read-only mode. It uses `CODEX_SQLITE_HOME` or `CODEX_HOME` when set; for a custom `sqlite_home` configuration, pass `--db /path/to/state_N.sqlite`. Missing thread records or token usage make the total `incomplete`. If Codex has no persisted local state, there is nothing to audit. Thread metadata is not a per-request model history: use fresh, single-model threads for comparisons. It reports usage, **not** money saved; compare complete runs before drawing a credit or latency conclusion.

## Benchmark results

These are small, synthetic tests of the routing policy, **not** a general savings guarantee. The skill was supplied in test prompts; it was not installed on the device. Both campaigns counted the lead and every descendant, and all completed outputs passed their predeclared checks.

The [natural-routing retest](evals/live-routing-retest-2026-09-23.md) covered seven task types in 11 matched pairs with an Astra/ultra lead. Controls could delegate normally; the skill chose seven direct runs and four Luna/medium worker runs.

| Natural-routing test | Total tokens | Estimated Standard-speed credits |
| --- | ---: | ---: |
| Without skill | 2,841,526 | 218.604 |
| With skill | 2,813,604 | 109.182 |
| Change | **−0.98%** | **−50.05%** |

The seven direct treatment runs saved 671,952 tokens, but the four delegated runs added 644,030. Both repetitions of the graph bug and scheduler used more tokens with delegation; the modeled credit drop reflects the much lower Luna token rate, not lower token usage on those tasks.

A separate [forced-strategy comparison](evals/sol-manager-comparison-2026-09-23.md) used two implementation tasks, two runs per task and strategy. Managed arms were explicitly required to use one Luna worker, so this does **not** test the skill's natural route choice.

| Forced strategy (four runs each) | Total tokens | Estimated credits | Later missing-root bug check |
| --- | ---: | ---: | ---: |
| Sol direct | 789,757 | 18.715 | 2/2 passed |
| Sol → Luna | 1,961,251 | 14.533 | 0/2 passed |
| Astra → Luna | 2,558,922 | 59.197 | 1/2 passed |

Sol → Luna used **148.3% more tokens** than Sol direct despite **22.3% fewer modeled credits**. The later check was supplemental, not predeclared; its failures mean the lower credit estimate is not evidence of an equally correct bug fix. Credits were calculated from recorded model-specific input, cached input, and output using [OpenAI's Standard-speed Codex rate card](https://learn.chatgpt.com/docs/pricing) as of 26 September 2026. They are **not actual charges, subscription debits, or quota measurements**.

See the [full benchmark analysis (PDF)](evals/codex-model-routing-benchmark-2026-09-26.pdf), its [editable HTML source](evals/codex-model-routing-benchmark-2026-09-26.html), and [scenario notes](evals/scenarios.md) for methods, task-level data, limitations, and excluded runs.

## Project files

- [SKILL.md](SKILL.md) — routing policy and dispatch contract
- [agent-profiles/](agent-profiles/) — optional `scout`, `builder`, and `implementer` profiles
- [references/setup.md](references/setup.md) — installation and verification
- [evals/scenarios.md](evals/scenarios.md) — pressure tests and earlier results
- [evals/codex-model-routing-benchmark-2026-09-26.pdf](evals/codex-model-routing-benchmark-2026-09-26.pdf) — full token, credit, and correctness analysis
- [scripts/runtime_usage.py](scripts/runtime_usage.py) — local runtime-model and token audit

Run the small audit-script test with `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
