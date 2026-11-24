# Fleet audit, 2026-11-24 (partial: 3 of 5 repos)

Brief: the coordinator session "Kit · Fleet v2 coordinator 2", for the Maintainer's choice "Fleet audit first" and "Also let it fix" (2026-11-24 ~05:55 America/Chicago). Procedure: `.claude/skills/audit/SKILL.md`, "Fleet audit" and "Rules for the auditor". Counts only; no personal data. Started 2026-11-24 07:32, measured 08:06 America/Chicago.

As of: kit main `6a4b727`, 33-332.Z main `4f23703`, RADE main `97e7f4b`.

## Coverage and blocks

| Repo | Access | Audited |
|---|---|---|
| rhope-ops/archimedes_lever (kit) | session source, push | yes |
| rhope-ops/33-332.Z | `add_repo` push: attached | yes |
| rhope-ops/RADE | `add_repo` push: denied by the auto-mode classifier; `add_repo` read: public, anonymous read clone | yes (read only; no fix PR possible) |
| rhope-ops/90-161.Z | `add_repo` push and read: denied by the auto-mode classifier | **no** |
| rhope-ops/ICF-Source | `add_repo` push and read: denied by the auto-mode classifier | **no** |

Unblock: the Maintainer allows `add_repo` for this session (approve the prompt, or add a permission rule for `mcp__claude-code-remote__add_repo`), or runs the 2 repos in a session that has them. Because 2 of 5 repos are not read, a whole-file retirement of a kit tool is not a "clear cut" here (audit skill: "Nothing in the repo calls it" does not prove a thing is unused; P2 found `build_site.py` in use by other repos).

## Per repo

Commands (scratch scripts, not in any repo; each is listed in "Method" below). Windows: kit history on this clone starts 2026-11-11 (13 days), RADE 2026-11-14 (10 days), 33-332.Z 2026-11-20 (4 days). So "last 30 days" is the whole history of each repo.

| Measure | kit | 33-332.Z | RADE |
|---|---|---|---|
| Kit version / lock | 11.0.1 (`KIT_VERSION`; release commit `9e3f6fa`); no lock | 11.0.1 (`9e3f6fa`), 69 locked files | 11.0.1 (`9e3f6fa`), 69 locked files |
| Kit lag (kit non-merge commits after the lock commit) | 134 not released yet (P1, P2 on main after 11.0.1) | 0 releases, 134 commits (lock of 2026-11-23 = latest release 11.0.1) | 0 releases, 134 commits (same) |
| AGENTS.md lines (cap 200) | 73 | 78 | 82 |
| Session load, tokens (cap 5,500) | ~4,657 | ~5,473 (warning: 27 under the cap) | ~5,413 (warning) |
| Rule bullets (guide 28) / Project rules | 28 / 1 | 31 / 9 (WARN) | 31 / 12 (WARN) |
| Duplicate lines, 80+ chars, 2+ files (budget 20) | 56 (over) | 51 (over) | 52 (over) |
| Big files (over 500 KB) | 0 | 1 | 0 |
| Remote branches (main included) | 15 | 37 (36 at 07:40: one new branch in between) | 15 |
| T2 script lines: total / kit-owned / project-owned | 19,228 / 19,228 / 0 | 14,155 / 13,237 / 918 | 14,686 / 13,237 / 1,449 |
| Non-merge commits in window | 535 | 225 | 511 |
| Fix commits (subject has fix, fixes, fixed, repair or correct) | 126 | 48 | 72 |
| Fix-of-a-fix (a fix commit that touches a file a fix commit touched in the 7 days before) | 116 (21.7% of commits) | 45 (20.0%) | 67 (13.1%) |
| Files changed per kit change: median / mean | 2 / 4.0 (each kit commit) | 41 / 35.1 (7 commits that touch `.check.lock`) | 12 / 17.8 (16 commits that touch `.check.lock`) |
| Defects found per check (CI) | 25 failed of 240 `checks` runs, 2026-11-13 to 11-24: rule caps and pointers 17, CI content step 6 (setup error: Dependabot PRs get no denylist secret), cli_tests 1, check.sh self-test 1; every other check 0 (section "Defects per check") | not measured (the pre-push hook catches locally; no record) | not measured |
| Mutant kill rate | not measured (no mutation tool; seeded defects in W-A and W-B stand in) | not measured | not measured |
| AUDIT DUE (project audit) | not due; fleet: due (no `fleet.last_audit`) | due (never audited) | due (529 commits since `67f7681`) |

