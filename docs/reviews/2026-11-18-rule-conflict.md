# Rule conflict check: 2026-11-18, save an approved plan; continue it after a restart

Fresh-context check of the rule line changed against origin/main (`.claude/skills/rule-change/SKILL.md`, "Conflict check"). Reviewer: `reviewer` subagent, model Opus (the author's tier). It got only the changed line, AGENTS.md and docs/DECISIONS.md.

## Changed line (AGENTS.md "Handoff")

- `+` appended: "When the owner approves a plan, save it in docs/NEXT_PROMPT.md with the approval date and push it before step 1; after a restart or a compaction, continue it without a new review." The owner approved this exact text on 2026-11-18 (docs/DECISIONS.md).

## Findings

1. Conflict with "Delegation" ("a fix made after a review gets its own review"): "without a new review" can be read as skipping a code review. Proposed rule fix: "without a new plan review or approval". To the owner.
2. Conflict with the 40-line cap of docs/NEXT_PROMPT.md: a long plan does not fit. Fixed in the handoff skill: a long plan goes in docs/reviews/, linked from NEXT_PROMPT.
3. Conflict with the handoff skill: the kit clone must not fill NEXT_PROMPT. Fixed in the skill: in the kit clone, the plan goes in the pull request text.
4. Overlap: the skill repeated the rule. Fixed: the skill now gives only the steps.
5. Overlap with "Rules and decisions" (where to record a decision): fixed in the skill: NEXT_PROMPT "Approved plan" is the plan's canonical place.
6. Related, existing: the skill said to skip the start steps after a restart, but AGENTS.md "Start of session" runs the check-in each session. Fixed: the RESUMED line and the skill now run the check-in and skip only the plan review and repeated questions.

rule-conflict-check: b41b0311e421
