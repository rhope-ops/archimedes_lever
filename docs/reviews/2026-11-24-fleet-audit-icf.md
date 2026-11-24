# ICF Companion (rhope-ops/icf-source): audit inputs, measured 2026-11-24 (America/Chicago), main dd5ce4bf

Machine: Linux, `nproc` = 4, Python 3.13.18, Node v22.23.5 (shared VM; run-to-run noise is large, see 1.2).
Read only. No `--record`, no network, no `session_checkin.mjs`. `git status --short` empty after every run.
Scratch outputs: /tmp/claude-0/-home-user/de601a4d-1b6c-5e2b-b3e9-0b666edd4d50/scratchpad/icf-work/ (bloat.txt, check.txt, steptimes.txt, callers.json, unreach.json, dups.py, callers.py).
Last audit before this one: 2026-11-17, commit a4622652, docs/reviews/2026-11-17-bloat-audit.md (`.check.state.json` audit.last_audit). AUDIT DUE: 887 commits since a462265.

## 1. Step 1: inventory and baseline

### 1.1 Report-table inputs (command for each)

| Measure | Value now | Command | Last audit (2026-11-17) |
|---|---|---|---|
| Start read (~tokens) | 5,143 (20,572 bytes), cap 5,500, warning at 5,000 | `python3 scripts/bloat_check.py --time` | 6,318 after fixes (7,146 before) |
| Rule bullets (AGENTS.md / Project rules) | 31 bullets (guide 28) / 8 (budget 15); AGENTS.md 77 lines (cap 200); 39 rule lines in all (8 Hard + 23 Defaults + 8 Project) | `--rules` | 24 / 10 (older layout) |
| Rule lint flags | 8 (all 8 Project rules: "untested", no scenario in .claude/rule-tests.md and no script named) | `--lint` | 0 |
| Skills | 12 skills, 3 warnings (cloud-start: description not "Use when", orphan; deliver: description not "Use when") | `--skills` | n/a |
| Handoff | docs/NEXT_PROMPT.md 13 lines (budget 40) | `--time` | 37 |
| Duplicate lines (80+ chars, 2+ files) | 437 (budget 20) | `--time` | 55 after P3 (2,338 before) |
| Tracked files / size | 3,377 files / 244,393,621 bytes (233 MiB); `.git` pack 157.78 MiB | `git ls-files \| wc -l`; `git ls-files -z \| xargs -0 stat -c '%s %n'`; `git count-objects -vH` | 2,870 / 218.5 MiB |
| Big files (over 500 KB, after `audit-ignore`) | 72 (97 without the ignore globs) | `--time`; own script with the `.check` globs | 63 |
| check_project solo | 191.2 s inside `--time` (baseline 35.8 s: "SLOWER"); my solo runs: 101.2 s and 103.3 s (`time bash scripts/check_project.sh`, `time scripts/check.local.sh`) | `--time` | 36.3 to 39.2 s |
| Full lane `scripts/check.sh` | 168.7 s wall (baseline `timings.check.seconds` 144.8 s, +16.5%); CHECK PASS 28 passed, 1 skipped, of 29 | `scripts/check.sh` | n/a |
| Fast lane `scripts/check.sh --fast` | 8.0 s wall on a clean main (project checks SKIP: no changed file; not a representative fast run); CHECK PASS 8 passed, 2 skipped, of 10 | `scripts/check.sh --fast` | n/a |
| Timing named operations | `check_project` 191.2 s (baseline 35.8 s); the only `cmd` timing in `.check.state.json` `timings` | `--time` | n/a |

Exact lines:

- `--time` last lines: `timings:  check_project: 191.2 s (baseline 35.8 s, limit +25%, exit 0) SLOWER`, `over budget: duplicates, big files, timing check_project`, `warning: session load over warning (5,000 tokens); trim rules before the cap`, `AUDIT DUE (887 commits since a462265)...`. The `--time` run took 3 m 11.8 s real.
- `--rules`: `rules: AGENTS.md 77 lines (cap 200) · session load ~5,143 tokens (cap 5,500) · 31 rule bullets · Project rules 8`; `WARN session load ~5,143 tokens is over the warning (5,000)`; `WARN 31 rule bullets (guide 28)`; `RULES PASS`.
- `--lint`: `LINT: 8 flag(s) in 39 rule lines (warn only)`.
- `--skills`: `SKILLS PASS: 12 skills, 3 warnings`.
- full lane TIME line: `TIME  full lane 168.7 s wall; slowest: project checks (check.local.sh) 166.9 s, code_standard self-test 75.2 s, content check 73.0 s`.
- Same run: `WARN slower than the baseline:` 21 steps listed, for example check_settings self-test 5.2 s (baseline 0.6 s), project checks 166.9 s (baseline 71.8 s), code_standard self-test 75.2 s (baseline 22.5 s), check.sh self-test 61.6 s (baseline 19.6 s). Many baselines are 0.2 to 1.5 s steps, so the second limit (0.5 s) does not hide them: they all ran 2 to 8 times slower than their baselines. This looks like a different or loaded machine (baseline machine type is not recorded in `.check.state.json`), not 21 separate regressions. Cause not isolated: no 3-run comparison was done.
- Noise evidence: the same `bash scripts/check_project.sh` took 191.2 s inside `--time` and 101.2 s run solo on the same machine minutes later (1.9x).

### 1.2 Wrapper chain and time of each layer (Step 2 item 5/6)

Command for the numbers: `time` on each layer; `CHECK_SERIAL=1 bash <timed copy of check_project.sh>` in scratch (copy at icf-work/cp_timed.sh, writes only to scratch).

```
scripts/check.sh (kit, locked)  168.7 s wall, 3m27s user
 |- 20 kit self-tests in parallel (code_standard 75.2, check_content 67.4, check.sh self-test 61.6 s ...)
 |- content check of all tracked files: 73.0 s (full lane); 7.7 s fast lane
 |- scripts/check.local.sh (14 code lines)  103.3 s solo, 166.9 s in the lane
 |   '- scripts/check_project.sh (98 lines): 72 checks (`bash scripts/check_project.sh` prints `CHECK PASS: 72 checks`), 4 jobs  101.2 s solo
 |       '- bash scripts/cloud_python.sh (21 ms per call, python3 start is 14 ms: ~7 ms x ~65 calls = ~0.5 s total)
 |           '- python script
 '- .github/workflows/check.yml runs scripts/check.sh again (PR; public repo only)
```

