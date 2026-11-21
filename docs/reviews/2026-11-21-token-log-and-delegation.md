# Token log and delegation: evidence and open items (2026-11-21, America/Chicago)

Session: "Token use tracking" (renamed at handoff). Branch of work: ccr-faf67883-token-fixes (merged). Times in America/Chicago.

## Merged to main

| PR | Merge commit | What |
|---|---|---|
| #97 | fbdda6d | `agent` column in the token log (subagent type per row; `main`, type, or `unknown`). |
| #98 | f4a1442 | Token log: non-text message id skipped; non-number or infinite token count counts as 0. Delegation wording (owner-approved). Conflict-check records. |

Checks on the merged head (54fe9e6): full lane 26 passed, 1 skipped; CI `checks` success.

## Token data (aggregated; no rows shown)

- Source: the token log on branch `claude/token-usage` in 6 tracker repos (archimedes_lever, icf-source, sec-source, 33-332.Z, RADE, 90-161.Z). 27,781 API calls, deduplicated by message id, days in America/Chicago. Query: `daily.py` and `models.py` in the session scratchpad.
- Total 6.22 B tokens; 97.8% cache reads.
- Subagent calls: 11,944 on opus (86% of subagent tokens); 1,217 sonnet; 727 fable; 16 haiku. The `scout` role (haiku) was almost unused.
- Cause not confirmed: the log had no agent type until PR #97. Built-in agents with no pinned model inherit the main model. The `agent` column is the first data that can test this. Confidence: low on cause, high on counts.

## Delegation rule (AGENTS.md "Delegation", owner-approved text)

- Text in force: "Delegate only substantial independent work (about 30 minutes or more, and the fresh review) with bounded files and measurable done criteria. Exception: the main session sends searches, file lists and summaries of test or log output to `scout` at any size and scope. ..."
- Skill (`.claude/skills/delegate/SKILL.md`, size rule): "Where the host has no subagents, do it yourself. Do other small tasks yourself."
- Conflict-check records: `docs/reviews/2026-11-21-rule-conflict-scout.md` (hashes 5e8df6ce3d96 and 15f2316c8448). The final text has a recorded check; no MAJOR finding.

## Open items (not done; owner decision)

1. Non-text timestamp still drops the session's rows (`scripts/token_log.py`, `log_rows` / `to_csv` sort; predates PR #97). Fix in a separate pull request with a review. REC: do it.
2. Five MINOR wording findings on the Delegation line (`docs/reviews/2026-11-21-rule-conflict-scout.md`, "Final wording, second check"): (1) the parenthesis can read as "30 minutes AND the review"; (2) skill sentence "Do other small tasks yourself." can cut against a lane B reviewer; (3) "sends" can read as an order; (4) the exception does not name the bounded-files and done-criteria clauses; (5) "main session" vs "orchestrator". REC: approve 1, 3, 5; delete the sentence in 2; reword 4 to "Exception to size, files and done criteria".
3. Decision row in `docs/DECISIONS.md` (2026-11-21, Delegation) says the wording before the exception had a MAJOR conflict in an earlier fresh check. No repo file records that check. The owner should confirm or remove the clause.
4. Docstring of `tokens()`: "non-numeric text" is loose ('1.5' also returns 0). Change to "text that is not an integer" with item 1.

## Process notes

- Subagent findings were checked against the code; several were fixes that needed their own review (a fix after a review gets its own review).
- A failed CI on intermediate commits (2b9af52, 109aa95) was caused by a missing conflict-check record for the rule text in force then; the head that merged was green.
