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
- [ ] 3. One home per rule: rule texts approved and applied; skills cleaned; 3 conflict checks recorded. Left: the fourth conflict check (merge rule: ask by default) and its record; a recount against the audit.
- [ ] 4b. Config layout `.check` + `.check.lock` + `.check.state.json` (`scripts/check_settings.py --migrate`); needs its own fresh review.
- [x] 4. Kit lock `.check.lock`, `KIT_VERSION`, [CHANGELOG.md](CHANGELOG.md).
- [ ] 5. Deliver the kit: the first fresh review is done and its 3 MAJOR findings are fixed; a review of the fixes and of 4b, a project log row, full lane and Action green, then ask the owner for the merge of pull request 41.
- [x] 6. Projects attached and measured (clones next to the kit). 5 kit projects: RADE and 90-161.Z (47 of 64 items differ; session load about 7,084 and 8,269 tokens, over the cap), SPAR, 65-601.Z, 36-3003.Z (56 of 64; older kit). icf-source and sec-source have their own layout.
- [ ] 7. Port to those 7 (the owner's scope): one worker and one pull request per repo (sync or hand port, `check_settings.py --migrate`, delete the renamed files, lock; trim the two large ones under the cap). A project rule that conflicts with a kit rule goes to the owner in one dialog. The owner merges each, unless waived.
- [ ] 8. A paste block of the revised PREFERENCES.md for the owner's account.
- [ ] 9. Setup guide for the owner (asked 2026-11-18): how to configure each Claude cloud environment and each GitHub repo for the new `check` (word lists, Actions secrets, the required check `checks`), one deep link per step.

## Open (in order)

1. Step 3, then 5 to 8. Done = each repo has a merged pull request with a green full lane, and `drift.py` shows 0 changed kit files.

## Needs the owner

- Not in the plan (add only on approval): branch protection with the required check `checks`; GitHub secret scanning; CODEOWNERS; the kit as a Claude Code plugin; semantic versions.

## Do not

- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