- Serial sum of the 72 steps: 168.97 s (`steptimes.txt`); parallel solo wall 101.2 s on 4 cores. So parallel speed-up is 1.67x, not 4x: the longest single step is 21.2 s, and the order is "slowest first" (check_project.sh:44-). In the lane the project checks take 166.9 s, because the content check (73 s) and 20 self-tests compete for the same 4 cores (full lane user time 207 s on 4 cores: CPU bound).
- Top 10 steps of check_project (serial seconds): test_lint_content.py 21.2; picture_layout.mjs 16.6; test_apply_revision.py 12.0; test_mutation_gates.py 10.3; test_disable.py 10.2; lint_content.py 10.0; test_new_bank_add.py 9.5; test_audit_question_set.py 8.3; test_pin_block_approvals.py 7.2; build_site_bank.py --check 5.9. The `node --test site/tests/*.test.mjs` step is 3.8 s. Top 10 = 111 s of 169 s (66%).
- Python interpreter starts: about 65 per run (one per step), plus the 20 kit self-tests. `scripts/check_project.sh` is one shell; batching candidates: the 26 `test_*.py` in the `for check in ...` loop (check_project.sh:69) each start a fresh interpreter (about 0.05 to 0.1 s each of startup, 2 to 3 s all told) but spend 90% of their time in work, so the gain is small.
- `scripts/refresh_site.sh` (29 lines): per block (5 blocks): validate_questions, build_hard_bank, build_exam_bank (15 calls) then build_site_bank, build_source_reader, build_glossary, build_scholar, disabled, a `cat | perl` stylesheet join, build_site_assets. Not run by me (it writes site/dist and reports). Not timed: unknown. Its steps are the same builders that check_project runs with `--check` (check_project.sh: build_site_bank, build_glossary, build_hard_bank, build_exam_bank, build_source_reader, build_scholar, disabled `--check`). So one change that touches content runs the builders three times: refresh_site (build), check_project (`--check`), and `content_pipeline.py --verify-all` (the same `--check` steps again, serial, content_pipeline.py:146-153) when the runbook is followed. Plus the pre-push hook runs the lane.
- Layer cost: `check.local.sh` adds 2 ms of logic; `cloud_python.sh` about 0.5 s total; none of the wrappers hide a retry. No retry-around-retry found (`grep -n retry scripts/check*.sh` empty).

### 1.3 Session load, bytes and tokens (bytes / 4)

Command: `wc -c`; and the `--time` header.

| Start-read item | Bytes | ~Tokens |
|---|---|---|
| AGENTS.md (imported by CLAUDE.md) | 17,272 | 4,318 |
| skill and agent descriptions (12 skills, 3 agents) | 2,368 | 592 |
| docs/NEXT_PROMPT.md (13 lines) | 921 | 230 |
| CLAUDE.md | 11 | 3 |
| Total | 20,572 | 5,143 (cap 5,500; 357 left; warning 5,000) |

Inside AGENTS.md (`awk` on `## ` headings): Defaults 8,765 B (~2,191 tok), Hard rules 4,486 B (~1,121), Project rules 2,297 B (~574), Order of authority 672, header 647, Commands 405. Kit owns the text of Hard rules and Defaults (AGENTS.md "Kit files"), so only Project rules (2,297 B) and Commands can be cut in this repo; any change is Lane C (rule text).
Not counted (not measurable here): hook output (SessionStart hooks `first_use_check.py` 0.05 s, `.claude/hooks/session-start.sh`, timeout 300 s, not run), personal preferences, host prompts. docs/DECISIONS.md (216 lines) is not imported by a start-read file (AGENTS.md "Order of authority": on demand). NEXT_PROMPT.md says "Before content work, read the standing decisions in the handoff detail" (docs/reviews/2026-11-18-handoff-detail.md), on demand.
Skill files on demand: audit/SKILL.md 16,645 B (4.2k tok), deliver 9,067, kit-update 6,382, instructions 6,055, handoff 5,934, rule-change 5,651, delegate 5,568, verify 4,530, personal-data 4,373, data-change 3,235, project-log 2,279, cloud-start 763 = 70,482 B.

### 1.4 Tracked files

- Count 3,377; total 244,393,621 bytes (`git ls-files -z | xargs -0 stat -c '%s %n'`).
- Weight by area (`du -sm`): data/sources 95 MB (raw PDFs 46 files 78,270 KB + Block_5.7z 8,082 KB, tracked on purpose: .gitignore:12-15 "Keep only manifest-approved originals in PRIVATE source Git"; prior audit F-13), data/publication 31 MB, docs/reviews 43 MB (1,556 tracked files, 276 entries in the folder), docs/quality 29 MB, site/dist 9 MB, docs/archive 1 MB.
- Big files, 72 over 500 KB (after the `audit-ignore` globs in `.check:75-82`), grouped by folder (command: own Python with fnmatch on `.check` globs; matches `bloat_check.py` 72):

| Folder | Files | Size KB | Class |
|---|---|---|---|
| data/sources/raw | 46 | 78,270 | source (approved course PDFs) |
| data/sources/b5/originals | 1 | 8,082 | source (7z original) |
| site/dist | 8 | 7,449 | GENERATED (rebuilt by scripts/refresh_site.sh: questions.json, glossary.json, migrations.json, scholar-B1/B2/B3/B5.json, source-links.json) |
| data/questions/exam | 5 | 7,093 | source (merged exam banks; `--check` by build_exam_bank; not written by refresh_site) |
| docs/quality | 2 | 5,071 | source (defects.json 3,956 KB frozen Phase-1 output; mapping.json 1,115 KB) |
| data/scholar | 5 | 3,750 | source (build_scholar reads them; generated copy is site/dist/scholar-*.json) |
| docs/quality/points | 2 | 3,376 | source (B1, B2 point lists) |
| site/tests/history | 1 | 923 | source (migration-bodies.json.gz test fixture) |
| data/coverage/b1 | 1 | 625 | source (tested-point-index.json) |
| data/questions/hard | 1 | 525 | source (hard block-5.json) |
| Total | 72 | 115,564 (~113 MiB) | 7,449 KB generated (6.4%); the rest source |

- No change in 90+ days: the repo's first commit was 2026-11-04 (`git log` / LOG.md row #1), so no file is 90 days old; the 90-day rule cannot fire until 2027-02. Not computed per file.

