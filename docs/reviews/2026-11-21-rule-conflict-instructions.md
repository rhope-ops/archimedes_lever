# Rule conflict check: "Instructions people follow" (2026-11-21)

- Changed line: the new AGENTS.md "Hard rules" bullet **Instructions people follow.** (the owner's exact text of 2026-11-21, kit PR 104).
- Reviewer: the `reviewer` subagent, a fresh context, model tier opus (the author's tier). Input: the changed line, the whole AGENTS.md, docs/DECISIONS.md and the brief of `.claude/skills/rule-change/SKILL.md` "Conflict check". It did not get the author's view.
- Result: 2 MAJOR, 4 MINOR. The MAJOR findings go to the owner before the merge (the rule text is the owner's; the author does not reword it).

## MAJOR

1. **The rule against "Reporting" and "Host limit" (Defaults).** "Show each step on the screen where the action happens" covers messages and hand steps; "Reporting" puts steps for the owner in the chat summary (Copy), and "Host limit" puts "what unblocks it" in the chat report. Case: an agent asks the owner to paste text into GitHub settings; the chat is not that screen. Fix proposed: add "(in chat: the step names the screen where the action happens)". Related: the skill's "no link to another file" against "full clickable links" in "Reporting".
2. **The rule against the owner's personal preferences.** "Reporting" and "Decisions" follow the format of the owner's preferences (rank 3 in "Order of authority", below a hard rule); the rule's only exception is "the Owner's own message". Case: the preferences set another language or style. Fix proposed: "unless the owner's own message or personal preferences say otherwise".

## MINOR (recorded; no change of rule text for these)

3. "Owner's own message" against "Owner changes" (a brief from a task the owner started): which channel can lift the rule is not named. The capital "O" in "Owner" is out of the file's style.
4. "Enforced: `scripts/check_instructions.py` on every push" is broader than the check: with no `audit-instructions:` line in `.check` it checks no file (the kit itself today).
5. The step parts in the rule repeat "The step form" in the skill ("One home").
6. "Enforced: the skill before any such text" overlaps "Skills"; acceptable as a pointer.

Checked and OK: the DECISIONS row agrees with the rule; no conflict with "Rule text", "Guards and checks", "Fresh review" or "README".

rule-conflict-check: 4fc72c5af855

## Second check: the changed line (2026-11-21)

The owner changed the line in this session's question dialog: "(in chat: the step names the screen where the action happens)" after "at the time it is needed" (finding 1 above); the exception stays "the Owner's own message" (finding 2 above: no change). A fresh `reviewer` subagent (opus) checked the changed line with the same input and brief.

- Result: no MAJOR finding. 6 MINOR, recorded:
  1. "Delivery" lane A merges a README step change on green checks, while the rule asks for "a fresh-reader test before release" ("release" is not defined).
  2. "Owner changes" accepts a brief from a task the owner started; the exception needs "the Owner's own message".
  3. The step form is in the rule and in the skill ("One home", "Lean instructions").
  4. "on every push" is not true in the kit while `.check` has no `audit-instructions:` line (the owner decided: a later pull request rewrites the kit's own README steps and adds the lines).
  5. "Reporting" (the owner's preferences) and the rule both cover steps in a turn summary.
  6. The skill added an owner-approval case ("goes to the owner"): fixed in the skill ("Fix each marked step before the release").

rule-conflict-check: 62190488efd6
