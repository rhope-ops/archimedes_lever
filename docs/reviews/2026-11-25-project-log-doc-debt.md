# Fleet debt: sessions write the private project log doc (kit 14.0.0)

Date: 2026-11-25 (America/Chicago). Plan: [2026-11-25-project-log-doc-plan.md](2026-11-25-project-log-doc-plan.md).

Method: a sparse read of each fleet repo's `AGENTS.md` on its default branch, 2026-11-25 ~20:50 CST.

| Repo | Today | Fails the new line | Fix |
|---|---|---|---|
| RADE, SPAR, 65-601.Z, 36-3003.Z, 33-332.Z, 90-161.Z | "Project log" names a private Claude doc | no | none |
| ICF-Source, no-more-beyond, SEC-Source, transcription_assistant | private repos, not read | no: a private repo keeps docs/LOG.md | none |
| icf, SEC, archimedes_plugins | public, no AGENTS.md read | not known | check at their next kit sync |

Known content debt (not a fail of this line): the 90-161.Z and RADE log docs hold rows that `scripts/log_check.py` would flag (82 and 1 findings, an older format), and the 90-161.Z doc names the owner by first name in about 200 cells. A fix is a separate task.

debt-check: 284fd2660e67
