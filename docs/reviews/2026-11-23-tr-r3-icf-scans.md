# Tool retirement R3: ICF pre-transfer scans (read-only)

Run 2026-11-23 ~15:20 America/Chicago by session "Kit · Tool retirement · 2026-11-23 · #125" (coverage row B2-7; master
plan item 4.3, scan part only). ICF-Source clone: full history, HEAD 02a7ed2d (the #250 merge, after fleet v2 closed).
Counts only: no names or addresses are written here or in chat.

| Scan | Command | Result |
|---|---|---|
| Commits and refs | `git rev-list --all --count`; `git for-each-ref` | 2,877 commits; 16 branches |
| Authors in history | `git log --all --format='%an <%ae>' \| sort -u` (counted, not printed) | 11 name/address pairs; 7 unique addresses: 5 GitHub noreply, **2 other addresses** (also 2 non-noreply committer addresses) |
| Content check, tracked files | `scripts/check.sh --content --all` | PASS: 0 findings in 3,376 tracked files; 9 skip rules; profile dod |
| ICF-Source branch rulesets and protection | `gh api repos/rhope-ops/icf-source/rulesets`, `.../branches/main/protection` | **Not available**: HTTP 403 "Upgrade to GitHub Pro or make this repository public". The private repo on the current plan cannot have a ruleset or branch protection |
| ICF-Source secret scanning | `gh api repos/rhope-ops/icf-source` (`security_and_analysis`) | **null**: GitHub secret scanning is not available for this private repo on the current plan. CI has its own scan: gitleaks/content steps in `check.yml` and `release-checks.yml` |
| icf (deploy repo) rulesets and secret scanning | GitHub API | **Blocked**: the API needs the repo attached with credentials; the attach was denied in this session (auto mode classifier). Unblock: the Maintainer allows it, or reads Settings › Rules and Settings › Code security of rhope-ops/icf |

## Findings for the handover (the Maintainer's decision; not acted on)

1. 2 addresses in ICF-Source history are not GitHub noreply addresses. History keeps them for good; a transfer gives the
   incoming maintainer the full history. Options: accept, or rewrite history before transfer (a hard-rule "Git history"
   case: only the Maintainer can change it). REC: the Maintainer looks at the 2 addresses locally and decides.
2. ICF-Source main has no server-side protection (plan limit). Options: the receiving account has a plan that allows
   rulesets, or the repo goes public, or the local pre-push hook stays the only guard. REC: record it in the handover
   runbook; decide with the incoming maintainer.
3. The icf deploy repo settings are not checked (blocked above).
