# Rule conflict check: Delegation line (scout exception), 2026-11-21

Changed line (AGENTS.md, "Delegation"), approved by the owner as the "Exception wording" option on 2026-11-21:

> Delegate only substantial independent work (about 30 minutes or more) with bounded files and measurable done criteria. Exception: the orchestrator may send searches, file lists and summaries of test or log output to `scout` at any size. Give parallel agents disjoint files, and check delegated output (diff, touched files, no approval or exemption changes) before you report it as done.

Replaces: the same line without the "Exception" sentence.

Reviewer: fresh-context `reviewer` subagent, model tier `fable` (the strongest tier; the author's tier is lower). Inputs: the whole AGENTS.md, docs/DECISIONS.md, the changed line and its old text, and the brief "find conflicts, overlaps and decision-row contradictions". The author's view was not given.

## Result

- MAJOR: none.
- Conflict: none. The exception is clear; the check clause applies to `scout` with no conflict (its output is checked before the report); subagents stay under the 30-minute sentence because the exception names "the orchestrator".

## MINOR findings (recorded; they do not change the rule text again)

1. "may" in AGENTS.md against "go to" in the skill and the decision row. A one-grep search may be done by the orchestrator, and the skill is loaded only before a delegation. Owner decision: "sends" or "may" in both places.
2. Overlap: the delegate skill repeats the scout sentence. "One home" (AGENTS.md) says to keep it in one place. Possible fix: the skill line becomes a pointer to AGENTS.md "Delegation".
3. "bounded files" and "disjoint files" in the line do not fit two parallel searches of one folder. Possible fix: "at any size and scope", or "disjoint files to edit".
4. "orchestrator" is not defined in AGENTS.md. Possible fix: "the main session".
5. Existing conflict (not created by this change): AGENTS.md "Fresh review" orders the `reviewer` subagent for a routine diff, while "Delegation" limits delegation to about 30 minutes or more. Possible fix: name the fresh review in the exception.

Checked: AGENTS.md, docs/DECISIONS.md, `.claude/skills/delegate/SKILL.md` (context), `.claude/agents/scout.md` (tools: Read, Grep, Glob).

rule-conflict-check: 5e8df6ce3d96

## Final wording, second check (2026-11-21)

Changed line (AGENTS.md "Delegation"), approved by the owner ("approve all", 2026-11-21), with the choices the agent made for the five items above:

> Delegate only substantial independent work (about 30 minutes or more, and the fresh review) with bounded files and measurable done criteria. Exception: the main session sends searches, file lists and summaries of test or log output to `scout` at any size and scope. Give parallel agents disjoint files, and check delegated output (diff, touched files, no approval or exemption changes) before you report it as done.

Delegate skill, size rule: "Size rule: AGENTS.md "Delegation". Where the host has no subagents, do it yourself. Do other small tasks yourself."

Reviewer: fresh-context `reviewer` subagent, model tier `fable`. Inputs: the whole AGENTS.md, docs/DECISIONS.md, the changed line and its old text, and the same brief as before.

Result: MAJOR: none. MINOR (recorded; the owner decides; the rule text is not changed again without approval of the exact new text):

1. The parenthesis "(about 30 minutes or more, and the fresh review)" can read as "30 minutes AND the review", which would forbid a short fresh review that the "Fresh review" rule orders. Possible fix: name the fresh review as an exception to size, "(any size; the fresh review)".
2. The skill sentence "Do other small tasks yourself." can cut against the reviewer order for a small lane B review. Possible fix: delete that sentence.
3. "sends" can be read as an order rather than a permission. Possible fix: "may send" or "sends (not optional)".
4. The exception waives size and scope, but its wording does not say it waives "bounded files" and "measurable done criteria" too. Possible fix: "Exception to size, files and done criteria: ...".
5. "main session" is not defined, while the skill and scout.md say "orchestrator". Possible fix: one term for both.

Checked: AGENTS.md, docs/DECISIONS.md, delegate SKILL.md (context).

rule-conflict-check: 15f2316c8448
