# Tool retirement program: research phase plan (approved)

Approved by the Maintainer, 2026-11-23 ~15:00 America/Chicago, in session "Kit · Tool retirement · 2026-11-23 · #125"
(question dialog: "Approve as proposed", installs "Allow all"). Scope: the research phase only. Input: the approved coverage
list [2026-11-23-tool-retirement-coverage.md](2026-11-23-tool-retirement-coverage.md) and the prompt
[2026-11-23-tool-retirement-prompt.md](2026-11-23-tool-retirement-prompt.md). After a restart, continue from the first open
step; no new approval is needed.

Result: one plan (phases, lanes, models, agents, hours, rollback, GAPS, exact rule texts) for the Maintainer's approval.
Nothing is built. Project repos are read only; the kit gets docs/tools.md and the plan, by lane A pull requests.

| Step | Work | Who (model) | Hours | State |
|---|---|---|---|---|
| R1 | Kit inventory into docs/tools.md (prompt step 1: job, lines, callers, self-test and mutant counts, 30-day changes, sync PRs) | Main session (Opus) | ~1 | open |
| R2 | Project tool inventory of the 10 other repos (prompt step 3; coverage rows S3a-S3d, B2-5) | 2 workers (Sonnet), 5 repos each | ~2 | open |
| R3 | ICF pre-transfer scans (coverage row B2-7): author counts only, `scripts/check_content.py --all`, rulesets and secret scanning of icf and ICF-Source | Main session | ~0.5 | open |
| R4 | Side-by-side trials on the kit, RADE, 90-161.Z, 33-332.Z, ICF-Source (prompt steps 2 and 6; coverage rows S2a-S2e, P2-2..P2-8b), each with retire / shrink / keep and evidence | 4 workers (Sonnet), in parallel, disjoint tool groups | ~5 each | open |
| R4e | Ion PII detector benchmark (coverage row ION-1; added by the Maintainer 2026-11-23 ~16:15) | 1 worker (Sonnet) | ~3-4 | open |
| R4f | Sample audit of check-driven splits (coverage row AUD-4; added 2026-11-23 ~16:45) | 1 reviewer (a model other than the split authors') | ~2 | open |
| R5 | Plan with exact rule texts T1, T2, T5, T6, T7, R1, R3 and the 31 -> 28 bullet cut (prompt steps 4, 5), then 1 fresh review | Main session; reviewer (Opus) | ~2.5 | open |

Totals: 9 agents, ~31 agent-hours (R4e and R4f added). The usage limit can stop background workers; the main session
reports what stopped and resumes it.

Installs (allowed, this container only; each package and version goes into the plan): gitleaks, trufflehog,
detect-secrets, pylint, radon, shellcheck, Vale, copier, cruft, pip-tools, cyclonedx, PSScriptAnalyzer. CodeQL runs as a
GitHub Action on a trial branch of the kit (public repo).

Trial worker groups (disjoint):
- W-A: code_standard.py vs ruff + pylint + radon; bash checks vs shellcheck; PowerShell checks vs PSScriptAnalyzer.
- W-B: check_content* vs gitleaks rules, detect-secrets, trufflehog; check_instructions vs Vale.
- W-C: sync_baseline / sync_merge / drift / check_settings vs copier and cruft; token_log vs OpenTelemetry metrics;
  distribution candidates (pre-commit hook repo, reusable workflow, pip/pipx package).
- W-D: CodeQL, CycloneDX SBOM, pip-compile hashes; paste truncation sentinel; build-time Markdown (90-161.Z, RADE);
  pac solution and versioned module (90-161.Z); WinForms layout and DPI (RADE); ICF ==term== and block-split JSON (trial only).
