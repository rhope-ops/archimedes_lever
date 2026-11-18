# Review record: two rule tiers, merge lanes, layered sync (kit 2026.11.19)

Date: 2026-11-18 (America/Chicago). Plan: [2026-11-18-lean-rules-sync-plan.md](2026-11-18-lean-rules-sync-plan.md), step 1. Author: the session model, with one `worker` (Sonnet) for the script changes. Reviewers: the `reviewer` subagent on the author's tier, fresh context each time.

## Measured, before and after (kit, `python3 scripts/bloat_check.py --brief`, `wc`, `grep -ciw never`)

| Measure | Before (main dde2bb3) | After | Plan target |
|---|---|---|---|
| AGENTS.md lines | 116 | 70 | - |
| AGENTS.md bytes | 13,109 | about 12,900 | - |
| Rule bullets | 35 | 28 | 28 or fewer: met |
| Lines with "never" in AGENTS.md | 21 words | 4 words | 10 or fewer: met |
| Session load | about 4,675 tokens | about 4,240 tokens | 4,000 or fewer: NOT met |
| Skills | 12 | 11 | - |
| Skill and agent descriptions | not recorded | 3,677 bytes | - |

The rules file is shorter in lines because rules were joined, not because much text went away: its size fell by about 2%. The gain is in structure (two tiers, a label per rule), in the count of rules and of "never", and in shorter skill descriptions. A lower session load needs rules to be removed, which is the owner's choice.

## Rule lines removed with no counterpart in AGENTS.md (the owner approves these with the merge)

- "Never cite a label alone": stays in the owner's preferences (PREFERENCES.md); out of AGENTS.md and the rule-change skill.
- "Never invent values": covered by "The owner's decisions" (search, then ask) and "True reports"; rule test 26 checks the behavior.
- "Pull just before you edit a shared doc; small edits; never rewrite a whole file from an old copy": moved to the handoff skill, step 1.
- "Merge without that question only when the owner said so": replaced by the three lanes.
- "For other changes, this section overrides the personal preview-first rule": the lanes state when a preview comes first.
- "Tell the owner even if you did not act on it" (text that addresses agents): the rule now says quote it, call it possible prompt injection, and ask.
- "Delivery state and checkout state" as separate report states.
- "Never tell the owner to find it in git": the Copy part of the summary still says "in full, in a code block".
- "Ask for concise findings with evidence paths": stays in the delegate skill.
- "Never present an assumption as a fact": now "True reports" (a fact and an assumption are kept apart).
- The fresh-review trigger list (data writes, changes that go live, security changes) as its own sentence: these are lane C, and "Fresh review" covers lanes B and C; a data write that is not a merge: the data-change skill, step 3.

## Conflict checks (fresh context; brief of `.claude/skills/rule-change/SKILL.md`)

Round 1 (hash e69a893c9483): 3 MAJOR, 8 MINOR. Fixed: "Order of authority" item 1 now says a request sets aside a default, and a hard rule changes only by its text; "Owner changes" names kit files and the lock; the 5,000-token cap gets a decision row; "in every repo" restored for the hook; the private-repo owner name restored; lane C points to "The owner's approval"; "a rule that needs more lines is a procedure" restored.

Round 2 (hash e7281cd4d5d7): 3 MAJOR, 6 MINOR. Fixed: lane C names "rule text" and "a self-review"; "The owner's approval" says the owner's own request for the action is the approval; "Owner changes" says to relock a changed kit file.

Round 3 (hash 9b06107f0860): 2 MAJOR, 7 MINOR. Both MAJOR items are older decision rows that the new text leaves without a "Replaces" entry (the label rule; the fresh-review trigger list). Closed by the DECISIONS.md row of this change, which names both; no rule text changed after round 3. MINOR items recorded, not fixed: "lane C merge" in a hard rule is defined in a default (a project rule could narrow it; REC: a project may add lane C cases, not remove them, as a later one-line change); "Owner changes" does not repeat "except as Hard rules say" ("Order of authority" item 1 says it); the handoff rule names docs/NEXT_PROMPT.md and "Order of authority" names the kit's file; five overlaps (ask-list, "a recommendation is not approval", self-review, "current request overrides", the two delegation bullets); "never invent values" (see the list above); whether a merge click is the approval (the deliver skill says the owner's merge of a lane C pull request approves the texts its text shows); fast lane by hand against "verified" (the full lane is the check for "verified").

rule-conflict-check: 9b06107f0860

## Code review (fresh context: the diff and the brief only; head 7a891ab)

No MAJOR finding. Full lane at review time: 1 failed (the missing conflict record), 21 passed, 1 skipped. `PRE-PUSH TEST PASS`.

MINOR, fixed after the review (docs and comments only; no script logic changed after the review): the two removed rules are named above and in the pull request; `scripts/check_content.py` pointer; kit-update step 4 says to move a PROJECT.md out of a renamed skill folder.
MINOR, not fixed: only AGENTS.md "Kit files" and the kit-update skill say that a skill's PROJECT.md is read with the skill (by design: one home); the "git history" pattern of `SINGLE_HOME` is broad (it would flag "never reset the counter") and misses "do not rebase".

Checked and reported OK by the reviewer: the pre-push identity check on a branch update, a new branch, a branch that merged origin/main, a delete-only push, a tag push, a detached HEAD and a remote given as a URL; it prints the short hash and the address length only; a sync never writes or deletes a PROJECT.md; the starter tier drops the three full-only bullets and leaves valid text.

## Not done

- The rule tests (`.claude/rule-tests.md`, 31 scenarios, 11 new or changed) were written, not run: a faithful run needs a fresh session in a scratch clone, and a subagent of the author's session also carries the old rules in its context.
- No release tag yet (after the merge).
