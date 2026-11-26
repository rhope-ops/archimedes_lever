# Rule conflict check: faster small fixes (2026-11-26)

Changed lines: AGENTS.md "Fresh review" and "Checks" (texts T1, T2 of [the plan](2026-11-26-faster-fixes-plan.md)), as `python3 scripts/bloat_check.py --rules` lists them. Reviewer: the `reviewer` subagent, fresh context, model inherit (the author's tier), 2026-11-26 about 11:10-11:13 America/Chicago. Brief: rule-change "Conflict check" step 1, plus the skill sections the new text points to.

## Findings

| # | Grade | Texts | Case | Fix | State |
|---|---|---|---|---|---|
| 1 | MAJOR | deliver "Small change": "no lane C file … merge by lane B"; AGENTS.md "Delivery" and deliver "Merge lanes": a UI change not approved, a security change, a data write are lane C | a 12-line security change in a normal file, with a test | "nothing in lane C, by file or by effect" | to the Maintainer |
| 2 | MAJOR | "Fresh review": "The review covers the head commit you merge: a later fix or a base merge with a conflict gets a review"; deliver step 4: "the fresh review on that head commit" | a clean merge of main after the review moves the head | "The review covers the changes you merge"; deliver step 4 names the clean merge | to the Maintainer |
| 3 | MINOR | "no lower than the author's (a small change: deliver skill)"; decision row "may use"; deliver step 3 an order | which tier a small change must use | "(a small change may use the fast tier: deliver skill)" | recorded |
| 4 | MINOR | handoff step 5 "runs the review again"; "Fresh review" reviews the new diff only | a handoff commit after the review | point step 5 to "Fresh review" | recorded |
| 5 | MINOR | delegate: fast tier for a small change; strong tier for "a refactor that must not change behavior" | a 15-line refactor | the strong-tier cases are not "small" | recorded |
| 6 | MINOR | handoff step 5 "once … in the last pull request"; AGENTS.md "Handoff": push an approved plan before step 1 | an approved plan at the start | name the plan exception in step 5 | recorded |
| 7 | MINOR | the 2026-11-26 decision row "Replaces" | the "Checks" text approved 2026-11-18 | add it to "Replaces" | recorded |

Checked and OK: the 2026-11-16 row "reviewer model: inherit" stays for every other review; the private-repo case keeps its home in deliver step 4; rule-change step 3 does not conflict with "Lean instructions".

MINOR findings do not change rule text again (rule-change "Conflict check" step 3).

rule-conflict-check: 210907f36b08
