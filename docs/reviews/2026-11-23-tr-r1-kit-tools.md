# Tool retirement R1: kit tool inventory

Input for docs/tools.md (prompt step 1). Not yet at docs/tools.md: `scripts/bootstrap.sh` copies `docs/` into a new
project, and this kit-only list failed `bootstrap_cli_test` (role word in a copied file). Where docs/tools.md lives in a
project (own list, or a kit-only file that bootstrap removes like docs/FILES.md) is a decision in the plan (rule T1). Measured 2026-11-23 ~15:30 America/Chicago on kit main 641023e.
Research input, not a decision: each family's verdict (retire / shrink / keep) comes from the trials
(docs/reviews/2026-11-23-tr-*.md) and the plan.

How measured (re-run to update):
- Lines: newline count of each file. Files: `scripts/*.py`, `scripts/*.sh`, `scripts/git-hooks/*`.
- Callers: the file stem appears in `scripts/check.sh`, `scripts/git-hooks/*`, `.github/workflows/*`, `.claude/settings.json`;
  "+N scripts" = other kit scripts that name it.
- Self-test: the file has a `--test` mode or is a `*_test.py` file. Mutant counts: **not measured** (the kit has no
  mutation tool; the trials use seeded defects instead; GAP for the plan).
- Changes: `git log origin/main --since=2026-10-24 --numstat` (kit history on this clone starts 2026-11-11): commits and
  lines added + deleted.
- Sync churn: commits in the last 30 days that touch the same path in RADE, 90-161.Z, 33-332.Z and ICF-Source (proxy for
  "sync PRs it caused"; each kit change reaches each project as a sync commit).

## Families

| Family | Files | Lines | Commits 30 d | Lines changed 30 d | Sync churn | Standard candidates | Trial |
|---|---|---|---|---|---|---|---|
| Code standard | 10 | 2,415 | 48 | 4,479 | 77 | ruff, pylint (max-module-lines), radon | W-A |
| Content check | 9 | 2,677 | 64 | 4,531 | 101 | gitleaks (custom rules), detect-secrets, trufflehog | W-B |
| Instructions check | 3 | 861 | 14 | 1,509 | 20 | Vale (custom style), proselint, textlint | W-B |
| Sync, drift, lock, settings | 17 | 3,757 | 212 | 7,316 | 94 | copier, cruft, pre-commit autoupdate / Renovate | W-C |
| Token log | 5 | 1,426 | 50 | 3,733 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API | W-C |
| Rule caps and audit | 6 | 1,691 | 82 | 4,247 | 121 | markdownlint (line caps), wc-based CI step, none known for rule census | none (keep candidate) |
| Guards and hooks | 7 | 1,872 | 144 | 2,823 | 154 | pre-commit framework, Claude Code permission rules, GitHub rulesets | W-C (distribution) |
| Site and brand | 4 | 1,398 | 21 | 1,814 | 43 | python-markdown / markdown-it-py, MkDocs, Style Dictionary | W-D (Markdown build) |
| Log, fleet, usage | 5 | 1,264 | 39 | 2,422 | 44 | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest | none (keep candidate) |
| **Total** | **66** | **17,361** | **674** | **32,874** | **654** | | |

