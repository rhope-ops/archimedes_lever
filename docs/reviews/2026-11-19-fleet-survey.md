# Fleet decision hub: step 1 survey of the kit's own files

Date: 2026-11-19 14:55 America/Chicago. Plan: [2026-11-19-fleet-decision-hub-plan.md](2026-11-19-fleet-decision-hub-plan.md). Method: a Python pass with regular expressions over docs/DECISIONS.md and docs/KIT_HANDOFF.md at commit d149c0f (plan branch); counts only, no row text.

## Counts

| Item | Count | Can a parser read it? |
|---|---|---|
| DECISIONS.md rows | 81 | Yes: all 81 split into 4 cells (Date, Decision, By, Replaces) |
| Rows "By" the owner | 74 | Yes |
| Rows "By" Agent | 7 | Yes, but see finding 2 |
| Rows with an ID (D1, D2 ...) | 0 | No: IDs must be added (step 4 backfill) |
| Decision text length (characters) | min 97, median 483, max 2,357 | Too long for the page: store the first sentence, at most 140 characters, and a link |
| KIT_HANDOFF "Open (in order)" items | 2 | Yes, one per numbered line |
| KIT_HANDOFF "Needs the owner" items | 1 line | No: the line holds 4 separate actions (two tags, rulesets, secret scanning) |
| `Updated:` line | 1 | Yes (date and time) |
| Next planned update | none | No field exists |
| Timeline | none | No field exists |

The project template docs/NEXT_PROMPT.md has the same sections ("Open (in order)", "Needs the owner") and an `Updated:` line, so the same parser fits a ported project.

## Findings for step 2 (contract)

1. **One item per line.** "Needs the owner" must hold one decision or action per line, each with an ID; the format check must fail a line that has no ID.
2. **"By Agent" does not mean open.** Some Agent rows were settled later by a merge the owner approved (for example the kit 3.1.0 row), and the row still says Agent. A parser that treats Agent rows as open shows false items. The open list must come from "Needs the owner" only; DECISIONS.md rows are the resolved list, and the format needs an explicit state where a row is still open.
3. **Summaries, not full text.** The page stores the first sentence (at most 140 characters) and a link to the row; the full text stays in the repo. This keeps the page rows and the harvest's token cost small.
4. **New fields.** `Next update:` (a date) and a `Timeline:` section (date and milestone per line) are new; until a project has them, the page shows "not set", never a guess.
5. **IDs for 81 old rows.** The backfill numbers the rows from the oldest (D1) to the newest (D81) and does not change their text.
