# Rule conflict check: 2026-11-16, "one line per rule"

Fresh-context check of the rule line that changed against origin/main (`.claude/skills/rule-change/SKILL.md`, "Conflict check"). The owner approved the new text on 2026-11-16 (docs/DECISIONS.md).

## Changed line

- `+` "Instruction files and host prompts hold rules only, one line per rule (every line costs tokens on every task and can lower adherence); a rule that needs more lines is a procedure. A rule a hook or test enforces becomes a pointer to it; a procedure that only some tasks need becomes a skill."
- `-` the same bullet with "one line each where possible (...)." in place of "one line per rule (...); a rule that needs more lines is a procedure."

## Reviewer

`reviewer` subagent on the Opus tier (model: inherit), given only the changed lines, AGENTS.md, docs/DECISIONS.md and the rule-change skill.

Result: no conflict. Two minor findings, for the owner before the merge:

1. OVERLAP: "A rule is a line in this file" ("Rules and decisions") and "one line per rule" ("Bloat, drift and assumptions") both say a rule is one line. They agree; duplication, not a conflict.
2. DECISION (soft gap): the new text does not say where a procedure that every session needs goes. The Agent row of 2026-11-16 (not yet approved by the owner) keeps the 2 "Start of session" bullets in AGENTS.md; a reader could argue they must move out.

rule-conflict-check: 621887e48487
