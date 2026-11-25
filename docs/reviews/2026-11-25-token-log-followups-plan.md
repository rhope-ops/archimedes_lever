# Token log follow-ups: plan (2026-11-25, America/Chicago)

Source: the token log audit of 2026-11-25 (independent reviewer, head ffe67ad) and the review of #200.
Approved by the Maintainer in the question dialog, 2026-11-25 shortly before 08:10: "Pin to release tags (Recommended)", "Narrow it (Recommended)", and the other fixes "Alarm on 0 rows, One ls-remote, exact ref, Docs and one home, Auto-attach token-logs".
Branch: ccr-40a78b02-eyp568 (restarted from main f6ef0a9). One pull request, lane C (guard files: token_log*.py install path, pre-push, session check-in).

| # | Item | Files | Done when |
|---|---|---|---|
| 1 | Self-update installs the newest `v*` release tag, not main | scripts/token_log.py | self-test case: picks the highest tag; no tag: not updated |
| 1b | Setup script installs the same tag | Work environment setup script (update_environment, Maintainer approves the prompt) | script clones the newest `v*` tag |
| 1c | Protect `v*` tags | GitHub ruleset (the Maintainer, hand step) | ruleset exists |
| 2 | Fall back to origin only when the private repo is not reachable; never push costs/ and limits/ to origin when a private repo is set | scripts/token_log.py | self-test cases for both |
| 3 | Alarm when a transcript with replies gives 0 rows | scripts/token_log.py | push.log line; self-test case |
| 4 | One ls-remote per try; exact `refs/heads/<branch>` match | scripts/token_log.py | self-test case for a suffix ref |
| 5 | Stale docs; one home for the SKILL.md path rule | token_log.py header, docs/tools.md, token_log_rows.py, skill_use.py | bloat and code checks pass |
| 6 | Session check-in tells the agent to attach rhope-ops/token-logs when a private log repo is set and not reachable | scripts/session_checkin.sh | self-test case |
| 7 | pre-push log_only fails closed with a shallow file; test for the commit-graph defence | scripts/git-hooks/pre-push | self-test cases |

Checks: scripts/check.sh full lane, the two self-tests, a fresh review of the head commit; the Maintainer approves the merge (lane C) and a new script-line baseline.
