# P6 branch list (2026-11-24)

Made 2026-11-24 ~22:20 America/Chicago by "Kit · Fleet coordinator 3" for plan P6 (tool retirement). Deletes are irreversible: each needs the Maintainer's OK.
Method: a bare clone of each repo; `git merge-tree --write-tree <default> <branch>`. CONTAINED = the merge result equals the default branch tree, so all the branch's changes are already on the default branch (safe to delete). NOT-CONTAINED = the branch holds a change the default branch does not have.

| Repo | CONTAINED (safe) | NOT-CONTAINED |
|---|---|---|
| 33-332.Z | 74 | 6 |
| 36-3003.Z | 0 | 2 |
| 65-601.Z | 0 | 2 |
| 90-161.Z | 11 | 7 |
| ICF-Source | 10 | 4 |
| RADE | 6 | 6 |
| SEC-Source | 0 | 3 |
| SPAR | 0 | 2 |
| archimedes_lever | 11 | 7 |
| no-more-beyond | 0 | 1 |
| transcription_assistant | 0 | 1 |
| Total | 112 | 41 |

Delete list with each branch's SHA (the Maintainer approved the deletes, 2026-11-25): [2026-11-24-p6-delete.tsv](2026-11-24-p6-delete.tsv); a branch whose SHA changed is skipped.

REC: delete every CONTAINED branch (includes `claude/tr-r2a-project-tools`, named in the plan). Keep the NOT-CONTAINED branches; each is listed below with its last commit date and a note.

## NOT-CONTAINED (keep unless you decide otherwise)

| Repo | Branch | Last commit | Note |
|---|---|---|---|
| archimedes_lever | `claude/content-test-split-samples` | 2026-11-24 |  |
| archimedes_lever | `claude/dependabot-signoff-allow` | 2026-11-24 |  |
| archimedes_lever | `claude/kit-followups-pr3` | 2026-11-25 | closed PR 181 (DEC 5) |
| archimedes_lever | `claude/kit-security-private` | 2026-11-25 | open PR 187 |
| archimedes_lever | `claude/magical-faraday-o9phhz` | 2026-11-21 |  |
| archimedes_lever | `claude/token-log-private-repo` | 2026-11-25 |  |
| archimedes_lever | `claude/token-usage` | 2026-11-25 | token log branch |
| ICF-Source | `claude/social-preview` | 2026-11-21 |  |
| ICF-Source | `claude/token-usage` | 2026-11-25 | token log branch |
| ICF-Source | `claude/trusting-cray-x9xjty` | 2026-11-25 |  |
| ICF-Source | `claude/upbeat-bell-uxsavx` | 2026-11-18 |  |
| 90-161.Z | `claude/adoring-wright-mf4sbi` | 2026-11-18 |  |
| 90-161.Z | `claude/clever-edison-95eaxo` | 2026-11-18 |  |
| 90-161.Z | `claude/kind-ramanujan-p3nzf4` | 2026-11-25 | open PR 231 (R42) |
| 90-161.Z | `claude/rade-lock-engine-v18` | 2026-11-18 |  |
| 90-161.Z | `claude/social-preview` | 2026-11-21 |  |
| 90-161.Z | `claude/token-usage` | 2026-11-25 | token log branch |
| 90-161.Z | `gh-pages` | 2026-11-20 | Pages branch: keep |
| RADE | `ccr-bed23091-ty0rtg` | 2026-11-19 |  |
| RADE | `claude/adoring-gauss-ejvjtl` | 2026-11-20 |  |
| RADE | `claude/r25-window-fixes` | 2026-11-16 |  |
| RADE | `claude/social-preview` | 2026-11-21 |  |
| RADE | `claude/spike-pfm-window` | 2026-11-17 |  |
| RADE | `claude/token-usage` | 2026-11-25 | token log branch |
| 33-332.Z | `ccr-9805d725-onoreq` | 2026-11-24 |  |
| 33-332.Z | `claude/ecstatic-johnson-c1mg5q` | 2026-11-20 |  |
| 33-332.Z | `claude/ion-five-defects` | 2026-11-24 | open PR 61 (paused) |
| 33-332.Z | `claude/social-preview` | 2026-11-21 |  |
| 33-332.Z | `claude/token-usage` | 2026-11-25 | token log branch |
| 33-332.Z | `rhope-ops-patch-1` | 2026-11-21 |  |
| 36-3003.Z | `claude/token-usage` | 2026-11-25 | token log branch |
| 36-3003.Z | `claude/upbeat-bell-uxsavx` | 2026-11-18 |  |
| no-more-beyond | `claude/token-usage` | 2026-11-25 | token log branch |
| 65-601.Z | `claude/token-usage` | 2026-11-25 | token log branch |
| 65-601.Z | `claude/upbeat-bell-uxsavx` | 2026-11-18 |  |
| transcription_assistant | `claude/token-usage` | 2026-11-25 | token log branch |
| SPAR | `claude/token-usage` | 2026-11-25 | token log branch |
| SPAR | `claude/upbeat-bell-uxsavx` | 2026-11-18 |  |
| SEC-Source | `claude/gracious-curie-c9pbgj` | 2026-11-20 |  |
| SEC-Source | `claude/social-preview` | 2026-11-21 |  |
| SEC-Source | `claude/token-usage` | 2026-11-25 | token log branch |