## 2. Step 2

### 2.1 Rule census (item 14), 39 rule lines

Classes: E = enforced by a hook or test (shorten to a pointer); P = a procedure (move to a skill); M = model does it without the rule; K = evidence it changed an outcome (cited); N = no evidence found (retire, or give a review date). Evidence searched: scripts, hooks, check_project.sh, docs/DECISIONS.md, docs/LOG.md, docs/reviews. `.claude/rule-tests.md` has 36 scenarios and docs/reviews holds no rule-tests run record (`ls docs/reviews | grep -i rule-test` empty), so class M cannot be shown and I assigned it to 0. The class choice per rule is my reading; the evidence column is checkable.

| Rule (bullet) | Class | Evidence |
|---|---|---|
| Hard: Git history | E | scripts/git-hooks/pre-push; .claude/settings.json deny rules; scripts/check_blocks.py (PASS "deny rules") |
| Hard: Secrets and personal data | E | scripts/check_content.py PreToolUse hook (settings.json PreToolUse, timeout 10 s; 0.06 to 0.08 s measured) |
| Hard: Guards and checks | E | scripts/check_lock.py (PASS "kit lock"), scripts/check_settings.py |
| Hard: Untrusted input | N | no hook; rule-tests scenario 3, no run record |
| Hard: The Maintainer's approval | N | no hook; scenario 2 and 22, no run record |
| Hard: True reports | N | no hook; scenario 8, no run record |
| Hard: Instructions people follow | E | scripts/check_instructions.py `--hook` on Write/Edit (settings.json); the push-time part SKIPs: no `audit-instructions:` line in `.check` |
| Hard: Rule text | K (and E in part) | 7 files docs/reviews/*rule-conflict*.md (2026-11-16 to 2026-11-20); rule gate in `bloat_check.py --rules --gate` |
| Def: Start of session | E | scripts/first_use_check.py, .claude/hooks/session-start.sh, scripts/session_checkin.sh (all with self-tests) |
| Def: Decisions | N | no hook; scenario 2 |
| Def: Assumptions | N | scenario 7, no run record; this repo's only assumption table is in the audit report |
| Def: The Maintainer's decisions | K | docs/DECISIONS.md 209 table lines, each dated with scope |
| Def: Maintainer changes | N | no evidence |
| Def: Delivery | P | .claude/skills/deliver/SKILL.md (9,067 B) |
| Def: Host limit | N | no evidence |
| Def: Checks | E | pre-push hook; `.git/check-pass` stamp |
| Def: Fresh review | P | skills deliver and delegate; .claude/agents/reviewer.md |
| Def: Verification | P | .claude/skills/verify/SKILL.md |
| Def: Skills | N | no evidence (skill use not measured; `scripts/skill_use.py` needs session records, none available here) |
| Def: Reporting | N | no evidence |
| Def: Handoff | E | `bloat_check.py` handoff budget (13 of 40 lines) + handoff skill |
| Def: One home | N | `--time` says duplicates 437 vs budget 20, and a "report only" count; no gate |
| Def: README | E in part | `bloat_check.py` (README Purpose line) |
| Def: Lean instructions | E in part | `bloat_check.py --rules` caps (31 bullets vs guide 28 = WARN) |
| Def: Caps and audit | E | `bloat_check.py` caps; AUDIT DUE line |
| Def: Project log | E | scripts/log_check.py, PASS "project log" (390 numbered rows in docs/LOG.md) |
| Def: Agents | P | .claude/skills/delegate/SKILL.md (+ PROJECT.md) |
| Def: Delegation | N | no evidence |
| Def: Unattended work | N | no evidence |
| Def: Access | E in part | settings.json `sandbox.network.allowedDomains` (hosts only; "add a dependency" part has no check) |
| Def: Kit files | E | scripts/check_lock.py, `.check.lock` (77 lines) |
| Proj: Owner and product | E | scripts/owner.py + test_owner.py (check_project.sh:69 list) |
| Proj: Question rules | E | scripts/quality_spec.py (test_quality_spec.py), bank_gate.py, blind_check.py check (check_project.sh:69, 75-76) |
| Proj: Content records | E in part | test_pin_block_approvals.py, test_check_audit_holds.py, validate_questions.py |
| Proj: Code | E | scripts/code_standard.py (PASS "code standard", 31.8 s) |
| Proj: Publication | E in part | scripts/publish_pages.py + test_publish_pages.py (2.3 s) |
| Proj: Release | P | docs/RELEASE-CHECKS.md, scripts/check_release.py (+ test_check_release.py) |
| Proj: Previews | N | cannot be checked by script; no evidence |
| Proj: Check-in | P | docs/session-checkin.md (27 lines); repeats Default "Start of session" (item 1) |

Count per class (39): E 18 (Hard 4, Defaults 9 incl. 3 "in part", Project 5 incl. 2 "in part"); P 6; M 0; K 2 (Rule text is also E in part, counted once as K); N 13 (Hard 3, Defaults 9, Project 1). Check: 18 + 6 + 0 + 2 + 13 = 39.
Of the 31 Defaults and Project bullets: E 14, P 6, K 1, N 10 (Defaults 9 + Project 1 is 10; Hard N = 3 not in this 31).
Candidate cuts inside this repo's own text: the 8 Project rules (2,297 B, ~574 tok): the 5 class-E ones name no script (lint: "no script named"), so each could become a pointer to its test, saving a part of ~574 tok; "Check-in" duplicates "Start of session" and docs/session-checkin.md; "Release" and "Publication" restate docs/RELEASE-CHECKS.md and PROJECT_INSTRUCTIONS.md "Purpose and content". All are rule text: Lane C, the Maintainer approves each exact text. Hard and Defaults are kit text (change in the kit).
Since last audit: bullets 24 to 31 (guide 28); session load 6,318 to 5,143 tokens (-1,175); lint flags 0 to 8.

### 2.2 Items 1 to 21

| # | Category | What / where (path:line) | Evidence (number) | Cost | Candidate fix | Risk |
|---|---|---|---|---|---|---|
| 1 | Duplication | `site/dist/styles.css` vs `site/styles/00..80-*.css`: 319 of 437 duplicate lines (73%): 137 (30-components), 76 (40-screens), 34 (70-scholar), 25 (50-utilities), 25 (80-pictures), 8, 6, 4, 4 (command: icf-work/dups.py using `bloat_check.duplicates`). Generated copy: scripts/refresh_site.sh:27 `cat site/styles/*.css \| perl ... > site/dist/styles.css` | 319 lines | the duplicate budget (20) can never be met; hides the 118 other lines | A: add `audit-duplicate-ignore: site/dist/styles.css` to `.check` (guard file: Maintainer request only; hides one generated file from the scan). B: leave; accept 437 | low; one file hidden |
| 1 | Duplication | Kit helper lines copied across 3 files: `.claude/hooks/session-start.sh`, `scripts/git-hooks/pre-push`, `scripts/session_checkin.sh` (`unset git_config_parameters ...`, `eq()` test helper; 16 same-body-function groups known) | 14 + 2 + 2 lines | tokens when read | none in this repo: all three are kit-locked files, change in the kit | none |
| 1 | Duplication | docs/rules/AUTHOR-EXAM/HARD/STANDARD/BANK-AND-PROCESS.md + 3 more: 7 files, 1 generated header line; generated from docs/quality/spec.json 3.12.1 | 1 line x 7 | none | none (generated; `build_rule_checks.py --check`) | none |
| 1 | Duplication | 4 audit prompts share the same 1-line opening: docs/AUDIT_PROMPT.md, BLOCK5_QUALITY_OVERLAP_AUDIT_PROMPT.md, RULES_DEEP_AUDIT_PROMPT.md, SYSTEM_AUDIT_PROMPT.md | 4 files; also each repeats `node scripts/session_checkin.mjs --fetch` (AUDIT_PROMPT.md:24, RULES_DEEP:37, SYSTEM:26) | prompts for 4 older audits (2026-11-09 to 2026-11-12) | check whether they are still used (item 4) | low |
| 1 | Duplication | scripts/build_exam_bank.py vs build_hard_bank.py: 5 lines (`if approval.get('question_ids') or approval.get('approved_su...`); new_bank_apply.py vs pin_block_approvals.py: 4; test_new_bank_hard.py vs test_new_bank_tools.py: 4; apply_b3_fresh_withdrawal vs withdraw_items.py: 2 | 15 lines | small | shared helper (code change, Lane B) | low |
| 1 | Duplication | `.github/workflows/check.yml` vs `release-checks.yml`: the `check_content.py --require-denylist ...` step (about 25 lines) is copied; 2 duplicate lines counted | 2 lines (about 25 in text) | maintenance | merge into a reusable workflow: guard file, Maintainer request | medium (guard file) |
| 1 | Duplication | docs/product/flash-cards.md, study.md, ui.md: 1 shared line ("part of the product requirements; read project_instructions.md"); docs/CONTENT_EDITING_RUNBOOK.md vs HANDOVER.md 4 lines ("open a pull request, click create pull request") | 5 lines | small | one pointer | low |
| 1 | Duplication | docs/quality/SPEC-ARCHIVE.json vs baseline/check-baseline.json 8 lines (`measured_on`); data/questions/exam/exam-batch-60.md vs hard/folds-2026-11-08.md 5 lines | 13 lines | none | none (history records) | none |
| 2 | Drift | `.claude/skills/audit/PROJECT.md:13` says check_project "about 4 minutes"; measured 101 s solo (103 s via check.local.sh); scripts/check_project.sh:6 says "36 s, 2026-11-17"; `.check.state.json:370-373` baseline 35.8 s vs 101 to 191 s measured | 36 s vs 101-191 s (2.8 to 5.3x) | the "SLOWER" flag fires on every `--time` | decide: re-record after a 3-run median on the usual machine (`--record` needs a Maintainer ask: settings.json "ask"), fix the 2 comments | low |
| 2 | Drift | `.check.state.json` check-step baselines are 2 to 8x below today's step times for 21 steps (1.1) | 21 steps | noise in every lane output (WARN line of about 2 KB) | find the cause first (machine type not recorded); then re-record | low |
| 2 | Drift | docs/session-checkin.md:5 "Two check-in scripts exist": kit `scripts/session_checkin.sh` (153 lines) and project `scripts/session_checkin.mjs` (248 lines + 2 test files, 265 lines) | 666 lines of code + tests for the project one | a second check-in command that AGENTS.md "Project rules: Check-in" requires at each start and finish | candidate: fold the project's delivered-commit check into the kit script (kit change) or keep; Maintainer decides | medium |
| 2 | Drift | Mutant record (see 2.4): spec 3.9.0 in docs/quality/work/check-mutants.json:4; SPEC.json now 3.12.1 | 3 minor versions behind | record is stale | re-run when wanted (long) | low |
| 2 | Drift | `scripts/check_project.sh:6` header says "4:40 serial -> 36 s"; today serial 169 s, parallel 101 s (72 checks; was fewer) | 4.7x | misleading comment | update comment (project file, Lane B) | none |
| 3 | Dead code | 183 own script files (157 py/sh = T2 own, 33,645 lines; plus 26 .mjs/.js, 4,199 lines): 15 py/sh files unreachable from check.sh/check.local.sh/check_project.sh/refresh_site.sh/hooks/workflows/site tests through code references (graph in icf-work/callers.py; reachable = imported or named by file name). 11 of 183 (incl. mjs) have no code reference at all (list 2.3). None is shown dead: each has a doc reference or a recorded reason (2.3) | 15 files, 2,148 lines unreachable | 6.4% of T2 | see ranked list 6 | see 6 |
| 3 | Dead code | Tests not run by check_project.sh: scripts/test_content_pipeline.py (71 lines; new 2026-11-23), test_environment.py (138), test_read_7z.py (117); on-demand per docs/cloud-environment.md:9 for the last two | 3 files, 326 lines | a gap, not a cut: content_pipeline.py's test never runs in any lane | candidate: add test_content_pipeline.py to check_project.sh (Lane B) | low |
| 3 | Dead code | `except` handlers: 24 `except Exception/BaseException/bare` in 15 script files (`grep -cE 'except (Exception\|BaseException)\|except:' scripts/*.py`) | 24 | see item 18 | review | low |
| 4 | Stale docs | docs/BLOCK3_RUN_PLAN.md (plan for Block 3, finished 2026-11-11: "Done in one session" line 39); docs/archive/handoff-2026-11-13.md; the 4 audit prompts (item 1); docs/coverage-b1/b2/b3/b5.md; docs/reviews 276 entries (1,556 files, 43 MB) | 276 review entries; repo age 20 days, so none is 90 days old | start-read cost none; repo weight 43 MB | archive after the audit-ignore (already ignored by `.check:75`); no action needed | low |
| 4 | Stale docs | `.github/workflows/release-checks.yml:3` "check_project.sh takes 36 s on 4 cores, 2026-11-17" and "1 to 2 minutes (estimate)" | 101 s vs 36 s | misleading estimate | update (guard file: Maintainer request) | low |
| 4 | Stale docs | Broken-link check not run (no link checker in repo; prior audit F-15 found 44 relative links broken in docs/reviews/HANDOFF-HISTORY.md, listed as debt) | not re-measured | | run a link walk next time | low |
| 5 | Layered wrappers | 1.2: check.sh -> check.local.sh -> check_project.sh -> cloud_python.sh -> python; content_pipeline.py (new 2026-11-23, 188 lines) wraps refresh_site.sh + the same `--check` builders as check_project; check.sh also runs everything in CI (`check.yml`) | 5 layers; 3 runs of the same builders per content change (refresh, check_project, verify-all) | about 0.5 s of wrapper time; the repeated builders cost about 25 s per run (build_site_bank 5.9 + glossary 5.8 + source_reader 5.2 + exam/hard/scholar checks) | nothing to cut in the shell layers; for `--verify-all` document that check_project already does it | low |
| 6 | Performance | Slowest op: check_project 101 s solo / 167 s in lane; top 3 costs: test_lint_content.py 21.2 s, picture_layout.mjs 16.6 s, test_apply_revision.py 12.0 s (this is one 4-core run each, single sample). In-lane the 4 cores are saturated: full lane user 207 s, wall 168.7 s | serial 169 s, parallel 101 s (1.67x) | 3 min per push to main and per merge | candidates: (a) CHECK_JOBS higher than nproc for the I/O parts: no data; (b) split test_lint_content.py (21 s, one test file) so the 4 jobs balance; (c) check why the content check takes 73 s of a 4-core lane (the fast lane runs the same scan in 7.7 s: full lane scans history? not checked); (d) the 20 kit self-tests are 60 to 75 s each for 3 of them (check_content 67 s, code_standard 75 s, check.sh 62 s) and are kit-locked: change in the kit | medium: kit files locked |
| 7 | Dependencies | scripts/requirements-content.txt, requirements-cloud.txt: 15 pinned packages (PyMuPDF 1.26.6, pypdf 6.10.0, pdfplumber 0.11.9, pypdfium2, pdfminer.six, Pillow 13.0.0, cryptography 50.0.0, cffi, pycparser, pytest...). Two PDF readers: PyMuPDF and pdfplumber/pypdf/pypdfium2/pdfminer. No package.json (Node scripts use no packages: not checked per file) | 4 PDF libraries named | install time in cloud setup | `grep -l 'import fitz\|pdfplumber\|pypdf\|pypdfium2' scripts/*.py` to see which are used: not run | low |
| 8 | Repo weight | 233 MiB tracked; 113 MiB of 72 big files; data/sources 95 MB by design (.gitignore:12-15); docs/quality/defects.json 3.9 MB frozen Phase-1; docs/quality/work/*.jsonl 5.2 MB of Phase-1 working files (defects-A..D 2.8 MB, old-rules-docs 0.9 MB) | 5.2 MB in work/ | clone time | archive or compress with approval; text frozen (Content records rule) | medium |
| 9 | CI | check.yml: on `pull_request` (skipped when the repo is private: `if` at check.yml:15) and `workflow_dispatch`; runs scripts/check.sh then the content check (timeout 10 min). release-checks.yml: `workflow_dispatch` only; 2 jobs (clean-build mandatory, claude-tooling optional); header: Actions off since 2026-11-14. Neither runs on push | 2 workflows, 0 automatic runs on a private repo | 0 Actions minutes by design | none | none |
| 10 | Process bloat | Hand steps: release walks (faststart_walk, readiness_walk, feature_walk, screen_walk*, snapshot_walk: docs/RELEASE-CHECKS.md:15-21), republishing the test artifact (AGENTS.md Release rule) | 26 .mjs files, 4,199 lines | minutes of a person per release | not measured | n/a |
| 11 | Tech-debt | see section 5 | | | | |
| 12 | Instruction bloat | 2.1: 13 N rules; Project rules repeat docs (Release, Publication, Check-in) | see 2.1 | ~574 tok Project rules | pointer shortening: Maintainer approves text | Lane C |
| 13 | Context cost | Start read 5,143 tok, 357 below the cap, 143 over the 5,000 warning; AGENTS.md is 84% of it (4,318 tok) and is mostly kit text. Skill descriptions 592 tok. DECISIONS.md not imported | 5,143 | every turn of every session | nothing cheap in this repo: Project rules (574 tok) is the only own text; the rest is a kit change | Lane C |
| 14 | Rule census | 2.1 | 39 rule lines: E 18, P 6, K 2, N 13 | | | |
| 15 | Cross-host duplication | docs/host-prompts.md (exists); personal preferences and claude.ai Project not readable from the repo | not measured (outside the repo) | | the Maintainer to compare | n/a |
| 16 | Handoff and memory rot | NEXT_PROMPT.md 13 lines (budget 40), State date 2026-11-23, links to 3 plans (Code clean-up "done", Study app gaps, Visual identity "on hold"); no memory files in the repo; docs/reviews 276 entries, repo 20 days old | 0 items older than 90 days | none | none | none |
| 17 | Agent-made helpers | Names with date or one-off purpose: scripts/apply_b3_fresh_withdrawal_2026_11_11.py (222), merge_split_unit.py (220, Block 3 unit 3 only), quality_golden_reserve.py (119), quality_merge_defects.py (190), quality_split_agreement.py (161). `git ls-files \| grep -Ei '_old\|_v2\|_new\|\.bak\|scratch'`: only docs/reviews/OFFLINE-COPY-2.1.68.md matched "tmp"-class; no _old/_v2 copy in scripts. Prior removals: merge_b5_exam.py, merge_b5_units.py removed 2026-11-17 (P4 approved) | 5 one-off scripts, 912 lines | 2.7% of T2 own | see ranked list 6 | see 6 |
| 18 | Defensive layering | 24 broad `except` in 15 files (bare/Exception); `set -uo pipefail` without `-e` in check_project.sh:13 by design (results collected after `wait`). Not reviewed one by one | 24 | hides errors if any | review the 24 sites in a later audit (Lane B) | low |
| 19 | Hooks and tools | PreToolUse `check.sh --hook` 0.064 / 0.081 / 0.068 s (3 runs); `check_instructions.py --hook` 0.061 s; `first_use_check.py` 0.054 s; `session-start.sh` (timeout 300 s) and `stop_check.py` (fetches origin) not run (they write git config or use the network). Skills: 12; skill use not measured (no session records here); the 3 skill warnings in 1.1 | 0.05 to 0.08 s per call | negligible | skill use: run `scripts/skill_use.py` on session records (host `list_events`, not reachable here) | none |
| 20 | Delegation overhead | Not measured here (briefs are in chat, not in the repo) | n/a | | | |
| 21 | Output verbosity | The lane's slow-baseline WARN line is one 2 KB line (21 steps) every run; fixing the baselines (item 2) removes it | 2 KB per run | tokens | re-record after a 3-run median | low |

### 2.3 Scripts: callers and no-caller list

Command: `python3 -I icf-work/callers.py` (code references: any tracked .py/.sh/.mjs/.js/.yml/.json outside data/, docs/reviews/, docs/archive/, site/dist/; a file name match or `import <stem>`). Raw table with each script's callers and line count: /tmp/claude-0/-home-user/de601a4d-1b6c-5e2b-b3e9-0b666edd4d50/scratchpad/icf-work/callers.json. Set: 183 files (157 py/sh = 33,645 lines, ties to your count; plus 26 .mjs/.js = 4,199 lines; T2 total `cat scripts/*.py scripts/*.sh | wc -l` = 46,882 lines in 204 files, the other 47 files / 13,237 lines are kit-locked).

Entry points, by code (a script is "reached" when named by one of these or by a script they reach): scripts/check.sh, scripts/check.local.sh, scripts/check_project.sh, scripts/refresh_site.sh, .claude/hooks/*, .claude/settings.json, .github/workflows/*, scripts/git-hooks/*, site/tests/*.mjs. There is no package.json.

No caller at all, by code (11 of 183): reason from `git log --diff-filter=A` and docs:

| File | Lines | Reason it exists | By hand per docs? |
|---|---|---|---|
| scripts/disable_scenarios.py | 135 | added 2026-11-17 to prove each kind can be disabled in a temporary worktree | yes: docs/EDITING.md, docs/HANDOVER.md, docs/LOG.md |
| scripts/faststart_walk.mjs | 197 | Playwright release walk | yes: docs/RELEASE-CHECKS.md:15 |
| scripts/feature_walk.mjs | 167 | release walk | yes: RELEASE-CHECKS.md:19 |
| scripts/readiness_walk.mjs | 136 | release walk | yes: RELEASE-CHECKS.md:17 |
| scripts/render_lesson_pages.js | 21 | page render helper | not found |
| scripts/merge_split_unit.py | 220 | added 2026-11-11 with "Block 3 Unit 3 parts B and C merged": one-off for 3 branches (the header's command names b3-gen-u3a..c, base 83ecdec) | docs/BLOCK3_RUN_PLAN.md, NEW_BLOCK_CHECKLIST.md (as history) |
| scripts/quality_golden_reserve.py | 119 | Quality standard Phase 1 step 5 (2026-11-12): reserve the golden test pool, frozen | docs/quality/STATE.md only |
| scripts/quality_merge_defects.py | 190 | Quality standard Phase 1: merge defects-*.jsonl into defects.json (frozen, 2026-11-12) | docs/quality/STATE.md only |
| scripts/test_content_pipeline.py | 71 | added 2026-11-23 with content_pipeline.py | none: a test no lane runs |
| scripts/test_environment.py | 138 | added 2026-11-05 cloud setup contract | on demand: docs/cloud-environment.md:9 |
| scripts/test_read_7z.py | 117 | added 2026-11-05 (source originals) | on demand: docs/cloud-environment.md:9 |

Reachable only through docs or JSON, not through code (15 py/sh unreachable, graph in icf-work/unreach.json): the 7 above that are py/sh without code caller (disable_scenarios, merge_split_unit, quality_golden_reserve, quality_merge_defects, test_content_pipeline, test_environment, test_read_7z) plus 8 more with a doc reference but no code caller: scripts/cloud_env_setup.sh (20; the paste for the cloud environment, named in config/cloud-environment.example.json and docs/cloud-environment.md), content_pipeline.py (188; hand-run entry named in README.md:21 and :55, docs/CONTENT_EDITING_RUNBOOK.md, docs/README.md:10, docs/SCHEMA_GUIDE.md), cross_item_candidates.py (151; docs/AUDIT_PROMPT.md, NEW_BLOCK_CHECKLIST.md, QUESTION_DECISIONS.md, SPEC.json), diff_glossary_links.py (144; AUDIT_PROMPT.md), extract_sources.py (189; NEW_BLOCK_CHECKLIST.md), merge_block_units.py (171; NEW_BLOCK_CHECKLIST.md:62), quality_split_agreement.py (161; docs/LOG.md, STATE.md), review_content.sh (12; README.md, docs/README.md). A script a person runs by hand per docs is not dead: all 8 are named in a doc a person follows (NEW_BLOCK_CHECKLIST.md, README.md, CONTENT_EDITING_RUNBOOK.md, cloud-environment.md).
Sets by caller type (157 py/sh; count by an icf-work script; a name match in an entry-point file counts as direct): 78 are named directly by an entry point (check.sh, check.local.sh, check_project.sh, refresh_site.sh, a workflow, a hook, site/tests); 64 are reached only through other scripts (imports or calls); 15 are unreachable (above). 78 + 64 + 15 = 157. The 64 include the split modules (such as audit_question_set_b1/b2_b5/b6_b9, build_glossary_*, lint_content_*, new_bank_*, build_site_*: these are the code-standard splits of 2026-11-20 "Code clean-up" plan: not dead).
Scripts whose only caller is their own test file: content_pipeline.py (test_content_pipeline.py, not run in any lane), read_7z.py (restore_source_uploads.py imports it, so not only a test).

### 2.4 Mutation tooling

Files: scripts/quality_check_mutants.py 1,876 lines (the largest script; `.check.state.json:238` code-standard file_size debt 1,877), mutant_gates.py 375, mutant_gates_spec.py 220, mutant_harness.py 382, mutant_records.py 48, test_mutation_gates.py 382, test_mutation_gates_gates.py 149 = 3,432 lines (7.3% of T2; 10.2% of T2-own).
In lane: only test_mutation_gates.py runs (check_project.sh:45, 10.3 s serial); it imports quality_check_mutants in one test (test_mutation_gates.py:360-362, "own page row"). quality_check_mutants.py header: "Report-only; never part of check_project.sh before Stop 2" (line 2). A full run writes docs/quality/work/check-mutants.json (repo file), so I did not run it.
Recorded result: docs/quality/work/check-mutants.json (233 KB; last commit 2026-11-19 "Mutant harness re-based: 41 errors -> 0, 46 misses -> 3", then "Block 5 clean controls..."), spec_version 3.9.0, `totals`: 316 mutants, caught by a gate 305, caught by a report 6, judgment-not-check 3, missed 2. Kill rate: (305 + 6) / 316 = 98.4%; gate only 305 / 316 = 96.5%; misses 2 (0.6%). Clean false fails recorded for quality_profile:provenance (list of B5 hard items). Staleness: the record is on spec 3.9.0; SPEC.json is 3.12.1.
Prior audit P5 (2026-11-17): keep quality_baseline.py and quality_check_mutants.py (reports cite them); owner approved REC B.
Cut candidates: none by evidence of "unused": cited by docs/quality/STATE.md:65, phase34-report.md:115, DECISIONS.md:75 and mapping.json; the second group (mutant_gates*, mutant_harness, mutant_records) is imported by quality_check_mutants.py and by test_mutation_gates.py.

### 2.5 Same-body functions / code-standard debt

Known inputs not redone (16 groups, 137 lines). `.check.state.json` `code_standard.debt` lists per-function debt for many files (comment: 40+ entries under docs/archive/, docs/reviews/ tools); `code_standard.debt.file_size`: 3 entries (lint_content.py 727, quality_check_mutants.py 1,877, docs/reviews/.../audit.py 800). Not counted further.

## 3. Step 3: key assumptions (10) and stale ones

| # | Assumption | Where used (path:line) | Source | Confidence |
|---|---|---|---|---|
| 1 | Source originals are tracked on purpose (about 95 MB); raw/ is never served | .gitignore:12-15; docs/sources.md | .gitignore comment; prior audit F-13 (commit 7fc2afc7); Publication rule | high |
| 2 | Data JSON and generated CSS repetition is by design | `.check:83-85` `audit-duplicate-ignore: data/...`; bloat duplicate count | structure of files; prior audit F-05 | medium (CSS copy of 319 lines is not in the ignore list, so it counts) |
| 3 | check_project takes about 36 s (baseline) / "about 4 minutes" | .check.state.json:370-373; scripts/check_project.sh:6; .claude/skills/audit/PROJECT.md:13 | measurement 2026-11-17; PROJECT.md text | low: today 101 s solo / 167 s in lane / 191 s in `--time`; the 2 texts disagree with each other (36 s vs 4 min) and with today |
| 4 | Full-lane baseline 144.8 s and its 21 step baselines come from the same kind of machine | .check.state.json `timings.check` | recorded; no machine type | low: today 168.7 s, 21 steps 2 to 8x slower; machine type not recorded |
| 5 | The repo is private, so the pull-request Action does not run and local checks are the gate | .github/workflows/check.yml:5-6, 15; release-checks.yml:1-3; AGENTS.md "Checks" | owner 2026-11-17 (workflow comment); DECISIONS | medium (visibility not read from GitHub here: network not allowed) |
| 6 | CI runs Node 24 and Python 3.12 | .github/workflows/release-checks.yml:48,51,67,70; scripts/requirements-cloud.txt:1 ("Python 3.12") | the workflow | medium: this machine has Node v22.23.5 and Python 3.13.18; check_project.sh:77-79 already branches for Node 22 and 23.6 or later |
| 7 | Cloud sessions have limited network plus package managers | scripts/cloud_env_setup.sh:9; .claude/settings.json sandbox.network.allowedDomains | file comment, 2026-11-11 | medium (tool behaviour; not re-tested) |
| 8 | Five blocks are configured and `refresh_site.sh` and `check_project.sh` loop over every configured block | config/content-blocks.json (default_block 4); scripts/list_blocks.py; refresh_site.sh:10-14; check_project.sh:41, 57 | system audit 2026-11-09 comment in both scripts; validate PASS | high (verified by passing checks today) |
| 9 | The mutant record (98.4% killed) still describes today's gates | docs/quality/work/check-mutants.json:4 (spec 3.9.0); docs/quality/STATE.md:65 | the record, 2026-11-19 | low: gates and SPEC moved to 3.12.1; counts in STATE.md:65 (317 / 299 / 18 missed) differ from the JSON (316 / 305 / 2 missed), so the doc and the record disagree |
| 10 | Hooks are cheap enough for every tool call | .claude/settings.json (PreToolUse timeout 10 s) | measured 0.06 to 0.08 s today (3 runs) | high |

Stale or untraced:
- #3 and #4 (baselines, "4 minutes", "36 s", "1 to 2 minutes": release-checks.yml:3).
- #9: docs/quality/STATE.md:65 says 299 caught, 18 missed; the JSON says 305 / 2 (that line is older than the 2026-11-19 re-base; history text).
- AGENTS.md "Check-in" rule: assumes a session can fetch origin (session_checkin.mjs `--fetch`); with the sandbox proxy, branch deletes failed twice before (prior audit F-11); not re-tested.
- docs/quality/work/*.jsonl and defects.json "frozen": assumed no further change; `quality_merge_defects.py` and `quality_golden_reserve.py` would rewrite them if run (they have no caller).
- Questions for the Maintainer (options, REC): (1) re-record the 2 baselines now (A re-record after 3 runs on this kind of machine; B keep and accept SLOWER on every run; REC A, after you say which machine is the usual one). (2) the duplicate-ignore for `site/dist/styles.css` (A add; B none; REC A). Not resolved by me.

## 4. Step 5 input: items a test could check (Step 3.4)
- Baseline vs reality: `bloat_check.py --compare` already warns; no new test needed.
- A test for `content_pipeline.py` exists (test_content_pipeline.py) but no lane runs it: add to check_project.sh (Lane B).

## 5. Tech-debt register

| Item | Owner (role) | Review date |
|---|---|---|
| Timing baselines (check 144.8 s, check_project 35.8 s, 21 step baselines) are 2 to 8x below measured; machine type not recorded | the Maintainer (approves re-record) | next audit (2026-12-08, 14 days) |
| Duplicate budget 437 vs 20; 319 are site/dist/styles.css against its partials | the Maintainer (`.check` change) | 2026-12-08 |
| Session load 5,143 tok, over the 5,000 warning, 357 below cap; 31 bullets vs guide 28 | the Maintainer (rule text; kit owns most of it) | 2026-12-08 |
| 8 Project rules flagged untested (rule lint): name each enforcing script or add a scenario | the Maintainer | 2026-12-08 |
| scripts/test_content_pipeline.py, test_environment.py, test_read_7z.py not run by any lane | the Release Manager (Lane B change) | next release |
| Mutant record is on spec 3.9.0 (SPEC 3.12.1); STATE.md:65 counts differ | the Content Approver (re-run decision) | next question-spec change |
| quality_check_mutants.py 1,876 lines, code-standard file_size debt (.check.state.json:238) | the Maintainer | next code-standard ratchet |
| 24 broad `except` handlers in 15 scripts, not reviewed | the Maintainer (Lane B review) | 2026-12-08 |
| 44 broken relative links in docs/reviews/HANDOFF-HISTORY.md (prior audit F-15), not re-measured | the Maintainer | next audit |
| Merged-branch deletes need the Maintainer on GitHub (prior audit F-11), not re-checked | the Maintainer | next audit |
| Stale texts: check_project.sh:6, release-checks.yml:3, audit/PROJECT.md:13 | the Maintainer (the last two are guard/kit-layer files) | 2026-12-08 |

## 6. Ranked T2 cut candidates (project-owned py/sh scripts)

Rule for the list: only files with no caller by code (or a one-off header) and a doc that names them as history; none is removed without the Maintainer's approval (Chesterton's fence below). T2 = 46,882 lines; T2 own = 33,645. Savings are lines of T2.

| Rank | File | Lines | Evidence of unused or duplicated | Why it exists | Risk |
|---|---|---|---|---|---|
| 1 | scripts/apply_b3_fresh_withdrawal_2026_11_11.py | 222 | date-named one-off, "Command (history only)" (line 14); only caller text is withdraw_items.py (a reference); 2 duplicate lines with withdraw_items.py; ran once 2026-11-11 (commit 6a16a0be) | applied the Block 3 fresh-review withdrawal; its path is cited as the "fix" in docs/quality/defects.json:46596 and defects-C.jsonl (frozen records) | medium: frozen evidence cites the path; `git log` keeps the text |
| 2 | scripts/merge_split_unit.py | 220 | no caller by code; header command names 3 Block 3 branches and base 83ecdec | merged the split Block 3 unit 3 (2026-11-11); named in BLOCK3_RUN_PLAN.md, NEW_BLOCK_CHECKLIST.md, archive handoff as history | low to medium: merge_block_units.py (171) is the block-generic helper for the same job (NEW_BLOCK_CHECKLIST.md:62), so a merge of the two is the other option |
| 3 | scripts/quality_merge_defects.py | 190 | no caller; Phase 1 tool; its output docs/quality/defects.json is "frozen" | Quality standard Phase 1 (2026-11-12, self-tested); named in docs/quality/STATE.md | medium: reports cite it as the method |
| 4 | scripts/quality_split_agreement.py | 161 | no caller by code; report-only; named only by SPEC-ARCHIVE.json, docs/LOG.md, STATE.md | Quality standard phase 2a (2026-11-12) | medium (history evidence) |
| 5 | scripts/quality_golden_reserve.py | 119 | no caller; frozen golden test pool step 5 | Quality standard Phase 1 (2026-11-12) | medium: rerun would change the golden pool; "never re-run" is a reason to archive, not to delete |
| 6 | scripts/diff_glossary_links.py | 144 | no code caller; named in AUDIT_PROMPT.md; added 2026-11-09 "Keep the question-set audit tools as maintained scripts (D13)" (a decision) | D13 audit tools | high: a decision kept it |
| 7 | scripts/test_environment.py + test_read_7z.py + cloud_env_setup.sh | 138 + 117 + 20 | on-demand tests, not in any lane (docs/cloud-environment.md:9) | cloud setup contract, 2026-11-05 | high: they are the only check of the cloud setup |
| 8 | scripts/quality_check_mutants.py family (7 files) | 3,432 | 1 of 7 files runs in a lane (test_mutation_gates, 531 lines with its helper); quality_check_mutants.py 1,876 lines is "report only" with a record from 2026-11-19 at 98.4% | Phase 4.1 mutants (MUTANT-BRIEF.md); prior audit P5 kept it by owner choice (REC B, 2026-11-17) | high: the owner decided to keep; changes need a new Maintainer request |
| - | Not cut candidates (named for the table): content_pipeline.py (188), cross_item_candidates.py (151), extract_sources.py (189), merge_block_units.py (171), review_content.sh (12), disable_scenarios.py (135): hand-run per docs | | | | |

Sums: ranks 1 to 5 = 912 lines (2.7% of T2 own; 1.9% of T2); with rank 6 = 1,056. Rank 8 is the only large block (3,432 lines, 7.3% of T2) and is a Maintainer choice already made once.
Other T2 levers (not cuts): 26 .mjs files are outside T2. The largest files in T2 own: quality_check_mutants.py 1,876; lint_content.py (727 lines per state file); apply_revision_edits.py 408; lint_content_clues.py 408; new_bank_apply.py 437; new_bank_check.py 433.
`git ls-files scripts | wc -l` = 233 (includes 5 non-script files and git-hooks).

## 7. What I did not do (and why)
- Did not run `scripts/refresh_site.sh` (writes site/dist and reports), `session_checkin.mjs` (forbidden), `session-start.sh` and `stop_check.py` (git config write; fetch), the full mutant run (writes docs/quality/work/check-mutants.json), `--record` anything.
- `scripts/check.sh` writes `.git/check-pass` and `.git/check-last` (inside .git, documented in check.sh header); `check_project.sh` wrote its own reports; `git status --short` stayed empty after every run.
- No 3-run median for any timing (budget): every time here is one run unless stated.
- Item 15 (cross-host), 20 (delegation) and skill use (19) need data outside the repo; not measured.
- Doc link walk (item 4) not run.
