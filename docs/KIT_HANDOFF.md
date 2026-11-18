# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 12:20 by the session that wrote the plan below.

## State

- main: `dde2bb3` (pull request 43: the plan below). Work branch in the kit and in each project: `claude/archimedes-lever-workflow-0mydsw`.
- No project is synced yet: 0 of 7 have `.check.lock`; all 7 still use `.pii-guard`.

## Approved plan (the owner, 2026-11-18 12:15): lean two-tier rules and the kit as a synced baseline

Full text, measured facts, proposals 1 to 26, risks and targets: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md). Scope (the owner, 2026-11-18): all 26 proposals; skills may be rewritten or combined. Toggle record: https://claude.ai/artifact/7XSV5V62Wv8bKQYZsLpJLz (all Yes).

- [x] 0. Plan saved; toggles set.
- [ ] 1. Kit, in one lane C pull request: AGENTS.md in "Hard rules" and "Defaults", three merge lanes, skills `verify` and `kit-update`, scripts, caps, docs, version 2026.11.19. Reviews: [reviews/2026-11-18-lean-rules-review.md](reviews/2026-11-18-lean-rules-review.md). Left: the owner's merge; a release tag; a run of the rule tests in fresh sessions (not run yet).
- [ ] 2. Pilot sync: 36-3003.Z, 65-601.Z, SPAR (one pull request each; steps: `.claude/skills/kit-update/SKILL.md`; starter tier until their first code, proposal 21).
- [ ] 3. RADE and 90-161.Z, one session each: give each project guard a home first; trim their session load under 5,000 tokens.
- [ ] 4. icf-source and sec-source: convert to the kit layout, then sync.
- [ ] 5. Owner layer and server side: PREFERENCES.md rewrite and paste block (proposal 5); ruleset and secret-scanning links per repo (4, 17); kit-update pull request on release (15); fleet status page (22); allow list (25); "not set yet" lines (24); the setup guide for cloud environments and repos.
- [ ] 6. Proposal 20 (kit rules as one imported file): test it in one pilot repo after step 2, then decide. Anthropic's memory page says an import does not lower the context cost, so its only gain is a simpler sync.

## Open (in order)

1. Steps 1 to 6. Done = `drift.py --strict` shows 0 kit items different in 7 repos, `scripts/check.sh` passes in each, and the targets in the plan's "Verification" table are met.

## Needs the owner

- Step 1: merge the kit pull request (its text shows every rule in full; the merge approves the rule text).
- Step 2 to 4: approve the removal of each project's "No kit sync" rule (AGENTS.md "Kit files" replaces it).

## Do not

- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not run `sync_baseline.py --apply` in a project before its step: five projects still have a "No kit sync" rule, and it stands until that step's pull request replaces it.
