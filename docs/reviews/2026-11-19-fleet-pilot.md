# Fleet decision hub: step 4 pilot on the kit

Date: 2026-11-19 about 15:30 America/Chicago. Plan: [2026-11-19-fleet-decision-hub-plan.md](2026-11-19-fleet-decision-hub-plan.md).

## What changed in the kit

- `.check`: the line `fleet: on`.
- docs/DECISIONS.md: `python3 scripts/fleet_harvest.py --add-ids .` added IDs to 82 rows (D1 = 2026-11-13, D82 = the newest). The new pilot row is D87.
- docs/KIT_HANDOFF.md: a `Next update:` line, a Timeline section with 5 lines, and "Needs the owner" as 5 lines: D83 to D86 (it was 1 line with 4 actions) and D88, the owner's approval of the first page write. Kept at 40 lines.

## Results

| Check | Command | Result |
|---|---|---|
| Format check | `python3 scripts/fleet_harvest.py --check` | `fleet: 5 open, 83 resolved, 0 lines not read` (D83 to D86, and D88 for the first page write) |
| Counts match the files | `grep -c "^\| D[0-9]" docs/DECISIONS.md`; `grep -c "^- D[0-9]" docs/KIT_HANDOFF.md` | 83 and 5, the same as the check |
| First harvest (dry run, no page write) | `--harvest . --repo archimedes_lever --url ... --state FILE --out DIR` | 89 documents: 88 items (set) and 1 repos row (update), 0 deletes |
| Second harvest after `--save-state`, no file change | the same | 0 items changed, 0 deletes (the repos row is always sent, with `harvested_at`) |

## Token cost (measured with `wc -c`; about 4 bytes per token)

| Form of the page write | Bytes | About tokens |
|---|---|---|
| Inline JSON of the first full write (88 items and the repos row) | 49,047 | 12,000 |
| `--out`: the batch entries only (file paths; the documents stay in files; the size depends on the length of the DIR path) | 20,556 | 5,000 |
| A daily run with 1 to 3 changed items and the repos row (estimate, not measured) | under 1,500 | under 400 |

The first write is one time per project. The daily cost is mostly the fixed start of the scheduled session, not the data. Next step for the daily task (step 7): keep the state file on the page (one document per repo) or in the repo, because a fresh container has no earlier state and would send every item again.

## Found and fixed in this step

- The "Open (in order)" steps read as 0: the heading rule that reads "Needs the owner (2)" also cut "(in order)". The parser now looks up "Open".
- `--out DIR`: writes each document to a file and prints only the batch entries, so the page write sends file paths, not document text.
