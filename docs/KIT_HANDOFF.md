# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 12:20 by the session that wrote the plan below.

## State

- main: `730b726` (kit 2026.11.20: two rule tiers, three merge lanes, layered sync, and the two sync fixes from the first pilot).
- Synced and locked to 730b726: 36-3003.Z, 65-601.Z, SPAR (drift 0 of 51 each). Not synced: RADE, 90-161.Z, icf-source, sec-source.

## Approved plan (the owner, 2026-11-18 12:15; updates approved 13:25 and 14:35): lean two-tier rules and the kit as a synced baseline

Full text, proposals 1 to 26, risks and targets: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md). Scope (the owner, 2026-11-18): all 26 proposals; skills may be rewritten or combined. Records: [reviews/2026-11-18-lean-rules-review.md](reviews/2026-11-18-lean-rules-review.md), [reviews/2026-11-18-rule-tests-lean.md](reviews/2026-11-18-rule-tests-lean.md).

- [x] 0. Plan saved; toggles set (all Yes).
- [x] 1. Kit 2026.11.19 and 2026.11.20 merged (pull requests 44 and 45). Rule tests: 10 pass, 1 not valid, of 11 run.
- [x] 2. Pilot sync merged: 36-3003.Z (pull request 5), 65-601.Z (5), SPAR (10). They keep the tier "full" (the owner, 2026-11-18: the starter tier drops the project log rule).
- [ ] 3. RADE and 90-161.Z, one session each (a RADE session does not edit an app repo): steps in `.claude/skills/kit-update/SKILL.md`. First give each project guard a home (PROJECT.md, `scripts/check.local.sh`, `.check`); 90-161.Z tuned `reviewer.md` (now a kit file); both are over the 5,000-token session load. Lane C: ask the owner for each merge.
- [ ] 4. icf-source and sec-source: convert AGENTS.md to the kit layout, then sync. Lane C.
- [ ] 5. Owner layer and server side: PREFERENCES.md rewrite and paste block (proposal 5); ruleset and secret-scanning links per repo (4, 17); kit-update pull request on release (15); fleet status page (22); allow list (25); "not set yet" lines (24); a release tag (8); the setup guide for cloud environments and repos.
- [ ] 6. Proposal 20 (kit rules as one imported file): test in one pilot repo, then decide. An import does not lower the context cost (Anthropic's memory page), so its only gain is a simpler sync.
- [ ] 7. Next kit release (lane C, batch them): rule test 22 (ask for 60 s) and a new "Kit files" scenario; `sync_baseline.py` prints "An older kit hook entry is replaced" when nothing changes; `check_settings.py --migrate` keeps the old comment lines of `.check`; lane C in a hard rule is defined in a default (a project may add lane C cases, not remove them).

## Open (in order)

1. Steps 3 to 7. Done = `drift.py --strict` shows 0 kit items different in 7 repos, `scripts/check.sh` passes in each, and the targets in the plan's "Verification" table are met (session load target 4,000 not met: about 4,240; the owner accepted it for now).

## Needs the owner

- Steps 3 and 4: the merge of each sync pull request, and the removal of each "No kit sync" rule.
- Step 5: paste the new preferences; 7 rulesets (about 3 minutes each).

## Do not

- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not run `sync_baseline.py --apply` in a project before its step: five projects still have a "No kit sync" rule, and it stands until that step's pull request replaces it.
