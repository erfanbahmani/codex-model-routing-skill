# Sol manager comparison — 2026-09-23

## Verdict

Sol managing Luna used **23.4% fewer total tokens than Astra managing Luna** across these trials. However, it used **148.3% more tokens than Sol working directly**. Changing the manager helped relative to the Astra/Luna strategy; it did not make delegation beat direct execution on these fixtures.

There is also a correctness caveat: an additional missing-root check failed in both Sol/Luna bug-fix outputs and one Astra/Luna output. Both Sol-direct outputs passed it. Do not treat the token difference as proof of equivalent quality.

Recommendation: use direct Sol for bounded work like these fixtures. If a manager/worker split is mandatory, Sol is worth further validation, but this is not sufficient evidence to adopt it as a generally token-saving replacement. Keep delegation selective and address the observed correctness gap before making stronger claims. No default was changed.

## Token results

Each value includes the lead and every descendant. Two fresh runs per task/strategy; lower is better.

| Task | Strategy | Repetition 1 | Repetition 2 | Mean tokens |
|---|---|---:|---:|---:|
| Recursive usage-report bug fix | Sol direct | 247,610 | 240,017 | 243,813.5 |
| Recursive usage-report bug fix | Sol → Luna | 432,152 | 309,365 | 370,758.5 |
| Recursive usage-report bug fix | Astra → Luna | 461,812 | 527,998 | 494,905 |
| Dependency-aware scheduler | Sol direct | 159,667 | 142,463 | 151,065 |
| Dependency-aware scheduler | Sol → Luna | 553,449 | 666,285 | 609,867 |
| Dependency-aware scheduler | Astra → Luna | 601,386 | 967,726 | 784,556 |

Sol/Luna versus Astra/Luna: **25.1% fewer** tokens on the bug fix and **22.3% fewer** on the scheduler. Sol/Luna versus direct Sol: **52.1% more** on the bug fix and **303.7% more** on the scheduler.

Combined accounting across four trials per strategy:

| Strategy | Lead tokens | Worker tokens | Total tokens |
|---|---:|---:|---:|
| Sol direct | 789,757 | 0 | 789,757 |
| Sol → Luna | 774,941 | 1,186,310 | 1,961,251 |
| Astra → Luna | 901,339 | 1,657,583 | 2,558,922 |

The complete measured experiment consumed **5,309,930 reported tokens across 20 agent threads**. This excludes benchmark setup, the supervising conversation, the read-only review helper, and report generation. These are processed-token totals, not API charges or Codex subscription-credit measurements.

## Quality results

All twelve outputs passed the predeclared independent acceptance checks and their final unittest suites. The scheduler additionally passed the frozen original eleven-test suite, executed outside the agents' editable test files.

| Strategy | Bug-fix planned checks | Scheduler planned checks | Additional missing-root check |
|---|---:|---:|---:|
| Sol direct | 2/2 | 2/2 | 2/2 |
| Sol → Luna | 2/2 | 2/2 | 0/2 |
| Astra → Luna | 2/2 | 2/2 | 1/2 |

The additional check was introduced after read-only review of the first bug-fix outputs, then applied unchanged to all six bug-fix outputs. It tests a root ID with no thread row but an existing edge to a child with known usage. Under the broader missing-row requirement, the root should remain visible as `unknown`, the child should remain visible with its known tokens, and the total should be incomplete. Three outputs instead exited with `Thread not found`.

This is a post-review check, not a predeclared acceptance criterion. No corrective instructions were fed into the live trials, and no failed output was repaired or replaced to improve the table. The defect concerns the trial-generated fixture solutions; it does not establish the behavior of the current repository implementation. Passing the original checks did not prove the strategies had equal quality.

Final verification reran every independent checker and:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

All twelve final suite invocations passed. The additional root check retained the three failures shown above.

## Were the intended models actually used?

Yes. Every run's persisted model/effort and recorded turn contexts matched:

- Direct: `gpt-6-sol` / `ultra`, with no children.
- Sol-managed: `gpt-6-sol` / `ultra`, with exactly one `gpt-6-luna` / `medium` child.
- Astra-managed: `gpt-6-astra` / `ultra`, with exactly one `gpt-6-luna` / `medium` child.

