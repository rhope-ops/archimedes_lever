# Plan: faster small fixes (2026-11-26)

Written 2026-11-26 10:55 America/Chicago by session "Kit · Faster small fixes · 2026-11-26". Status: **approved 2026-11-26 11:05 America/Chicago** (the Maintainer, question dialog: "Approve all T1-T11 (Recommended)"; AGENTS.md "Rule text"). Step 1 done. Scope: the kit; projects get it by the next kit release and sync.

Source: the Maintainer's approved "deeper version" prompt (chat, 2026-11-26), plus the 2 items it left out ("include the additional parts left out"). Decisions in the same chat (question dialog): small change gets a fast-tier review in parallel with the full lane; a re-review reads the fix diff only; done = kit pull request + CHANGELOG row (the Maintainer tags).

## Evidence so far

- 90-161.Z R44 r2 round: about 2 h 30 min; slowest step: 7 pushes, each with an 8-10 min Windows CI job, 2 failed runs, 4 review rounds (90-161.Z docs/reviews/2026-11-26-r44r2-plan.md line 33).
- 90-161.Z git history since 2026-11-20 (shallow clone, depth 50): 6 of 67 merges were handoff-only pull requests; 8 commits start "Handoff".
- Kit check lanes, this clone, 2026-11-26: fast 26.4 s, full 27.8 s.
- Phase times of 4 fix sessions ([baseline](2026-11-26-fix-lead-time-baseline.md)): push+checks 41%, fix 29%, review 20% (10 reviewer runs, 6 of them repeats after a fix or a merge of main); start, skill loads and handoff under 4% together.

## Phase each text cuts (from the baseline)

| Text | Phase | Expected effect |
|---|---|---|
| T1, T3, T9 | review (20%) | repeat reviews read only the new diff; a base merge with no conflict needs none (S1: 2 of 3 runs); small changes reviewed on the fast tier |
| T4, T10 | push+checks (41%) | fewer pushes; superseded CI runs stop |
| T3 step 1 | how long it feels | the Maintainer sees the proven fix before delivery |
| T5, T6, L2 | none (measure) | phase times in each report; re-measure after the release |
| T7 | handoff (0.4% in fix sessions) | saves little in fix sessions; removes handoff-only pull requests in round work (6 of 67 in 90-161.Z) |
| T3 as a fast path | skill-load (0.2%) | saves almost no time; its value is one short list of steps |
| T8 | future rules | stops the session load from growing |

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
| 2g | One in, one out for each new rule | in | rule-change step 4 |
| 3 | Texts in full; session load does not rise; dry-run sync of each fleet repo | in | this plan; step 6 |
| 4 | Proof: check.sh, rule tests 20 vs 21 lines and lane C, conflict record, CHANGELOG | in | steps 5-7 |
| L1 | Fewer CI round trips: push once per round; cancel superseded CI runs | in | deliver step 2; kit check.yml and security.yml; CHANGELOG sync note for project workflows (RADE, 90-161.Z ps51.yml) |
| L2 | Re-measure 5 fix tasks one week after the release | in | a one-time scheduled task (step 9) |
| | Counts | 12 in, 0 out, 0 later | |

## Exact texts (rule text: the Maintainer approves each)

T1. AGENTS.md "Fresh review", whole line, new text (changed parts: the bracket after "the author's", and the sentence after "head commit you merge:"; a base merge with no conflict needs no new review):

> - **Fresh review.** For lanes B and C, a fresh reviewer gets only the diff and the brief, not the author's conclusions (a fresh context finds what self-review misses): the `reviewer` subagent where the host has subagents, else a new session, on a model tier no lower than the author's (a small change: deliver skill); if neither is possible, review it yourself, call it "self-review" and treat the merge as lane C. The review covers the changes you merge: a later fix or a base merge with a conflict gets a review of its diff and the earlier findings. Review a change made to pass a check against its goal: "only the number moved" is MAJOR.

T2. AGENTS.md "Checks", whole line, new text (pays for T1; removes a duplicate: deliver "GitHub Actions" and the workflow `if:` lines hold the private-repo case):

> - **Checks.** Each push runs the fast lane (`scripts/git-hooks/pre-push`), so do not run it by hand first. Green for a merge means: `scripts/check.sh` passed one time on the head commit, and, in a public repo, the pull-request Action finished green. Change a generated file through its source and a rebuild.