## CONTAINED (safe to delete)

- 33-332.Z (74): `claude/check-skip-social-preview`, `claude/dazzling-planck-rwssz3`, `claude/device-probe-2`, `claude/device-probe-4`, `claude/device-probe-5`, `claude/device-probe-6`, `claude/esig-minors`, `claude/esig-month-dates`, `claude/esig-more-dates`, `claude/exciting-hawking-18a1ck`, `claude/exciting-shannon-mlq8mc`, `claude/festive-wozniak-yo5ss3`, `claude/fleet-audit-site-page-dedup`, `claude/fleet-v2-guard-files`, `claude/fleet-v2-kit-11`, `claude/fleet-v2-local-items`, `claude/fleet-v2-site-page`, `claude/handoff-1824`, `claude/handoff-esig`, `claude/handoff-roster`, `claude/handoff-sign-in`, `claude/ion-detector-resume-ygrmcl`, `claude/ion-esig-gaps`, `claude/ion-handoff`, `claude/ion-hang-limits`, `claude/ion-onedrive`, `claude/ion-onedrive-tests`, `claude/kit-10-0-0`, `claude/kit-11-1-0`, `claude/kit-9-0-0`, `claude/kit-sync`, `claude/kit-sync-p3`, `claude/nice-wozniak-7ak6yz`, `claude/one-sign-in`, `claude/one-sign-in-per-run`, `claude/onedrive-hybrid`, `claude/onedrive-hybrid-design`, `claude/onedrive-probe-result`, `claude/p3-check-lines`, `claude/p3-handoff-trim`, `claude/p3-package-mode`, `claude/p4c-sentinel`, `claude/pam-answers`, `claude/passport-label`, `claude/paste-format-rule`, `claude/pii-spot-check`, `claude/plan-no-persistence`, `claude/plan-workbook-esig`, `claude/probe-3-run-2`, `claude/probe-3b`, `claude/probe-4-result`, `claude/probe5-doc-fixes`, `claude/probe5-results`, `claude/readme-social-preview`, `claude/recall-device-1`, `claude/recall-run2-cause`, `claude/recall-run3`, `claude/recall-test`, `claude/review-fixes`, `claude/roster-labels`, `claude/script-scan-feedback-hy6zf4`, `claude/several-sites`, `claude/sign-in-wording`, `claude/site-label-mask`, `claude/site-page`, `claude/split-pii-detectors`, `claude/step4-device-result`, `claude/trusting-keller-v8vtua`, `claude/version-stamp`, `claude/workbook-hits-table`, `claude/workbook-qol`, `kit-hook-sync`, `step6-docs`, `step6-parallel-downloads`
- 90-161.Z (11): `ccr-762ebfbe-85mi65`, `claude/adoring-meitner-nbm9xg`, `claude/confident-brahmagupta-8ptem3`, `claude/eloquent-clarke-cdfg4p`, `claude/exciting-bohr-9jcawc`, `claude/fleet-v2-local-items`, `claude/r28-full-solution`, `claude/r34-results`, `claude/r41-build`, `claude/r41-restore`, `claude/t22-window-r2`
- ICF-Source (10): `ccr-5b1ac00e-m7pcs6`, `claude/affectionate-pasteur-qxc46a`, `claude/gracious-thompson-em3npn`, `claude/gracious-thompson-xevhy2`, `claude/loving-pasteur-wr50xu`, `claude/pensive-volta-iweefp`, `claude/relaxed-mccarthy-r4thir`, `claude/sharp-ride-isxmtg`, `claude/sleepy-franklin-327hro`, `claude/tender-goldberg-hpot0s`
- RADE (6): `ccr-762ebfbe-85mi65`, `claude/adoring-meitner-nbm9xg`, `claude/charming-curie-e9oz3r`, `claude/eloquent-clarke-cdfg4p`, `claude/exciting-turing-aomdcr`, `claude/upbeat-bell-uxsavx`
- archimedes_lever (11): `claude/keen-cori-eiotd2`, `claude/tr-p1-checks`, `claude/tr-p1-texts`, `claude/tr-r2a-project-tools`, `claude/tr-r2b-kit10-repos`, `claude/tr-r4e-ion-benchmark`, `claude/tr-wa-linters`, `claude/tr-wb-scanners`, `claude/tr-wc-sync-distribution`, `claude/tr-wd-standard-replacements`, `dependabot/github_actions/actions/checkout-7.0.1`
