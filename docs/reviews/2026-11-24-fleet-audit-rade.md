# RADE fleet audit, measuring pass (2026-11-24) - Steps 1, 2, 3

Repo: /home/user/rhope-ops/rade, main 97e7f4b (715 commits; first commit 2026-11-14, last 2026-11-23). Read only: no file edited or created in the work tree, no commit, no branch, no install. Machine: 4 cores (`nproc`), Linux, load shared with the lane's own parallel steps. Last audit: 2026-11-15, commit 67f7681, docs/reviews/2026-11-15-bloat-audit.md (.check.state.json audit.last_audit); bloat_check says "AUDIT DUE (529 commits since 67f7681)".

## Deviations and limits (read first)

1. `python3 scripts/bloat_check.py --time` runs `scripts/check.sh` (the `cmd` of timing `check`), and that runs `scripts/check.local.sh`, which in the full lane runs the app canary (scripts/check_apps.py) and the README apps part (scripts/build_readme.py): both need github.com (scripts/check.local.sh:61-68). That run therefore used the network, through the sandbox proxy, to the repo's own allowed host github.com only (.claude/settings.json sandbox allowedDomains). It reached `full 97e7f4b` pass (stamp in .git/check-pass). The brief said "no network"; the command the brief named does it. No recon, no other host. My two later `check.sh` runs set `RADE_OFFLINE=1` (the repo's own switch), so they skipped both and failed at the end by design (check.local.sh:79-83: "full lane incomplete"). The offline runs are not a pass.
2. Files written outside the work tree: only the scratchpad. Inside `.git/` (not tracked): check.sh writes `.git/check-pass` and `.git/check-last` (header of scripts/check.sh). The first run left `.git/check-pass` = `full 97e7f4b...`; my failed offline runs then removed it. `git status --short` = 0 lines at the end. I set PYTHONDONTWRITEBYTECODE=1 for every Python run.
3. Timings are NOT comparable with the baseline (.check.state.json timings.check.seconds = 51.1 s). The lane starts about 30 parallel steps on 4 cores (load average 16-36 during a run, 3 when idle; user CPU 5m54s in a 4m14s wall run). Nothing else was on the machine that I know of; other agents may have shared the host. Run 1 (396 s) had 16 engine-test failures (window layout numbers) that run 2 and the `--time` run did not have: treat window-layout results as load-sensitive here (evidence: check-offline.txt "ENGINE pass=146 fail=16" vs the passing runs).
4. Not measurable here (no network, no host records): the 15 remote branches of the brief (see 2.3), Actions minutes, other-host rule copies (item 15), skill use (item 19, needs `list_events`), `stop_check.py` and `session_checkin.sh` run time (both fetch from origin; not run).
5. Brief said "15 remote branches": the clone has `origin/main` only (`git branch -r`: origin/HEAD, origin/main). I did not fetch.

## 1. Step 1: inventory and baseline

### 1.1 bloat_check outputs (raw: scratchpad/rade-work/step1.txt)

`python3 scripts/bloat_check.py --time` (no --record; wall 4m32.0s, it ran the full lane):
```
session load: 21,655 bytes, ~5,413 tokens (cap 5,500)
  AGENTS.md: 17,841 bytes | skill and agent descriptions: 2,282 bytes | docs/NEXT_PROMPT.md: 1,521 bytes | CLAUDE.md: 11 bytes
rules:       AGENTS.md 82 lines (cap 200) · session load ~5,413 tokens (cap 5,500) · 31 rule bullets · Project rules 12
handoff:     docs/NEXT_PROMPT.md 9 lines (budget 40)
duplicates:  52 lines of 80+ characters in 2+ files (budget 20)
big files:   0 over 500 KB
timings:
  check: 270.7 s (baseline 51.1 s, limit +25%, exit 0) SLOWER
  checkin: 1.1 s (baseline 1.0 s, limit +25%, exit 0) ok
over budget: duplicates, timing check
warning:     session load over warning (5,000 tokens); trim rules before the cap
AUDIT DUE (529 commits since 67f7681)
```
`--rules` (0.09 s): `RULES PASS`; WARN session load ~5,413 over warning 5,000; WARN 31 rule bullets (guide 28).
`--lint` (0.08 s): `LINT: 12 flag(s) in 43 rule lines (warn only)`. All 12 are "untested (no scenario for "Project rules" in .claude/rule-tests.md, no script named)": one per Project rules line (all 12). 0 near-duplicate, 0 vague.
`--skills` (0.08 s): `SKILLS PASS: 11 skills, 1 warnings`; WARN .claude/skills/deliver/SKILL.md: description does not start with "Use when"/"Use before" (kit-owned file).

### 1.2 check.sh TIME lines (`scripts/check.sh`)

| Run | Command | TIME line | Result |
|---|---|---|---|
| A | inside `--time` (network canary on) | `TIME full lane 270.5 s wall; slowest: project checks (check.local.sh) 270.1 s, code_standard self-test 83.6 s, check_content self-test 65.8 s` (.git/check-last, 2026-11-24 14:21) | pass, stamp `full 97e7f4b` |
| B | `RADE_OFFLINE=1 scripts/check.sh` | `TIME full lane 396.1 s wall; slowest: project checks (check.local.sh) 395.1 s, code_standard self-test 125.7 s, check_content self-test 101.1 s` | CHECK FAIL: 1 failed (engine tests, 16 window-layout fails under load), 28 passed, 2 skipped |
| C | `RADE_OFFLINE=1 scripts/check.sh` | `TIME full lane 254.1 s wall; slowest: project checks (check.local.sh) 253.4 s, code_standard self-test 75.7 s, check_content self-test 71.9 s` | CHECK FAIL: 1 failed ("full lane incomplete" by design), 28 passed, 2 skipped |

