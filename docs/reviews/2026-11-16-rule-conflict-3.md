# Rule conflict check: 2026-11-16, the guard bullet names the hook

Fresh-context check of the rule line that changed against origin/main (`.claude/skills/rule-change/SKILL.md`, "Conflict check"). The owner approved the new text on 2026-11-16 (docs/DECISIONS.md, row "Personal-data scan of outgoing content").

## Changed line

- `+` "The guard (`scripts/pii_guard.py`, on when `.pii-guard` exists) checks every push and pull request, and a PreToolUse hook (`pii_guard.py --hook`, `.claude/settings.json`) checks each outgoing tool call. When it blocks, ..." (rest unchanged)
- `-` the same bullet without ", and a PreToolUse hook (...) checks each outgoing tool call".

## Reviewer

`reviewer` subagent, model set to Opus (the author's tier), given only the changed lines, AGENTS.md and docs/DECISIONS.md.

Result: no conflict, no overlap, no decision row contradicted. Two notes, for the owner (no fix required):

1. Wording: "each outgoing tool call" is wider than the hook's matcher, which names the call types (Agent, Artifact, SendUserFile, web, GitHub write, Gmail, Docs/Drive/Sheets, session messages). Narrower text would need the owner's approval.
2. Clarity: in "When it blocks", "it" can now mean the guard or the hook. Both lead to the same skill, so they give no different orders.

rule-conflict-check: a76ca0a80bcc
