# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 16:50 by the kit owner (session "Archimedes Lever workflow optimization", the owner, 2026-11-18 16:20). Only the kit owner changes the kit and runs kit syncs; other sessions report kit faults here or to it.

## State

- main: kit 2.0.1 (79540fe; 2.0.0 = 7b80101, tag v2.0.0 by the owner; 1.0.1 was 591b4cd). Fleet page: https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW (private; the kit owner updates its rows).
- Synced: 36-3003.Z, 65-601.Z, SPAR on 2.0.1 (pull requests 8, 8, 13). RADE sync pull request 108 open (2.0.1). 90-161.Z sync pull request 155 open, blocked: its own engine-lock test fails (engine-v16, newest engine-v17), also on main; a 90-161.Z session bumps the lock, then 155 merges. Not synced: icf-source, sec-source.

## Approved plan (the owner, 2026-11-18 12:15; updates approved 13:25 and 14:35): lean two-tier rules and the kit as a synced baseline

Full text, proposals 1 to 26, risks and targets: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md). Scope (the owner, 2026-11-18): all 26 proposals; skills may be rewritten or combined. Records: [reviews/2026-11-18-lean-rules-review.md](reviews/2026-11-18-lean-rules-review.md), [reviews/2026-11-18-rule-tests-lean.md](reviews/2026-11-18-rule-tests-lean.md).

- [x] 0. Plan saved; toggles set (all Yes).
- [x] 1. Kit 2026.11.19 and 2026.11.20 merged (pull requests 44 and 45). Rule tests: 10 pass, 1 not valid, of 11 run.
- [x] 2. Pilot sync merged: 36-3003.Z (pull request 5), 65-601.Z (5), SPAR (10). They keep the tier "full" (the owner, 2026-11-18: the starter tier drops the project log rule).
- [x] 3. RADE and 90-161.Z synced to 1.0.1 (RADE pull requests 104 and 105; 90-161.Z by the session "90-161.Z: kit 1.0.1 sync").
- [ ] 4. icf-source and sec-source: convert AGENTS.md to the kit layout, then sync. Lane C.
- [ ] 5. Owner layer: preferences text and the two account skills (ship, turn-summary) done and pasted by the owner (2026-11-18); tag v1.0.0 done; rulesets and secret scanning are the owner's clicks ([github/README.md](github/README.md)); fleet page done (link under "State"); allow list (25) and "not set yet" lines (24) open.
- [x] 6. Proposal 20 dropped (the owner, 2026-11-18): an import does not lower the context cost.
- [ ] 7. Kit 2.0.0 (pull request 53) and 2.0.1 (54: shorter descriptions, so RADE and 90-161.Z stay under 5,000 tokens) merged; 3 of 5 repos synced; RADE and 90-161.Z open (State). Tag v2.0.0: the owner, from a release link.
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
- Do not add kit text without measuring RADE and 90-161.Z session load first: they sit near the 5,000 cap (about 4,807 and 4,771 after 2.0.1).