Median of 3 wall times: 270.5 s (baseline 51.1 s: +429%; the baseline machine is unknown: record cores before comparing). pwsh is present (no SKIP for pwsh). SKIP lines: `SKIP project log (no docs/LOG.md: the log lives in the place AGENTS.md Project rules names)`; `SKIP instructions (no audit-instructions: lines in .check: ...)` (so scripts/check_instructions.py never checks any file in this repo: see 2.12/2.19). `nproc` = 4.
Fast lane: not run (no change to compare; baseline steps only).

### 1.3 Start-read files in tokens (bytes / 4)

| File | Bytes | ~Tokens |
|---|---|---|
| AGENTS.md (imported by CLAUDE.md) | 17,841 | 4,460 |
| skill and agent descriptions (11 skills, 3 agents) | 2,282 | 571 |
| docs/NEXT_PROMPT.md (handoff, 9 lines, 40 budget) | 1,521 | 380 |
| CLAUDE.md | 11 | 3 |
| SessionStart hook output (scripts/first_use_check.py) | 0 | 0 (prints nothing when set; run time 2.07 s, 3 runs) |
| Total (bloat_check) | 21,655 | 5,413 (98.4% of cap 5,500; 108% of warning 5,000) |
Not measured: personal preferences, host prompts (docs/host-prompts.md 446 bytes is not start-read).
docs/DECISIONS.md is 89,658 bytes (~22,400 tokens), 175 lines, not start-read: AGENTS.md:19 and :41 say "read on demand"; NEXT_PROMPT.md cites it only as a reference (lines 5, 7). No start-read file imports it: OK (Step 2.13).

### 1.4 Tracked files (`git ls-files | wc -l`; `du -cb`)

244 files, 2,879,488 bytes (2.75 MiB). Files over 50 KB: 7 (docs/assets/RADE-social-preview.png 99,532; docs/DECISIONS.md 89,658; assets/logo/rho-fulcrum-512.png 60,100; assets/logo/rho-usaf-512.png 58,005; docs/window-design.md 53,004; tests/window_driver.ps1 52,086; engine/rade_ui.ps1 51,778). Over 500 KB: 0. assets/ + docs/assets: 330,827 bytes in 20 files; engine/fonts: 133,825 bytes in 4 files. Code lines (`git ls-files scripts engine tests` py/sh/ps1/psm1/js/cs): 24,895. No file older than 90 days (repo is 10 days old), so "no change in 90+ days" = 0 files. Files with no reference from another file (`git grep -F <basename>`): docs/WORKING_WITH_AGENTS.md (0), .github/dependabot.yml (0; read by GitHub, not by files); 1 reference only: tests/engine_marker.sh, tests/rade_hash_test.py.

## 2. Step 2: bloat findings

### 2.1 Rule census (item 14). Method and limits