Read the fix-of-a-fix row with care: 116 of 126 kit fix commits touch a file that another fix touched in the 7 days before. With a 13-day window and a few hot files (check.sh, DECISIONS, the handoff), the measure is near its ceiling and says little about a commit that repairs a commit (Audit-the-audit, item A4).

## Defects per check

Source: the pull-request Action of the kit, all 398 runs (2026-11-13 to 2026-11-24); the tail of the job log of each of the 25 failed `checks` runs, read by an agent (step names only, no finding values; in 8 runs the step is inferred from the visible lines).

| Check step | Failed runs | What it caught |
|---|---|---|
| rule caps and pointers | 17 | A changed rule line with no rule-conflict check record (the same gate each time; 7 branches). A process gate: it caught a missing step, not a code bug |
| content step of the CI (not a check.sh step) | 6 | Nothing: every run is a Dependabot PR, where GitHub gives no repository secret, so "no denylist found". A setup error that fails each Dependabot PR (2 Dependabot branches still open) |
| cli_tests self-test | 1 | A real test failure in a change (`bootstrap_cli_test.py`, role word) |
| check.sh self-test | 1 | Unknown (the failing sub-test is outside the log tail) |
| every other step (content check, code standard, instructions, log checks, lock, drift, ...) | 0 | Nothing in CI in 11 days |

Read with care: the pre-push hook runs the fast lane on each push, so most defects are caught before CI and leave no record. A CI count of 0 does not show that a check is useless; it shows that this audit cannot see what it catches (item A9).

## T2 cuts

### Made (fix PR)

