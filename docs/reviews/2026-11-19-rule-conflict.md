# Rule conflict check: kit 4.0.0, session names (2026-11-19)

Changed lines: AGENTS.md "Start of session" (output lines list adds `TITLE, SESSIONS`); new header line `- Short name: {{SHORT_NAME}}`.
Reviewer: fresh `reviewer` subagent, Opus tier (same tier as the author), given only the changed lines, AGENTS.md, docs/DECISIONS.md and the handoff skill section; brief as in the rule-change skill.

| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | MAJOR | Archive step vs "The owner's approval": no rule line holds the owner's standing approval. | The owner gives it in the account preferences (layer 3 of "Order of authority"); the skill names it. A rule line would push RADE and icf-source over the 5,000 cap. |
| 2 | MAJOR | The pointer did not reach the PR-number and archive steps. | TITLE line names `.claude/skills/handoff/SKILL.md` "Session names"; deliver skill step 3 points to steps 3 and 6. |
| 3 | MINOR | "merged or closed" vs the decision "merged". | Skill says merged. |
| 4 | MINOR | Archive vs "Unattended work" and "Git history" (agents and scheduled tasks). | Skill counts their pull requests and waits while they are pending. |
| 5 | MINOR | Resume-prompt title vs start date. | Resume prompt gives the title without date and PR number; a title from a resume prompt gets today's date. |
| 6 | NIT | Fallback short name not in the skill. | Skill states it. |

All findings fixed in the same pull request. Code review (separate fresh reviewer, Opus): no MAJOR; MINOR and NIT findings fixed (trim in check-in, short-name self-tests, merged-only, archive after verify, handoff margin note).

rule-conflict-check: ed75f93bad28
