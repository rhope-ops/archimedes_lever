---
name: port
description: Use when the owner asks to bring a change of the archimedes_lever kit (a new version, a pull request, a decision, a script or a skill) into a project, when scripts/drift.py shows that a project differs from the kit, and when a project needs its own code in a kit file. Gives the sync steps, where a project's own code lives, how to record one kit file that differs, the approval of rule lines, and the before and after proof.
---

# Bring a kit change into a project

A project takes kit changes by sync (`scripts/sync_baseline.py`, README "Update an existing project"). The sync replaces the kit files and the kit sections of AGENTS.md, keeps the project's own files and text, and writes the kit lock `.check.lock`; after it, `scripts/check.sh` fails when a kit file differs from the lock. Run the steps in the project repo, with the kit cloned next to it (`../archimedes_lever`). What each kit version asks of a project: the kit's docs/CHANGELOG.md.

## Where a project's own code and text live

| The project's own | Its place |
|---|---|
| Tests | `scripts/check.local.sh` (`scripts/check.sh` runs it last; it gets `--fast` in the fast lane) |
| Finders of the content check (a pattern of its own, one more check) | `scripts/check_content_local.py`; the interface is in the header of `scripts/check_content_scan.py` |
| Stricter code-standard rules | `scripts/code_standard_gate.py`, with `code-` lines in `.check`; the interface is in the header of `scripts/code_standard.py` |
| Settings | `.check` |
| Rules and commands | AGENTS.md "Project rules" and "Commands" |
| Text next to a kit doc or skill | a file of its own that links to the kit's file |

A kit file that the owner wants different in this one project: change it, then run `python3 scripts/check_lock.py --relock <file>` on the owner's request, and record the request (step 8). Each check run then lists that file as an override, and the next sync shows its diff again. First ask whether the change belongs in the kit (an extension point, or a fix for every project): propose it there under Suggest.

## Steps

1. Read the kit change: its row in the kit's docs/CHANGELOG.md, its rows in the kit's docs/DECISIONS.md (date, scope) and the pull request diff. A kit decision whose scope does not name this project needs the owner's approval here first. A limit of the project wins over the kit change (for example a frozen spec or a protected file list): name the limit in the record (step 8).
2. Measure before, in the project: `python3 scripts/bloat_check.py --brief` and `--rules`, the `TIME` line of `scripts/check.sh`, and the drift report (`python3 ../archimedes_lever/scripts/drift.py --project .`: each kit section and file as same, changed or missing; a file the project may tune as same, older or tuned).
3. Dry run: `python3 ../archimedes_lever/scripts/sync_baseline.py --baseline ../archimedes_lever`. Read the whole diff. For each kit file where the diff removes code or text of this project: move that part to its place in the table above, on the branch, before the sync writes. A file the kit moved (`MOVED_FILES` in the kit's `scripts/sync_baseline.py`) is deleted in the project only after its text is in the new place.
4. Rule lines: each changed line in a kit section of AGENTS.md and each new "Project rules" line is a rule change. Show the exact texts to the owner in one dialog and wait for approval of each (`.claude/skills/rule-change/SKILL.md`). Then run the conflict check of that skill.
5. Sync on a branch: the same command with `--apply`, then the steps the changelog row names (for example `python3 scripts/check_settings.py --migrate`). Do not edit `.check.lock` by hand. The sync never copies the kit's docs/DECISIONS.md, docs/LOG.md or reviews: the project has its own.
6. Project tests: `scripts/check.local.sh` accepts `--fast` (it checks each changed file in full, and that generated files are not stale). An extension file proves itself: give it a `--test` mode, and `scripts/check.sh` runs it. Profile before you change a test (`.claude/skills/efficiency/SKILL.md`); keep the same tests and the same PASS lines.
7. Prove it: the full lane passes, with `LOCK PASS` and no override that the owner did not ask for; give the numbers of step 2 before and after, and the drift report after.
8. Record: a row in the project's docs/DECISIONS.md ("synced kit version N, date; overrides: ...; skipped: ..."), and a project log row when it is a milestone.
9. Deliver it (`.claude/skills/deliver/SKILL.md`).
