# Rule conflict check: 2026-11-16, second kit pull request

Fresh-context check of the rule lines that changed against origin/main (`.claude/skills/rule-change/SKILL.md`, "Conflict check"). The owner approved both texts on 2026-11-16 (docs/DECISIONS.md).

## Changed lines

- `+` "Handoff" bullet, with "Steps: `.claude/skills/handoff/SKILL.md`." appended.
- `+` `scripts/bloat_check.py` bullet, with "A run slower than its baseline: `.claude/skills/efficiency/SKILL.md`." appended.
- `-` the same two bullets without the appended text.

## Reviewer

`reviewer` subagent, given only the changed lines, AGENTS.md, docs/DECISIONS.md, the two skills the pointers name, and the brief in the skill.

- Run 1: Sonnet tier. Result: no conflict. Not counted: its tier is lower than the author's (Opus). The `reviewer` agent's default tier is lower, so the skill now says to set the model.
- Run 2: Opus tier. Result: no conflict between rule lines. Two findings in the skill text the pointers lead to, both fixed in this pull request:
  1. CONFLICT (minor): `efficiency` step 1 said to run the slow process 2 more times; AGENTS.md "Checks" says not to run by hand a lane that the hook runs next. Fix: a hook run counts as one of the 3 runs.
  2. OVERLAP: `handoff` repeated the 40-line cap and the evidence place from AGENTS.md "Handoff". Fix: the skill points to the AGENTS.md values.

rule-conflict-check: 905e23d5e43e
