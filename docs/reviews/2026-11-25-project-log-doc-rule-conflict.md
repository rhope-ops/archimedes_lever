# Rule conflict check: AGENTS.md "Project log" (kit 14.0.0)

Date: 2026-11-25 (America/Chicago). The changed line is in "Defaults", not "Hard rules", so this is the short record (rule-change skill, "Conflict check" step 4). The PR's fresh review reads the line again.

Old line:

> - **Project log.** Write a project log row only for a story event (a decision, milestone, breakthrough or miss), in the turn it happens: in docs/LOG.md, unless "Project rules" names another place (a public repo names a private place). Format: `.claude/skills/project-log/SKILL.md`. If you cannot write to the log, put the full entry in your turn summary under Copy, with "Paste into: project log".

New line:

> - **Project log.** Write a project log row only for a story event (a decision, milestone, breakthrough or miss), in the turn it happens: in docs/LOG.md, unless "Project rules" names another place (a public repo names a private Claude doc). Format, and the steps to add a row to a Claude doc: `.claude/skills/project-log/SKILL.md`. Only when that place refuses the write, put the full row, in the log's table format, in your turn summary under Copy, with the refused step and "Paste into: project log".

Step 1 search (AGENTS.md, all sections and header values; docs/DECISIONS.md):

- "Secrets and personal data": the content check hook covers `mcp__Claude_Docs__update`, so a row is checked before it is written. No conflict.
- "The Maintainer's approval" (a data write): the Maintainer's decision of 2026-11-25 sets the log doc as the place for each row, and the old line already asked for the write. No new conflict.
- docs/DECISIONS.md 2026-11-13 (the kit's own log is public): the clause for a public repo names a private place, as before; the kit's exception is unchanged.

Result: no conflict, no overlap.

rule-conflict-check: 284fd2660e67
