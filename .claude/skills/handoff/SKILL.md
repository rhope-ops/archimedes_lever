---
name: handoff
description: Use when a session ends with work still open, before a long pause or a context compaction, when the owner asks for a handoff or a resume prompt, and at the start of a session that continues earlier work. Gives what goes into docs/NEXT_PROMPT.md, what goes to docs/reviews/ and docs/DECISIONS.md, the resume prompt, and how to start from a handoff.
---

# Handoff

AGENTS.md "Handoff" points here. The next session cannot see this chat: it reads only the repo. A fact that is only in chat is lost.

## Write a handoff

1. docs/NEXT_PROMPT.md is a shared doc: edit it as AGENTS.md "Git safety" says.
2. Update docs/NEXT_PROMPT.md, within the AGENTS.md "Handoff" cap, in its sections:
   - `Updated:` date and time (the time zone in the AGENTS.md header) and who.
   - State: what is on main (commit), open branches and pull requests (full links), what runs now and who owns it.
   - Approved plan: the plan the owner approved, with the approval date; mark each step done as it lands. A plan that does not fit the 40-line cap goes in docs/reviews/, with a link here. This section is the plan's canonical place (not docs/DECISIONS.md).
   - Open (in order): the next steps, one line each, with what "done" is.
   - Needs the owner: each open decision in one line, with its options and the recommendation.
   - Do not: approaches that failed, with one line of why.
3. Put detailed evidence (logs, tables, review findings) in its own file in the place AGENTS.md "Handoff" names (`YYYY-MM-DD-<topic>.md`), and link it.
4. A decision by the owner: a row in docs/DECISIONS.md (date, scope, what it replaces). Full tier: a story event also gets a project log row (the `project-log` skill).
5. Deliver it like any change (`.claude/skills/deliver/SKILL.md`); AGENTS.md "Delegation" says which changes need a fresh review.
6. In the turn summary, give a resume prompt: one code block, at most 100 words, that stands alone (goal, state, approved decisions, next step, full links).

In the kit clone itself (the KIT line at start), docs/NEXT_PROMPT.md is the template that projects get: do not fill it. The kit's own handoff file is docs/KIT_HANDOFF.md, with the same sections.

## Start from a handoff

1. Read docs/NEXT_PROMPT.md as AGENTS.md "Start of session" says. After a restart or a compaction (the RESUMED line at start), run the check-in for the git state, then continue the approved plan from its first step that is not done. Do not review the plan again or ask approved questions again; code reviews and checks still apply.
2. Check each claim against the repo before you act on it: is the commit on origin/main, is the pull request still open, does the file exist? A claim that fails is drift: report it.
3. If the handoff and the current request conflict, say so; AGENTS.md "Order of authority" decides.
