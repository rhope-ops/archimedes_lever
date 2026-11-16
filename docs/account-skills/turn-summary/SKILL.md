---
name: turn-summary
description: Use at the end of every work turn (not for a pure question), before you write the end-of-turn summary. Gives the lines that apply (Proof, Drift, Assumptions, Applied, PII, Delegated, Suggest) and the full form when a decision or work stays open.
---

# End-of-turn summary

An account skill: the owner uploads this file at claude.ai (Settings, Capabilities, Skills). The one-line default stays in the preferences (PREFERENCES.md, "End-of-turn summary"); this file holds the rest.

- Below that line, add only the lines that apply. In a repo, put the same lines in the pull request text.
  - Proof: the outside evidence, the method and the result. Always, when the work changed something.
  - Drift: each difference from what I asked for, with the reason.
  - Assumptions: only those with medium or low confidence.
  - Applied: each rule or earlier decision that changed the work, with its text in one line and its source.
  - PII: only when you published, committed, delegated or sent content to an external service, or when you found PII.
  - Delegated: task · model · reason for the model · how you checked the result.
  - Suggest: at most 3 proposals (new rule, change, retire, new skill, speed-up), and only after my correction, the same event 2 times, or a measured cost. Each one: the exact text, the trigger, what it replaces. Write nothing until I approve that text.
- Use the full form only when a decision is open or work stays open after this turn, in this order, leaving out empty parts:
  1. Decide: numbered questions, options A/B/C, **REC:** with reason. Carry open ones forward with "(open since <date time>)".
  2. Copy: each text to paste, with "Paste into: <place>" above it.
  3. Resume in a new chat: one code block, at most 100 words, with a stand-alone prompt: goal, current state, approved decisions, next step, full URLs.
  4. Table with an empty header, one short line per cell: Step, Status, Risk, Running, Next, Links.
