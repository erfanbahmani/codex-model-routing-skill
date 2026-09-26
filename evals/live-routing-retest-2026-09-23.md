# Live routing retest — 2026-09-23

## Verdict

Routing worked, but token reduction was not reliable across task types.

In **11 matched pairs (22 completed runs)**, all completed outputs passed the
independent acceptance checks. Total recorded tokens were **2,841,526 without
the skill versus 2,813,604 with it**: only **27,922 fewer tokens (0.98%)**.

The seven direct-execution treatment runs saved 671,952 tokens combined.
The four delegated treatment runs added 644,030 tokens compared with their
controls, almost cancelling those savings. Both repetitions of each delegated
task used more tokens.

The skill was **not installed**. No Codex/Zed configuration or global AGENTS.md
was changed. The skill source was not changed during testing.

## Results

Tokens mean reported input plus output across the lead and every descendant.
Negative change means fewer tokens with the skill. Means are shown where
there were two repetitions; single-pair categories are explicitly marked.

| Task | Matched pairs | Without skill, mean tokens | With skill, mean tokens | Change |
|---|---:|---:|---:|---:|
| Small edit | 2 | 142,529.5 | 59,893.5 | -58.0% |
| Document extraction | 1 | 156,149 | 60,468 | -61.3% |
| 12-file configuration change | 1 | 114,498 | 79,509 | -30.6% |
| Feature implementation | 2 | 224,717.5 | 82,080 | -63.5% |
| Graph-accounting bug fix | 2 | 391,021.5 | 535,448.5 | +36.9% |
| Refund design/code review | 1 | 224,384 | 133,649 | -40.4% |
| Multi-module scheduler | 2 | 414,979 | 592,567 | +42.8% |

This is a small controlled sample, not a statistically established savings rate.
The aggregate weights the eleven actual pairs, not each category equally.
It does not establish lower billing, credits, or subscription-quota usage.

## Actual models and delegation

Every completed lead was runtime-confirmed as `gpt-6-astra`/`ultra`.

- Without the skill: 13 descendants in total, all runtime-confirmed
  `gpt-6-astra`/`ultra`.
- With the skill: seven direct runs, plus four runs with one
  `gpt-6-luna`/`medium` worker each.
- All four treatment spawns explicitly requested `agent_type="default"`,
  `model="gpt-6-luna"`, `reasoning_effort="medium"`, and
  `fork_turns="none"`. Persisted model/effort and turn-context records matched.
- No treatment worker spawned another agent.
- The `gpt-5.6-terra` route did not trigger; this experiment does not validate it.

Thus, lower-model execution genuinely occurred. A lower model did not
automatically mean fewer tokens.

## Why the delegated runs increased usage

For the first graph-accounting bug-fix pair:

| Component | Without skill | With skill |
|---|---:|---:|
| Astra/Ultra lead | 217,164 | 214,039 |
| All workers | 199,345 | 321,551 |
| Total | 416,509 | 535,590 |

The manager saved only 3,125 tokens, while the treatment worker used 122,206
more tokens than the control workers combined.

Observable traces show that the treatment manager re-read source/tests,
inspected a diff, and requested a follow-up for two coverage gaps. The Luna
worker rebuilt the test file, inspected diffs, ran checks, then amended tests
and reran checks in a second turn. There were three manager wait calls and
one follow-up call. These observations support handoff, repeated-context, and
correction overhead as the explanation; they do not establish a universal
property of the model.

The repeated bug-fix run again used more tokens: 535,307 versus 365,534.
The two scheduler treatment runs also both increased usage: 604,222 versus
451,801, and 580,912 versus 378,157.

The current delegation criterion therefore did not reliably predict the
lower-token route for these substantial implementations. Avoiding unnecessary
agents helped the smaller tasks; delegating implementation did not.

## Method and isolation

- Tested commit: `d846c8bfaad23f1b3d799924594020e847a617e3`.
- SKILL.md SHA-256: `9ca16bcc188b24cd1dc50404117a1822a14064178671f6efdf7cd16fd64ce795`.
- Codex CLI: `0.156.1`.
- Fresh disposable workspace and lead session for every run; no production
  projects, real payment providers, or external application data were used.
- Identical task instructions, starting fixtures, manager model/effort, and
  acceptance criteria within each pair. Only the treatment received the
  current SKILL.md verbatim in its prompt.
- Nothing was copied or linked into an installed skill directory. This tests
  the routing policy when explicitly supplied, not automatic skill discovery.
- Both sides used `--ignore-user-config`, `workspace-write`, multi-agent
  support, disabled apps/plugins and installed-skill discovery overrides.
  Both received the same test-only instruction not to load global/project
  skill guidance. No settings file was edited.
- Both sides received a runtime.json snapshot generated from their own
  persisted session metadata, allowing the skill's model-confirmation gate
  to see actual model/effort evidence.
- The small edit, feature, bug fix, and scheduler were repeated. The second
  batch reversed arm enqueue order; concurrency was capped at two benchmark
  sessions.
- Both leads were pinned to Ultra to isolate routing. This does **not**
  compare the skill against a lower-effort daily session. The user's existing
  global effort setting was left unchanged.
