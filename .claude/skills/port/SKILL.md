---
name: port
description: Use when the owner asks to bring a change of the archimedes_lever kit (a pull request, a decision, a script or a skill) into a project by hand, when a sync with scripts/sync_baseline.py would overwrite the project's own text, and when scripts/drift.py shows that a project's kit sections differ. Gives how to choose between a sync and a port, the port steps, the approval of rule lines, and the before and after proof.
---

# Port a kit change to a project

A sync (`scripts/sync_baseline.py`, README "Update an existing project") replaces kit files and kit sections. A port brings one change by hand, so the project keeps its own text. Run it in the project repo, with the kit cloned next to it (`../archimedes_lever`).

## Sync or port

- `python3 ../archimedes_lever/scripts/drift.py --project .` shows each kit section and file as same, changed or missing.
- Sync when the kit sections and files are "same" or the project's changes are small: read the sync diff, then `--apply`.
- Port when the project changed kit sections, has its own versions of kit scripts, or the owner asked for one change only.

## Steps

1. Read the kit change: its rows in the kit's docs/DECISIONS.md (date, scope), the pull request diff and its "Not in this pull request" part. A kit decision whose scope does not name this project needs the owner's approval here first. A limit of the project wins over the kit change (for example a frozen spec, a protected file list or its own delivery rule): adapt or skip that part and name the limit in the record (step 8).
2. Measure before, in the project: `python3 scripts/bloat_check.py --brief` and `--rules`, the `TIME` line of `scripts/check.sh`, and the drift report.
3. Plan each kit file: copy as is, merge by hand, or skip (with the reason). Keep the project's header values, "Commands", owner word (for example "the Administrator"), "Project rules" and its own tests. A file the kit moved (`MOVED_FILES` in the kit's `scripts/sync_baseline.py`) is deleted in the project only after its text is in the new place.
4. Rule lines: each changed line in a kit section of AGENTS.md and each new "Project rules" line is a rule change. Show the exact texts to the owner in one dialog and wait for approval of each (`.claude/skills/rule-change/SKILL.md`). Then run the conflict check of that skill.
5. Copy and merge on a branch. Do not edit `.baseline` by hand (a sync writes it). Never copy the kit's docs/DECISIONS.md, docs/LOG.md or reviews: the project has its own.
6. Project tests: when the port brings the two check lanes, make `scripts/check.local.sh` accept `--fast` (check each changed file in full, and that generated files are not stale). Profile before you change a test (`.claude/skills/efficiency/SKILL.md`); keep the same tests and the same PASS lines.
7. Prove it: the full lane passes; give the numbers of step 2 before and after, and the drift report after.
8. Record: a row in the project's docs/DECISIONS.md ("ported kit pull request N, date; skipped: ..."), and a project log row when it is a milestone.
9. Deliver as a pull request (`.claude/skills/deliver/SKILL.md`). A port changes guard files, so it needs the fresh review; the owner merges.