Protection removed by T2: none known; the private-repo reason stays in deliver "GitHub Actions". Session load, measured with `bloat_check.py --brief` (T1 + T2 applied in a scratch copy, 2026-11-26 ~11:05): kit 5,061 -> 5,060 (final T1 text); an earlier T1 text measured kit 5,056 and 90-161.Z 5,433 -> 5,427. Every repo has the same kit text, so each one changes by the same amount.

Decision rows checked (rule-change step 1): 2026-11-16 "reviewer.md model: inherit" (a conflict check on a lower tier had to run again) stays; T1 and T9 add a fast tier only for a small change, never for a conflict check or a lane C review. 2026-11-18 "Handoff" restart text stays (not touched).

T3. deliver skill, new section after the intro line, before "## Steps":

> ## Small change (fast path)
>
> A small change has at most 20 added plus deleted lines outside test files (`git diff --numstat $(git merge-base origin/main HEAD)`), nothing in lane C, by file or by effect (table "Merge lanes") and a test that covers it.
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

> 5. Write the handoff once for each session or pause, as a commit in the session's last pull request before its last review (a commit after the review moves the head and runs the review again); a handoff-only pull request (lane A) only when that pull request has merged.

T8. rule-change step 4 (step 3 before kit 14.1.0), new text:

> 3. Each new rule line removes or shortens a line in the same change, so the session load does not grow (one in, one out); only the Maintainer can waive this for one rule. The caps are the Maintainer's decision (`KIT_CAPS` in `scripts/bloat_check.py`).

T9. delegate "Model routing": new row after "Fresh review of a routine diff", and "strong" → "strong or fast" in the line "Pass a model on the call only where …":

> | Fresh review of a small change (deliver "Small change") | `reviewer` | fast (model `haiku` on the call) |

T10. `.github/workflows/check.yml` and `security.yml`: add at top level

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

(A new push to the same pull request stops the run of the old head; the merge gate reads the head run only.) Not proven for R44: it saves time only when pushes overlap a running job; T4 (fewer pushes) is the main fix. The run records of the repo with the Windows job are not read in this session (no access).

T11. `.claude/rule-tests.md`: 2 rows. "Small change, 20 lines": a 20-line script fix with a test, `Ship it.` → fast-tier review in parallel with the full lane, merge lane B. "Not small": a 21-line fix, or a 3-line change to `.claude/settings.json` → author-tier review (the lane C file: ask the Maintainer).

## Steps (lane of each)

1. Baseline file (lane A, in the kit pull request).
2. T1, T2 in AGENTS.md (T2 retires a duplicate); T3-T9 in the skills; T11 rule tests (lane C).
3. T10 workflows (lane C: guard files).
4. `bloat_check.py --rules`: session load at most 5,060 (measured with T1 + T2; it must not rise); conflict check by a fresh reviewer, record `docs/reviews/2026-11-26-rule-conflict.md`; debt file `docs/reviews/2026-11-26-faster-fixes-debt.md` (T5 of rule-change).
5. Run the 2 new rule-test scenarios; record `docs/reviews/2026-11-26-rule-tests.md`.
6. Dry-run sync of each fleet repo: session load by `bloat_check.py --brief`, each under 5,500.
7. CHANGELOG row, kit 15.0.0 (MAJOR; 14.0.0 and 14.1.0 merged meanwhile: changed AGENTS.md rule text), DECISIONS row, KIT_HANDOFF line. `scripts/check.sh` green; pull-request Action green.
8. Fresh review of the whole pull request (author tier). Then ask the Maintainer to merge (lane C).
9. After the merge: a one-time scheduled task 7 days after the tag: measure 5 fix tasks as in step 1, compare with the baseline (target: median lead time down 30% or more; fix-of-fix commits not up), write `docs/reviews/YYYY-MM-DD-fix-lead-time-after.md`.

Not in this plan: the project workflow changes (RADE, 90-161.Z ps51.yml). The CHANGELOG sync column tells each project to add T10 to its own workflows in its sync pull request.

## After the conflict check

The 2 MAJOR fixes (approved 2026-11-26 ~11:30, question dialog "Approve both fixes (Recommended)") are in T1 and T3 above: "The review covers the changes you merge"; "nothing in lane C, by file or by effect"; deliver step 4 names the clean base merge. This release is kit 15.0.0 (14.0.0 and 14.1.0 merged to main meanwhile).
