# Fleet format: port a project, harvest it to the fleet page

The fleet page (https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW, private) shows each ported project's last and next update, timeline, open and resolved decisions, and keeps the owner's choices on them. The fleet format is a template: the owner ports it into a project when that project needs it (the owner, 2026-11-19). The kit itself is not ported. Format: the handoff skill (`.claude/skills/handoff/SKILL.md`, "Fleet format"); contract and design: [reviews/2026-11-19-fleet-contract.md](reviews/2026-11-19-fleet-contract.md).

## Port a project (one pull request in that project)

Needs kit 4.1.0 or later in the project (`scripts/fleet_harvest.py`).

1. Add the line `fleet: on` to the project's `.check` (a guard file: the owner asks for it; lane C).
2. Run `python3 scripts/fleet_harvest.py --add-ids`. It numbers the rows of docs/DECISIONS.md: D1 = the oldest row. The row text does not change.
3. In docs/NEXT_PROMPT.md: add the `Next update:` line under `Updated:`, a `## Timeline` section, and write each "Needs the owner" line as `- D<n> · <question> · Options: <A> / <B> · REC: <option>`, with the next free IDs. Keep the file at 40 lines or fewer.
4. Run `python3 scripts/fleet_harvest.py --check` until it exits 0 (`0 lines not read`, no duplicate ID); `scripts/check.sh` then runs it on every push.
5. Optional: add the project's "Fleet choices" line to its own "Project rules" (the owner approves the exact text; the kit's line is in the kit's AGENTS.md).
6. Merge the pull request, then run the harvest below once for the project, as a dry run first: show the owner the counts (`counts` in the output) and write to the page only after the owner approves (AGENTS.md "The owner's approval").

## Harvest a project to the page (one run)

Run it from a session that has the project's checkout and the fleet page's database tool (ArtifactData). Page database layout: contract section 3. The state of the last run lives on the page itself, in the document `meta/harvest~<repo>` (field `state`, the JSON text of the hashes), so a fresh container does not send every item again.

1. Read the state: ArtifactData `get` of `meta/harvest~<repo>` with `out_dir`; write its `state` field to `<tmp>/state.json` (no document yet: start without one).
2. Cross-check input (optional, for "Not filed" items): write `<tmp>/cross.json` as `{"pull_requests": [{title, url}], "sessions": [{title, url}]}` from the project's open pull requests and its sessions that wait for the owner (`list_sessions`, status "blocked", tag `project:<short name>`).
3. `python3 scripts/fleet_harvest.py --harvest . --repo <repo> --url https://github.com/<owner>/<repo> --state <tmp>/state.json --cross <tmp>/cross.json --out <tmp>/out` (leave out `--cross` when step 2 was skipped). It prints only batch entries (file paths; deletes as `{op: "delete", collection, doc_id}`) and counts.
4. Read the versions of the project's documents that exist on the page now, whatever the state says (an earlier run can have written some of them before it failed): ArtifactData `query` of `items` where `repo` equals the project name, with `out_dir`, and `get` of `repos/<repo>`. Write the entries with ArtifactData `batch`, at most 50 per batch, and give each entry whose document exists its `if_version`; a document that does not exist gets none. The repos row usually exists already (the kit sync writes it), so its `update` needs a version.
5. After every batch succeeded: `python3 scripts/fleet_harvest.py --save-state <tmp>/state.json --repo <repo>`, then write the file back to `meta/harvest~<repo>` (`set`, field `state`, pinned to the version read in step 1). If a batch failed, do not save: the next run sends the same documents again.

Token cost: the first full write of a project with about 90 decisions sends about 5,000 tokens of batch entries (measured 2026-11-19 on a copy of the kit: 20,556 bytes with `--out`, 49,047 inline); a daily run with a few changed items stays under about 1,000 tokens of data (an estimate). Most of a scheduled run's cost is the fixed start of its session.

## Daily harvest task (template; made only when the owner asks)

A scheduled task that starts a fresh session each day (`create_trigger` with `create_new_session_on_fire`), on the environment that has the ported repositories. Prompt:

```text
Fleet harvest. For each repository in this list: <owner>/<repo>, ... (only ported projects, `fleet: on` in .check):
attach it (add_repo), check out main, and run the "Harvest a project to the page" steps of docs/fleet.md in the
archimedes_lever kit, with the fleet page https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW. Write only what the
harvest prints; never edit a choice. If `--check` reports lines not read, still harvest (the page shows the count).
End with one line per repository: documents changed, deleted, lines not read, or the step that failed and why.
```

## Apply the owner's choices

The fleet page's "Copy prompt" and "Start session" buttons give the prompt. The applying session follows contract section 5 and the "Fleet choices" rule: it shows every pending choice in full and waits for the owner's confirmation in their own message before any change.
