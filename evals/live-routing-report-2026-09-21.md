# Live routing and token report — 2026-09-21

## Verdict

The skill is **not reliable for its Sol/Ultra decision guarantee** in the tested
Codex CLI environment. In two completed, synthetic refund-design runs, it
spawned a `default` decision child without a model or effort override. Both
children actually ran on `gpt-5.6-terra` / `medium`, and the lead used their
decisions. An explicit-pinning diagnostic proved that this CLI can run a
`gpt-5.6-sol` / `ultra` child; the skill-guided spawn omitted the arguments.

The skill did select `scout` and `builder` for larger tasks, and their
profiles actually ran on `gpt-5.6-luna` / `medium`. In these single paired
runs, delegation raised **total tokens** substantially. This is not evidence
about monetary credits, and one pair per task is not a savings estimate.

## Method

- Codex CLI `0.153.4`; fresh `codex exec --json` sessions, all leads pinned to
  `gpt-5.6-terra` / `medium`.
- Identical prompt and synthetic Git fixture for each pair, with mixed A/B
  order. The prompt asked Codex to choose direct work or delegation and then
  complete the task. The control home had no routing skill; the treatment
  home symlinked this repository. Both homes contained identical
  `scout`, `builder`, and `implementer` profiles, so only the skill differed.
- Both arms used `--ignore-user-config --enable multi_agent --disable apps
  --disable plugins` and were outside the user's project/AGENTS.md hierarchy.
  A discovery probe confirmed that only treatment could see
  `codex-model-routing`.
- The local `workspace-write` sandbox failed with `bwrap: loopback: Failed
  RTM_NEWADDR: Operation not permitted` before touching the fixture. The
  comparison therefore used `danger-full-access` **only on disposable,
  synthetic repositories**. That failed sandbox run is excluded.
- The first tiny-edit pilot and a later pair used faulty check commands;
  neither is included below. The final tiny pair used a prevalidated check.
- Token totals are the sum of persisted `threads.tokens_used` for the lead and
  every descendant in `thread_spawn_edges`. Each lead total matched its
  `turn.completed.usage.input_tokens + output_tokens` JSONL record.
  `cached_input_tokens` and `reasoning_output_tokens` are subsets, not
  additional tokens. Child tokens are added only once.
- The test runs did not change production systems, payment providers, or user
  project files. This report is the only project file added. Raw synthetic run
  metadata is in `/tmp/codex-routing-eval.ZEr3d2` and may disappear.

## Paired completed tasks

| Task | Without skill | With skill | Change | Actual treatment route | Independent outcome |
|---|---:|---:|---:|---|---|
| Tiny one-file label edit | 51,534 | 40,677 | -21.1% | Terra lead, direct | Exact Python assertion passed; outputs identical |
| Eight short policy docs | 40,826 | 42,583 | +4.3% | Terra lead, direct | Both reconciled policy and stale note correctly |
| 24-file policy matrix | 87,154 | 254,740 | +192.3% | Terra lead 128,106 + Luna scout 126,634 | Both produced the correct 24 rows and six flags |
| One-pattern change in 12 TOMLs | 53,862 | 41,718 | -22.5% | Terra lead, direct | Objective check passed; outputs identical |
| Distinct CSV-mapped change in 12 TOMLs | 55,528 | 214,071 | +285.5% | Terra lead 116,424 + Luna builder 97,647 | Three tests passed; outputs identical |
| Approved service + CLI behavior change | 53,739 | 87,036 | +62.0% | Terra lead, direct | Three tests passed in both; no child |
| Refund architecture design, no edits | 26,678 | 70,586 | +164.6% | Terra lead 56,987 + **Terra decision child 13,599** | Both designs covered the fixture invariants; treatment's model gate failed |
| **Sum of these seven pairs** | **369,321** | **751,411** | **+103.5%** | — | Diagnostic sample only; not a general savings claim |

