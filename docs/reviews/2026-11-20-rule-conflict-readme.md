# Rule conflict check: "README" (new default), 2026-11-20

Changed line (AGENTS.md "Defaults", added; text approved by the owner in this session, answer "3a"):

> - **README.** A change that alters what the project is, does, or how to install, run or use it updates README.md in the same pull request; README.md opens with the "Purpose" line of this file. Enforced in part: `scripts/bloat_check.py`.

Only a default changed, so this is the short record (`.claude/skills/rule-change/SKILL.md` "Conflict check", step 4): step 1 of "Steps" by the author.

## Step 1: same topic in AGENTS.md and docs/DECISIONS.md

- AGENTS.md: no other line names README. Nearest lines:
  - "One home": a change removes what it makes obsolete (docs included) in the same commit. Overlap, not a conflict: "README" adds that an affected README is updated, and what it must open with.
  - "Handoff": status lives in repo files. No conflict: README describes the project; the handoff holds status.
- Header value `- Purpose:`: the new line reads it; it does not change it.
- docs/DECISIONS.md: the 2026-11-13 de-duplication row says README links to FILES.md, FIRST_USE.md and PREFERENCES.md. No conflict: that row sets links in the kit README; the new check skips the kit (its Purpose is the `{{PURPOSE}}` template value).

## Result

No conflict, no MAJOR finding. Lint: no vague word; the line names the script that enforces it. The kit bullet count is 30 (guide 28; it only warns).

rule-conflict-check: 5a514e87e120
