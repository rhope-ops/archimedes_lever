# Conflict check: narrower scout exception (2026-11-21, America/Chicago)

Only a default changed (AGENTS.md "Delegation"), so this is the short record of `.claude/skills/rule-change/SKILL.md` "Conflict check", item 4.

## Changed line

- Old: "Exception: the main session sends searches, file lists and summaries of test or log output to `scout` at any size and scope."
- New: "Exception: the main session sends searches that span many files, and summaries of long test or log output, to `scout`; it does a lookup with a known target itself."

## Step 1 (same topic in AGENTS.md and docs/DECISIONS.md)

- AGENTS.md "Agents" (line 56) points to the delegate skill: no conflict.
- docs/DECISIONS.md 2026-11-21 "Delegation, final wording": it recorded the old exception text. The new row of 2026-11-21 replaces it ("Replaces" column).
- docs/DECISIONS.md 2026-11-13 (a fix after a review gets its own review): no conflict.
- Delegate skill, "Model routing": "Search, file lists, summaries of test or log output" go to `scout` when delegated; the new text decides when to delegate, not to whom. No conflict.

Result: no conflict, no overlap. Approval: the owner, 2026-11-21 ("i approve your fixes. proceed", on the text shown in full).

rule-conflict-check: 17d51f073a30
