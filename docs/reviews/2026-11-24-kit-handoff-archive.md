# Kit handoff archive, 2026-11-24

Items moved word for word from docs/KIT_HANDOFF.md on 2026-11-24, when the kit's session-load cap started to count the handoff (fleet audit finding A10, docs/reviews/2026-11-24-fleet-audit.md). Open items here stay open; the handoff points to this file.

## State (as of 2026-11-21)

- main: kit 10.0.0 (f397b52; main 29d190c adds PR 108, no synced kit file changed). Tags (the owner makes them): v6.2.0, v7.0.0, v8.0.0, v10.0.0 exist; v8.1.0 and v9.0.0 not made yet.
- Fleet on 10.0.0 (merged 2026-11-21, each verified on main): RADE 165, 33-332.Z 48, ICF-Source 240, SEC-Source 27, SPAR 19, 36-3003.Z 14, 65-601.Z 14, no-more-beyond 66, transcription_assistant 8. 90-161.Z on 9.0.0 (PR 215); its 10.0.0 sync is PR 216 of its own session (K2). Session load (cap 5,500): 33-332.Z ~5,352, ICF ~5,322, RADE ~5,278, TA ~5,250, SEC ~5,210, NMB ~5,178. Owner steps per repo: `audit-instructions:` lines in `.check`; 33-332.Z README does not open with its Purpose line (warning).

## Earlier plans

- Fleet v2 (approved 2026-11-23) is done and closed: [reviews/2026-11-23-fleet-v2-plan.md](2026-11-23-fleet-v2-plan.md), lessons [reviews/2026-11-23-fleet-v2-lessons.md](2026-11-23-fleet-v2-lessons.md).
- Earlier approved plan 2026-11-19 (fleet decision hub, kit template): steps 0-5 and 7 done, step 4 dropped; open: step 6 loop proof after the owner ports a first project. Record: [reviews/2026-11-19-fleet-decision-hub-plan.md](2026-11-19-fleet-decision-hub-plan.md); live page preview https://claude.ai/artifact/RZwwoMT9fNJDARDcBzn7AR.

## Open (in order)

- Plan 2026-11-20 done: kit 5.0.0 (PR 78) and 5.0.1 (PR 79); the design packs became a claude.ai skill, not repo files. Tags v5.0.0 (24c2391) and v5.0.1 (59528df) not made yet: [reviews/2026-11-20-third-party-skills-plan.md](2026-11-20-third-party-skills-plan.md).

0. Kit fixes for the next PATCH (found by the 3.2.0 reviews; none blocks a repo): (a) the sync swaps "the owner" for each repo's role inside `scripts/check_settings.py`, so `OLD_HEADER_LINES` misses the old "the owner's request" line: exclude that file from the swap or match any role (5 repos got a hand fix in their sync PR); (b) `new_header` stops at a blank line; (c) NITs: the `audit-duplicate-ignore` wording in `bloat_check.py`, the CHANGELOG 3.2.0 row does not name `sync_merge.py`; (d) `fix_hooks` in session_checkin.sh keeps any non-kit hooks path, so a converted repo with an old `tools/git-hooks` path skipped the content check (NMB and TA fixed it in their project layer; the kit should repoint known old paths or warn); (f) first use keeps the kit's own "Project rules" lines (the Fleet choices line, 4.1.0) in a new project: empty that section at first use (docs/reviews/2026-11-19-rule-conflict-fleet.md finding 4); (e) 90-161.Z commit 50421f2 (DECISIONS "By" Agent to PFM, NIT) is unpushed: its pre-push needs pwsh, which the cloud sandbox lacks.
1. Step 5 (rulesets, secret scanning: the owner's clicks, docs/github/README.md).

Moved 2026-11-25 from the tool-retirement plan and the fleet audit at their close ([close-out list](2026-11-25-closeout-and-trim-proposals.md), Part A; decisions: its section "Outcome"). Text and evidence of each row: that list.

- Audit the audit (kit): A1 (T2 counts test files with code), A3 (a "seam" question for file splits; evidence [R4f](2026-11-23-tr-r4f-split-audit.md)), A4 (fix-of-a-fix rate by `git blame`), A5 (duplicate functions, low priority), A7 (session load as a typical session reads it; after the skill-use re-run of 2026-12-08), A8 (`fleet.last_audit` after a partial audit), A9 (defects per check from local runs; mutation kills), A12 kit part (the duplicate count includes generated files), A14 (no rule-test run records).
- PATCH item (g), A13: `scripts/bootstrap.sh:109` leaves the kit's review subfolders in a new project (lane C: a guard script).
- O1 (not approved, 2026-11-25): the kit counts the docs/NEXT_PROMPT.md template (141 tokens) in its session load, but kit sessions read KIT_HANDOFF.md. A change is lane C (`scripts/bloat_check_rules.py` or `.check`) and needs a fresh review that it corrects the measure.

### For the next 33-332.Z session

- T3: the "MAINTAINER_GUIDE step" of the P3 follow-ups: 33-332.Z has docs/MAINTAINER_GUIDE.md, and its kit-12 sync session recommended a fix there.
- T10: the 3 MINOR texts of its PR 118, after the PAM's ISE test. Its session load was 5,504 > 5,500 with that line; kit R1-R3 (2026-11-25) free about 116 tokens at the next sync.

### For the next ICF-Source session

- F1: cut 5, the one-off scripts (about -912 lines), at its own audit (the Maintainer, 2026-11-24).
- A12, ICF part: the `audit-duplicate-ignore:` glob for generated files in its `.check` (a guard change).

### For the next 90-161.Z session

- F2: cut 8, `measure_pdf.py` (-58 lines), at its own audit (the Maintainer, 2026-11-24).

### For the next RADE session

- F3: cut 9, `Split-Sentence` (about -20 lines; needs an engine release), at its own audit (the Maintainer, 2026-11-24).
- Verify T7, RADE part: SBOM PR #184 merged (kit records conflict; not verified).
- Verify T8: CodeQL Python PR #182 merged (c5ba723 per the coordinator state; not verified).

## Needs the owner

- T14 (2026-11-25): the session archive list of the tool-retirement P6, in [the coordinator state](2026-11-23-fleet-v2-coordinator-state.md) lines 219-223; which sessions are archived is not verified.
- Fleet v2: tags v11.0.0 (dedc3b3) and v11.0.1 (9e3f6fa) exist (checked 2026-11-23 15:13). The open fleet decisions and the Default setup script: coordinator state file, "Needs the Maintainer".
- 2026-11-21 items (decide in order): (a) fix the non-text timestamp crash in a separate PR, REC yes; (b) approve or change the five MINOR Delegation wording items, REC: approve 1, 3, 5; delete the skill sentence in 2; reword 4 to "Exception to size, files and done criteria"; (c) confirm or remove the DECISIONS claim of an earlier MAJOR check (no record file); (d) docstring of tokens(): "text that is not an integer" (with a).

- Delete the kit branches `claude/content-check-speed` (merged in PR 94) and `claude/kit-handoff-6-0-0` (same commit as PR 84; the cloud session's delete got HTTP 403): https://github.com/rhope-ops/archimedes_lever/branches. Account skills to save (files sent in the session of 2026-11-20): `pages-and-tools`, `ship`, `turn-summary`, `roadmap-update`, `stakeholder-update`; the 2 changed preference lines (PREFERENCES.md "Reporting" and "How to work"). Tags v5.0.0 (24c2391), v5.0.1 (59528df), v6.0.0 (43ad952).
- Tag v4.1.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v4.1.0&target=4135536a72e9a5e9c63fd57496f9739cefac0966&title=Kit%204.1.0). Tags v3.2.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v3.2.0&target=18896fc5ae5e954eeb0182bc4beae264eee9d541&title=Kit%203.2.0) and v4.0.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v4.0.0&target=c8339c31cc75d50106ede550afd1c36e4c7b529f&title=Kit%204.0.0); rulesets and secret scanning.

