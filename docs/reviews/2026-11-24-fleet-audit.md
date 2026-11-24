# Fleet audit, 2026-11-24 (5 of 5 repos)

Brief: the coordinator session "Kit · Fleet v2 coordinator 2", for the Maintainer's choice "Fleet audit first" and "Also let it fix" (2026-11-24 ~05:55 America/Chicago). Procedure: `.claude/skills/audit/SKILL.md`, "Fleet audit" and "Rules for the auditor". Counts only; no personal data. Started 2026-11-24 07:32, first measures 08:06 America/Chicago.

As of: kit main `6a4b727` (then `00a0102` with #158), 33-332.Z main `4f23703`, RADE main `97e7f4b`, 90-161.Z main `a1c6798`, ICF-Source main `dd5ce4bf`.

## Scope of this audit

This is the fleet audit of the audit skill ("Fleet audit"): every fleet repo measured (Steps 1-3 by one read-only agent each) and the clear cuts made. The per-project full audit Steps 4 and 5 did not run: no project got an `audit.last_audit` record or new time baselines, so each project's check-in still says AUDIT DUE. Whether to record these measurements as each project's audit is a question for the Maintainer (Open question 4).

## Coverage

| Repo | Access | Audited | Steps 1-3 evidence |
|---|---|---|---|
| rhope-ops/archimedes_lever (kit) | session source, push | yes | [2026-11-24-fleet-audit-kit.md](2026-11-24-fleet-audit-kit.md) |
| rhope-ops/33-332.Z | push (attached) | yes | [2026-11-24-fleet-audit-33-332.md](2026-11-24-fleet-audit-33-332.md) |
| rhope-ops/RADE | push (attached on the Maintainer's request, 2026-11-24); first read from a public read-only clone | yes | [2026-11-24-fleet-audit-rade.md](2026-11-24-fleet-audit-rade.md) |
| rhope-ops/90-161.Z | push (attached on the Maintainer's request, 2026-11-24) | yes | [2026-11-24-fleet-audit-90-161.md](2026-11-24-fleet-audit-90-161.md) |
| rhope-ops/ICF-Source | push (attached on the Maintainer's request, 2026-11-24) | yes | [2026-11-24-fleet-audit-icf.md](2026-11-24-fleet-audit-icf.md) |

Access history: the first `add_repo` calls for RADE, 90-161.Z and ICF-Source were denied by the session's auto-mode classifier; the Maintainer then asked in the session chat to attach all 3 with push access. The coordinator agreed that this session owns measurement and fix PRs in all 5 repos. Each appendix file is the output of one read-only Sonnet measuring agent (audit skill Steps 1-3); its numbers are single runs on a shared 4-core container (see "Gaps").

## Per repo

Windows: the whole history of each clone (first commit: kit 2026-11-11, RADE 11-14, 33-332.Z 11-20, 90-161.Z 11-10, ICF-Source 11-04), so "last 30 days" is the whole history. Method and commands: "Method" below.

| Measure | kit | 33-332.Z | RADE | 90-161.Z | ICF-Source |
|---|---|---|---|---|---|
| Kit version / lock | 11.0.1 (`KIT_VERSION`); no lock | 11.0.1 (`9e3f6fa`), 69 files, LOCK PASS | 11.0.1 (`9e3f6fa`), 69 files | 11.0.1 (`9e3f6fa`), 69 files, LOCK PASS | 11.0.1 (`efb9bf1`), 69 files, LOCK PASS |
| Kit lag | 134 commits on main not released (P1, P2) | 0 releases; 134 kit commits | 0 releases; 134 | 0 releases; 134 | 0 releases; 132 |
| AGENTS.md lines (cap 200) | 73 | 78 | 82 | 86 | 77 |
| Session load, tokens (cap 5,500) | ~4,657 counted; **~6,100 real** (A10) | ~5,473 | ~5,413 | ~5,381 | ~5,143 |
| Rule bullets (guide 28) / Project rules | 28 / 1 | 31 / 9 | 31 / 12 | 31 / 15 | 31 / 8 |
| Duplicate lines (budget 20) | 56 -> 51 (#158) | 51 | 52 | 253 | 437 (319 from one generated CSS file) |
| Big files (over 500 KB) | 0 | 1 (the rule-source PDF) | 0 | 1 | 72 (113 MiB; 8 generated) |
| Remote branches (main included) | 15 | 38 (37 besides main; 30 merged) | 15 | 19 | 14 |
| T2 total / kit-owned / project-owned | 19,228 -> 19,123 / same / 0 | 14,155 / 13,237 / 918 | 14,686 / 13,237 / 1,449 | 17,986 / 13,237 / 4,749 | 46,882 / 13,237 / 33,645 |
| Non-merge commits / fix commits (subject regex below) | 535 / 126 | 225 / 48 | 511 / 72 | 1,001 / 151 | 2,011 / 333 |
| Fix-of-a-fix (share of all commits) | 116 (21.7%) | 45 (20.0%) | 67 (13.1%) | 138 (13.8%) | 283 (14.1%) |
| Files per kit change: median / mean (n) | 2 / 4.0 (535) | 41 / 35.1 (7) | 12 / 17.8 (16) | 10 / 18.0 (16) | 22 / 25.9 (8) |
| Defects found per check | CI: 25 of 240 runs failed (next section) | CI not read | CI not read | CI not read | CI not read |
| Mutant kill rate | not measured (no tool) | not measured | not measured | not measured | **98.4%** (311 of 316 caught; gate only 96.5%), run 2026-11-19 on spec 3.9.0 (now 3.12.1); docs/quality/STATE.md:65 gives other counts |
| Full lane (one run, shared 4-core box; not comparable) | 64.2 s, CHECK PASS | 104.2 s, CHECK PASS | 254-396 s | 153.9 s, CHECK PASS | 168.7 s |
| Rule census: enforced / procedure / outcome evidence / no evidence (other) | 12 / 4 / 8 / 5 | 19 / 2 / 8 / 9 (2 model-does) | 21 / 12 / 0 / 3 (7 model-does) | 18 / 9 / 2 / 17 | 18 / 6 / 2 / 13 |
| Key assumptions: high / medium / low | 2 / 6 / 2 | 4 / 5 / 1 | 4 / 4 / 2 | 4 / 5 / 1 | 3 / 4 / 3 |
| Project audit due | not due; fleet: not due after this audit (`fleet.last_audit` 2026-11-24) | due (never audited) | due (529 commits) | due (789 commits) | due (887 commits) |

Read with care:
- Fix-of-a-fix: 116 of 126 kit fix commits touch a file another fix touched in the 7 days before; short windows and a few hot files (check.sh, DECISIONS, the handoff) put the measure near its ceiling (A4).
- Times: 5 agents shared 4 cores; RADE's 3 runs spread 254-396 s. No time here is a median of 3, so no slow-run finding is made from them (A11).
- Rule census classes are each agent's reading; "model does it without the rule" cannot be proven with no rule-test run on record (A14).

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

### Made (fix PRs)

| PR | What | Lines | Proof | State |
|---|---|---|---|---|
| [archimedes_lever #158](https://github.com/rhope-ops/archimedes_lever/pull/158) | 4 word-for-word copies of the CLI test helpers import the canonical copy in `sync_baseline_cli_test.py`; unused names removed (ruff F401) | **-105** (kit 19,228 -> 19,123) | 48 CLI tests OK before and after; full lane CHECK PASS on `e32dd28`; Opus review MAJOR 0; CI green | merged on the Maintainer's "merge 158" (`00a0102`) |
| [33-332.Z #77](https://github.com/rhope-ops/33-332.Z/pull/77) | `site_page.py` imports `contrast()` from the kit's `fulcrum_palette.py` (kit-locked there) in place of a word-for-word copy | **-13** (33-332.Z 14,155 -> 14,142) | site page tests PASS on branch and main; full lane CHECK PASS on `487d3ee`; Opus review MAJOR 0 (3 MINOR: the import relies on `build_site_local.py` putting `scripts/` on the path; a kit rename would fail loudly; the fast lane does not rerun the page test when `fulcrum_palette.py` changes) | waits for "merge 77" |

Both are audit skill exception (d) (exact duplicates). Fleet T2: -118 lines.

### What is left: measured, no clear cut remains

- Same-body functions (2+ lines, AST) in two differently named files, after #158 and #77: kit 2 pairs, 90-161.Z 2 pairs (8 lines), ICF-Source 16 small groups (137 lines, mostly 3-line `read` helpers), RADE 0, 33-332.Z 0. None is a clear cut: `ok` (kit `check_lock.py:208`, `check_blocks.py:93`) is a closure over each self-test's own list; `is_kit` sits in a project-synced file and a kit-only file; the ICF groups save about 1 line each after the import line.
- Dead code (code references only): kit 0; 33-332.Z 0 (4 Python files, 285 PowerShell functions); RADE 1 PowerShell function (`Split-Sentence`, `engine/ps/07-checks.ps1:205`; its removal needs an engine release); 90-161.Z 0 with a code caller missing only for `measure_pdf.py` (a person may run it by hand); ICF-Source 11 of 183 own files have no code reference, none dead (hand-run tools named in docs, on-demand tests, frozen one-offs).
- Unused imports and variables (ruff F401, F841, F811): kit 5 (0 to 1 line each), project-owned code in 33-332.Z and RADE 0.

### Ranked list (proposals; each needs the Maintainer)

Ranked by lines that leave the fleet. "Decided" = a dated decision already chose; this audit does not re-propose it.

| # | Cut | Lines | Who uses it | Standard tool | State |
|---|---|---|---|---|---|
| 1 | Kit scripts leave each project tree (a package, plan P3) | -13,237 in each of 4 projects (-52,948 fleet); kit T2 unchanged | every project (check.sh, hooks) | pip/pipx package (plan decision 3) | planned: P3, pilot 33-332.Z |
| 2 | Content check family -> gitleaks with custom rules | up to -2,787 (kit, with tests) | all repos; the PreToolUse hook | gitleaks: 10 of 11 checks with custom rules (W-B) | decided keep (plan decision 9 A, "Accept all RECs", 2026-11-23 17:09) |
| 3 | ICF-Source mutation family | -3,432 | ICF quality gates; kill rate 98.4% | mutmut (Python code only, not question content) | decided keep (ICF audit 2026-11-17, per its appendix) |
| 4 | Token log family | -1,566 (kit only) | Stop hook; P2 (j) skill-use counts | Claude Code OpenTelemetry (W-C) | decided keep (plan decision 5) |
| 5 | ICF-Source one-off scripts with no code caller: `apply_b3_fresh_withdrawal_2026_11_11.py` 222, `merge_split_unit.py` 220, `quality_merge_defects.py` 190, `quality_split_agreement.py` 161, `quality_golden_reserve.py` 119 | -912 | none by code; frozen records cite the first (`docs/quality/defects.json`) | none | **new proposal**: archive or delete; medium risk (records cite them; content records rule) |
| 6 | Instructions check -> Vale | -863 (with tests) | kit and 2 repos with `audit-instructions:` (RADE and 33-332.Z read 0 files: A15) | Vale (W-B) | decided keep (plan decision 10 A) |
| 7 | timeline.py, fulcrum_palette.py, build_site*.py | -413, -313, -712 | timeline: real use; build_site: RADE, 33-332.Z; fulcrum_palette: now also 33-332.Z `site_page.py` (#77) | none | timeline.py: decided keep; the other two measured in P2, not decided |
| 8 | 90-161.Z `measure_pdf.py` | -58 | no code caller; a comment at `Publication.Word.ps1:258`; imports `pdfplumber`, which no requirements file lists | none | **new proposal**; medium risk (hand use) |
| 9 | RADE `Split-Sentence` | about -20 (PowerShell, not in T2) | no caller | none | **new proposal**; needs an engine release |

Weight outside T2 (proposals): 90-161.Z keeps a 708 KB sample of the retired T25 task and a 1.43 MB round file twice (`.ps1` and `.txt`); ICF-Source: 319 of its 437 duplicate lines are the generated `site/dist/styles.css` against its source partials (an `audit-duplicate-ignore:` line in `.check` is a guard change).

Conclusion: every large family has a dated keep or a plan. The free duplicates are taken (-118). What is left needs a decision: items 5, 8 and 9 (-990 lines with RADE's function), or a reversal of a keep. Item 1 is the largest lever by far, and it lowers project T2, not kit T2.

## docs/tools.md lines

Each check and the audit skill got a retire / shrink / keep line in docs/tools.md, section "Fleet audit verdicts (2026-11-24)". They are recommendations (**REC**), not decisions.

## Audit the audit

Which numbers of this audit an agent can move with no better code, and the proposed change. Proposals only: a change to rule or skill text needs the Maintainer's approval of its exact text (AGENTS.md "Rule text").

| # | Metric | How it can be gamed | Evidence | Proposal |
|---|---|---|---|---|
| A1 | T2 script lines | Delete tests: test files are 5,849 of 19,123 lines (31%, on the #158 branch); join lines; move code into `.claude/`, workflows or `.mjs` (outside `scripts/*.py`, `*.sh`) | `bloat_check_files.py` counts `scripts/*.py` and `*.sh` only | Count test files apart (T2 = code lines; tests are their own number, which a review may not see fall); count every hand-written code file of the repo, not only `scripts/` |
| A2 | T2 baseline rises | A ceiling approval ("up to 20000", DECISIONS 2026-11-24, for P2 items g, j and i, all now merged; the downward ratchet stayed) lets rises pass with no new question while it is open | DECISIONS row of 2026-11-24 "up to 20000" | Each approval names one PR and its number (the rows do this today); a blanket ceiling expires with its program |
| A3 | File size cap (450 lines) | Split a file to pass the cap: R4f found 11 of 22 splits mixed or arbitrary; each split adds a header, a docstring and imports | docs/reviews/2026-11-23-tr-r4f-split-audit.md | Already a WARN (decision of 2026-11-23); next: count splits per audit and ask "does this split follow a seam" in the review brief |
| A4 | Fix-of-a-fix rate | Word choice ("fix" or not in the subject) moves it; short windows put it near its ceiling | kit 116 of 126 fixes; RADE 67 of 72 | Measure by `git blame`: a fix commit whose removed lines came from a commit of the last 7 days; report the count with the window length |
| A5 | Duplicate lines | Reword or reflow one copy; the 80-character floor hides short copies | budget 20; kit 56, 33-332.Z 51, RADE 52 | Use same-body functions (the AST scan of this audit) beside the line count; report both |
| A6 | Rule bullet count | Merge two rules into one long bullet | P1 merged 3 bullets; guide 28 | Count rules by sentence or by enforced check, not by bullet |
| A7 | Session load tokens | Move text from AGENTS.md to a skill that every task reads anyway | 33-332.Z at 5,473 of 5,500 | Measure what a typical session reads (skill-use counts from P2 (j)), not only the start files |
| A8 | `fleet.last_audit` and AUDIT DUE | Write the date after a partial audit: the warning goes away for 14 days | this audit first covered 3 of 5 repos; the date was written only after all 5 (the Maintainer's choice "Only when all 5 done", relayed by the coordinator, 2026-11-24) | Write the date only when every fleet repo is covered, or store the covered repos with the date |
| A9 | Defects per check, mutant kill rate | Measured in CI only (this audit); what the pre-push hook catches has no record, and kills are not measured, so a check that catches all its defects locally reads as 0 | 25 CI failures; 0 for most checks | Smallest instrument: check.sh appends one JSON line per FAIL (step, commit, date) to a file the audit reads; mutation: run `mutmut` on 1 check per audit (adds a dependency: the Maintainer chooses) |
| A10 | Session load (kit) | Counts the wrong handoff: `bloat_check_rules.py:30` reads `docs/NEXT_PROMPT.md` (a 567 B template in the kit), not `docs/KIT_HANDOFF.md` (6,340 B) that kit sessions read; the kit passes a cap it breaks | counted ~4,657, real ~6,100 tokens (18,630 B counted - 567 B + 6,340 B = 24,403 B / 4), about 600 over the cap of 5,500 | Count the handoff that "Order of authority" names (KIT_HANDOFF.md in the kit); then trim the handoff (lane C: a check change). Why it exists: `START_READ` dates from `6135a05` (2026-11-13); KIT_HANDOFF.md came on 2026-11-18 (`ee1c0af`); `fleet_harvest_parse.py:41` already reads it as the kit's handoff, so the cap missed it by omission, not by a decision (none found in DECISIONS or the changelog) |
| A11 | Slow-run baselines | A baseline with no machine type and fewer steps than the lane makes WARN fire on every run, so people stop reading it | kit `check` 4.2 s for 14 of 36 steps; ICF 21 step baselines 2-8x low; 33-332.Z has none | Record the machine (cores) with each baseline and the median of 3; re-record when a lane gains a step |
| A12 | Duplicate lines | Counts generated copies and is hard to reproduce | ICF 319 of 437 are a generated CSS file; 90-161.Z reproduction gave 303, not 253 | Skip files a build makes (from `.check`), and print the file pairs with the number |
| A13 | Kit text in new projects | Not a metric: `bootstrap.sh:109` deletes only top-level `docs/reviews/20*.md`, so a review subfolder of the kit stays in each new project (found when CI failed on this report's first layout) | 2 kit subfolders today (`2026-11-18-port-notes/`, `2026-11-20-skill-tests/`) | Delete `docs/reviews/20*/` too (lane C: a guard script) |
| A14 | Rule census "outcome evidence" | With no recorded rule-test run, "the model does it without the rule" cannot be shown, so no rule can be retired on evidence | `.claude/rule-tests.md` scenarios exist; 0 run records in any repo since 2026-11-18 | Record each rule-test run (date, scenario, result) in docs/reviews; the census reads it |
| A15 | Instructions check | Passes when it reads 0 files: RADE and 33-332.Z have no `audit-instructions:` line, so "enforced" is on paper only | `check_instructions` SKIP or 0 files in 2 repos | WARN when a repo has a README or go.md but no `audit-instructions:` line |

A metric that favours real refactors: lines removed per change with tests unchanged or more, and the time of the full lane on a recorded machine (both fall only when work falls).

## Gaps (with cost and benefit)

- **Defects per check: CI of the kit only.** 25 failed CI logs; local pre-push catches leave no record; the 4 projects run CI on pull requests too, not read here. Cost of A9's instrument: about 15 script lines (raises T2). Benefit: a count of what each check catches before CI.
- **Dependabot PRs always fail** the kit's CI content step (6 of 6 runs; 2 Dependabot branches open). Fix candidate (lane C): skip the denylist need for the Dependabot actor, or give Dependabot its own secret. Proposal only.
- **Mutant kill rate:** only ICF-Source has a mutation tool; its record is on an old spec. Other repos: a new dependency would be needed.
- **No timing is a median of 3** (shared CPU); no slow-run finding is made.
- **RADE measuring agent used the network:** `bloat_check.py --time` runs RADE's full `check.sh`, whose app canary reads github.com (`scripts/check.local.sh:61-68`, the repo's own fixed host). The brief said no network; reported as a deviation. Not reconnaissance (one fixed host, the repo's own check).
- **Appendix differences:** the kit appendix gives ~6,044 tokens and 6,114 B for KIT_HANDOFF.md at `6a4b727`; the report uses 6,340 B, its size on this branch (this audit's handoff line). The 33-332.Z appendix says "31 of 37" merged branches in one place and 30 in two; 30 is used here.
- **Fix commits:** counted with the regex in "Method"; a fresh reviewer's other match gave 119 for the kit, not 126. The rate is a weak measure either way (A4).
- **CI of the 4 projects not read** for defects per check (only the kit's 25 failed runs).
- **Not measured:** skill use (no session records), cross-host rule copies, Actions minutes, link checks in 3 repos.

## Method

- T2: `cat scripts/*.py scripts/*.sh | wc -l`; kit-owned = the files in the project's `.check.lock`.
- Fix commit: non-merge subject matching `\b(fix|fixes|fixed|repair|correct)\b` (case-insensitive); fix-of-a-fix: a fix commit whose files meet another fix commit's files in the 7 days before.
- Lock: `python3 scripts/check_lock.py --verify` in each project: LOCK PASS in all 4 (69 kit files, 11.0.1).
- Per repo numbers: a scratch script (`git log origin/main --no-merges --name-only`, `git ls-remote --heads`, `.check.lock`), run on full-history clones.
- Caps: `python3 scripts/bloat_check.py --brief` and `--rules` in each repo; lock: `python3 scripts/check_lock.py --status`.
- Dead code: a scratch AST scan (a def whose name occurs once in all tracked files), and the agents' code-reference scans; same-body functions: an AST dump of each function body (docstring dropped), 2+ lines, in 2+ differently named files; unused imports: `ruff check --select F401,F841,F811`.
- Steps 1-3 per repo: one read-only Sonnet measuring agent per repo; their files are the appendices (Coverage).
- No package was installed (the install of `vulture` was refused in this session; the AST scan replaced it).

## Open questions for the Maintainer

1. New cut proposals 5, 8 and 9 (ICF one-offs -912, 90-161.Z `measure_pdf.py` -58, RADE `Split-Sentence`): approve, keep, or decide at the next project audit? REC: next project audit of each repo (each is AUDIT DUE), because records cite item 5 and item 9 needs an engine release.
2. Which audit-the-audit proposals (A1-A15) to turn into exact rule, skill or check text? REC: A10 first (the kit passes a cap it breaks by about 600 tokens; the handoff must lose about 2,400 bytes), then A11 and A15.
3. Dependabot content-step failure: which fix (skip for the Dependabot actor, or a Dependabot secret)?
4. Record these measurements as each project's audit (`audit.last_audit` in each project's `.check.state.json`, by a PR per project), or leave each project's AUDIT DUE for its own session? REC: leave it; the project audit also needs Steps 4-5 (fixes and baselines on a quiet machine).