| PR | What | Where | Lines | Proof |
|---|---|---|---|---|
| [#158](https://github.com/rhope-ops/archimedes_lever/pull/158) | 4 word-for-word copies of the CLI test helpers (`KIT`, `GIT`, `run`, `py`, `new_repo`, `sync`) import the canonical copy in `sync_baseline_cli_test.py`; unused names removed (ruff F401) | `scripts/{bootstrap,check_lock,drift,sync_merge}_cli_test.py` | **-105** (19,228 -> 19,123) | 48 CLI tests OK before and after; full lane `CHECK PASS` 33 passed, 3 skipped on `e32dd28`; lane C (tests that check.sh runs); waits for the Maintainer's "merge 158" |

Audit skill exception (d) (exact duplicates). Kit-only files: neither 33-332.Z nor RADE has them.

### What is left: measured, no clear cut remains

- Same-body functions in two differently named files: at 5+ lines, across kit, 33-332.Z and RADE (after #158): **0** (all 40 groups are the synced kit copies). At 2+ lines, kit only: the 4 helper groups of #158 and 2 more pairs, neither a clear cut: `ok` (5 lines, `check_lock.py:208`, `check_blocks.py:93`) is a closure over each self-test's own list (merging it is a refactor, not exception (d)); `is_kit` (3 lines, `bloat_check_files.py:55`, `code_standard_rules.py:126`): projects get `code_standard_rules.py` but not `bloat_check_files.py`, so one cannot import the other.
- Dead functions: none found by a name scan (a `def` whose name occurs once in all tracked files of the kit; it misses a common name that occurs in docs or comments). Every hit is a unittest test or an `HTMLParser` callback, which run by name.
- Unused imports and variables (ruff F401, F841, F811): kit 5, 33-332.Z 0, RADE 0 (project-owned files). They cut 0 to 1 line each: `scripts/timeline.py:27` (`json`, -1), `scripts/bloat_check.py:100`, `scripts/check_content.py:110`, `scripts/check_settings_test.py:24`, `scripts/token_log_test_report.py:333`. Chesterton check not done for the 2 imports of a module (they can be re-exports): next audit, or one small PR when the Maintainer wants it.

### Ranked list (proposals; each needs the Maintainer)

Ranked by lines that leave the fleet. "Decided" = a dated row in docs/DECISIONS.md or the plan already chose; this audit does not re-propose it.

| # | Cut | Lines | Who uses it | Standard tool | State |
|---|---|---|---|---|---|
| 1 | Kit scripts leave each project tree (a package, plan P3) | -13,237 in 33-332.Z, -13,237 in RADE (kit-owned lines); 90-161.Z and ICF-Source not measured; kit T2 unchanged | every project (check.sh, hooks) | pip/pipx package (plan decision 3) | planned: P3, pilot 33-332.Z |
| 2 | Content check family -> gitleaks with custom rules | up to -2,787 (kit, with tests) | all repos; the PreToolUse hook | gitleaks: 10 of 11 checks with custom rules; not `unscanned`, commit metadata, `.check` semantics, the hook (W-B) | decided keep (plan decision 9 A, "Accept all RECs", 2026-11-23 17:09); repairs in P2 (b) |
| 3 | Token log family | -1,566 (kit only; in no project lock) | the cloud setup script, Stop hook; P2 (j) skill-use counts | Claude Code OpenTelemetry (needs a collector; no web searches) (W-C) | decided keep (plan decision 5) |
| 4 | Code standard: Python checks to ruff + pylint | 0 left: P2 (a) moved parse, line and size; the fallback without linters stays | all repos | ruff, pylint (W-A) | done in P2 (a) (DECISIONS row of 2026-11-23) |
| 5 | Instructions check -> Vale | -863 (with tests) | kit, 2 repos with `audit-instructions:` | Vale: 8 of 9 seeded, 54 false positives on real steps (W-B) | decided keep (plan decision 10 A, same answer) |
| 6 | timeline.py, fulcrum_palette.py, build_site*.py | -413, -313, -712 (file lines at `6a4b727`; P2 measured cuts of 475, 314 and 481 with tests and callers) | timeline: real use; build_site: RADE and 33-332.Z | none | timeline.py: decided keep ("Keep it, no retirement", 2026-11-23); fulcrum_palette.py, build_site*.py: measured in P2, no free cut, not decided |

Conclusion: every large family has a dated keep or a plan, except fulcrum_palette.py and build_site*.py (measured, not decided). Without a reversal of a decision, the only way down for kit T2 is the free duplicates, and after #158 no clear one remains. Item 1 is the largest lever by far for the fleet, and it lowers project T2, not kit T2.

## docs/tools.md lines

Each check and the audit skill got a retire / shrink / keep line in docs/tools.md, section "Fleet audit verdicts (2026-11-24)". They are recommendations (**REC**), not decisions.

## Audit the audit

Which numbers of this audit an agent can move with no better code, and the proposed change. Proposals only: a change to rule or skill text needs the Maintainer's approval of its exact text (AGENTS.md "Rule text").

| # | Metric | How it can be gamed | Evidence | Proposal |
|---|---|---|---|---|
| A1 | T2 script lines | Delete tests: test files are 5,849 of 19,123 lines (31%, on the #158 branch); join lines; move code into `.claude/`, workflows or `.mjs` (outside `scripts/*.py`, `*.sh`) | `bloat_check_files.py` counts `scripts/*.py` and `*.sh` only | Count test files apart (T2 = code lines; tests are their own number, which a review may not see fall); count every hand-written code file of the repo, not only `scripts/` |
| A2 | T2 baseline rises | A blanket approval ("up to 20000", DECISIONS 2026-11-24) turns the ratchet off for 772 lines | DECISIONS row of 2026-11-24 "up to 20000" | Each approval names one PR and its number (the rows do this today); a blanket ceiling expires with its program |
| A3 | File size cap (450 lines) | Split a file to pass the cap: R4f found 11 of 22 splits mixed or arbitrary; each split adds a header, a docstring and imports | docs/reviews/2026-11-23-tr-r4f-split-audit.md | Already a WARN (decision of 2026-11-23); next: count splits per audit and ask "does this split follow a seam" in the review brief |
| A4 | Fix-of-a-fix rate | Word choice ("fix" or not in the subject) moves it; short windows put it near its ceiling | kit 116 of 126 fixes; RADE 67 of 72 | Measure by `git blame`: a fix commit whose removed lines came from a commit of the last 7 days; report the count with the window length |
| A5 | Duplicate lines | Reword or reflow one copy; the 80-character floor hides short copies | budget 20; kit 56, 33-332.Z 51, RADE 52 | Use same-body functions (the AST scan of this audit) beside the line count; report both |
| A6 | Rule bullet count | Merge two rules into one long bullet | P1 merged 3 bullets; guide 28 | Count rules by sentence or by enforced check, not by bullet |
| A7 | Session load tokens | Move text from AGENTS.md to a skill that every task reads anyway | 33-332.Z at 5,473 of 5,500 | Measure what a typical session reads (skill-use counts from P2 (j)), not only the start files |
| A8 | `fleet.last_audit` and AUDIT DUE | Write the date after a partial audit: the warning goes away for 14 days | this audit: 3 of 5 repos | Write the date only when every fleet repo is covered, or store the covered repos with the date |
| A9 | Defects per check, mutant kill rate | Measured in CI only (this audit); what the pre-push hook catches has no record, and kills are not measured, so a check that catches all its defects locally reads as 0 | 25 CI failures; 0 for most checks | Smallest instrument: check.sh appends one JSON line per FAIL (step, commit, date) to a file the audit reads; mutation: run `mutmut` on 1 check per audit (adds a dependency: the Maintainer chooses) |

A metric that favours real refactors: lines removed per change with tests unchanged or more, and the time of the full lane (both fall only when work falls).

## Gaps (with cost and benefit)

- **Defects per check: CI only.** Measured from 25 failed CI logs (section above); local pre-push catches leave no record. Cost of A9's instrument: about 15 script lines (raises T2). Benefit: a count of what each check catches before CI.
- **Dependabot PRs always fail** the CI content step (6 of 6 runs; 2 Dependabot branches open). Fix candidate (lane C, guard file): skip the denylist need for the Dependabot actor, or give Dependabot its own secret. Proposal only.
- **Mutant kill rate: not measured.** A mutation tool is a new dependency.
- **2 of 5 repos not audited** (access block above).
- **Slow-run WARN not confirmed:** the full lane on `e32dd28` printed `WARN slower than the baseline` (check 30.9 s against 4.2 s), but a reviewer agent ran tests on the same CPU at that time. The audit skill needs 3 runs; not done.
- **Python lint SKIP** in this container: pylint is not installed, so the full lane ran with the fallback (`code_standard` parse).

## Method

- T2: `cat scripts/*.py scripts/*.sh | wc -l`; kit-owned = the files in the project's `.check.lock`.
- Per repo numbers: a scratch script (`git log origin/main --no-merges --name-only`, `git ls-remote --heads`, `.check.lock`), run on full-history clones.
- Caps: `python3 scripts/bloat_check.py --brief` and `--rules` in each repo; lock: `python3 scripts/check_lock.py --status`.
- Dead code: a scratch AST scan (a def whose name occurs once in all tracked files); same-body functions: an AST dump of each function body (docstring dropped), 5+ lines; unused imports: `ruff check --select F401,F841,F811`.
- No package was installed (the install of `vulture` was refused in this session; the AST scan replaced it).

## Open questions for the Maintainer

1. Access: allow `add_repo` for 90-161.Z and ICF-Source in this session, or audit them in their own sessions?
2. `fleet.last_audit`: write 2026-11-24 now (3 of 5 repos), or only when all 5 are covered (REC, item A8)?
3. Which audit-the-audit proposals (A1-A9) to turn into exact rule or skill text?
