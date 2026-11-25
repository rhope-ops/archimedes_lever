# Fleet v2: coordinator state at handoff

Written 2026-11-23 ~09:45 America/Chicago by session "Kit · Fleet v2 coordinator · 2026-11-23 · #114"
(session_01PyXpdUat26YdmzaenEFPpj). Plan: [2026-11-23-fleet-v2-plan.md](2026-11-23-fleet-v2-plan.md) (DEC 1-14 there;
DEC 15 in docs/DECISIONS.md). Briefs: [2026-11-23-fleet-v2-session-briefs.md](2026-11-23-fleet-v2-session-briefs.md).

## Kit (stage 1): done

- Kit 11.0.0 merged: PR 114, main dedc3b3. Kit 11.0.1 merged: PR 118, main 9e3f6fa (2 check.sh lines wrapped under 200
  characters, the Maintainer's merge OK). Handoff PR 117 merged.
- Reviews: 8 fresh reviews and 2 rule conflict checks; every MAJOR fixed before the merge
  ([2026-11-23-rule-conflict.md](2026-11-23-rule-conflict.md): open MINOR 2-7).
- Session load after a sync (cap 5,500): RADE ~5,232, 90-161.Z ~5,427, 33-332.Z ~5,468 after its handoff trim, ICF ~5,341.
- Sync command for a project: `python3 <kit clone>/scripts/sync_baseline.py --baseline <kit clone> --owner "the Maintainer"`
  (dry run, then `--apply`). Project steps: the CHANGELOG 11.0.0 row.

## Project sessions (each reports with send_message to the coordinator)

| Session | Id | State at handoff | Waits for |
|---|---|---|---|
| RADE · Fleet v2 engine-v36 | session_01PyXpdW7BwVyr1toNxZv4RB | The Administrator approved both narrowings in its chat; it finishes the engine PR (branch claude/fleet-v2-engine-v36), then merges by DEC 10, runs release.yml for engine-v36 (DEC 13), then the guard-file PR, then the kit 11.0.1 sync PR | Its own work. The Administrator approves its DECISIONS owner row (By: the Administrator) for the .check change in its chat |
| 33-332.Z · Fleet v2 local items | session_01PyXpdT48J9ZNT5qxN2AiiC | PRs 51, 53, 54 merged (54: Fulcrum palette, the PAM's choice). Kit 11.0.1 sync on branch claude/fleet-v2-kit-11, 4 local commits, not pushed | The PAM's explicit chat message that sets the new DECISIONS row's By cell to "the PAM" (its permission check refused the general "I approve your recommendations"). Then PR 55 (guard files) turns green |
| 90-161.Z · Fleet v2 local items | session_01PyXpdTU4iiPacMfazGVkEi | PRs 217-220 merged. Kit 11.0.1 sync done locally (8963ff2, 0bf465f, 4d6e777 on claude/fleet-v2-local-items); the PFM approved its owner row; dod-security off | "engine-v36 released" from the coordinator, after the coordinator checks the release and its attestation. Then one v36 PR: lock bump v32 -> v36, task-common Bypass + OneDrive, 6 file splits (C4 450), R41 rebuild, workflowKey rename, the kit sync commits |
| ICF · Fleet v2 handover and UX/UI | session_01PyXpdRk3bXkb6Hy4huH4Ux | PR rhope-ops/ICF-Source#241 (3C) in fresh review on 14ee5f4 after the build-number guard was dropped (kept on a local branch for its own PR after Stage 4). Then Stage 4, then the kit 11.0.1 sync (no dod-security; split new_bank_check.py, new_bank_expand.py, quality_baseline.py) | Its own work |

The first kit session (session_01PyXpdVJRLK33wotSnJgU3A) is done; branch claude/keen-cori-eiotd2 is merged.

## Rules the coordinator found in practice

- A session does not act on approvals the coordinator relays; the Maintainer writes in that session's own chat.
- An agent never writes a DECISIONS row whose By cell is the owner: the strict gate reads it as the owner's approval.
- Children cannot attach the kit repo; they read the public kit by a read-only clone.
- Relay "engine-v36 released" only after you check the release, its assets and its attestation yourself.

## Needs the Maintainer

- Tags: v11.0.0 on dedc3b3 and v11.0.1 on 9e3f6fa: done (both exist; checked 2026-11-23 15:13).
- 33-332.Z: the explicit By "the PAM" message in its chat.
- ICF preload tags: A keep (the static graph is the boot set; record a plan correction) or B lazy features later. REC: A.
- 90-161.Z: retire T17/T18/T25 in the v36 PR (REC yes); logo_svg.py B314: nosec with reason (REC) or defusedxml;
  gitleaks allow for 64-hex values in scripts/rade.lock.json only (REC yes; the hits are RADE engine file names).
- Default environment setup script: install token_log_rows.py, token_log_report.py and kit.config.json next to
  token_log.py (Work is done; the Maintainer declined the Default edit on 2026-11-23 for now).

## Kit follow-ups (not blocking)

- bootstrap.sh: one dod-security check instead of two; do not hide Python errors (review NITs).
- check_settings.py --validate-config does not read the `fleet:` key.
- Rule conflict MINOR 2-7 (Release Manager, "Owner" undefined, "a running owner", content approval against a request
  and against lane A): rule text, the Maintainer's call.

## Coordinator 2 (from 2026-11-23 ~10:17 America/Chicago)

Session "Kit · Fleet v2 coordinator 2 · 2026-11-23" (session_01PyXpdUBsuqmbKTGEWx1D5m). All 4 project sessions were told
to report to it.

- RADE engine-v36 released and verified by the coordinator (~10:30): release
  https://github.com/rhope-ops/RADE/releases/tag/engine-v36 on 6efe5c7 (the #167 merge), run 45214671013 success.
  Assets: rade-engine.sha256 `6f1a71ff…e005`, rade-engine.lock.json `5feb2292…25b1` (download hashes = release digests).
  The 42 listed files match a clone of the tag; the lock holds the same 42 hashes. Attestation: SLSA v1, 42 subjects =
  the list, cert SAN release.yml@refs/heads/main, commit 6efe5c7, DSSE signature valid, 1 Rekor entry.
  Not verified: the chain to the Sigstore root and Rekor inclusion (tuf-repo-cdn.sigstore.dev is blocked here).
  "engine-v36 released" was relayed to 90-161.Z.
- RADE was attached to the coordinator with push access (the Maintainer's message), used for API reads only.
- 90-161.Z: the PFM answered T17/T18/T25 (delete), logo_svg B314 (nosec with reason) and the rade.lock.json gitleaks
  allow (yes). Open: 2 DECISIONS rows By "the PFM" in local commit 5205e50 need the PFM's OK of their exact text.
- RADE: a DECISIONS row By "the Administrator" in its guard-file commit; the Administrator's OK of that text is not seen.
- ICF: #242 (Stage 4) MAJOR fixed at 47f0041; pytest and review round 2 were running. The forced-colors failure is
  pre-existing on main (own small PR).

### Coordinator 2 update (~12:00 America/Chicago)

- Done: RADE Stage 2 (#167, #169 kit 11.0.1 sync, #168 guard files, #170, #171 role word "the Maintainer"; release
  note added by the Maintainer, checked by API); 90-161.Z Stage 3A (#217-#222; #221 engine-v36 + kit 11.0.1, gitleaks
  allow proven green); ICF #242, #243, #244, #245, #246. Open: ICF forced-colours fix, ICF kit 11.0.1 sync (the
  Maintainer sent the read-only kit clone message), then Step 3 rule text.
- Decisions (the Maintainer, 2026-11-23, in the coordinator chat): (1) the owner's real name is never provided; an owner
  value is the role "Owner", or "Manager" on a conflict (scope: fleet v2 owner-name steps); (2) ICF owner rotation: no
  rotation and no date now, takeover only staged (ICF #246); (3) keep the token log branch, `/cost` in the plugin pane
  for a live view (scope: token tracking); (4) RADE #168 gitleaks: look again after the kit sync (done: a lock hash).
- Plan step added by the Maintainer (2026-11-23), after Step 3: draft a lessons-learned and preventive-measures
  introspection as .md (Drive › Rhope and docs/reviews/2026-11-23-fleet-v2-lessons.md, lane A; rule changes only as
  proposals), and export each repo changed today (archimedes_lever, RADE, 90-161.Z, 33-332.Z, ICF-Source) as
  <repo>-2026-11-23.7z with full git history (all branches and tags), no password, to Drive › Rhope.
- Token totals (2026-11-23 ~11:15): measured since tracking 7.52 B tokens, ~$2,665 at list prices (5 repos);
  estimated before tracking ~6.0 B, ~$2,230 (low-medium confidence); sum ~13.9 B, ~$5,000.

### Coordinator 2 close (~15:10 America/Chicago)

- Fleet v2 stages 1-4 done (RADE #167-#171, 90-161.Z #217-#222, 33-332.Z #51-#56, ICF #241-#250). Site 2.12.2 deployed by the
  coordinator at the Maintainer's request (rhope-ops/icf aadd154; 61 of 61 files equal live). Live pages 200: icf, RADE, 90-161.Z,
  33-332.Z and its Ion-script.txt link (2026-11-23 ~15:05).
- Step 3 (rule text) is NOT done: it moved into the Part 2 program (the Maintainer's choice 1C; rule texts approved through the
  program plan). The R1-R4 draft (2026-11-23-fleet-v2-step3-rules.md) is input only: R1, R3 kept; R2 replaced by T1, T2; R4 became T6.
- Lessons: 2026-11-23-fleet-v2-lessons.md (also Drive > Rhope). Exports: 6 full-mirror .7z archives (5 repos + icf) built and
  checked (fsck 0 errors, 7z t, RADE restore test, content check 0 findings); the Drive connector limit (~3.1 MB per call) blocked
  the upload, so they were sent to the Maintainer in the chat for a hand upload.
- Open: branch deletes (host 403); ICF modulepreload A/B; R41 r2 device run; attestation chain unverified;
  33-332.Z AUDIT DUE and the PAM role-line suggestion; plan GAPS "Get-ExecutionPolicy -List" proof and per-stage rollback notes.

## Rollback notes per stage (the Maintainer, 2026-11-23, plan GAP)

Undo by a revert pull request of the merge commit (`git revert -m 1 <merge>`), never a reset or force-push; take the
stages in reverse order (4, 3, 2, 1), because each later stage depends on the one before.

| Stage | What to revert | Extra step |
|---|---|---|
| 4 ICF | ICF-Source #250, #249 (kit sync), #248 (split), #247, #246, #245, #244, #243 (guard files), #242 | Site: after the revert is on main, run `publish_pages.py <clone of rhope-ops/icf> --push`; it publishes main's site/dist (the script refuses any commit not on origin/main). Today's live release: rhope-ops/icf aadd154 (2.12.2); before: e08c341 (2.10.2) |
| 3C ICF | ICF-Source #241 | Same Site step |
| 3B 33-332.Z | #56 (kit sync), #55 (guard files), #54 (palette), #53, #51 | Ion-script.txt link stays valid (only the .ps1 copy was deleted) |
| 3A 90-161.Z | #221 (engine-v36 lock + kit sync), then #217-#220 | The revert restores the engine-v32 lock and its bundles. To move forward instead: `python3 scripts/bump_lock.py engine-v35` (or another tag) downloads that release lock, rebuilds the round bundles with the next revision, traces them and runs check.sh |
| 2 RADE | #171, #170, #169, #168, #167 | engine-v36 stays published (a release is not deleted); apps pin their lock, so no app changes unless it bumps. Release a fixed engine as v37 if needed |
| 1 Kit | PR 118 (11.0.1), PR 114 (11.0.0) | Each project then needs its own revert of its kit sync PR |

Exports: the 6 .7z archives of 2026-11-23 are a reference copy; the Maintainer wants fresh exports after the tool
retirement program.

## Coordinator 2: evening (~19:00-23:30 America/Chicago)

Tool retirement program P2 (session_01PyXpdWCaPYjt4M7hbiPpzm) and the README cards. Each merge below had the Maintainer's
own merge message in the coordinator chat; the coordinator checked CI on the head commit and the merge on origin/main.

| PR | What | Merge commit | T2 baseline after |
|---|---|---|---|
| #144 | P2 (b) two-line marking and keyword+number | fdeed30 | |
| #146 | Kit README shows its social preview card (cards also fixed in RADE, 90-161.Z, 33-332.Z, ICF) | e0c9a52 | |
| #149 | P2 (d): the sync stops instead of overwriting a project's local kit edits | 6bd300e | 18,663 (+360) |
| #150 | P2 (a): ruff 0.17.6 + pylint 4.1.4 check Python parse, line length, file size (C0302 WARN only) | 7dd6f4d | 18,785 (+122) |
| #147, #148, #151, #152 | Handoffs and P2 (h) AUD-5 records (lane A) | 2fbde15, 747754f, 00356b1, e56eeef | |

- Feature retirements measured: timeline.py (-475), fulcrum_palette.py (-314), build_site.py (-481). The Maintainer chose
  "Keep it, no retirement" for timeline.py (real fleet use). No retirement is planned, so T2 has only risen tonight
  (18,303 -> 18,785).
- Freeze: the Maintainer lifted it in the P2 chat ("This chat: d at 18663"); each rise is still asked on its own.
- Open in P2 (built locally, each waits for its own T2 number): (g) shellcheck WARN +51, (j) skill-use counts +138,
  (i) worker_guard --scan + S8 +246. All three would put the baseline at 19,220.
- Ion (33-332.Z, session_01PyXpdRW1VbtvtPjBsVLfRe): paused at the Maintainer's request; PR #60 (013ca82) newest fixes not
  reviewed; PR #61 (fd64a8e) 1 open MAJOR (non-ASCII digits after "passport"). Nothing merged or released.

## Coordinator 2: P3 package-mode rollout closed (2026-11-24 ~19:10 America/Chicago)

The Maintainer approved all lane C merges of this plan in advance ("I want to approve all Lane C merges in advance ...
just finish the plan", coordinator chat, 2026-11-24). Every merge below had a last fresh review with 0 MAJOR and green
CI on its head (ICF-Source is private: the full lane on the head instead); the coordinator checked each CI run's head SHA.

| Repo | PRs merged | Tracked script lines before -> after |
|---|---|---|
| Kit | #171 (DoD test samples built at run time), #173 (kit install at session start), #174 (reviewer blocks deletes; T2 20,025) | 18,303 -> 20,025 |
| 33-332.Z | #99, #102-#104 (P3 pilot), #77, #108 (hook sync; 2 `.check` workaround lines removed) | 14,155 -> 7,896 |
| 90-161.Z | #226 (sync), #227 (package mode), #228 (hook sync) | 17,986 -> 14,849 |
| RADE | #174 (9 long lines; ENGINE_RELEASE 37), #175 (sync), #176 (package mode; release.yml split into a read-only checks job and a release job), #177 (handoff) | 14,686 -> 11,535 |
| ICF-Source | #265 (sync), #266 (package mode) | 46,895 -> 43,743 |
| Fleet | | 112,025 -> 98,048 (-12 %) |

The cut removes copies of kit scripts from projects; the code kept in one place (the kit) grew by 1,722 lines.

- RADE engine-v37 released (run 45516273420; tag on b645019). Checked by the coordinator: both asset sha256 values, the
  42 listed files against the tag, the lock's 42 hashes. Not checked: the attestation chain (Sigstore host blocked).
- Startup hook proven in a fresh RADE session: "SessionStart:startup hook success: KIT PACKAGE PASS: 17 kit scripts from
  the package at f38ec20 (written)", package at the lock commit, check.sh "PASS kit package".
- New cloud sessions can start from a saved container copy, so the environment setup script is not where the kit
  install happens (90-161.Z proof session, setup step 13 ms); kit #173 moved it to a SessionStart hook.

Kit follow-ups (not done): `code_standard.py --update` drops Python line debt that ruff/pylint still fail; the
approval-quote marker text says a sync adds it (no sync does; no `## Decisions` heading in some projects);
worker_guard_scan flags PowerShell `@(` (a fix must apply only to the joined value; a first try weakened the scan and
was dropped); `--kit-install` runs pip outside a venv (PEP 668); the delegate skill does not name the reviewer delete
block; kit-update SKILL.md and the check.sh comment disagree about the setup script; no CHANGELOG row for the Python
line cap moving to ruff/pylint; RADE and ICF-Source lack kit #174 until their next sync; session loads near the cap
(RADE 5,475, 33-332.Z 5,484, 90-161.Z 5,462 of 5,500). For the Maintainer: a first name in ICF-Source
docs/reviews/HANDOFF-HISTORY.md:58 (on main before this work).

## Coordinator 3: kit follow-ups, 11.1.0, master plan P4-P6 (2026-11-24 21:18 America/Chicago)

Session "Kit · Fleet coordinator 3 · 2026-11-24" (session_01PyXpdUk7tSsbCmQXyLSzEZ). Plan: [2026-11-24-kit-followups-plan.md](2026-11-24-kit-followups-plan.md)
(DEC 3-6 there). The Maintainer, 2026-11-24 ~20:40: "push forward and finish the master plan without stopping to seek my
approval for anything. if you have a doubt, go with your top recommendation every time."

- Kit merged: #175, #176 (plan), #178 (items 1, 4), #179 (item 2), #180 (items 5, 6), #182 (11.1.0 release files), #183
  (gate skips what ruff E501 skips), #184 (speed test 10 s). #181 (item 3) closed by DEC 5. T2 20025 -> 20132 (+107).
- Kit 11.1.0 = a6295509. Tag v11.1.0: NOT made; the git proxy refuses tag pushes (HTTP 403). The Maintainer's step:
  https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v11.1.0&target=a6295509a846e955550f1ab238fb76514c302cad
- Step 7 lock bumps to a6295509, all merged: 90-161.Z #230 (b77bdd2), ICF-Source #270 (489cf4e), RADE #178 (49bc202),
  33-332.Z #116 (0210855); drift 0 (ICF 1: FIRST_USE.md kept); T6 now runs in all 4. 90-161.Z #229 (docs "Work").
- Decisions: ICF name item closed, left as is (.check allows it). The shared pip package moves with each repo's
  --kit-install; run it again before a full lane when you switch repos in one container.
- Child sessions (each opens PRs; lane C PRs come to the coordinator to merge):
  P4a RADE session_01PyXpdVfw9jpFCReAUi1PYG; P4c 33-332.Z session_01PyXpdV3io8vBJPYeu9RznR; P4d ICF
  session_01PyXpdVWpiRDJgfTk7BNFAM; P5 kit 11.1.0 syncs: no-more-beyond session_01PyXpdURZvfgWsTwcw48S6m,
  transcription_assistant session_01PyXpdW1pEpCSe6jQ1u1wdd, SPAR session_01PyXpdTpQKmTxMrwFYEHUzA, 36-3003.Z
  session_01PyXpdScRUVW4B2tH7maZfR, 65-601.Z session_01PyXpdVti6gRLzAojGiRaDD.
- Next: P4b 90-161.Z after R42 (session_01PyXpdSTSEFZnDJfY86PNqg, same go.md) and the P4a engine release; then the P5
  fleet audit and the SEC-Source inventory; P6 exports and the branch-delete list.
- Known limits: strict gate without linters is a little looser than ruff (CI catches it); worker scan @( false finding
  stays (DEC 5).

### Coordinator 3: night run (2026-11-24 21:40-22:20 America/Chicago)

- P4c 33-332.Z: #118 merged (fae3916; paste check in Ion; CI 4/4, review 0 MAJOR). Open: 3 MINOR text items (one
  follow-up PR after the PAM's ISE test, expect "Paste check: OK", build 240bf873); #61 paused, rebuild after.
- P4a RADE: #179 merged (f5b4687, paste guard in build(); check.local.sh:73 runs tests/paste_guard_test.py), release
  engine-v38 tagged at f5b4687 (run 45544195036); #180 merged (2c7bedd, 175 % window run, green on Windows PS 5.1).
  Blocked: hashed requirements (7 pins, branch claude/p4a-hashed-requirements, local only in the child) and its
  CycloneDX SBOM (a person rejected the cyclonedx-py call at the prompt, 04:02Z); CodeQL Python workflow not started.
  Unblock: the Maintainer says go (or "pins without SBOM") in session_01PyXpdVfw9jpFCReAUi1PYG.
- P4b 90-161.Z: waits for R42 #231 (it moves its lock to engine-v38 before its merge).
- P6: full-history .7z exports made for 9 repos (all but the kit and 90-161.Z, which still change); branch list:
  [2026-11-24-p6-branch-list.md](2026-11-24-p6-branch-list.md) (112 CONTAINED, safe; 41 NOT-CONTAINED, keep).
