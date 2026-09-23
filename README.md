# Codex Model Routing

> Strong decisions. Small execution contexts. Fewer total tokens when the work earns a handoff.

**Codex Model Routing** keeps the strongest available model in charge of every task and gives bounded execution to a lower model only when the handoff is likely to reduce **total tokens**. The default manager is `gpt-6-astra` at `ultra`; you can choose a different manager pair for your account.

```text
Manager lead?          → Own scope, route, and final acceptance.
Lower-model lead?      → Switch to the manager model before task decisions.
One command or tiny edit? → Manager handles it directly.
Large implementation?  → One lower-model worker owns exploration, edit, check.
After the handoff      → Manager reads decisive evidence and accepts the result.
```

## Why it exists

A child starts a fresh context. In our first seven paired runs, the skill used more total tokens in five and failed to pin the strongest decision child twice. A follow-up live run pinned Astra/Ultra correctly, but a lower lead still added a scout and repeated waits. This revision requires a strongest-model lead, sends only whole jobs to one lower worker, and keeps one-step jobs direct. It does not promise savings on every task; measure complete runs before claiming them.

| Work | Route |
| --- | --- |
| Scope, plan, route, final acceptance | Astra / Ultra manager, or your selected strongest available pair |
| One small cohesive action | Manager directly; no worker context |
| Short lookup, extraction, summary, or mechanical edit | Manager uses a targeted tool directly |
| Substantial bounded investigation | Luna / medium worker when a fresh context is expected to reduce total tokens |
| Complete, specified multi-turn implementation | Luna / medium worker |
| Complete ordinary implementation needing more judgment | Terra / medium worker |
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

The current routing scenarios and live follow-up results live in [evals/scenarios.md](evals/scenarios.md). With the same Astra/Ultra lead and 24-document prompt, the direct-first revision used 50,110 tokens versus 155,435 when the preceding wording delegated; both answers were correct. This single pair verifies that route, not a general savings rate. More task types and repeated pairs are needed before a broad claim.

A later matched implementation trial used 194,422 tokens with the skill versus 312,921 without it, with both passing independent checks. The skill avoided an extra review agent; this does not establish savings from lower-model coding. Separately, a live Luna/medium executor completed the repository's accounting fix and checks. See the evaluation record for runtime models, thread IDs, and excluded attempts.

## Project files

- [SKILL.md](SKILL.md) — routing policy and dispatch contract
- [agent-profiles/](agent-profiles/) — optional `scout`, `builder`, and `implementer` profiles
- [references/setup.md](references/setup.md) — installation and verification
- [evals/scenarios.md](evals/scenarios.md) — pressure tests and results
- [scripts/runtime_usage.py](scripts/runtime_usage.py) — local runtime-model and token audit

Run the small audit-script test with `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
