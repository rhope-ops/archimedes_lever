# Plan: faster small fixes (2026-11-26)

Written 2026-11-26 10:55 America/Chicago by session "Kit · Faster small fixes · 2026-11-26". Status: **draft, waits for the Maintainer's approval of the exact texts below** (AGENTS.md "Rule text"). Scope: the kit; projects get it by the next kit release and sync.

Source: the Maintainer's approved "deeper version" prompt (chat, 2026-11-26), plus the 2 items it left out ("include the additional parts left out"). Decisions in the same chat (question dialog): small change gets a fast-tier review in parallel with the full lane; a re-review reads the fix diff only; done = kit pull request + CHANGELOG row (the Maintainer tags).

## Evidence so far

- 90-161.Z R44 r2 round: about 2 h 30 min; slowest step: 7 pushes, each with an 8-10 min Windows CI job, 2 failed runs, 4 review rounds (90-161.Z docs/reviews/2026-11-26-r44r2-plan.md line 33).
- 90-161.Z git history since 2026-11-20 (shallow clone, depth 50): 6 of 67 merges were handoff-only pull requests; 8 commits start "Handoff".
- Kit check lanes, this clone, 2026-11-26: fast 26.4 s, full 27.8 s.
- Phase times of 4 fix sessions: step 1 file (measurement running).

## Source items: in / out / later

| # | Item | Decision | Home |
|---|---|---|---|
| 1 | Baseline: phase times of 4+ fix sessions, handoff-only merges, CI times | in | docs/reviews/2026-11-26-fix-lead-time-baseline.md |
| 2a | Phase times in every delivery report | in | deliver step 8; audit "Time a new repeatable process" |
| 2b | Small change: fast-tier fresh review, parallel with the full lane | in | AGENTS.md "Fresh review"; deliver "Small change"; delegate routing |
| 2c | Re-review reads the fix diff only | in | AGENTS.md "Fresh review" |
| 2d | Report the proven fix first, then deliver | in | deliver "Small change" step 1 |
| 2e | Handoff once per session, in the last pull request | in | handoff step 5 |
| 2f | Fast path at the top of deliver | in | deliver "Small change" |
| 2g | One in, one out for each new rule | in | rule-change step 3 |
| 3 | Texts in full; session load does not rise; dry-run sync of each fleet repo | in | this plan; step 6 |
| 4 | Proof: check.sh, rule tests 20 vs 21 lines and lane C, conflict record, CHANGELOG | in | steps 5-7 |
| L1 | Fewer CI round trips: push once per round; cancel superseded CI runs | in | deliver step 2; kit check.yml and security.yml; CHANGELOG sync note for project workflows (RADE, 90-161.Z ps51.yml) |
| L2 | Re-measure 5 fix tasks one week after the release | in | a one-time scheduled task (step 9) |
| | Counts | 12 in, 0 out, 0 later | |

## Exact texts (rule text: the Maintainer approves each)

T1. AGENTS.md "Fresh review", whole line, new text:

> - **Fresh review.** For lanes B and C, a fresh reviewer gets only the diff and the brief, not the author's conclusions (a fresh context finds what self-review misses): the `reviewer` subagent where the host has subagents, else a new session, on a model tier no lower than the author's (a small change, deliver "Small change": the fast tier); if neither is possible, review it yourself, call it "self-review" and treat the merge as lane C. The review covers the head commit you merge: after a fix, a new review reads the diff since the last review and its findings. Review a change made to pass a check against its goal: "only the number moved" is MAJOR.

T2. AGENTS.md "Handoff", retire part of the line (pays for T1; the handoff skill "Start from a handoff" step 1 already says it). Remove: "; after a restart or a compaction, continue it without a new plan review or approval". The sentence ends "…push it before step 1."

T3. deliver skill, new section after the intro line, before "## Steps":

> ## Small change (fast path)
>
> A small change has at most 20 changed lines (`git diff --numstat origin/main`), no lane C file (table "Merge lanes") and a test that covers it.
>
> 1. When its test passes, tell the Maintainer the fix and the test result in one line. Then deliver.
> 2. Steps 0-3 as below, with one push.
> 3. Start the fresh review on the fast tier (`reviewer` with model `haiku`) and run the full lane at the same time.
> 4. Fix all findings of one review in one commit and one push. The next review reads only that diff and the findings (AGENTS.md "Fresh review").
> 5. Steps 5-8 as below; merge by lane B.

T4. deliver step 2, new text:

> 2. Push once for each round of work: put the edits and the review fixes of one round in local commits, then push (each push runs the hook and, in a public repo, every job of the pull-request Action). The pre-push hook runs the fast lane.

T5. deliver step 8, add at the end:

> Add the phase times, from the clock (`date`, the header time zone): request, fix proven, first push, review done, merged; and name the slowest phase.

T6. audit "Time a new repeatable process", third bullet, new text:

> - An agent procedure (deliver, a review, an audit): write its phase times in the report (deliver step 8). When it runs a 2nd time, propose a script for it under Suggest.

T7. handoff step 5, new text:

> 5. Write the handoff once for each session or pause, as a commit in the session's last pull request; a handoff-only pull request (lane A) only when no pull request of the session is open.

T8. rule-change step 3, new text:

> 3. Each new rule line removes or shortens a line in the same change, so the session load does not grow (one in, one out); only the Maintainer can waive this for one rule. The caps are the Maintainer's decision (`KIT_CAPS` in `scripts/bloat_check.py`).

T9. delegate "Model routing": new row after "Fresh review of a routine diff", and "strong" → "strong or fast" in the line "Pass a model on the call only where …":

> | Fresh review of a small change (deliver "Small change") | `reviewer` | fast (model `haiku` on the call) |

T10. `.github/workflows/check.yml` and `security.yml`: add at top level

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

(A new push to the same pull request stops the run of the old head; the merge gate reads the head run only.)

T11. `.claude/rule-tests.md`: 2 rows. "Small change, 20 lines": a 20-line script fix with a test, `Ship it.` → fast-tier review in parallel with the full lane, merge lane B. "Not small": a 21-line fix, or a 3-line change to `.claude/settings.json` → author-tier review (the lane C file: ask the Maintainer).

## Steps (lane of each)

1. Baseline file (lane A, in the kit pull request).
2. T1, T2 in AGENTS.md; T3-T9 in the skills; T11 rule tests (lane C).
3. T10 workflows (lane C: guard files).
4. `bloat_check.py --rules`: session load at most 5,071 (5,061 + 10; T1 adds about 20 tokens, T2 removes about 18); conflict check by a fresh reviewer, record `docs/reviews/2026-11-26-rule-conflict.md`; debt file `docs/reviews/2026-11-26-faster-fixes-debt.md` (T5 of rule-change).
5. Run the 2 new rule-test scenarios; record `docs/reviews/2026-11-26-rule-tests.md`.
6. Dry-run sync of each fleet repo: session load by `bloat_check.py --brief`, each under 5,500.
7. CHANGELOG row (MINOR or MAJOR by the kit's version rule), DECISIONS row, KIT_HANDOFF line. `scripts/check.sh` green; pull-request Action green.
8. Fresh review of the whole pull request (author tier). Then ask the Maintainer to merge (lane C).
9. After the merge: a one-time scheduled task 7 days after the tag: measure 5 fix tasks as in step 1, compare with the baseline (target: median lead time down 30% or more; fix-of-fix commits not up), write `docs/reviews/YYYY-MM-DD-fix-lead-time-after.md`.

Not in this plan: the project workflow changes (RADE, 90-161.Z ps51.yml). The CHANGELOG sync column tells each project to add T10 to its own workflows in its sync pull request.
