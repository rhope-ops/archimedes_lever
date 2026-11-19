# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 18:20. Kit owner: the session that takes the 3.2.0 plan (the owner, 2026-11-18); the earlier kit owner session stops kit work.

## State

- main: kit 3.1.0 (88185f0). Tags (feature releases; the owner makes them): v2.0.0 (7b80101), v3.0.0 (67e7766), v3.1.0 (88185f0). Fleet page: https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW (private; the kit owner updates its rows).
- All seven repos on the kit: icf-source and 90-161.Z on 3.1.0 (PRs 135, 155); RADE, 36-3003.Z, 65-601.Z, SPAR, sec-source on 3.0.0 (3.1.0 adds only an optional setting). Session load near the cap: sec-source ~4,989, icf-source ~4,967.

## Approved plan (the owner, 2026-11-18 12:15; updates approved 13:25 and 14:35): lean two-tier rules and the kit as a synced baseline

Full text, proposals 1 to 26, risks and targets: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md). Scope (the owner, 2026-11-18): all 26 proposals; skills may be rewritten or combined. Records: [reviews/2026-11-18-lean-rules-review.md](reviews/2026-11-18-lean-rules-review.md), [reviews/2026-11-18-rule-tests-lean.md](reviews/2026-11-18-rule-tests-lean.md).

- [x] 0. Plan saved; toggles set (all Yes).
- [x] 1. Kit 2026.11.19 and 2026.11.20 merged (pull requests 44 and 45). Rule tests: 10 pass, 1 not valid, of 11 run.
- [x] 2. Pilot sync merged: 36-3003.Z (pull request 5), 65-601.Z (5), SPAR (10). They keep the tier "full" (the owner, 2026-11-18: the starter tier drops the project log rule).
- [x] 3. RADE and 90-161.Z synced to 1.0.1 (RADE pull requests 104 and 105; 90-161.Z by the session "90-161.Z: kit 1.0.1 sync").
- [x] 4. sec-source (PR 15) and icf-source (PR 135) converted to the kit layout and synced.
- [ ] 5. Owner layer: preferences text and the two account skills (ship, turn-summary) done and pasted by the owner (2026-11-18); tag v1.0.0 done; rulesets and secret scanning are the owner's clicks ([github/README.md](github/README.md)); fleet page done (link under "State"); allow list (25) and "not set yet" lines (24) open.
- [x] 6. Proposal 20 dropped (the owner, 2026-11-18): an import does not lower the context cost.
- [x] 7. Kit 2.0.0, 2.0.1, 3.0.0 (private repos skip the PR Action), 3.1.0 (`content-max-bytes`) merged; syncs as under State.
- [x] 8. Kit 2026.11.20.1 merged (pull request 42, from the session of pull request 41).

## Open (in order)

0. Kit 3.2.0: [plan](reviews/2026-11-18-kit-3.2.0-plan.md) (approved 2026-11-18 18:15; scope, checks, syncs).
1. Step 5 (rulesets, secret scanning: the owner's clicks, docs/github/README.md).

## Needs the owner

- The merge of each lane C pull request of the 3.2.0 plan; the v3.2.0 release link; rulesets and secret scanning.

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first: sec-source (~4,989) and icf-source (~4,967) sit near the 5,000 cap.
