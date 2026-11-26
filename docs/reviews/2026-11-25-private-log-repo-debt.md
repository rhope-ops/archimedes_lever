# Fleet debt: private project log in a git repo (kit 14.0.0)

Date: 2026-11-25 (America/Chicago). Plan: [2026-11-25-private-log-repo-plan.md](2026-11-25-private-log-repo-plan.md).

Changed rule line: AGENTS.md "Project log" (a public repo names a private repo; the paste fallback only for a refused write).

Method: a sparse read of each fleet repo's `AGENTS.md` on its default branch, 2026-11-25 ~20:50 CST.

| Repo | Today | Fails the new rule | Fix |
|---|---|---|---|
| RADE | "Project log" names a private Claude doc | yes | Plan step 4: point the line to `rhope-ops/token-logs`, branch `claude/project-logs`, `project-logs/RADE/LOG.md` (log copied in commit 2ddbab7) |
| SPAR | same | yes | same, `project-logs/SPAR/LOG.md` |
| 65-601.Z | same | yes | same, `project-logs/65-601.Z/LOG.md` |
| 36-3003.Z | same | yes | same, `project-logs/36-3003.Z/LOG.md` |
| 33-332.Z | same | yes | same, `project-logs/33-332.Z/LOG.md` |
| 90-161.Z | same | yes | same, `project-logs/90-161.Z/LOG.md` |
| ICF-Source, no-more-beyond, SEC-Source, transcription_assistant | private repos, not read | no: a private repo keeps docs/LOG.md | none |
| icf, SEC, archimedes_plugins | public, no AGENTS.md read | not known | check at their next kit sync |

Two copied logs fail `scripts/log_check.py` with findings that were already in their docs: 90-161.Z (82, an older row format) and RADE (1). They are copied as they were; a fix is a separate task.

debt-check: a3e7acd8ce66
