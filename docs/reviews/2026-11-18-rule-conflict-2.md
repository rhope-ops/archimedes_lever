# Rule conflict check, 2026-11-18 (second of the day): the plan "one `check`, one home per rule"

Reviewer: the `reviewer` subagent, fresh context, on the author's model tier (inherit). Input: the changed lines as `bloat_check.py --rules` lists them, the whole AGENTS.md, docs/DECISIONS.md and the fixed brief of `.claude/skills/rule-change/SKILL.md`. The author checked each finding against the files: all hold.

Changed lines (8, approved by the owner the same day): "Delivery" 1, "Delegation" 3, "Personal data" 2, "Git safety" 1, "Checks" 2, "Bloat, drift and assumptions" 4, "Rules and decisions" 3, "Handoff".

rule-conflict-check: 2950084f0f7b

## Findings: 2 MAJOR, 9 MINOR

| # | Severity | Finding | Action |
|---|---|---|---|
| 1 | MAJOR | "Handoff" puts the kit's plan in the pull request text, but "Start of session" reads only docs/NEXT_PROMPT.md, so a restarted kit session finds no plan; a pull request text cannot be "pushed". | To the owner: new text for both lines. |
| 2 | MAJOR | "Delivery" says merge when the lane is green and the review is clean; "Authority" and the 2026-11-13 row "Merge without per-PR approval" say ask for live or irreversible effects. | To the owner: the exception line names those cases. |
| 3 | MINOR | The 2026-11-16 "Audit" row ("only the owner merges") was not in "Replaces". | Done: the approval row of 2026-11-18 names it; the audit and port skills no longer say it. |
| 4 | MINOR | The rule says a skill that "states" a rule fails; decision 3 said "contradicts". | Record: the check finds a second statement (a contradiction is one); the approved rule text is the home. |
| 5 | MINOR | The two 2026-11-16 rows with the exact text of the guard bullet were not in "Replaces". | Done in the row of the final texts. |
| 6 | MINOR | "Personal data" is unclear on whether the push scan needs `.check`; "names or terms" against "DENYLIST". | To the owner: clearer text. |
| 7 | MINOR | "instruction files" names two different lists ("Rules and decisions", "Delegation"). | To the owner: "Delegation" points to the one list. |
| 8 | MINOR | Does a self-review satisfy the merge condition? | To the owner: one clause. |
| 9 | MINOR | The full-lane gate is in "Checks" and "Delivery" and names no deciding run (local green, Action red). | To the owner: "Checks" names it. |
| 10 | MINOR | The lock of kit files (decision 4) can block a change the owner asks for in a project. | Step 4 of the plan states the path (change it in the kit, then sync). |
| 11 | MINOR | The "Commands" Test line lists less than the lanes run. | Done: the line names the two commands and points to the header of scripts/check.sh. |

Checked with no finding: "Git safety"; "Never push to main directly" against the host-limit line; the header; "Project rules".

A later change of these lines makes a new hash and needs a new check (the record of it follows below when it exists).

## Second check, after the owner approved 6 changed texts

Same reviewer type, a new fresh context, same input and brief.

rule-conflict-check: f81c2ce9429d

| # | Severity | Finding | Action |
|---|---|---|---|
| 1 | MAJOR | The kit's handoff in the pull request text is not a source in "Order of authority", and "Untrusted input" treats pull-request text as data; with no open pull request there is nothing to read. | To the owner: a repo file for the kit's handoff, named in all three lines. |
| 2 | MAJOR | "never add an allow or skip entry: only the owner does" against "when the owner asks ... make it" (already on main; the new text widened it to skip entries). | To the owner: "unless the owner asks for that entry". |
| 3 | MINOR | A clean self-review: "Delivery" says merge, "Delegation" says ask. | "Delegation" is the more specific line; no text change proposed. |
| 4 | MINOR | "Delivery" asks for a live effect; "Authority" lists only irreversible effects. | To the owner: "live or irreversible effects". |
| 5 | MINOR | The full-lane condition is in "Delivery" and in "Checks". | To the owner: "Delivery" points to "Checks". |
| 6 | MINOR | Local run red, Action green: which decides? | To the owner: never merge while either is red. |
| 7 | MINOR | "a lane that the hook runs next" now covers only the fast lane. | To the owner: name the fast lane. |
| 8 | MINOR | The kit handoff when no pull request is open. | Solved by the fix of finding 1. |
| 9 | MINOR | "DENYLIST", "word lists", "the words of a list". | Accepted: DENYLIST is the script's output line; "word lists" covers names and terms. |
| 10 | MINOR | The cap values are in the rule and in the script. | Accepted: the owner approved the text with the values; the script is the enforcement. |
| 11 | MINOR | Rows not named in "Replaces": "Merge without per-PR approval" (2026-11-13) and the 2026-11-15 rows that name `.pii-guard`. | Done in docs/DECISIONS.md with the final texts. |
