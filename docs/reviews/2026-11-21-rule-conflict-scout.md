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