Without `scripts/git-hooks/pre-push`: 65 files, 17,096 lines (the prompt's baseline: 65 scripts, 17,096 lines). This total is the T2 ratchet baseline candidate.

## Code standard

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/code_standard.py` | Code standard check: measures every source file of this repo against docs/code-standard.md and fails on new de | 439 | check.sh +17 scripts | yes | 15 | 1621 | 18 |
| `scripts/code_standard_docs.py` | Full function docs for the code standard: the opt-in rule `code-c2: full` of docs/code-standard.md (C2 full). | 228 | check.sh +5 scripts | yes | 5 | 256 | 12 |
| `scripts/code_standard_parse.py` | The file readers of the code standard check (scripts/code_standard.py): the header comment of a file, its mark | 334 | check.sh +4 scripts | yes | 1 | 334 | 4 |
| `scripts/code_standard_ratchet.py` | The comparison of the code standard baseline with main: the Maintainer's decision test, the check of the setti | 111 | check.sh +3 scripts | no | 3 | 123 | 4 |
| `scripts/code_standard_rules.py` | The rule table of the code standard check and the measures of one function: the debt kinds with their labels a | 117 | check.sh +3 scripts | no | 2 | 123 | 4 |
| `scripts/code_standard_strict.py` | The kit's strict code-standard rules, an opt-in part of scripts/code_standard.py: a project turns them on with | 228 | check.sh +5 scripts | yes | 2 | 252 | 4 |
| `scripts/code_standard_strict_test.py` | Self-test of the kit's strict code-standard rules, scripts/code_standard_strict.py (run by | 328 | check.sh +3 scripts | yes | 3 | 412 | 4 |
| `scripts/code_standard_test.py` | Self-test of scripts/code_standard.py (run by `python3 scripts/code_standard.py --test`; kept in its own file  | 325 | check.sh +6 scripts | yes | 12 | 1039 | 19 |
| `scripts/code_standard_test_docs.py` | Self-test cases of the opt-in C2 full rule of scripts/code_standard.py (`code-c2: full`): a long function with | 115 | check.sh +3 scripts | yes | 2 | 125 | 4 |
| `scripts/code_standard_test_gate.py` | Self-test cases of the extension point of scripts/code_standard.py (a project's own gate): a sample gate file  | 190 | check.sh +5 scripts | yes | 3 | 194 | 4 |

## Content check

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/check_content.py` | The content check of scripts/check.sh: blocks personal data, secrets and the Maintainer's own blocked content  | 282 | check.sh,hooks,CI,settings +15 scripts | yes | 11 | 338 | 16 |
| `scripts/check_content_finders.py` | The finders of the content check: the patterns of each finding kind, the kit's finder functions, and the loade | 310 | check.sh +6 scripts | yes | 3 | 312 | 8 |
| `scripts/check_content_hook.py` | The Claude Code PreToolUse hook of check_content.py (`python3 scripts/check_content.py --hook`). | 240 | check.sh +6 scripts | no | 9 | 354 | 11 |
| `scripts/check_content_scan.py` | The scanner of check_content.py: the patterns, the readers of the word lists (names, terms) and of the setting | 374 | check.sh +11 scripts | yes | 11 | 1170 | 20 |
| `scripts/check_content_scan_settings.py` | The settings and word lists of the content check: the readers of the name denylist and the terms list, and of  | 251 | check.sh +5 scripts | no | 3 | 257 | 4 |
| `scripts/check_content_test.py` | Self-test of scripts/check_content.py (run by `python3 scripts/check_content.py --test`; kept in its own file  | 266 | check.sh +7 scripts | yes | 6 | 1022 | 12 |
| `scripts/check_content_test_blocks.py` | More cases of the self-test of scripts/check_content.py (check_content_test.py runs them; kept apart for the | 337 | check.sh +3 scripts | no | 13 | 381 | 14 |
| `scripts/check_content_test_cli.py` | More cases of the self-test of scripts/check_content.py: the CLI modes (--all, --push, --status, --stdin, file | 357 | check.sh +3 scripts | no | 1 | 357 | 4 |
| `scripts/check_content_test_local.py` | More cases of the self-test of scripts/check_content.py (check_content_test.py runs them; kept apart so that f | 260 | check.sh +3 scripts | yes | 7 | 340 | 12 |

## Instructions check

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/check_instructions.py` | Check the steps that a person reads and acts on (AGENTS.md "Instructions people follow"; the steps to write th | 310 | check.sh,settings +5 scripts | yes | 7 | 926 | 8 |
| `scripts/check_instructions_steps.py` | The step reader and the step measures of scripts/check_instructions.py: the word lists and patterns, the numbe | 280 | check.sh +3 scripts | no | 1 | 280 | 4 |
| `scripts/check_instructions_test.py` | Self-test cases of scripts/check_instructions.py (run: python3 scripts/check_instructions.py --test). | 271 | check.sh +3 scripts | yes | 6 | 303 | 8 |

## Sync, drift, lock, settings

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/bootstrap.sh` | Fill the template placeholders in a new project made from the kit (kit.config.json "kit_repo"). | 138 | check.sh +8 scripts | no | 49 | 337 | 2 |
| `scripts/bootstrap_cli_test.py` | The command line of scripts/bootstrap.sh, tested as a process. | 163 |  +1 scripts | yes | 5 | 179 | 0 |
| `scripts/check_lock.py` | The kit lock of a project: `.check.lock` records which kit version the project was synced from and a SHA-256 o | 237 | check.sh +11 scripts | yes | 6 | 257 | 11 |
| `scripts/check_lock_cli_test.py` | The command line of scripts/check_lock.py, tested as a process. | 108 |  +1 scripts | yes | 2 | 110 | 0 |
| `scripts/check_settings.py` | The one reader of the code standard and audit settings in `.check`, and the one reader and writer of | 343 | check.sh +21 scripts | yes | 21 | 1377 | 27 |
| `scripts/check_settings_read.py` | The reader of the `code-` and `audit-` lines of `.check`, and the reader and writer of `.check.state.json`: th | 328 | check.sh +3 scripts | no | 6 | 356 | 4 |
| `scripts/check_settings_test.py` | The self-test of scripts/check_settings.py (`python3 scripts/check_settings.py --test`), kept apart so that fi | 416 | check.sh +3 scripts | yes | 14 | 504 | 24 |
| `scripts/drift.py` | Report how a project repo differs from the archimedes_lever baseline. Report only: it never writes. | 317 | check.sh,settings +12 scripts | yes | 21 | 1217 | 11 |
| `scripts/drift_cli_test.py` | The command line of scripts/drift.py, tested as a process. | 92 |  +1 scripts | yes | 2 | 98 | 0 |
| `scripts/drift_test.py` | Self-test cases of scripts/drift.py (run by `python3 scripts/drift.py --test`; kept in its own file so drift.p | 319 | check.sh +3 scripts | yes | 3 | 335 | 0 |
| `scripts/kit_config.py` | The reader of kit.config.json: the one home of the kit's own addresses (fleet v2 plan DEC 7, 2026-11-23). | 109 | check.sh +5 scripts | yes | 3 | 113 | 0 |
| `scripts/sync_baseline.py` | Sync a project repo to the current kit baseline (the repo that kit.config.json "kit_url" names). | 445 | check.sh +18 scripts | no | 64 | 1669 | 15 |
| `scripts/sync_baseline_cli_test.py` | The command line of scripts/sync_baseline.py, tested as a process. | 148 | check.sh +3 scripts | yes | 4 | 152 | 0 |
| `scripts/sync_baseline_repo.py` | The reads of the baseline repo for scripts/sync_baseline.py: git, the baseline folder or clone, the earlier | 150 | check.sh +3 scripts | no | 2 | 150 | 0 |
| `scripts/sync_baseline_run.py` | The steps of one run of scripts/sync_baseline.py: read the command line, find the project and the baseline, sh | 74 | check.sh +3 scripts | no | 1 | 74 | 0 |
| `scripts/sync_merge.py` | The merges of scripts/sync_baseline.py: a sync does not replace these project files, it adds the kit's part to | 260 | check.sh +6 scripts | yes | 7 | 266 | 0 |
| `scripts/sync_merge_cli_test.py` | The merges of scripts/sync_merge.py, tested through the command line of scripts/sync_baseline.py (sync_merge.p | 110 |  +1 scripts | yes | 2 | 122 | 0 |

## Token log

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/token_log.py` | Claude Code Stop hook: log the token use of each API call to the branch claude/token-usage of the session's re | 394 | check.sh +7 scripts | yes | 26 | 2181 | 0 |
| `scripts/token_log_report.py` | The report part of scripts/token_log.py: the price tables and the --report command (estimated cost by week, by | 153 | check.sh +3 scripts | no | 1 | 153 | 0 |
| `scripts/token_log_rows.py` | The row part of scripts/token_log.py: reads a session log and its subagent logs into one row per API call | 162 | check.sh +4 scripts | yes | 1 | 162 | 0 |
| `scripts/token_log_test.py` | Self-test of scripts/token_log.py (run by `python3 scripts/token_log.py --test`; kept in its own file so each | 368 | check.sh +4 scripts | yes | 15 | 876 | 0 |
| `scripts/token_log_test_report.py` | More self-test cases of scripts/token_log.py: the agent and agent_id columns, bad agent input, the report, the | 349 | check.sh +3 scripts | yes | 7 | 361 | 0 |

## Rule caps and audit

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/bloat_check.py` | Cheap bloat and drift metrics for a project repo, and the audit due date. Report only, unless --record. | 396 | check.sh,hooks,settings +10 scripts | yes | 40 | 2128 | 53 |
| `scripts/bloat_check_rules.py` | The rule census of scripts/bloat_check.py (`--rules`, `--lint`): the session load, the rule lines of AGENTS.md | 419 | check.sh +3 scripts | yes | 7 | 453 | 17 |
| `scripts/bloat_check_skills.py` | The skills check of scripts/bloat_check.py (`python3 scripts/bloat_check.py --skills`; kept in its own file so | 186 | check.sh +6 scripts | no | 10 | 214 | 16 |
| `scripts/bloat_check_test.py` | Self-test of scripts/bloat_check.py (run by `python3 scripts/bloat_check.py --test`; kept in its own file so t | 323 | check.sh +4 scripts | yes | 20 | 1069 | 27 |
| `scripts/bloat_check_test_rules.py` | Self-test cases of the rule census of scripts/bloat_check.py: the rule count by place, the caps, the paths | 257 | check.sh +3 scripts | yes | 2 | 267 | 4 |
| `scripts/bloat_check_timing.py` | The timings of the bloat check: run the timed commands of .check.state.json and compare measured times with th | 110 | check.sh +3 scripts | no | 3 | 116 | 4 |

## Guards and hooks

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/check.sh` | One check command for the repo (AGENTS.md "Commands": Test): the one front door of every check and guard. | 445 | hooks,CI,settings +62 scripts | yes | 60 | 733 | 40 |
| `scripts/check_blocks.py` | The block lists of scripts/check.sh that are not content patterns: the git commands and file reads that | 150 | check.sh +8 scripts | yes | 3 | 158 | 4 |
| `scripts/first_use_check.py` | Session-start check: is this repo set up, and can the personal-data guard check names here? | 254 | check.sh,settings +9 scripts | yes | 16 | 366 | 10 |
| `scripts/session_checkin.sh` | Session check-in: run at the start and the end of each session. | 153 | check.sh,hooks,settings +6 scripts | yes | 24 | 229 | 29 |
| `scripts/stop_check.py` | Claude Code Stop hook: block the end of a turn while work is not on GitHub. | 317 | check.sh,settings +5 scripts | yes | 8 | 567 | 23 |
| `scripts/worker_guard.py` | PreToolUse hook for the worker and reviewer subagents (.claude/agents/): blocks git commands they must never r | 288 | check.sh +3 scripts | yes | 10 | 366 | 18 |
| `scripts/git-hooks/pre-push` | Git pre-push hook for Claude, any git client, and people. | 265 | check.sh,CI +13 scripts | yes | 23 | 404 | 30 |

## Site and brand

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/build_site.py` | Build the shared parts of the site page (index.html) from README.md, so the README is the one source of truth. | 441 | check.sh +7 scripts | yes | 6 | 785 | 17 |
| `scripts/build_site_html.py` | HTML parts of the kit's pages: the Markdown-to-HTML builders of scripts/build_site.py (moved here so that file | 233 | check.sh +7 scripts | no | 3 | 241 | 4 |
| `scripts/fulcrum_palette.py` | Build and check the Fulcrum Minimal design tokens: docs/brand/fulcrum.json is the source, docs/brand/fulcrum.c | 312 | check.sh +2 scripts | yes | 1 | 312 | 4 |
| `scripts/timeline.py` | Render one or more project logs (docs/LOG.md) as one self-contained HTML timeline page. | 412 | check.sh +6 scripts | yes | 11 | 476 | 18 |

## Log, fleet, usage

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn |
|---|---|---|---|---|---|---|---|
| `scripts/fleet_harvest.py` | Read a project's handoff and decisions files in the fleet format, for the fleet page and its format check. | 312 | check.sh +4 scripts | yes | 12 | 1192 | 10 |
| `scripts/fleet_harvest_parse.py` | The fleet format reader: the patterns and parsers that read a project's handoff and docs/DECISIONS.md. | 181 | check.sh +3 scripts | no | 3 | 189 | 4 |
| `scripts/fleet_harvest_test.py` | Self-test cases of scripts/fleet_harvest.py (run by `python3 scripts/fleet_harvest.py --test`; kept in its own | 231 | check.sh +3 scripts | yes | 11 | 269 | 10 |
| `scripts/log_check.py` | Check a project log (docs/LOG.md) against the project log rules (AGENTS.md "Project log" and .claude/skills/pr | 320 | check.sh,settings +4 scripts | yes | 9 | 448 | 16 |
| `scripts/skill_use.py` | Count which skills, agent types and tools a set of Claude session records really used. | 220 | check.sh +2 scripts | yes | 4 | 324 | 4 |
