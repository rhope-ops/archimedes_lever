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

- Tags: v11.0.0 on dedc3b3 and v11.0.1 on 9e3f6fa (links in docs/KIT_HANDOFF.md).
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
- Open: tags v11.0.0/v11.0.1; branch deletes (host 403); ICF modulepreload A/B; R41 r2 device run; attestation chain unverified;
  33-332.Z AUDIT DUE and the PAM role-line suggestion; plan GAPS "Get-ExecutionPolicy -List" proof and per-stage rollback notes.