## Plan detail and the last Updated line (as of 2026-11-24 08:44)

Updated: 2026-11-24 08:44 by "Kit · Fleet audit · 2026-11-24 · #158": fleet audit of all 5 repos done, report [reviews/2026-11-24-fleet-audit.md](2026-11-24-fleet-audit.md) with 5 appendices; #158 merged (T2 19123); 33-332.Z PR 77 (-13) waits for "merge 77"; `fleet.last_audit` 2026-11-24; open: 3 questions in the report. P2 done: [reviews/2026-11-23-tool-retirement-handoff.md](archive-index.md#2026-11-23-tool-retirement-handoff-md)

Plan, texts and decisions 1-10: [reviews/2026-11-23-tool-retirement-plan.md](2026-11-23-tool-retirement-plan.md); coverage list (85 rows) and research files beside it. Session "Kit · Tool retirement · 2026-11-23 · #125".

- [x] Research R1-R4f and plan (PRs 125, 127, 131). [x] P1 rules and checks (PR 137, 067726a). [~] P2 kit shrink and repair: split in the handoff file. [ ] P3 pilot 33-332.Z (pip/pipx; trim its handoff ~50 tokens first).
- [ ] P4 RADE sentinel + release, 90-161.Z, 33-332.Z, ICF runbook. [ ] P5 kit 10.0.0 repos, fleet audit. [ ] P6 exports, branch deletes (with the Maintainer's OK).

## Dependabot secret (hand steps, 2026-11-24)

Fleet audit: every Dependabot pull request fails the content step of CI, because GitHub gives Dependabot runs no Actions secret.

1. In a browser, open https://github.com/rhope-ops/archimedes_lever/settings/secrets/dependabot/new . You see the page **New Dependabot secret**. Go on.
2. In the box **Name**, type `PII_GUARD_DENYLIST`. You see the name in the box. Go on.
3. In the box **Secret**, paste the master denylist text from your Google Drive. You see the text in the box. Go on.
4. Click **Add secret**. You see the page **Dependabot secrets** with the row `PII_GUARD_DENYLIST`. Go on.
5. Open https://github.com/rhope-ops/archimedes_lever/pull/115/checks . You see the page **Checks** of pull request 115. Go on.
6. On the page **Checks**, do these actions:
   1. Click **Re-run jobs**.
   2. Click **Re-run all jobs**.
   You see the check **checks** start. Wait until it shows a green mark. Go on.
7. Open https://github.com/rhope-ops/archimedes_lever/pull/116/checks . You see the page **Checks** of pull request 116. Go on.
8. On the page **Checks**, do these actions:
   1. Click **Re-run jobs**.
   2. Click **Re-run all jobs**.
   You see the check **checks** start. Wait until it shows a green mark. The task is complete.
