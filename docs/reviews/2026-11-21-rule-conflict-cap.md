# Rule conflict check: session-load cap 5,500 (2026-11-21)

Changed line (AGENTS.md "Caps and audit", a default; only the number changes):

- before: "... fails when this file passes 200 lines, when the session load passes 5,000 tokens ..."
- after: "... fails when this file passes 200 lines, when the session load passes 5,500 tokens ..."

Only a default changed, so this is the short record (`.claude/skills/rule-change/SKILL.md`, "Conflict check", item 4). Step 1 search of AGENTS.md and docs/DECISIONS.md for the same topic:

- AGENTS.md: no other line states the cap.
- docs/DECISIONS.md 2026-11-20 (third-party skills): recorded the approved "Caps and audit" text with 5,000. Replaced by the 2026-11-21 row.
- docs/DECISIONS.md 2026-11-18 (session load over the cap after 2.0.0): "not with project trims or a higher cap", scope kit 2.0.1. It does not bind this change; the 2026-11-21 row names it.
- `scripts/check_settings.py` `AUDIT_DEFAULTS` and `KIT_CAPS`: the code home of the number; changed in the same commit, with the two tests that name it.

Result: no conflict left. Author: Claude (main session); the fresh diff review of the pull request follows.

rule-conflict-check: 924f85aab3fb
