# Rule conflict check: tool retirement P1 (AGENTS.md C1-C3, C7-C12)

Fresh-context check, 2026-11-23 ~17:36 America/Chicago, `reviewer` subagent on the strong tier (Opus), per
`.claude/skills/rule-change/SKILL.md` "Conflict check". Input: the changed lines as `python3 scripts/bloat_check.py --rules`
lists them on branch claude/tr-p1, the whole AGENTS.md and docs/DECISIONS.md; not the author's view or the plan.

First run on hash 3d5e2184a902 (the approved texts). Second run, on the changed C9 line, below.

## MAJOR (to the Maintainer before the merge)

1. Decision row 112 (2026-11-23, fleet v2 DEC 2): "Not changed: 'the Owner's own message' in 'Instructions people
   follow', ... the kit's own Project rules". C10 changes that text to "the Maintainer's own message"; C11 changes
   "Fleet choices" (including its dated attribution "(the owner, 2026-11-19)"). The plan (section 3, "Change against
   the prompt's T6 text") disclosed it, but no DECISIONS row replaces that part of row 112.
2. Decision row 109 (2026-11-13): "AUDIT DUE is reported and asked, never run unasked". The new "Caps and audit" text
   ("The full audit runs when the Maintainer asks for it and for all fleet repos at each kit release or 14 days after
   the last one") and skill text S3 ("At each kit release, or 14 days after ..., run the full audit") read as an audit
   run without asking.

Resolution (the Maintainer, question dialog, 2026-11-23 17:37):
- MAJOR 1: "Keep texts, add Replaces": C10 and C11 stay as approved; the plan-approval row in docs/DECISIONS.md replaces
  row 112's "Not changed" list for the role word.
- MAJOR 2: "Approve the new texts": C9 now says "The full audit runs when the Maintainer asks for it; at each kit
  release or 14 days after the last fleet audit the check-in reports AUDIT DUE (fleet) and you ask; ...", and S3 says
  "... report it and ask the Maintainer; when the Maintainer says yes, run the full audit ...". Row 109 stands. This
  also fixes MINOR 6. The changed C9 line makes a new hash: the check ran again on it (below).

## MINOR (recorded; no further rule-text change)

3. "Fresh review": "only the number moved is MAJOR", while "Caps and audit" allows an approved higher baseline (a
   change where only a number moves). Read with the approval: a Maintainer row approves the number (T2).
4. "Fresh review" partly repeats "Guards and checks" ("a pass must mean the work is right").
5. "fleet debt" and "fleet repos" are not defined in AGENTS.md; the text reaches projects without `fleet: on`.
6. "14 days after the last one": the last release or the last audit (the skill says "the last fleet audit").
7. Row 14 ("450-line cap for hand-written code") against "file size only warns" (decision 1 = A, plan 2026-11-23).
8. The merged "Decisions" text: "(without them:" became "(else"; "binds ... every session only as a line" reads
   less clearly than before.

## No finding

"Host limit" into "Delivery"; "README" into "One home" (matches row 24); "Decisions" against "Order of authority";
the session-load and third-party caps (rows 17, 30); "Lean instructions" against "Rule text".

## Second run (hash 0abd68228388, the changed C9 line)

Fresh-context `reviewer` (Opus), 2026-11-23 ~17:40, same inputs and brief.

- MAJOR: the new C9 and S3 texts had no DECISIONS row. Fixed: a row By the Maintainer quotes "Approve the new texts"
  (2026-11-23 17:37) and names what it replaces.
- MINOR: the plan-approval row's Replaces cell did not name the 2026-11-21 "Instructions people follow" row. Fixed.
- MINOR (recorded): "One home" now ends with the README sentence's "Enforced in part: `scripts/bloat_check.py`",
  which reads as if it covers the whole bullet.
- No finding: Start of session against Caps and audit (`bloat_check.py` prints "tell the Maintainer and ask"),
  Delivery with the host-limit sentence, Decisions against Order of authority, Fresh review against Guards and
  checks, Lean instructions against the rule-change skill, Fleet choices (covered by Replaces).

rule-conflict-check: 0abd68228388