31 bullets (8 Hard + 23 Defaults) + 12 Project rules = 43 lines (`--lint`: "43 rule lines"). The text of Hard rules and Defaults is kit-owned (AGENTS.md "Kit files": the kit owns it; `.check.lock` entry `AGENTS.md (kit sections)`), so a change to those classes is a proposal to the kit, not to this repo. "Enforced" = a hook, test or check names it or implements it (evidence column). "Evidence it changed an outcome" needs session logs/rule-test records: docs/reviews has no rule-test run record (`ls docs/reviews | grep -i rule-tests` = 0 files; only 7 rule-conflict notes), the project log is private and unread, so no bullet is placed in that class by me (it would need the Maintainer's log). Classes used: E enforced, P procedure/pointer, M model does it without the rule (my judgement, low confidence), N no evidence found.

| # | Bullet | Class | Evidence |
|---|---|---|---|
| H1 | Git history | E | scripts/git-hooks/pre-push, .claude/settings.json deny list (settings.json:22-50), scripts/worker_guard.py --test, check_blocks.py |
| H2 | Secrets and personal data | E | scripts/check_content.py (self-tests), PreToolUse hook settings.json:56, pre-push, check.yml content step |
| H3 | Guards and checks | E (part) | scripts/check_lock.py (kit lock), check_blocks.py --settings, check.yml reads .check from base |
| H4 | Untrusted input | N | rule-tests.md scenario 3 (a scenario, no run record in this repo) |
| H5 | The Maintainer's approval | P | no hook; scenarios 2, 22 only |
| H6 | True reports | N | scenario 8 only |
| H7 | Instructions people follow | E (part) | scripts/check_instructions.py exists and its hook runs (settings.json:70), but `.check` has no `audit-instructions:` lines, so the check SKIPs (1.2): the rule is enforced on no file here |
| H8 | Rule text | P | skill .claude/skills/rule-change/SKILL.md; docs/reviews/*rule-conflict*.md (7 notes show the procedure ran: 2026-11-16 x3, 11-17 x2, 11-18, 11-23) |
| D1 | Start of session | E | SessionStart hook first_use_check.py; scripts/session_checkin.sh |
| D2 | Decisions | P | scenario 2 |
| D3 | Assumptions | M | scenario 7; no hook |
| D4 | The Maintainer's decisions | P | docs/DECISIONS.md (175 lines); row 2026-11-23 shows the procedure |
| D5 | Maintainer changes | M | no hook |
| D6 | Delivery | P | .claude/skills/deliver/SKILL.md |
| D7 | Host limit | M | scenario 6 (only some hosts) |
| D8 | Checks | E | scripts/check.sh + pre-push + check.yml |
| D9 | Fresh review | P | reviewer.md agent, deliver skill |
| D10 | Verification | P | verify skill |
| D11 | Skills | M | no hook (skill_use.py measures it, not run here) |
| D12 | Reporting | M | scenario 8 |
| D13 | Handoff | E (part) | bloat_check handoff line budget (9 of 40) |
| D14 | One home | E (part) | bloat_check duplicates count (52 vs 20: over budget) |
| D15 | README | E (part) | bloat_check README.md opening check; build_readme.py check (check.local.sh:65-68) |
| D16 | Lean instructions | E | bloat_check caps (82 of 200 lines; 5,413 of 5,500 tokens) |
| D17 | Caps and audit | E | bloat_check; AUDIT DUE line |
| D18 | Project log | E (part) | scripts/log_check.py exists but SKIPs here (no docs/LOG.md; log is private) |
| D19 | Agents | P | delegate skill |
| D20 | Delegation | P | delegate skill |
| D21 | Unattended work | M | none |
| D22 | Access | M | settings.json sandbox allowedDomains (7 hosts) partly |
| D23 | Kit files | E | .check.lock + check_lock.py |
| P1 | Project log (pointer) | P | private doc; D18 holds the format |
| P2 | Engine source | E | scripts/engine_files.py, release.yml (SHA-256 list), check.local.sh:49 |
| P3 | App repos | N | no hook stops an edit of another repo (only this session's scope); docs/engine.md |
| P4 | No reconnaissance (cannot be changed) | E | scripts/no_recon.py --test and run (check.local.sh:39-40), tests/net_rules_test.sh |
| P5 | DoD365 boundary (cannot be changed) | E (part) | net_rules_test.sh (web requests in one place, line 54), check_content.py; not provable by a word search |
| P6 | RADE and the app | P | docs/engine.md "RADE and the app" table; check_manifest.py partly |
| P7 | No code fetch at run time | E (part) | tests/net_rules_test.sh:54 (one place makes web requests) |
| P8 | Windows PowerShell 5.1 | E | window.yml job text51 + tests/text_mode_51.py, scripts/lint.sh (PSUseCompatibleSyntax 5.1, PSScriptAnalyzerSettings.psd1:6) |
| P9 | Personal-data guard | E | check_content.py profile: dod (.check) |
| P10 | Public repo | E | check_content.py (mil-host list scripts/check_content_milhosts.py) |
| P11 | Code standard | E | scripts/code_standard.py (+ strict gate; .check code- lines) |
| P12 | Window | P | docs/window-design.md (143 lines); tests/engine_window.sh, window.yml |

Counts by class letter as in the table: E (incl. "E (part)"): H1 H2 H3 H7 D1 D8 D13 D14 D15 D16 D17 D18 D23 P2 P4 P5 P7 P8 P9 P10 P11 = 21; P: H5 H8 D2 D4 D6 D9 D10 D19 D20 P1 P6 P12 = 12; M: D3 D5 D7 D11 D12 D21 D22 = 7; N: H4 H6 P3 = 3; evidence-changed-outcome: 0 placed (not measurable here). Total 21 + 12 + 7 + 3 = 43. Of the E rules, "(part)" = H3 H7 D13 D14 D15 D18 P5 P7 = 8 where the enforcement covers only part of the text.
Lint flags (item 14): 12 untested (all 12 Project rules have no scenario in .claude/rule-tests.md; they are enforced by named scripts in 9 cases, per the table, so "untested" is about scenario, not script: the linter reads rule-tests.md and "script named"). 0 near-duplicate, 0 vague.
Candidates (proposals, nothing removed): E rules that are long text with a hook could shrink to a pointer (D8 Checks, D16/D17 caps, D23); this is a kit-text change (kit repo), saves about 100-200 tokens per rule line (est. from 400-900 bytes per line). Risk: the kit lock breaks; Maintainer approval needed.

### 2.2 Items 1-21 table

Cost: "tokens" = bytes/4 of a start-read file; "s" = measured wall seconds on this 4-core host.

| # | Item | Finding (what, where, evidence, cost) | Candidate fix | Risk |
|---|---|---|---|---|
| 1 | Duplication | `bloat_check` count 52 lines (budget 20). Project-involved 29, kit-only 23 (computed with scripts/bloat_check.duplicates, scratchpad/rade-work/dups.py). Project: (a) engine/ps ensure-folder idiom `if (-not (Test-Path -LiteralPath $dir -PathType Container)) { [void](New-Item ...) }` 12 copies in 9 files: 02-config.ps1:51,68,83; 03-files.ps1:86,114; 05-installed.ps1:35,294; 07-checks.ps1:62; 15-restore-run.ps1:46; window/05-alignment.ps1:306 (+08-hand-step.ps1:173 variant); (b) PnP load block (`Get-Module -ListAvailable ... Import-Module ... Start-SignInSize`) 4 copies: 13-maintenance.ps1:124-128, 14-restore.ps1:269-273, 16-site-scripts.ps1:81-85,149-153; (c) tests/window_driver.ps1 vs tests/window_real_driver.ps1: 8 shared lines; (d) tests/resume_unit.ps1:19 = tests/tools_unit.ps1:19 (`Assert-Case`); (e) tests/text_mode_51.py vs tests/window_real.py: 3 lines (manifest load, build call); (f) schemas rade-checks vs rade-installed: `at` pattern; (g) scripts/engine_files.py vs tests/bundle_layout_test.py (1 line) and engine/rade_build.py vs rade_parts.py (1), rade_fields.py vs rade_tokens.py (docstring). Kit-only (23): fulcrum.css vs fulcrum_palette.py 8, check_content_test_* 5, argparse line in bloat_check/check_lock/check_settings 1, session_checkin/pre-push 2, others. | (a)(b): a shared helper only if the text is one generated script that can share it: the 4 copies in 13/14/16 are inside separate text blocks that run on the gov device as one paste, so a function in the engine may not be visible there (needs a check of docs/engine.md "Bundle layout"). (c)(d)(e): one shared test helper file. Kit-only: fix in the kit. Or `audit-duplicate-ignore:` for generated/reference files (proposal: hides files). | (a)(b) medium: engine files are locked by SHA-256 by app repos; every edit needs an engine release (docs/engine.md). Tests: low. |
| 2 | Drift | (a) AGENTS.md says "- Owner: the Maintainer" and 10 Project rules lines now say "the Maintainer" (DECISIONS.md:8, row 2026-11-23, applied), but docs/NEXT_PROMPT.md:5 still lists this as open item (1); stale. (b) 167 rows in docs/DECISIONS.md say "the Administrator" (history, kept by the 2026-11-23 row). (c) AGENTS.md:74-75 keep "the Administrator" by that row. (d) docs/reviews/2026-11-18-handoff-detail.md:65,66 link `reviews/...` from inside docs/reviews/ (broken; see 2.4). README vs AGENTS.md opening line: checked by bloat_check (no WARN printed). | (a) update NEXT_PROMPT.md (Lane A doc) | low |
| 3 | Dead code | Python: 0 project-owned functions with no other reference (`scratchpad/rade-work/dead.py`; names searched in all 244 tracked files). PowerShell: 228 function definitions in engine/ and tests/; 1 with no reference outside its definition: `Split-Sentence` engine/ps/07-checks.ps1:205 (3 lines; `git log -S` first adds it in 6f1b1c3 "Move the RADE engine here"; it was moved byte-identical in 49f3a29). The other 14 hits of the first scan were false (prefix `global:` in tests/window_driver.ps1 and window_real_driver.ps1, each called once). Branches: see 2.3. | Remove `Split-Sentence` (proposal; Chesterton: comment says "One sentence per line on screen (PFM 14 Nov 26)": a UI rule; the window may have taken another route, `git log -S` shows no later caller) | engine file, so an engine release and all apps' locks (docs/engine.md); saving 4 lines; low value, medium process cost |
| 3b | Dead configs | `.github/dependabot.yml` is read by GitHub only (0 file references). docs/WORKING_WITH_AGENTS.md has 0 references from any file (4,188 bytes, ~1,047 tokens, not start-read; check if kit-owned: it is not in .check.lock). | Check owner; link it from README or retire it | low |
| 4 | Stale docs | Link check of 70 .md files, 189 relative links (scratchpad script, inline): 4 broken: docs/reviews/2026-11-14-window-redesign-proposals.md:37 -> `.claude/skills/ui-verify/SKILL.md` (skill not in repo); docs/reviews/2026-11-15-bloat-audit.md:43 (`path`, a placeholder); docs/reviews/2026-11-18-handoff-detail.md:65,66 (`reviews/...` should be `./...`). TODO/FIXME/XXX in non-kit text: 0 found (`git grep -nE "TODO\|FIXME\|XXX"` after excluding check*/bloat*/code_standard* scripts: no lines). Handoff detail files: docs/reviews has 32 files, 167,491 bytes; the two handoff-detail files are 10,055 and 20,308 bytes; the 2026-11-16 one is superseded by the 2026-11-18 one (revision pair). NEXT_PROMPT.md:5 item (1) is stale (2.2). | Fix 2 links; archive superseded handoff-detail 2026-11-16 into an index (Step 2.16 rule: reviews older than 90 days: none yet, repo is 10 days old) | low |
| 5 | Layered wrappers | Call chain of `scripts/check.sh` (32,265 bytes, 4 layers): hook / CI -> check.sh -> [parallel: 22 kit self-tests, code standard, rule caps, skills, deny rules, kit lock, site from README, content check, personal-data scan] and -> check.local.sh -> {tests/engine_test.sh (background; 11 `pwsh` mentions; calls engine_window.sh 4, resume_test.sh 2) ; check_manifest.py; code_standard.py --test then code_standard.py; net_rules_test.sh; no_recon.py --test then no_recon.py; ui_tokens.py; rade_hash_test.py; py_compile; engine_files.py; apps.json one-liner; page_test.py; build_logo.py; check_apps_test.py; check_apps.py (network); build_readme_test.py; build_readme.py (network); bundle_layout_test.py; text_mode_51.py; lint.sh}. Depth = 4 (check.sh -> check.local.sh -> engine_test.sh -> engine_window.sh/pwsh_batch.ps1). Times (baseline `timings.check.steps`, a quieter machine): check.local.sh 52.2 s of 51.1 s lane wall (it IS the critical path), check_content self-test 39.8, code_standard self-test 18.3, check.sh self-test 16.2, pii_guard self-test 10.1, code standard 5.5, stop_check self-test 5.7. Same test twice: `code_standard.py --test` + `code_standard self-test` in check.sh (kit step) and check.local.sh:32 (`python3 scripts/code_standard.py --test`): 2 runs of the same self-test per lane (kit step 18.3 s baseline; the local one is "about 1 s" per its comment). Also `check_apps_test.py`/`build_readme_test.py` run in check.local.sh and likely once more in tests (not checked). | Remove the duplicate `code_standard.py --test` call from check.local.sh:32 (the kit step covers it): saves up to ~1 s (comment says "reads every file in about 1 s", the self-test is the part that costs) | the project's own test file is guard-adjacent (AGENTS.md "Guards and checks"): needs the Maintainer's request; low risk |
| 6 | Performance | Step times above (1.2 and item 5). Lane wall 254-396 s on 4 cores vs 51.1 s baseline; the whole lane is bound by check.local.sh (engine tests 11 `pwsh` starts in engine_test.sh, each pwsh start ~0.3-1 s; groups already parallel: `go NAME;` blocks at tests/engine_test.sh:24, "bloat audit P8"). Top 3 costs (run C): check.local.sh 253.4 s, code_standard self-test 75.7 s, check_content self-test 71.9 s. Process starts: scripts/check_content_test*.py, code_standard_test*.py each start Python many times (not counted). Parallelism: check.sh already runs its steps in parallel (header line 33); CHECK_SERIAL=1 would time each alone (not run: +4 min per run). Same step run per change: pre-push (fast lane on branch, full on main), check.yml (full lane on every PR), window.yml (engine/tests paths), security.yml (every PR), release.yml (full lane again): a PR touching engine/ runs the engine tests locally (pre-push) and in check.yml and window.yml (3 times). | Profile with `time`/`cProfile` on the two self-tests (`python3 -m cProfile -s cumtime scripts/code_standard_test.py`) before any change; both are kit scripts (fix in the kit). | The engine tests are the proof of the 5.1 window; do not cut them |
| 7 | Dependencies | Python: standard library only (imports of all `*.py`: top names pathlib, re, sys, json, subprocess, ... no third party). No requirements/package/pyproject file. Non-Python: bandit==1.9.4 (security.yml:22), gitleaks (security.yml:36), playwright (scripts/render_logo.js:12, manual, no pin file), PSScriptAnalyzer (1.23.0 is another repo's pin; here lint.sh:8 uses the runner's), PnP.PowerShell 1.12.0 (engine, tests/fake-pnp). Vendored: tests/fake-pnp (63 lines, a stand-in, not a copy), 4 OFL fonts 133,825 bytes (engine/fonts; needed, engine reads them). | none | none |
| 8 | Repository weight | 7 files over 50 KB; none over 500 KB; assets + docs/assets 330,827 bytes (PNGs); fonts 133,825; DECISIONS.md 89,658 (not start-read). Generated files: assets/logo/logo-rho.svg checked stale by check.local.sh:58; PNGs from a browser render (not byte-stable). `.gitignore` has `__pycache__/`; 0 tracked caches. | none | none |
| 9 | CI and automation | 4 workflows (.github/workflows/): check.yml (checks; pull_request + workflow_dispatch, skipped on private repo; 1 job; timeout 10 min; runs full check.sh then the content check), security.yml (bandit -r engine/ scripts/ -ll; gitleaks; pull_request + workflow_dispatch; 2 jobs, 10 min each), window.yml (windows-latest; pull_request on paths engine/**, tests/**, schemas/**, assets/logo/**, apps.json, itself, + workflow_dispatch; jobs window 15 min, text51 10 min), release.yml (workflow_dispatch only; runs check.sh again, signs the file list). dependabot weekly, github-actions only, limit 3. None runs on push. Public repo: runner minutes free (window.yml:7), so no budget to count. Duplicate of a local check: check.yml re-runs check.sh (the merge gate in AGENTS.md "Checks" says the Action must be green in a public repo: by design); window.yml `text51` job repeats tests/text_mode_51.py that check.local.sh also runs on Linux pwsh 7 (check.local.sh:73) on the 5.1 target: not a duplicate, a different shell. Minutes used: not measurable (no network). | none | none |
| 10 | Process bloat | Hand steps: engine release note (NEXT_PROMPT.md:5 open item 2, a hand step for the Maintainer), work-computer proof rounds (open item 3). Release: one `workflow_dispatch` per engine release; releases so far engine-v36 (NEXT_PROMPT.md:5) = about 36 releases in 10 days. | Not enough data to propose | n/a |
| 11 | Tech-debt | See section 6. | | |
| 12 | Instruction bloat | AGENTS.md 17,841 bytes, 82 lines, 5,413-token session load at 98.4% of cap. 31 bullets vs guide 28 (WARN). Hard rules and Defaults are kit-owned text (cannot be changed here without breaking `.check.lock` entry "AGENTS.md (kit sections)"); the project's own text is 12 Project rules, about 4,340 bytes (computed from AGENTS.md:71-82; ~1,085 tokens), 2 of them 'cannot be changed'. Repeats: the "Administrator" role word 2x (AGENTS.md:74-75) kept by decision; the 12 Project rules duplicate sentences of docs/engine.md "RADE and the app" (AGENTS.md:79 says "Table: docs/engine.md" - a pointer, fine). Longest Project rules lines: Code standard, Window pointers already short. Rules that restate enforcement: D8 Checks, D16, D17, D23 (see 2.1). | Kit-level: shorten E-class rules to pointers; project-level: nothing to trim without losing a rule | any rule change needs the Maintainer (AGENTS.md "Rule text") |
| 13 | Context cost | Start read 5,413 tokens (above). DECISIONS.md not imported at start (checked: AGENTS.md:19, :41; NEXT_PROMPT.md:5,7 reference only). Decisions that bind every session are lines in Project rules (12): OK. 11 skills: audit 16,645 bytes (~4,161 tokens), delivery 9,067, verify 4,530 (+ measure.mjs 8,934) are read on demand, not at start. | none | none |
| 14 | Rule census | See 2.1. | | |
| 15 | Cross-host duplication | Not measurable (needs claude.ai Project, preferences, memory). In-repo: docs/host-prompts.md 446 bytes (what it holds: not read; it has 2 reference files). | Maintainer checks claude.ai Project text | n/a |
| 16 | Handoff and memory rot | NEXT_PROMPT.md 9 lines of 40 but 1,521 bytes in 5 long lines (line 5 alone is about 900 bytes); item (1) done but still listed (see 2.2). docs/reviews: 32 files, 167,491 bytes, newest 2026-11-21; 0 older than 90 days. Pairs: handoff-detail 2026-11-16 (10,055) and 2026-11-18 (20,308) with open items numbered 0-17 and 17-25 (NEXT_PROMPT.md:7 "Open: detail 17-25"). | Update item (1); fold 2026-11-16 detail into the 2026-11-18 one | low |
| 17 | Agent-made helpers | `git ls-files \| grep -Ei '_old\|_v[0-9]\|_new\|\.bak\|\.orig\|copy\|scratch\|debug\|tmp'` = 0 files. Project scripts, 13 files, 1,449 lines (scratchpad script): build_fonts.py 55, build_logo.py 64, build_readme.py 236, check.local.sh 83, check_apps.py 285, check_content_local.py 80, check_content_milhosts.py 153, check_content_test_milhosts.py 109, check_manifest.py 100, engine_files.py 63, lint.sh 28, no_recon.py 82, ui_tokens.py 111. Callers: each has 2-28 referencing files (git grep -F basename); scripts/build_fonts.py and scripts/render_logo.js are manual generators (callers: docs). | none | none |
| 18 | Defensive layering | engine/ has 321 try/catch lines; 170 are `catch { $null = $_ }` (top: window/05-alignment.ps1 30, rade_ui.ps1 28, window/04-record-parts.ps1 12, window/10-keys.ps1 11, 07-checks.ps1 11). docs/code-standard-rade.md:28 (X7) allows it only with a reason comment on the same line, and scripts/code_standard.py checks that. Not a finding as such. Python: no `except Exception: pass` scan run (not measured). | none (standard-conform) | n/a |
| 19 | Hooks and tools | Hooks (.claude/settings.json): PreToolUse check.sh --hook 0.08 s x3 (median 0.082 s), check_instructions.py --hook 0.069 s (median 0.069), Stop stop_check.py (not run: fetches from origin; limit 30 s), SessionStart first_use_check.py 2.07 s (3 runs: 2.073, 2.067, 2.084; output 0 bytes). Per session start: 2.07 s with no output (it checks the denylist and the template; candidates: cache or skip when set). Allow list 14, deny 31 entries, ask 2. `skill_use.py` not run (needs session records; no `list_events` here). check_instructions never checks a file (no `audit-instructions:` line in .check; check.sh prints SKIP). | Ask the Maintainer whether `audit-instructions:` should name README.md and docs/FIRST_USE.md (this repo has pages and hand steps: docs/make-an-app.md 8,158 bytes, docs/FIRST_USE.md 12,022) | enabling the check can fail pushes (guard change: Maintainer's request) |
| 20 | Delegation overhead | `.claude/agents/` worker 1,499, reviewer 1,545, scout 689 bytes: short. Briefs: not measurable here. | none | none |
| 21 | Output verbosity | docs/DECISIONS.md rows: 175 lines, 89,658 bytes, so about 512 bytes/line average and some single rows over 700 bytes (e.g. DECISIONS.md:8, :49); README.md 6,632 bytes. NEXT_PROMPT.md line 5 about 900 bytes. | Shorten at the source only for new rows; old rows are history | low |

### 2.3 Branches (item 3)

`git branch -r` = `origin/HEAD -> origin/main`, `origin/main` (1 remote branch). `git rev-list --count origin/main..origin/main` = 0. The brief's 15 remote branches are not in this clone and I could not fetch (no network). Candidate: the orchestrator runs `gh api repos/rhope-ops/RADE/branches --paginate` and `git merge-base --is-ancestor` per branch.

### 2.4 Call chain, one line each (item 5)

- Push (pre-push hook): fast lane -> check.sh --fast -> kit self-tests of changed kit scripts + check.local.sh --fast (SKIP app canary, README apps part; engine tests only if a file they read changed against the merge base).
- Pull request (public repo): check.yml -> check.sh (full) -> check.local.sh (full, with network canary) ; + content check; security.yml; window.yml (path filter).
- Release: release.yml -> check.sh (full) -> engine_files.py list -> attestation.
- Claude hooks: PreToolUse check.sh --hook (0.08 s), check_instructions.py --hook (0.07 s); Stop stop_check.py; SessionStart first_use_check.py (2.07 s).

## 3. Same-body functions (scratchpad/rade-work/samebody.py, psbody.py)

- Python, 68 `.py` files (all tracked), 559 functions with a body of 2+ lines (docstring dropped, `ast.dump` of the statements, names and arguments ignored): groups with the same body in 2+ places: 1 group, and it is kit-only (all copies in files listed in .check.lock). Groups involving a project-owned file (not in .check.lock; scripts/*, tests/*.py, engine/*.py): 0. Command: `python3 -I scratchpad/rade-work/samebody.py` printed `functions>=2 lines 559 files 68` and `Counter({'kit-only': 1})`.
- PowerShell in engine/ (29 `.ps1` files, 184 `function` definitions, brace-matched, comments dropped, whitespace collapsed, bodies of 2+ lines): same-body groups: 0; same function name defined twice: 0. (`psbody.py`.) The repeated code in engine/ is inline lines, not whole functions: see item 1 (a), (b).
- tests/: `Assert-Case` is defined once in each of tests/resume_unit.ps1:19 and tests/tools_unit.ps1:19 with the same text (1 line, so below the 2-line threshold of this section; counted as duplicate line in item 1(d)).

## 4. Step 3: assumption audit

Counts: high 4, medium 4, low 2 (10 key assumptions). "Untraced" (no source at all): 0. Stale: 2 (rows 11, 12).

| # | Assumption | Used at (path:line) | Source | Confidence |
|---|---|---|---|---|
| A1 | Windows PowerShell 5.1 is the floor on every NIPR computer | AGENTS.md:78 (Project rules "Windows PowerShell 5.1"); engine/ps/07-checks.ps1:100-101; tests/text_mode_51.py | DECISIONS 2026-11-14; test: window.yml job text51 (windows-latest PS 5.1); work-computer round "is the 5.1 proof" (AGENTS.md:78) | high for the code (a test runs it); medium that every NIPR machine has 5.1 only |
| A2 | The only module version tested on the gov device is PnP.PowerShell 1.12.0; 2.x might behave differently | engine/ps/07-checks.ps1:295; 13-maintenance.ps1:126; 14-restore.ps1:271; 16-site-scripts.ps1:83,151; tests/fake-pnp | DECISIONS 2026-11-14 (platform); fake module test only: the fake is not the real module | medium |
| A3 | The CAC sign-in window of `Connect-PnPOnline -UseWebLogin` (1.12.0) opens very large and the engine can resize it to 480 x 360 | engine/ps/16-site-scripts.ps1:16-24; 13-maintenance.ps1:128; 14-restore.ps1:273 | comment "E3"; NEXT_PROMPT.md:5 item 3 ("work-computer proof" still open) | low (no on-device proof recorded) |
| A4 | Pasted text into PowerShell ISE is allowed, needs no ISSM approval, and the script is endorsed or will be | DECISIONS.md:49 (2026-11-18: "Not verified by an agent against an official source (as the row of 2026-11-14)") | Maintainer account of a talk with the ISSM; no document | low |
| A5 | TLS 1.2 is enough for GitHub and TLS 1.3 may be added only when available on older Windows | engine/ps/03-files.ps1:94-102; engine/ps/07-checks.ps1:100-101 | DECISIONS (fleet v2 DEC 1); NEXT_PROMPT.md:5 item 3 "TLS 1.3 on older Windows" still open | medium |
| A6 | Scripts run with no `-ExecutionPolicy` flag; `PSExecutionPolicyPreference` may be set to Bypass by an old shortcut and must be removed by the engine | tests/engine_test.sh:12-16; engine/ps/04-steps.ps1:27 and 07-checks.ps1:171,265 | DECISIONS (fleet v2 DEC 3); test: "Test script ran" (engine_test.sh) | high (tested on Linux pwsh 7), medium on Windows (open item 3) |
| A7 | The runner `windows-latest` still has Windows PowerShell 5.1 and PSScriptAnalyzer | .github/workflows/window.yml:22,40; scripts/lint.sh:8 | runner image; test: the job | medium (image can change) |
| A8 | `ubuntu-latest` has pwsh 7 and python3 and `github.com` is reachable (app canary) | scripts/check.local.sh:61-68; tests/engine_test.sh:25; check.yml:16 | test: check.yml run; RADE_OFFLINE flag handles the no-network case | high |
| A9 | The engine files an app locks are exactly those listed by docs/engine.md and `engine_files.py`; apps check each file's SHA-256 | AGENTS.md:73 ("Engine source"); scripts/engine_files.py; release.yml | DECISIONS 2026-11-14, 2026-11-17; test check.local.sh:49 (engine_files.py trace names rade_build.py) | high |
| A10 | Public repo means GitHub Actions minutes on standard runners are free | .github/workflows/window.yml:7; check.yml:4 | GitHub terms (no source in the repo) | medium |

Stale (true when written, not true now):
- S1: docs/NEXT_PROMPT.md:5 open item (1) "Project rules and DECISIONS say 'the Administrator' while AGENTS.md says Owner: the Maintainer" is closed by DECISIONS.md:8 (2026-11-23) and AGENTS.md:71-82 (10 lines changed; 74-75 kept by decision).
- S2: baseline `timings.check.seconds` 51.1 s (.check.state.json) no longer holds on this host (270.5 s median of 3) and the machine type was not recorded with it (audit Step 1.2: "record the machine type"); also the previous audit baseline commit 67f7681 is 529 commits old.
Questions for the Maintainer (2-3 options, REC first) are for the orchestrator: A3, A4, A5 (low or medium and matter to the design).

Test candidates (Step 3.4): A8 (`RADE_OFFLINE` path has a test, check.local.sh:79-83); A2/A3 cannot be tested off-device.

## 5. Report table inputs (minimum table of the audit skill)

| Measure | Before (this pass) | Budget |
|---|---|---|
| Start read (~tokens) | 5,413 (AGENTS.md 4,460; descriptions 571; handoff 380; CLAUDE.md 3) | cap 5,500; warn 5,000 |
| Rule bullets: AGENTS.md / Project rules | 31 (Hard 8 + Defaults 23) / 12 | guide 28 / 15 |
| Check lanes: fast / full (s), slowest step | fast: not run; full 270.5 s median of 3 (270.5 / 396.1 / 254.1, 4 cores, contended); slowest check.local.sh 253-395 s; baseline 51.1 s | +25% of baseline |
| Duplicate lines (80+ chars, 2+ files) | 52 (29 project-involved, 23 kit-only) | 20 |
| Tracked files / size | 244 / 2,879,488 bytes | n/a |
| Big files | 0 over 500 KB; 7 over 50 KB | 500 KB |
| Timing: each named operation (s) | check 270.7 (bloat --time); checkin 1.1 (baseline 1.0); hooks: check.sh --hook 0.08, check_instructions --hook 0.07, first_use_check 2.07 | baselines in .check.state.json |
| Removals proposed / approved / made | proposals listed above: 1 code removal (Split-Sentence), 1 duplicate call (code_standard --test), 2 links, 1 stale handoff item; approved 0, made 0 | n/a |
| Rules removed or merged | 0 | n/a |
| Key assumptions: high / medium / low / untraced | 4 / 4 / 2 / 0 (note: A1, A6 scored high for code and medium for the device; counted high) | n/a |

## 6. Tech-debt register (accepted, not fixed; owner = role; review date proposed from audit cadence of 14 days after 2026-11-24 = 2026-12-08, unless stated)

| Item | Evidence | Owner (role) | Review date |
|---|---|---|---|
| Code-standard debt baseline: 236 accepted entries (comment 61, docs 101, line 31, safety 41, length 2; duplicate, file_size, generated, header, parse 0) in .check.state.json code_standard.debt, shrink-only | .check.state.json (python count) | Maintainer | 2026-12-08 |
| Engine duplicates: ensure-folder idiom 12 copies, PnP load block 4 copies (item 1a, 1b); fixing needs an engine release | engine/ps/*.ps1 lines in 2.2 item 1 | Maintainer (engine) | 2026-12-08 |
| Dead `Split-Sentence` (engine/ps/07-checks.ps1:205), 3 lines | 2.2 item 3 | Maintainer (engine) | next engine release |
| Time baseline 51.1 s is stale; machine type not recorded | .check.state.json timings.check; this pass 270.5 s median on 4 cores | Maintainer / Release Manager | before the next release |
| Duplicates budget exceeded: 52 vs 20 (kit-only 23: report to the kit) | `bloat_check --time` | Maintainer | 2026-12-08 |
| Session load 5,413 tokens, 98.4% of cap (kit text 4,460 of it in AGENTS.md) | `bloat_check --time` | Maintainer (kit change) | before the next kit sync |
| `audit-instructions:` not set: check_instructions checks no file | check.sh SKIP line; .check | Maintainer | 2026-12-08 |
| 12 Project rules without a rule-test scenario | `--lint` 12 flags | Maintainer | 2026-12-08 |
| 4 broken links in docs/reviews; stale open item (1) in NEXT_PROMPT.md | 2.2 items 2 and 4 | Content Approver | 2026-12-01 |
| Work-computer proof open: TLS 1.3 on old Windows, scripts with no -ExecutionPolicy, shortcut repair (assumptions A3, A5, A6) | NEXT_PROMPT.md:5 item 3 | Maintainer (the device rounds) | next round |
| The 15 remote branches: merged status unknown (clone has 1) | 2.3 | Maintainer | 2026-11-30 |
