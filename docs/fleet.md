# Fleet format: port a project, harvest it to the fleet page

The fleet page (private; its address is `fleet_page` in the kit's kit.config.json) shows each ported project's last and next update, timeline, open and resolved decisions, and keeps the Administrator's choices on them. The fleet format is a template: the Administrator ports it into a project when that project needs it (the Administrator, 2026-11-19). The kit itself is not ported. Format: the handoff skill (`.claude/skills/handoff/SKILL.md`, "Fleet format"); contract and design: [reviews/2026-11-19-fleet-contract.md](reviews/2026-11-19-fleet-contract.md).

## Port a project (one pull request in that project)

Needs kit 4.1.0 or later in the project (`scripts/fleet_harvest.py`).

1. Add the line `fleet: on` to the project's `.check` (a guard file: the Administrator asks for it; lane C).
2. Run `python3 scripts/fleet_harvest.py --add-ids`. It numbers the rows of docs/DECISIONS.md: D1 = the oldest row. The row text does not change.
3. In docs/NEXT_PROMPT.md: add the `Next update:` line under `Updated:`, a `## Timeline` section, and write each "Needs the Administrator" line as `- D<n> · <question> · Options: <A> / <B> · REC: <option>`, with the next free IDs. Keep the file at 40 lines or fewer.
4. Run `python3 scripts/fleet_harvest.py --check` until it exits 0 (`0 lines not read`, no duplicate ID); `scripts/check.sh` then runs it on every push.
5. Optional: add the project's "Fleet choices" line to its own "Project rules" (the Administrator approves the exact text; the kit's line is in the kit's AGENTS.md).
6. Merge the pull request, then run the harvest below once for the project, as a dry run first: show the Administrator the counts (`counts` in the output) and write to the page only after the Administrator approves (AGENTS.md "The Administrator's approval").

## Harvest a project to the page (one run)

Run it from a session that has the project's checkout and the fleet page's database tool (ArtifactData). Page database layout: contract section 3. The state of the last run lives on the page itself, in the document `meta/harvest~<repo>` (field `state`, the JSON text of the hashes), so a fresh container does not send every item again.

1. Read the state: ArtifactData `get` of `meta/harvest~<repo>` with `out_dir`; write its `state` field to `<tmp>/state.json` (no document yet: start without one).
2. Cross-check input (optional, for "Not filed" items): write `<tmp>/cross.json` as `{"pull_requests": [{title, url}], "sessions": [{title, url}]}` from the project's open pull requests and its sessions that wait for the Administrator (`list_sessions`, status "blocked", tag `project:<short name>`).
3. `python3 scripts/fleet_harvest.py --harvest . --repo <repo> --url https://github.com/<owner>/<repo> --state <tmp>/state.json --cross <tmp>/cross.json --out <tmp>/out` (leave out `--cross` when step 2 was skipped). It prints only batch entries (file paths; deletes as `{op: "delete", collection, doc_id}`) and counts.
4. Read what the page holds for the project now, whatever the state says (an earlier run can have written some documents before it failed): ArtifactData `query` of `items` where `repo` equals the project name, and `get` of `repos/<key>` (key: the repo name with "/" as "_"), each with `out_dir` set to its own folder `<tmp>/page` (never `<tmp>/out`, which holds the documents to write). Then: give each write whose document the page holds its `if_version` (a new document gets none; the repos row usually exists, because the kit sync writes it); leave out a delete whose document the page no longer holds; and add a delete, with its version, for each item of the project that the page holds but whose path (`items/<doc id>`) is not a key of the new hashes file `<tmp>/state.json.<key>.pending` (an item that an earlier failed run wrote and the files no longer have; that file lists every current document, changed or not). Write the entries with ArtifactData `batch`, at most 50 per batch.
5. After every batch succeeded: `python3 scripts/fleet_harvest.py --save-state <tmp>/state.json --repo <repo>`, then write the file back to `meta/harvest~<repo>` (`set`, field `state`, pinned to the version read in step 1). If a batch failed, do not save: the next run sends the same documents again.

Token cost: the first full write of a project with about 90 decisions sends about 5,000 tokens of batch entries (measured 2026-11-19 on a copy of the kit: 20,556 bytes with `--out`, 49,047 inline); a daily run with a few changed items stays under about 1,000 tokens of batch data, plus the step 4 read of the project's documents (about one line each in the `out_dir` listing; an estimate). Most of a scheduled run's cost is the fixed start of its session.

## Daily harvest task (template; made only when the Administrator asks)

A scheduled task that starts a fresh session each day (`create_trigger` with `create_new_session_on_fire`), on the environment that has the ported repositories. Prompt:

```text
Fleet harvest. For each repository in this list: <owner>/<repo>, ... (only ported projects, `fleet: on` in .check):
attach it (add_repo), check out main, and run the "Harvest a project to the page" steps of docs/fleet.md in the
archimedes_lever kit, with the fleet page (`fleet_page` in kit.config.json). Write only what the
harvest prints; never edit a choice. If `--check` reports lines not read, still harvest (the page shows the count).
End with one line per repository: documents changed, deleted, lines not read, or the step that failed and why.
```

## Apply the Administrator's choices

The fleet page's "Copy prompt" and "Start session" buttons give the prompt. The applying session follows contract section 5 and the "Fleet choices" rule: it shows every pending choice in full and waits for the Administrator's confirmation in their own message before any change.
