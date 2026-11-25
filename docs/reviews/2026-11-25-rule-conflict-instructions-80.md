# Rule conflict check: "Instructions people follow" at 80% (2026-11-25)

Changed line: the hard rule "Instructions people follow" in AGENTS.md. Its middle text changed to the text the Maintainer approved on 2026-11-25 (plan: [2026-11-25-instructions-80-plan.md](2026-11-25-instructions-80-plan.md)). The rest of the line is the same.

Reviewer: the `reviewer` subagent, Opus tier, fresh context. It got the changed line with its old text, the whole AGENTS.md, docs/DECISIONS.md, the `instructions` skill and rule-tests row 36, with the kit brief ("Find conflicts, overlaps, and rules that a decision row contradicts ... Do not judge whether the rules are good.").

## Findings and what was done

| # | Severity | Finding | Done |
|---|---|---|---|
| 1 | MAJOR | The old rule allowed "the numbered actions that are all on one screen"; the new rule allows "up to three short actions on one screen". The skill and the check still allowed a lead-in step with any number of numbered actions. | The approved rule text stays. The skill and `scripts/check_instructions.py` now count the numbered actions of a lead-in as its actions (at most 3; more go in more steps). New test case: a lead-in with 4 actions fails. |
| 2 | MINOR | The skill's context check added a wait cue whenever something "goes wrong" early; the rule says wait "only when acting early breaks something". | The skill now says: a wait cue when acting early breaks something; a "Do not ..." sentence for the other-window case. |
| 3 | MINOR | The skill restated the rule's clauses (a second home). | The step form now points to AGENTS.md and keeps only the format and the example. |
| 4 | MINOR | Attribution tags in text that ships to projects (skill and check header). | Removed; the record is the 2026-11-25 row of docs/DECISIONS.md. |

The MAJOR finding needed no new rule text, so it does not go back to the Maintainer.

rule-conflict-check: 8fbc03e13926
