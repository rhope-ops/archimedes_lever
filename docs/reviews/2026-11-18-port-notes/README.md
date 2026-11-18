# Notes for the two re-ports (kit 2026.11.18.1)

Made on 2026-11-18 from scratch copies of the two port branches (RADE 56e61a0, 90-161.Z b031e94) and the kit working
tree on branch claude/upbeat-bell-uxsavx. Nothing was written into the project clones.

Folders: `rade/` and `90-161.z/` hold the project files that the scratch runs used (ready to copy, then review);
`results/` holds the check output before (`*-ref-*`) and after (`*-new-*`) and the sync dry-run diffs.

## Order of work, both projects

1. On the port branch, add or change the project files listed in the project's notes file. Commit (the sync needs a
   clean tree).
2. Dry run: `python3 ../archimedes_lever/scripts/sync_baseline.py --baseline ../archimedes_lever`. Expect only kit
   files, `.claude/agents/reviewer.md` (RADE: an older kit copy, replaced) and a "kept" line for a tuned docs/FIRST_USE.md.
   AGENTS.md, .claude/settings.json and .gitignore did not change in either scratch run.
3. Apply: the same command with `--apply`. It writes `.check.lock` (44 kit files, kit version 2026.11.18.1).
4. `python3 scripts/check_settings.py --migrate`: it replaces the old first comment line of `.check` (nothing else).
5. `git add -A`, then `python3 scripts/code_standard.py` (only FIXED lines, no FAIL), then
   `python3 scripts/code_standard.py --update` (the debt list only shrinks; no kit file is left in it).
6. `bash scripts/check.sh`. New PASS lines: `check_content_local self-test`, `code_standard_gate self-test`.
7. Rule lines: each project still has a "Project rules" line "No kit sync"; the owner decision of 2026-11-18 lifts
   it, and its removal needs the owner's approval of the exact text (rule-change skill). The scratch runs did not
   touch any rule line.

## What a project file must do (the interfaces)

- `scripts/check_content_local.py`: `REPLACE = {kind: [finder]}` and/or `ADD = {kind: [finder]}`;
  `finder(line)` yields `(start, end, value)`. Header of the kit's scripts/check_content_scan.py.
- `scripts/code_standard_gate.py`: `RULES`, `OPT_IN`, `file_rules`, `decided`, `new_debt_refusal`. Header of the
  kit's scripts/code_standard.py.
- A `--test` mode in each: `scripts/check.sh` runs it (full lane always; fast lane when the file, a sibling
  `<name>*.py` file or the kit file it extends changed).
