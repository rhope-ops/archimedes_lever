---
name: turn-summary
description: Use at the end of every work turn (not for a pure question), before you write the end-of-turn summary. Gives the order (status line, questions, the lines that apply, Notes) and what to add when work stays open.
---

# End-of-turn summary

An account skill: the Administrator uploads this file at claude.ai (Settings, Capabilities, Skills). The preferences (the last line of "Reporting") hold the short form; this file holds the details. Keep it short: each line must change what the Administrator knows or does.

1. Status line: "Step X of Y · <status> · Next: <step, who> · <links>".
2. Questions, only when a decision is open: 1 to 10, most important first, each with 2–4 options, the recommendation first, and **REC:** with the reason. Use question dialogs of 4, one after another; do not repeat them in text. Carry an open question forward with "(open since <date time>)".
3. Only the lines that apply, one line each:
   - Proof: the outside evidence, the method and the result. Always, when the work changed something.
   - Drift: each difference from what I asked for, with the reason.
   - Risks: each risk with a REC.
   - GAP: practices or standards the work misses (the preferences, "Style").
   - Suggest: at most 3 rule or process proposals; also asked as a question. In a repository with `.claude/skills/rule-change/SKILL.md`, that skill is the home of the Suggest form: load it and use its form. Elsewhere, each item: the exact text, the trigger and what it replaces. Write nothing until I approve that text.
4. Notes (one line, or the pull request text when there is one): Applied (rule and source), Assumptions (medium or low confidence only), PII (scan result, only when content left this place), Delegated (task · model · how you checked it).
5. Only when work stays open after this turn: Copy (each text to paste, with "Paste into: <place>"), and a resume prompt. In a repository with `.claude/skills/handoff/SKILL.md`, that skill is the home of the resume prompt: load it and follow its step 6. Elsewhere: one code block of at most 100 words (goal, state, approved decisions, next step, full URLs).
