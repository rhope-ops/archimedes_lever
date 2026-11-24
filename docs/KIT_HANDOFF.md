# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-23 18:12 by "Kit · Tool retirement · 2026-11-23 · #125": stopping point; P1 built on branch, finish in a new session ([reviews/2026-11-23-tool-retirement-handoff.md](reviews/2026-11-23-tool-retirement-handoff.md))

## State

- main: kit 10.0.0 (f397b52; main 29d190c adds PR 108, no synced kit file changed). Tags (the owner makes them): v6.2.0, v7.0.0, v8.0.0, v10.0.0 exist; v8.1.0 and v9.0.0 not made yet.
- Fleet on 10.0.0 (merged 2026-11-21, each verified on main): RADE 165, 33-332.Z 48, ICF-Source 240, SEC-Source 27, SPAR 19, 36-3003.Z 14, 65-601.Z 14, no-more-beyond 66, transcription_assistant 8. 90-161.Z on 9.0.0 (PR 215); its 10.0.0 sync is PR 216 of its own session (K2). Session load (cap 5,500): 33-332.Z ~5,352, ICF ~5,322, RADE ~5,278, TA ~5,250, SEC ~5,210, NMB ~5,178. Owner steps per repo: `audit-instructions:` lines in `.check`; 33-332.Z README does not open with its Purpose line (warning).

## Approved plan (the Maintainer, 2026-11-23 17:12): custom tool retirement
Plan, texts and decisions 1-10: [reviews/2026-11-23-tool-retirement-plan.md](reviews/2026-11-23-tool-retirement-plan.md); coverage list (85 rows) and research files beside it. Session "Kit · Tool retirement · 2026-11-23 · #125".

- [x] Research R1-R4f and plan (PRs 125, 127, 131). [~] P1 rules and checks (kit, lane C): built on branch `claude/tr-p1` (2161319), not a PR yet; next: verify T1 first-cell match, full lane, fresh review, rule-conflict rerun if needed, PR for the Maintainer. [ ] P2 kit shrink and repair. [ ] P3 pilot 33-332.Z (pip/pipx; trim its handoff ~50 tokens first).
- [ ] P4 RADE sentinel + release, 90-161.Z, 33-332.Z, ICF runbook. [ ] P5 kit 10.0.0 repos, fleet audit. [ ] P6 exports, branch deletes (with the Maintainer's OK).
- Fleet v2 (approved 2026-11-23) is done and closed: [reviews/2026-11-23-fleet-v2-plan.md](reviews/2026-11-23-fleet-v2-plan.md), lessons [reviews/2026-11-23-fleet-v2-lessons.md](reviews/2026-11-23-fleet-v2-lessons.md).
- Earlier approved plan 2026-11-19 (fleet decision hub, kit template): steps 0-5 and 7 done, step 4 dropped; open: step 6 loop proof after the owner ports a first project. Record: [reviews/2026-11-19-fleet-decision-hub-plan.md](reviews/2026-11-19-fleet-decision-hub-plan.md); live page preview https://claude.ai/artifact/RZwwoMT9fNJDARDcBzn7AR.

## Open (in order)

- Plan 2026-11-20 done: kit 5.0.0 (PR 78) and 5.0.1 (PR 79); the design packs became a claude.ai skill, not repo files. Tags v5.0.0 (24c2391) and v5.0.1 (59528df) not made yet: [reviews/2026-11-20-third-party-skills-plan.md](reviews/2026-11-20-third-party-skills-plan.md).

0. Kit fixes for the next PATCH (found by the 3.2.0 reviews; none blocks a repo): (a) the sync swaps "the owner" for each repo's role inside `scripts/check_settings.py`, so `OLD_HEADER_LINES` misses the old "the owner's request" line: exclude that file from the swap or match any role (5 repos got a hand fix in their sync PR); (b) `new_header` stops at a blank line; (c) NITs: the `audit-duplicate-ignore` wording in `bloat_check.py`, the CHANGELOG 3.2.0 row does not name `sync_merge.py`; (d) `fix_hooks` in session_checkin.sh keeps any non-kit hooks path, so a converted repo with an old `tools/git-hooks` path skipped the content check (NMB and TA fixed it in their project layer; the kit should repoint known old paths or warn); (f) first use keeps the kit's own "Project rules" lines (the Fleet choices line, 4.1.0) in a new project: empty that section at first use (docs/reviews/2026-11-19-rule-conflict-fleet.md finding 4); (e) 90-161.Z commit 50421f2 (DECISIONS "By" Agent to PFM, NIT) is unpushed: its pre-push needs pwsh, which the cloud sandbox lacks.
1. Step 5 (rulesets, secret scanning: the owner's clicks, docs/github/README.md).

## Needs the owner
- Fleet v2: tags v11.0.0 (dedc3b3) and v11.0.1 (9e3f6fa) exist (checked 2026-11-23 15:13). The open fleet decisions and the Default setup script: coordinator state file, "Needs the Maintainer".
- 2026-11-21 items (decide in order): (a) fix the non-text timestamp crash in a separate PR, REC yes; (b) approve or change the five MINOR Delegation wording items, REC: approve 1, 3, 5; delete the skill sentence in 2; reword 4 to "Exception to size, files and done criteria"; (c) confirm or remove the DECISIONS claim of an earlier MAJOR check (no record file); (d) docstring of tokens(): "text that is not an integer" (with a).

- Delete the kit branches `claude/content-check-speed` (merged in PR 94) and `claude/kit-handoff-6-0-0` (same commit as PR 84; the cloud session's delete got HTTP 403): https://github.com/rhope-ops/archimedes_lever/branches. Account skills to save (files sent in the session of 2026-11-20): `pages-and-tools`, `ship`, `turn-summary`, `roadmap-update`, `stakeholder-update`; the 2 changed preference lines (PREFERENCES.md "Reporting" and "How to work"). Tags v5.0.0 (24c2391), v5.0.1 (59528df), v6.0.0 (43ad952).
- Tag v4.1.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v4.1.0&target=4135536a72e9a5e9c63fd57496f9739cefac0966&title=Kit%204.1.0). Tags v3.2.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v3.2.0&target=18896fc5ae5e954eeb0182bc4beae264eee9d541&title=Kit%203.2.0) and v4.0.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v4.0.0&target=c8339c31cc75d50106ede550afd1c36e4c7b529f&title=Kit%204.0.0); rulesets and secret scanning.
## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first (`scripts/bloat_check.py --brief` on a dry-run sync): after 10.0.0 the highest is 33-332.Z ~5,352 of the 5,500 cap.