- The baseline was allowed its normal multi-agent behavior. It chose
  additional Astra agents in every completed control. Results may differ
  substantially with an already direct/minimal baseline or other plugins.

CLI machine-readable events provide session IDs and reported usage; see
[OpenAI's non-interactive-mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
The local audit followed the full recursive thread tree, counted each ID once,
and reconciled every included thread's final token event with its SQLite row.
Latest-task completion was checked for every counted thread.

Cached input is already part of input; reasoning output is already part of
output. Neither was added a second time. Evaluator preparation, analysis, and
reporting tokens are outside these subject-run comparisons.

## Quality checks

- Small edit: exact output for zero, positive and negative Decimal amounts.
- Extraction: exact structured retention answer; source documents unchanged.
- Bulk configuration: all twelve TOML files checked against the original,
  immutable CSV; names and CSV contents preserved.
- Feature: both APIs checked for exact Decimal averages, empty/missing
  customers, filtering, preserved count/total, and unchanged inputs.
- Bug fix: unique descendants, duplicate edges, cycles, unrelated threads,
  NULL usage, and traversal through a missing intermediate row.
- Refund review: both reviews passed all seven manually assessed criteria:
  cumulative limits, durable idempotency, transaction/lock ownership,
  provider deduplication, ambiguous outcomes, recovery after ledger failure,
  and appropriate failure/concurrency/reconciliation tests. Payment source
  and policy documents remained unchanged.
- Scheduler: independent config, readiness, retry, failure propagation,
  state/graph checks, plus the fixture unit suite.

The implementation acceptance checks rejected the unfinished starting
fixtures before live runs. After completion, independent checks were rerun for
all 22 included runs, and all 14 applicable fixture unit suites passed.
The repository's own three runtime-accounting tests also passed.

## Individual completed pairs

| Task / pair | Without skill | With skill | Baseline children | Treatment children |
|---|---:|---:|---:|---:|
| Small edit / 1 | 142,551 | 59,866 | 1 | 0 |
| Small edit / 2 | 142,508 | 59,921 | 1 | 0 |
| Document extraction / 1 | 156,149 | 60,468 | 1 | 0 |
| 12-file configuration change / 1 | 114,498 | 79,509 | 1 | 0 |
| Feature implementation / 1 | 224,828 | 80,530 | 1 | 0 |
| Feature implementation / 2 | 224,607 | 83,630 | 1 | 0 |
| Graph-accounting bug fix / 1 | 416,509 | 535,590 | 2 | 1 |
| Graph-accounting bug fix / 2 | 365,534 | 535,307 | 1 | 1 |
| Refund design/code review / 1 | 224,384 | 133,649 | 1 | 0 |
| Multi-module scheduler / 1 | 451,801 | 604,222 | 2 | 1 |
| Multi-module scheduler / 2 | 378,157 | 580,912 | 1 | 1 |

Feature pair 1 uses control run `metadata-feature-base-3`, the fresh retry
of the transport-failed control, with treatment `metadata-feature-skill-1`.
No successful run was selected out for having an unfavorable token result.

[Machine-readable results](live-routing-retest-2026-09-23.json) include stable
public aliases for root/child IDs, runtime models, token components, requested
spawn arguments, acceptance outcomes, and reconnect counts. Original local
session UUIDs were removed after the usage audit; the aliases preserve each
run's thread relationships but cannot look up the private local telemetry.

## Pilot failures, interruptions, and network errors

Before the main matrix, a pilot did not expose runtime metadata inside the
isolated workspace. The small-edit treatment refused to proceed because it
could not verify the manager, despite the client selecting Astra/Ultra.
It left the file unchanged and used 75,111 reported tokens; the control
completed using 111,229.

That is a runtime-evidence dependency, not a successful low-token result.
The subsequent comparisons supplied the same actual metadata file to both
arms. Accordingly, their results are conditional on accessible runtime
evidence; they do not prove the skill works autonomously in every client.

The pilot extraction completed at 127,269 control and 68,055 treatment tokens,
but included additional regional documents that were removed from both
main-matrix fixtures to keep the global-policy question unambiguous. It is
excluded from the main comparison.

Two pilot bulk runs were interrupted while correcting the harness, with
13,678 and 44,642 tokens recorded respectively. Their totals are partial,
not completed-run metrics. The pilot records total 439,984 known tokens,
separate from the matched comparison.

The first main feature control failed with transport errors before any model
usage was recorded (SQLite recorded zero; there was no completed usage event).
It was excluded and retried from the original fixture, without reusing partial
work. Completed runs that recovered from reconnects were retained and flagged
in the JSON. Network noise limits latency and billing conclusions.

The 22 included runs together used **5,655,130 reported tokens**. Including the
known pilot records gives **at least 6,095,114 recorded subject-run tokens**;
this is not the total cost of conducting the evaluation.

## Practical conclusion

The revised policy can suppress unnecessary delegation on short tasks, and
its explicit model pins work. It is **not yet demonstrated as a dependable
general token reducer**: both delegated task categories regressed in both
repetitions, leaving only a 0.98% net reduction across this test mix.

Do not infer that always handing implementation to a smaller model saves
tokens. Further tuning needs evidence about when delegation actually avoids
manager work and how to prevent repeated worker/manager correction cycles.
No skill changes, installation, commits, or pushes were performed by this test.
