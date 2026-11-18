# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 12:20 by the session that wrote the plan below.

## State

- main: `213c58c` (pull request 41 merged: one `check`, kit lock, caps, config layout). Work branch in the kit and in each project: `claude/archimedes-lever-workflow-0mydsw`.
- No project is synced yet: 0 of 7 have `.check.lock`; all 7 still use `.pii-guard`. Drift: 48 of 65 items (RADE) to 57 of 65 (65-601.Z).

## Approved plan (the owner, 2026-11-18 12:15): lean two-tier rules and the kit as a synced baseline

Full text, measured facts, proposals 1 to 26, usage estimate, risks and targets: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md). Decisions: the first 2026-11-18 row of [DECISIONS.md](DECISIONS.md). It replaces the open steps 3 to 9 of the plan "one `check`, one home per rule, locked kit files" (its steps 0 to 6 are done).

- [x] 0.1 Plan saved here; decisions recorded.
- [x] 0.2 Proposal toggles published: https://claude.ai/artifact/7XSV5V62Wv8bKQYZsLpJLz (private; state in its database, collection `proposals`, field `on`).
- [ ] 0.3 The owner sets the toggles. Read them (`ArtifactData` list `proposals`), write the result in this file. A proposal that is off drops out of every later step.
- [ ] 1. Kit: re-read the Anthropic pages (1.1); full new AGENTS.md with "Hard rules", "Defaults" and three merge lanes, shown to the owner once for approval of the exact text (1.2); rule tests before and after (1.3); sync, drift, pre-push, one-home check and caps (1.4); doc fixes (1.5); fresh review, owner merge, release tag (1.6).
- [ ] 2. Pilot sync: 36-3003.Z, 65-601.Z, SPAR (3 workers, one pull request each).
- [ ] 3. RADE and 90-161.Z, one session each: give each project guard a home first.
- [ ] 4. icf-source and sec-source: convert to the kit layout, then sync.
- [ ] 5. Owner layer: PREFERENCES.md paste block; ruleset and secret-scanning links per repo; kit-update pull request and fleet page if toggled on; final handoffs. Still open from the old plan and kept here: the setup guide for cloud environments and repos (old step 9).

## Open (in order)

1. Step 0.3, then 1 to 5. Done = `drift.py --strict` shows 0 kit items different in 7 repos, `scripts/check.sh` passes in each, and the targets in the plan's "Verification" table are met.

## Needs the owner

- Set the toggles (step 0.3). Default: proposals 1 to 19 on, 20 to 26 off.
- Step 1.2: approve the exact AGENTS.md text. Options: approve; change lines; keep a removed rule. REC: approve after the rule tests pass.

## Do not

- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not run `sync_baseline.py --apply` in a project before its step: five projects still have a "No kit sync" rule, and it stands until that step's pull request replaces it.
