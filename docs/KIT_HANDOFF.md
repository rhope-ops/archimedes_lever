# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-18 10:15 by the session of pull request 41.

## State

- main: `213c58c` (pull request 41 merged 2026-11-18, the owner approved). Kit version 2026.11.18.
- Project clones are next to the kit (`/home/user/<repo>`), each on branch `claude/upbeat-bell-uxsavx`. Port briefs: the session scratchpad `PORT_BRIEF.md`.

## Approved plan (the owner, 2026-11-18): one `check`, one home per rule, locked kit files

Decisions and rule texts: the 2026-11-18 rows of [DECISIONS.md](DECISIONS.md). Steps 0 to 6 are done.

- [ ] 7. Ports (scope: 7 repos). The owner merges; one dialog for all 7. State per repo:
  - SPAR `a2efe40`, 65-601.Z `c7a9646` (synced), 36-3003.Z `2c33d33` (hand port): pushed; drift 57 to 3 of 65; full lane green except the conflict-check record (hash `6741fcd34a6b`). Conflict check done: 1 MAJOR each ("No kit sync" against the kit lock: needs the owner). Miss: SPAR and 65-601.Z have a "No kit sync" decision row and were synced.
  - RADE `56e61a0`: pushed; load 5,917 of 6,000; own tests pass; 18 lock overrides (it added safety labels and full docs to the kit files); conflict hash `59fa42518535` not checked yet.
  - 90-161.Z `b031e94`: local only (its hook blocks the push): strict code standard fails on the kit files, load 6,759 of 6,000, a project rule names `scripts/pii_guard.py`. Record: its docs/reviews/2026-11-18-kit-port-one-check.md.
  - icf-source `562b527`: pushed; own check passes (75); `.bloat-audit.json` stays (own bloat check, own keys).
  - sec-source `6bd94d7`: local only: 2 marking findings already on main block the push; migration stopped on old budget keys.
- [ ] 7b. Second kit pull request (found by the ports): `check_settings.py --migrate` must not stop on old or project-only budget keys; accept `code-max-line-chars` and a strict safety level; kit files meet the strict code standard (take RADE's labels and docs, if the owner agrees); a sync refreshes `reviewer.md` and `FIRST_USE.md` when they are old kit copies; `--migrate` renews the old header comment of `.check`. Then re-copy into RADE and 90-161.Z and drop their overrides.
- [ ] 7c. Per repo: the owner's rule texts, a fresh conflict check and code review, pull request, then the one merge dialog.
- [ ] 8. A paste block of the revised PREFERENCES.md for the owner's account.
- [ ] 9. Setup guide for the owner: each Claude cloud environment and each GitHub repo (word lists, Actions secrets, the required check `checks`; a repo that required `scan` must rename it).

## Needs the owner

- Not in the plan (add only on approval): branch protection with the required check `checks`; GitHub secret scanning; CODEOWNERS; the kit as a Claude Code plugin; semantic versions.

## Do not

- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
