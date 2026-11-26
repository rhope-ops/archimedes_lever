# Rule conflict check: AGENTS.md "Project log" (kit 14.0.0)

Date: 2026-11-25 (America/Chicago). The changed line is in "Defaults", not "Hard rules", so this is the short record (rule-change skill, "Conflict check" step 4).

Old line:

> - **Project log.** Write a project log row only for a story event (a decision, milestone, breakthrough or miss), in the turn it happens: in docs/LOG.md, unless "Project rules" names another place (a public repo names a private place). Format: `.claude/skills/project-log/SKILL.md`. If you cannot write to the log, put the full entry in your turn summary under Copy, with "Paste into: project log".

New line:

> - **Project log.** Write a project log row only for a story event (a decision, milestone, breakthrough or miss), in the turn it happens: in docs/LOG.md, unless "Project rules" names another place (a public repo names a private repo). Format, and the steps for a log in a private repo: `.claude/skills/project-log/SKILL.md`. Only when that place refuses the write, put the full row, in the log's table format, in your turn summary under Copy, with the refused step and "Paste into: project log".

Step 1 search (AGENTS.md, all sections and header values; docs/DECISIONS.md):

- "Secrets and personal data": the log rows stay free of personal data in the private repo too; the skill runs the content check before the push. No conflict.
- "Git history" (never push to the default branch): the log branch `claude/project-logs` is not a default branch. No conflict.
- docs/DECISIONS.md 2026-11-13 (the kit's own log is public by the owner's decision): the old line had the same "a public repo names a private place" clause, so the kit's exception is unchanged. No new conflict.
- docs/DECISIONS.md 2026-11-25 (private log repo decision): the new line follows it.

Result: no conflict, no overlap. The pull request's fresh review reads the line again.

rule-conflict-check: a3e7acd8ce66
