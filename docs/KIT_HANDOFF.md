# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 12:20 by the session that wrote the plan below.

## State

- main: `d226ea3` (kit 2026.11.20.1: two rule tiers, three merge lanes, layered sync, extension files for project code; pull requests 42 to 46).
- Synced and locked to d226ea3 on their main: 36-3003.Z, 65-601.Z, SPAR (drift 0 of 56 each; second sync merged by pull requests 6, 6 and 11). Not synced: RADE, 90-161.Z, icf-source, sec-source.

## Approved plan (the owner, 2026-11-18 12:15; updates approved 13:25 and 14:35): lean two-tier rules and the kit as a synced baseline

Full text, proposals 1 to 26, risks and targets: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md). Scope (the owner, 2026-11-18): all 26 proposals; skills may be rewritten or combined. Records: [reviews/2026-11-18-lean-rules-review.md](reviews/2026-11-18-lean-rules-review.md), [reviews/2026-11-18-rule-tests-lean.md](reviews/2026-11-18-rule-tests-lean.md).

- [x] 0. Plan saved; toggles set (all Yes).
- [x] 1. Kit 2026.11.19 and 2026.11.20 merged (pull requests 44 and 45). Rule tests: 10 pass, 1 not valid, of 11 run.
- [x] 2. Pilot sync merged: 36-3003.Z (pull request 5), 65-601.Z (5), SPAR (10). They keep the tier "full" (the owner, 2026-11-18: the starter tier drops the project log rule).
- [ ] 3. RADE and 90-161.Z, one session each (a RADE session does not edit an app repo): steps in `.claude/skills/kit-update/SKILL.md`. First give each project guard a home (PROJECT.md, `scripts/check.local.sh`, `.check`); 90-161.Z tuned `reviewer.md` (now a kit file); both are over the 5,000-token session load. Lane C: ask the owner for each merge. Their own scanner and code-standard code go to `scripts/check_content_local.py` and `scripts/code_standard_gate.py`; notes: docs/reviews/2026-11-18-port-notes/.
- [ ] 4. icf-source and sec-source: convert AGENTS.md to the kit layout, then sync. Lane C.
- [ ] 5. Owner layer and server side: PREFERENCES.md rewrite (draft in pull request 48, waits for the owner's approval of its text); rulesets and secret scanning (the owner's clicks; steps given 2026-11-18); fleet status page (proposal 22); allow list (25); "not set yet" lines (24); a release tag with the next release (8).
- [x] 6. Proposal 20 dropped (the owner, 2026-11-18): an import does not lower the context cost.
- [ ] 7. Next kit release (lane C, one batch, after the sync pull requests of RADE and 90-161.Z are merged): the approved lane C text in "The owner's approval"; a deliver-skill line "after a kit release merges, the releasing session opens the sync pull request in each synced repo" (proposal 15); rule test 22 (ask for 60 s) and a new "Kit files" scenario; a quieter sync message when nothing changes; kit faults that RADE and 90-161.Z report; then a release tag, and the sync pull requests of the synced repos.
- [x] 8. Kit 2026.11.20.1 merged (pull request 42, from the session of pull request 41).

## Open (in order)

1. Steps 3 to 7. Done = `drift.py --strict` shows 0 kit items different in 7 repos, `scripts/check.sh` passes in each, and the targets in the plan's "Verification" table are met (session load target 4,000 not met: about 4,240; the owner accepted it for now).

## Needs the owner

- Steps 3 and 4: the merge of each sync pull request, and the removal of each "No kit sync" rule.
- Step 5: paste the new preferences; 7 rulesets (about 3 minutes each).

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not run `sync_baseline.py --apply` in a project before its step: RADE and 90-161.Z still have a "No kit sync" rule, and it stands until that step's pull request replaces it.
