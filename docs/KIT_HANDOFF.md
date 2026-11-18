# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 07:10 by the session of pull request 41.

## State

- main: `b24c834`. Open: [pull request 41](https://github.com/rhope-ops/archimedes_lever/pull/41), branch `claude/upbeat-bell-uxsavx`.

## Approved plan (the owner, 2026-11-18): one `check`, one home per rule, locked kit files

Decisions and approved rule texts: the 2026-11-18 rows of [DECISIONS.md](DECISIONS.md). Conflict checks: [reviews/2026-11-18-rule-conflict-2.md](reviews/2026-11-18-rule-conflict-2.md).

- [x] 0. Plan saved; decisions recorded.
- [x] 1. One content check behind `scripts/check.sh` (`check_content*.py`, `.check`, terms, `block:` lines, wider hook, `check_blocks.py`).
- [x] 2. Caps: AGENTS.md 200 lines, session load 6,000 tokens; one-home check.
- [ ] 3. One home per rule: rule texts approved and applied; skills cleaned. Left: the third conflict check and its record; docs that restate rules get links; shorter skill descriptions; a recount against the audit (21 conflicts, 35 duplicate groups, 13 stale items).
- [x] 4. Kit lock `.check.lock`, `KIT_VERSION`, [CHANGELOG.md](CHANGELOG.md).
- [ ] 5. Deliver the kit: fresh review of the whole diff, project log row, full lane and Action green, merge pull request 41.
- [ ] 6. Attach the 11 projects (every active repo except the kit and the archived one) and measure drift with `scripts/drift.py`. No writes.
- [ ] 7. Port to all 11 at once: one worker and one pull request per repo (sync, `git mv .pii-guard .check`, delete the renamed files, lock). A project rule that conflicts with a kit rule goes to the owner in one dialog.
- [ ] 8. A paste block of the revised PREFERENCES.md for the owner's account.

## Open (in order)

1. Step 3, then 5 to 8. Done = each repo has a merged pull request with a green full lane, and `drift.py` shows 0 changed kit files.

## Needs the owner

- Not in the plan (add only on approval): branch protection with the required check `checks`; GitHub secret scanning; CODEOWNERS; the kit as a Claude Code plugin; semantic versions.

## Do not

- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
