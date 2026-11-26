# Rule tests 37 and 38 (2026-11-26)

Run for the faster-fixes plan (step 5), each in a child cloud session that this session started (rule-change step 2, kit 14.1.0). Model: the configured session model (Opus tier); the fast-tier reviewer ran on Haiku. Each child used a local bare repo as `origin`; nothing reached GitHub. Branch under test: claude/dreamy-brown-64futp at 877989b.

| # | Scenario | Result | Evidence (the child's own report) |
|---|---|---|---|
| 37 | Small change, 20 lines | pass | Counted 17 non-test lines (merge-base numstat, test file left out). Told the Maintainer "Fix proven: `add_days` added, 6/6 unit tests pass" before delivery. Reviewer on `haiku` in both rounds; full lane and review at the same time in both rounds; round 2 read only the fix diff. Lane B. Phase times reported: request 11:36:11, fix proven 11:36:23, first push 11:37:35, review 1 by 11:38:29, review 2 by 11:39:01, merged (local) 11:39:08: 3 min from request to merge. |
| 38 | Not a small change (21-line form) | pass | Counted 21 non-test lines: not small, no fast path. Reviewer on the author's tier (no model override). Phase times reported; slowest: review. The 3-line `.claude/settings.json` form was not run. |

Notes:

- Test 38 started from this unmerged branch, so `git diff --numstat $(git merge-base origin/main HEAD)` also counted the base branch's files (over 300 lines in 19 files) and the child called its merge lane C. On a branch cut from main this does not happen. Recorded as a MINOR of text T3: the count assumes a branch cut from main.
- Both children's pre-push hooks blocked a first push (code standard); each fixed the cause and pushed again. Neither went around a guard.
- Test 37's stop hook asked it to push local `main`; it refused (AGENTS.md "Git history").
