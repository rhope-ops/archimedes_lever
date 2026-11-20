# Rule conflict check: "Caps and audit" (kit 5.0.0), 2026-11-20

Changed line (AGENTS.md "Defaults"): "Caps and audit". Old: "when the session load (the start-read files plus the skill and agent descriptions) passes 5,000 tokens, or". New (approved by the owner 2026-11-20, exact text): "when the session load passes 5,000 tokens (third-party skills and agents in `.check`: own cap 1,500), or".

Reviewer: the `reviewer` subagent, fresh context, Opus tier (same tier as the author). Input: the changed lines, the whole AGENTS.md, docs/DECISIONS.md, and the skill's brief.

## Findings

- MAJOR: none.
- MINOR 1: `.claude/skills/rule-change/SKILL.md` "The caps" and the `--rules` failure text still defined the session load with every skill and agent description. Fixed in the same pull request (both now leave out the `audit-third-party` ones).
- MINOR 2: the new DECISIONS row was at the bottom of a newest-first table, with the plan link in "Replaces". Fixed: moved to the top; "Replaces" names the removed text.
- NIT 3: AGENTS.md no longer defines "session load" in the line; its definition is the `scripts/bloat_check.py` header (a pointer, per "Lean instructions"). The owner approved the whole new text in the plan. No change.
- NIT 4: the one-home check (`SINGLE_HOME`) still reads third-party skill files. Recorded; a project whose third-party file states a kit rule reports it to the kit owner.

rule-conflict-check: f5f743823d7e
