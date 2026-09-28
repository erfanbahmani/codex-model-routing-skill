# Codex Model Routing

> Strong decisions. Selective handoffs. Measured outcomes.

**Codex Model Routing** keeps your current Codex model in charge of every task and gives bounded execution to a lower model only when the handoff is likely to reduce **total tokens**. If you are using `gpt-6-sol`, Sol remains the manager even when Astra is available.

```text
Current session lead?  → Own scope, route, and final acceptance.
One command or tiny edit? → Manager handles it directly.
Substantial multi-turn work? → Delegate one complete unit only when the handoff is justified.
After the handoff      → Manager reads decisive evidence and accepts the result.
```

## Why it exists

A child starts a fresh context. Early tests exposed over-delegation and model-pinning failures. The current session model stays in charge, complete jobs go to one lower worker only when the handoff is justified, and short work stays direct. The benchmark results below show why a cheaper worker does not automatically mean fewer tokens or equivalent quality.

| Work | Route |
| --- | --- |
| Scope, plan, route, final acceptance | Current session model and effort (for example, Sol) |
| One small cohesive action | Manager directly; no worker context |
| Short lookup, extraction, summary, or mechanical edit | Manager uses a targeted tool directly |
| Substantial bounded investigation | Luna / medium worker when a fresh context is expected to reduce total tokens |
| Complete, specified multi-turn implementation | Luna / medium worker when delegation is justified |
| Complete ordinary implementation needing more judgment | Terra / medium worker when delegation is justified |
| High-risk work | Manager decides; one writer and focused checks |

The active session model is the manager; the skill never requires a switch to Astra or another stronger model. Delegated workers execute under their parent's management. Worker spawns use the built-in `default` role with explicit model and effort chosen from the active tool's supported models, avoiding conflicting custom-profile settings. A requested worker model is **not** proof of the model that actually ran. See [SKILL.md](SKILL.md).

## Requirements

- A current, signed-in [Codex client](https://learn.chatgpt.com/docs/codex/cli) with skills and subagents available. No Astra access is required: your active model remains the manager. The optional profiles use `gpt-6-luna` and `gpt-5.6-terra`; adjust them to supported models before installation. Model access depends on your account and client. See the [Codex model guide](https://learn.chatgpt.com/docs/models) and [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- No pip, npm, or MCP dependency for core routing. `codebase-memory` is used only when already available. The optional local usage audit and tests need Python 3.10+ and only its standard library.
- The setup commands use a POSIX shell (Linux, macOS, or WSL).

## Install from the Codex marketplace

With a Codex client that supports `codex plugin`, add this repository's
marketplace and install the plugin:

```bash
codex plugin marketplace add erfanbahmani/codex-model-routing-skill
codex plugin add codex-model-routing@erfanbahmani-skills
```

This GitHub-backed marketplace is separate from OpenAI's public Plugins Directory.
Start a new Codex session and check `/skills` for `codex-model-routing`.
This installs the packaged skill and report script; it does not require an MCP
server, pip package, or npm package. If your client does not support plugins,
use the standalone install below. Choose one method so Codex does not discover
two copies of the same skill.

## Alternative: install the standalone skill

In a POSIX shell (Linux, macOS, or WSL), clone the whole repository into your
personal [Codex skills directory](https://learn.chatgpt.com/docs/build-skills):

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/erfanbahmani/codex-model-routing-skill.git "$HOME/.agents/skills/codex-model-routing"
```

Start a new Codex session and check `/skills`; restart Codex if it does not
appear. If you already have a checkout, use the
[symlink setup](references/setup.md) instead. The three
[custom-agent profiles](references/setup.md#optional-agent-profiles) are optional.

Keep whichever model and effort you already selected, then use the skill in a prompt:

```text
Fix the failing login test. $codex-model-routing
```

The skill cannot change your lead model for you. Codex can also select it when
a task matches its description, but `$codex-model-routing` invokes it
explicitly. See [OpenAI's skill guide](https://learn.chatgpt.com/docs/build-skills)
and [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Check what actually happened

Append `$codex-model-routing report` to a task prompt to request its routing
report in the final answer:

```text
Fix the failing login test. $codex-model-routing report
```

That report is provisional: it cannot count its own final answer. To inspect
the latest completed prompt later, send a new prompt:

```text
$codex-model-routing report last
```

These are prompt suffixes, not terminal commands. The report shows the route,
what each model worked on, input/cached-input/output/total tokens, and estimated
Standard-speed credits—not actual charges. It uses recorded turn-context models,
which may not reveal service-side reroutes. Queued or in-flight workers can be
unattributable; when coverage is uncertain, it shows an observed subtotal and
marks the full total and credit figure unavailable rather than guessing.

For a completed whole-thread audit with the standalone install, inspect the
lead and every descendant's persisted model, reasoning effort, and total tokens:

```bash
python3 "$HOME/.agents/skills/codex-model-routing/scripts/runtime_usage.py" --root YOUR_THREAD_ID
```

Marketplace users can use `$codex-model-routing report last` without locating
the installed plugin cache. For a manual whole-thread audit, find the script
inside the marketplace-installed skill folder and pass its absolute path to
`python3`. Resolve the script path relative to the installed `SKILL.md`, not the current working
directory. Both report modes run `python3 <skill directory>/scripts/runtime_usage.py --report current|last`, use `CODEX_SESSION_ID` to identify the session, and accept `--root` to override it. The helper reads local Codex state read-only. It uses `CODEX_SQLITE_HOME` or `CODEX_HOME` when set; for a custom `sqlite_home` configuration, pass `--db /path/to/state_N.sqlite`. If Codex has no persisted local state, there is nothing to report. Thread metadata is not a per-request model history: use fresh, single-model threads for comparisons. Credit estimates use the dated Standard-speed rate card and are not actual charges, subscription debits, or quota measurements.

## Benchmark results

These are small, synthetic tests of earlier fixed-manager routing policies, **not** a general savings guarantee or a fresh benchmark of the current-session lead rule. The skill was supplied in test prompts; it was not installed on the device. Both campaigns counted the lead and every descendant, and all completed outputs passed their predeclared checks.

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
- [plugins/codex-model-routing/](plugins/codex-model-routing/) — marketplace plugin package
- [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json) — GitHub marketplace catalog
- [agent-profiles/](agent-profiles/) — optional `scout`, `builder`, and `implementer` profiles
- [references/setup.md](references/setup.md) — installation and verification
- [evals/scenarios.md](evals/scenarios.md) — pressure tests and earlier results
- [evals/codex-model-routing-benchmark-2026-09-26.pdf](evals/codex-model-routing-benchmark-2026-09-26.pdf) — full token, credit, and correctness analysis
- [scripts/runtime_usage.py](scripts/runtime_usage.py) — local runtime-model and token audit

Run the small audit-script test with `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
