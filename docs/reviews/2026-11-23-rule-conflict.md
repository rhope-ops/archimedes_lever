# Rule conflict check: kit 11.0.0 role swap (fleet v2 DEC 2)

Date: 2026-11-23 (America/Chicago). Procedure: `.claude/skills/rule-change/SKILL.md`, "Conflict check".
Changed lines: the AGENTS.md lines that `python3 scripts/bloat_check.py --rules` lists at commit 2c4cc7c (the mechanical
swap "the owner" -> "the Maintainer", the heading "Owner changes" -> "Maintainer changes", and the DEC 2 header sentence).
Reviewer: the `reviewer` subagent, fresh context, strong tier (Opus 5.5), given only the changed lines, AGENTS.md,
docs/DECISIONS.md and the brief of the skill.

## Findings

| # | Severity | Texts | Case | Fix (proposed) | Status |
|---|---|---|---|---|---|
| 1 | MAJOR | AGENTS.md:3 "the Content Approver approves content changes" against :39 "Decisions": "Ask the Maintainer about ... content approval" | A content change, when two people hold the two roles: two orders for whom to ask | Change :39 to name the Content Approver for content approval (exact text: KIT_HANDOFF "Needs the owner") | To the owner before the merge |
| 2 | MINOR | :3 "the Release Manager makes tags and releases" against :29 (ask the Maintainer before a live or irreversible effect); DECISIONS rows "Tags" and "Kit owner" | A release when two people hold the roles | Name the Release Manager at :29, or say at :3 that the Maintainer approves releases | Recorded |
| 3 | MINOR | The new :3 no longer defines "Owner"; still used at :31 ("the Owner's own message"), :7 (`- Owner:` label), :76 (kit Project rule "Fleet choices") | Who may waive the STE rule; who confirms fleet choices | Add "The `- Owner:` line names the Maintainer." to :3, or swap those words by an approved change | Recorded (kept on purpose by the DEC 2 scope, DECISIONS 2026-11-23 row) |
| 4 | MINOR | :60 "a running owner" (an agent or task) is close to the role word | Reading | "a running agent or task" | Recorded |

Checked and OK: the swap is mechanical (the old lines with the swap applied equal the new lines); DEC 14 against Lane C
(:43) is no conflict (the Maintainer's own request is the approval, :29); the removed "public repo uses a role" text
is still covered by :26.

rule-conflict-check: 3008d5e5983d
