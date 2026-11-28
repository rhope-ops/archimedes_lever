---
name: project-log
description: Use before you write or change a project log row, and when a decision, milestone, breakthrough or miss happens.
---

# Project log: how to write a row

AGENTS.md "Project log" points here; `python3 scripts/log_check.py` checks the format. The log records how the project got there (milestones, breakthroughs, misses, decisions) for a timeline and a narrative deck. A public repo keeps it in a private place, because entries can hold environment or security detail.

- One row per story event (the types below). Not a change log: no row per commit, merge or file change; git log holds those. Columns, in this order: # | When | Type | Arc | Topic | Raised by | What the other missed | Evidence | Result.
- When: `YYYY-MM-DD HH:MM` in the project time zone (the `- Time zone:` line at the top of AGENTS.md). A range: `YYYY-MM-DD HH:MM–HH:MM`. Mark an estimate with `~` before the date or the time.
- Type, one of:
  - `milestone`: a deliverable exists or a goal is met (first import works, v1 published).
  - `breakthrough`: a test or idea removes a blocker or changes direction.
  - `miss`: a wrong assumption, failed test or dead end. Record it honestly for both sides.
  - `decision`: the Administrator decides, or overrules a recommendation. Also record it in docs/DECISIONS.md.
- Arc: a short kebab-case name for the narrative thread (for example `email-delivery`). Each arc has one row in the Arcs table: Arc | Span | Summary (one sentence) | Problem | Turning point | Outcome | Lesson.
- Story fields (they feed a narrative deck): Problem = why it mattered and the cost before, with a number where one exists. Turning point = the row(s) that changed direction, as #N. Outcome = the result, before → after. Lesson = what you would tell another team. Each field rests on rows or evidence in the log; write `-` until it is known, never invent. Update the arc row when its arc gets a milestone, breakthrough or miss.
- Story outline: `python3 scripts/timeline.py --outline story.md` (one section per arc, the source for a deck).
- Raised by: who first said it (the Administrator, Claude, a named agent or person). "What the other missed": the gap on the other side, or `-`.
- Evidence: a commit, file, test or measurement. Never chat text alone.

## A log in a Claude doc

A public repo names its log in "Project rules": a private Claude doc link. Write each row there, in the turn it happens. A session that another session starts has the Docs tools too (tested 2026-11-25), so try the write before any paste (test: docs/reviews/2026-11-25-project-log-doc-plan.md):

1. Load the Docs tools: ToolSearch `select:mcp__Claude_Docs__read,mcp__Claude_Docs__update,mcp__Claude_Docs__guide`.
2. Call `guide` with items `["topic.index","topic.editing"]`.
3. Call `read` with ref `{"object":"project","id":"<the id at the end of the link>"}` to get the tab body id.
4. Read the body outline (payload `{"projection":"outline"}`). Find the Log table: its header holds "What the other missed".
5. Read that table (payload `{"kind":"view","parentId":"<table id>"}`) to get the last row number.
6. Append the row: an `update` op `insert` on the table id, `"side":"end"`, `"as":"blocks"`, one cell for each of the 9 columns (topic.editing, ex.2).
7. Update the arc row in the Arcs table: `replace` each changed cell's words by `find`, `"as":"text"`.
8. If step 1 finds no Docs tools, or a Docs call is refused, put the full row in the turn summary under Copy. Use the table format above. Add the missing tool or the refused call, its error and "Paste into: project log".