All eight worker spawns explicitly used the default agent type, the requested model/effort, and no inherited conversation. There were no nested workers. Read-only inspection of observable tool calls confirmed that all eight managers left implementation and test edits to Luna; managers inspected, decided, reviewed, and requested corrections.

Each thread's final cumulative token event matched its persisted usage. All twenty threads had completed their latest task before final accounting. Cached input and reasoning output were treated as subsets, not added twice.

## Why delegation still used more tokens

Sol/Luna's lead alone consumed 774,941 tokens across four trials, almost the direct strategy's entire 789,757-token total. Delegation then added 1,186,310 worker tokens.

Observable traces showed repeated source/test reads, manager review, follow-up requests, and worker corrections with repeated suite runs. Scheduler workers ran suites three to four times. Switching managers did not remove those separate contexts or exchanges. Both manager and worker usage differed between the Sol/Luna and Astra/Luna trials; the whole difference cannot be attributed to the manager's own token generation.

These observations explain overhead in these runs, not a universal property of either model.

## Method and limitations

- **Controlled strategies, not automatic routing:** direct runs explicitly prohibited delegation and received no routing skill. Managed runs received the unchanged skill text plus an explicit manager choice and an assignment to use one Luna worker. This intentionally overrides the skill's route-selection heuristic. The Sol-versus-Astra manager contrast holds that managed procedure constant. The direct-versus-managed contrast changes both procedure and skill context, not just the model.
- **Matched inputs:** two task types × three strategies × two fresh sessions. Starting fixture hashes matched within each task. The bug fixture used the original files from commit `7562f4b`; the scheduler reused the previous evaluation's fixture and checks. Task prompts and hashes are retained in the accompanying JSON.
- **Isolation:** disposable workspaces, ignored user configuration, disabled installed skills/plugins/apps, and no project instruction loading. The skill was supplied only inside managed-run prompts, never installed. Real session metadata was supplied equally to all arms so the skill could verify its lead model.
- **Runtime:** Codex CLI `0.156.1`; source commit `d846c8bfaad23f1b3d799924594020e847a617e3`. CLI-recorded lead effort was `ultra`; workers used `medium`. At most two runs ran concurrently; task and strategy order were reversed for repetition two.
- **Accounting isolation:** each fresh session had a unique root ID. Usage was read from the existing local telemetry database using that root's complete descendant tree, not shared account-counter differences. All thread IDs were distinct between trials.
- **Small sample:** two repetitions are descriptive, not a statistically reliable estimate of general savings. These are bounded synthetic tasks and fresh contexts, not a representative collection of production repositories or long manager histories.
- **No Git history in fixtures:** some agents attempted Git status/diff commands that failed because the fixture folders were not repositories. Those attempts provided no diff evidence and could add overhead. Real Git-backed projects may behave differently; direct-versus-managed conclusions should not be generalized without testing that environment.
- **Connection retries:** scheduler repetition 1 produced one root-CLI reconnect notice in each managed arm; Sol/Luna scheduler repetition 2 produced three. All recovered and were retained. There were no replacement trials. Latencies are not clean model-speed comparisons; reported telemetry is not a provider billing audit.
- **Testing guidance:** matched fresh-session trials and independent checks followed the skill-testing guidance. Ponytail's reuse rule kept the existing fixtures and harness rather than introducing a new testing framework.

## Files and machine state

The routing skill remained absent from both personal skill locations. Before/after hashes matched for the source `SKILL.md`, Codex configuration, Codex `AGENTS.md`, and Zed `AGENTS.md`. No skill source, configuration, commit, or push was changed.

New outputs are this report and [the machine-readable evidence](sol-manager-comparison-2026-09-23.json). Existing retest reports were preserved. The JSON retains stable public aliases for per-run thread IDs, runtime model evidence, input/output breakdowns, fixture hashes, and supplemental results; original local session UUIDs, local transcript paths, and transcript content are excluded. The aliases preserve thread relationships but cannot look up the private local telemetry.