The short docs and one-pattern edit stayed direct, which is consistent with
the skill's fresh-context threshold. The approved service + CLI change also
stayed direct, although it added behavior across two interfaces; that route
appears inconsistent with the skill's stated direct gate. The larger reading
and mapped edits did invoke Luna children, but the parent continued to spend
more tokens than the no-skill lead in both pairs.

## Safety and model diagnostics

1. The first refund treatment spawned `default` with `fork_turns="none"`
   but **no `model` or `reasoning_effort` arguments**. Runtime metadata:
   child `gpt-5.6-terra` / `medium`; total 70,586 tokens.
2. A repeat of the same treatment prompt made the same omission. Runtime
   metadata: child `gpt-5.6-terra` / `medium`; total 141,557 tokens.
   This repeat was not paired with another control run.
3. A separate explicit diagnostic passed `model="gpt-5.6-sol"` and
   `reasoning_effort="ultra"` to `spawn_agent`. Runtime metadata confirmed
   `gpt-5.6-sol` / `ultra`, so model support was not the blocker.
4. Sequential named-profile diagnostics without explicit overrides confirmed:
   `scout` → Luna/medium, `builder` → Luna/medium, and `implementer` →
   Terra/medium. Profile pinning works; automatic route selection is separate.
5. The default Codex home used outside the test did **not** have this skill
   installed in `~/.codex/skills` or `~/.agents/skills` at test time.

The high-risk behavior is a failure even though the written refund designs
were reasonable: the documented model gate is about who makes the decision.
The lead correctly labeled the actual child model as unverified, but still
accepted the child decision without verifying it.

## Interpretation and next test

Do not rely on this version for high-risk or substantive decisions. The
observed failure is at dispatch: the prose specifies Sol/Ultra, while the
actual spawn call did not pin either field. A correction should make the
required `spawn_agent` arguments explicit and require runtime confirmation
before accepting a decision; then rerun the held-out refund case.

For token efficiency, the observed Luna routes did not lower total tokens in
these fixtures. After the safety correction, repeat paired tasks several
times with randomized order and a quality gate before claiming a saving or
estimating credits. Cached-token treatment and account pricing need separate
analysis; token totals alone do not establish credit savings.

The [official Codex non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode)
documents JSONL `turn.completed.usage`; the
[subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents)
documents model/effort inheritance and custom-agent profiles.

## Session IDs

| Task | Without skill | With skill |
|---|---|---|
| Tiny edit | `01a0c35e-f695-7f42-a7d8-486f8ad3e346` | `01a0c35e-f621-7b61-b570-cb0504b54bd8` |
| Eight docs | `01a0c35f-a634-7fa2-82eb-3664643c89ef` | `01a0c35f-a697-74f0-ab0c-b6ff3d8fa1ae` |
| 24 docs | `01a0c369-cba8-7be2-9c50-a09d4477c0e1` | `01a0c369-cb5b-7323-802e-50c172e8a5b9` |
| One-pattern TOMLs | `01a0c361-1eeb-78b1-af27-668d5900824f` | `01a0c361-1e92-7e22-b484-7fc523723706` |
| CSV-mapped TOMLs | `01a0c36c-a68f-7751-8bd2-5da892c7bae4` | `01a0c36c-a6f3-7790-8358-2cccac1d0e45` |
| Service + CLI | `01a0c362-7acc-7440-bac2-979af305668a` | `01a0c362-7b25-79a0-9f24-4a2fa55396b3` |
| Refund design | `01a0c35b-36a9-7921-a544-eb7b94d04400` | `01a0c35a-a713-7e83-9b3e-1a848b598aa5` |

Second treatment refund run: `01a0c365-6d98-7441-991a-fed5661b016b`.
Explicit Sol/Ultra diagnostic: `01a0c364-2ed0-7e31-9dbc-030d50a92905`.
Named-profile diagnostic: `01a0c367-e165-72a1-b0b2-0d32577ca288`.
