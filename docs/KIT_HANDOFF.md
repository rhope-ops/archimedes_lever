# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-19 15:33. Kit owner: the session "Kit · Fleet decision hub · 2026-11-19" (fleet hub plan). Before: "Kit · Session names and project tags · 2026-11-19" (kit 4.0.0).
Next update: 2026-11-20, the fleet page preview (plan step 5)
## State

- main: kit 4.1.0 (383a95b, PR 72, fleet format; before: 4.0.0, c8339c3, PR 64). Tags (feature releases; the owner makes them): v2.0.0 (7b80101), v3.0.0 (67e7766), v3.1.0 (88185f0); v3.2.0, v4.0.0 and v4.1.0 not made yet (Needs the owner). Fleet page: https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW (private; the kit owner updates its rows). Its "Waiting for you" list (2026-11-19) reads the `needs` field (`[{text, url}]`) of `meta/kit` and of each `repos` row: the session that closes or adds an owner action updates that field.
- Seven repos on 4.0.0 (c8339c3; merged 2026-11-19): RADE 126, 90-161.Z 179, icf-source 168, 36-3003.Z 12, 65-601.Z 12, sec-source 21, SPAR 17. Session load: RADE ~4,985, icf-source ~4,939, 90-161.Z ~4,850, sec-source ~4,745. First conversions merged 2026-11-19 (owner-approved rule texts): no-more-beyond PR 63 (~4,903 tokens), transcription_assistant PR 6 (~4,887). NMB follow-ups: delete superseded tools (D4); set `.claude/agents/nmb-reviewer.md` to opus (D3).

## Approved plan (the owner, 2026-11-19 about 14:45): fleet decision hub (kit template)
Full text, decisions and approved rule text: [reviews/2026-11-19-fleet-decision-hub-plan.md](reviews/2026-11-19-fleet-decision-hub-plan.md). Scope: the kit; the owner ports it per project. Earlier plans: kit 4.0.0 session names done except step 3 (tag v4.0.0) ([record](reviews/2026-11-19-session-names-plan.md)); lean rules done except step 5 (D86).
- [x] 0-3. Plan, [survey](reviews/2026-11-19-fleet-survey.md), [contract](reviews/2026-11-19-fleet-contract.md) (approved 15:10), kit PR 72 (merged 2026-11-19, kit 4.1.0). [ ] 4. [Pilot](reviews/2026-11-19-fleet-pilot.md): files done (PR 73); the page write waits for D88. Then [ ] 5. Page (preview first). 6. Loop proof. 7. Port guide, daily harvest task.

## Timeline

- 2026-11-19 · Kit 4.1.0, fleet format (PR 72) · done
- 2026-11-19 · Fleet pilot on the kit (plan step 4) · planned
- 2026-11-20 · Fleet page redesign, preview first (plan step 5) · planned
- 2026-11-21 · Loop proof and port guide (plan steps 6-7) · planned

## Open (in order)

0. Kit fixes for the next PATCH (found by the 3.2.0 reviews; none blocks a repo): (a) the sync swaps "the owner" for each repo's role inside `scripts/check_settings.py`, so `OLD_HEADER_LINES` misses the old "the owner's request" line: exclude that file from the swap or match any role (5 repos got a hand fix in their sync PR); (b) `new_header` stops at a blank line; (c) NITs: the `audit-duplicate-ignore` wording in `bloat_check.py`, the CHANGELOG 3.2.0 row does not name `sync_merge.py`; (d) `fix_hooks` in session_checkin.sh keeps any non-kit hooks path, so a converted repo with an old `tools/git-hooks` path skipped the content check (NMB and TA fixed it in their project layer; the kit should repoint known old paths or warn); (f) first use keeps the kit's own "Project rules" lines (the Fleet choices line, 4.1.0) in a new project: empty that section at first use (docs/reviews/2026-11-19-rule-conflict-fleet.md finding 4); (e) 90-161.Z commit 50421f2 (DECISIONS "By" Agent to PFM, NIT) is unpushed: its pre-push needs pwsh, which the cloud sandbox lacks.

## Needs the owner

- D83 · Make tag v3.2.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v3.2.0&target=18896fc5ae5e954eeb0182bc4beae264eee9d541&title=Kit%203.2.0) · Options: done / not done · REC: done
- D84 · Make tag v4.0.0 (https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v4.0.0&target=c8339c31cc75d50106ede550afd1c36e4c7b529f&title=Kit%204.0.0) · Options: done / not done · REC: done
- D85 · Make tag v4.1.0 at the merge commit of PR 73 (the link follows when it merges) · Options: done / not done · REC: done
- D88 · Approve the first fleet page write (dry-run counts: reviews/2026-11-19-fleet-pilot.md) · Options: yes / no · REC: yes
- D86 · Turn on the rulesets and secret scanning (docs/github/README.md) · Options: done / not done · REC: done

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first: after 4.0.0, RADE (~4,985) and icf-source (~4,939, and ~4,994 on an open branch) sit at the 5,000 cap; the next kit text needs a cut first.
