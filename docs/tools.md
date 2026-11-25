# Tools: kit script inventory

Kit-only inventory of the kit scripts (rule T1: every tool file this repo owns has a row here, with its candidates). `scripts/bootstrap.sh` removes this file from a new project, as it removes docs/FILES.md; each project keeps its own list. Measured 2026-11-23 ~15:30 America/Chicago on kit main 641023e.
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

Without `scripts/git-hooks/pre-push`: 65 files, 17,096 lines (the prompt's baseline: 65 scripts, 17,096 lines). This total is the T2 ratchet baseline candidate. Added after this measurement: `scripts/log_check_plan.py` (194 lines; the T6 and T7 checks, split from log_check.py by the 450-line cap).

## Code standard

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/code_standard.py` | Code standard check: measures every source file of this repo against docs/code-standard.md and fails on new de | 439 | check.sh +17 scripts | yes | 15 | 1621 | 18 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_docs.py` | Full function docs for the code standard: the opt-in rule `code-c2: full` of docs/code-standard.md (C2 full). | 228 | check.sh +5 scripts | yes | 5 | 256 | 12 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_parse.py` | The file readers of the code standard check (scripts/code_standard.py): the header comment of a file, its mark | 334 | check.sh +4 scripts | yes | 1 | 334 | 4 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_ratchet.py` | The comparison of the code standard baseline with main: the Maintainer's decision test, the check of the setti | 111 | check.sh +3 scripts | no | 3 | 123 | 4 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_rules.py` | The rule table of the code standard check and the measures of one function: the debt kinds with their labels a | 117 | check.sh +3 scripts | no | 2 | 123 | 4 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_strict.py` | The kit's strict code-standard rules, an opt-in part of scripts/code_standard.py: a project turns them on with | 228 | check.sh +5 scripts | yes | 2 | 252 | 4 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_strict_test.py` | Self-test of the kit's strict code-standard rules, scripts/code_standard_strict.py (run by | 328 | check.sh +3 scripts | yes | 3 | 412 | 4 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_test.py` | Self-test of scripts/code_standard.py (run by `python3 scripts/code_standard.py --test`; kept in its own file  | 325 | check.sh +6 scripts | yes | 12 | 1039 | 19 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_test_docs.py` | Self-test cases of the opt-in C2 full rule of scripts/code_standard.py (`code-c2: full`): a long function with | 115 | check.sh +3 scripts | yes | 2 | 125 | 4 | ruff, pylint (max-module-lines), radon |
| `scripts/code_standard_test_gate.py` | Self-test cases of the extension point of scripts/code_standard.py (a project's own gate): a sample gate file  | 190 | check.sh +5 scripts | yes | 3 | 194 | 4 | ruff, pylint (max-module-lines), radon |

## Content check

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/check_content.py` | The content check of scripts/check.sh: blocks personal data, secrets and the Maintainer's own blocked content  | 282 | check.sh,hooks,CI,settings +15 scripts | yes | 11 | 338 | 16 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_finders.py` | The finders of the content check: the patterns of each finding kind, the kit's finder functions, and the loade | 310 | check.sh +6 scripts | yes | 3 | 312 | 8 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_hook.py` | The Claude Code PreToolUse hook of check_content.py (`python3 scripts/check_content.py --hook`). | 240 | check.sh +6 scripts | no | 9 | 354 | 11 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_scan.py` | The scanner of check_content.py: the patterns, the readers of the word lists (names, terms) and of the setting | 378 | check.sh +11 scripts | yes | 11 | 1170 | 20 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_scan_settings.py` | The `.check` settings of the content check (the word lists are in check_content_scan_words.py) | 175 | check.sh +5 scripts | no | 3 | 257 | 4 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_scan_words.py` | The word lists of the content check: the readers of the name denylist and the terms list, and the fingerprint of a list | 94 | check.sh +4 scripts | no | 1 | 94 | 0 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_test.py` | Self-test of scripts/check_content.py (run by `python3 scripts/check_content.py --test`; kept in its own file  | 266 | check.sh +7 scripts | yes | 6 | 1022 | 12 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_test_blocks.py` | More cases of the self-test of scripts/check_content.py (check_content_test.py runs them; kept apart for the | 337 | check.sh +3 scripts | no | 13 | 381 | 14 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_test_cli.py` | More cases of the self-test of scripts/check_content.py: the CLI modes (--all, --push, --status, --stdin, file | 357 | check.sh +3 scripts | no | 1 | 357 | 4 | gitleaks (custom rules), detect-secrets, trufflehog |
| `scripts/check_content_test_local.py` | More cases of the self-test of scripts/check_content.py (check_content_test.py runs them; kept apart so that f | 260 | check.sh +3 scripts | yes | 7 | 340 | 12 | gitleaks (custom rules), detect-secrets, trufflehog |

## Instructions check

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/check_instructions.py` | Check the steps that a person reads and acts on (AGENTS.md "Instructions people follow"; the steps to write th | 310 | check.sh,settings +5 scripts | yes | 7 | 926 | 8 | Vale (custom style), proselint, textlint |
| `scripts/check_instructions_steps.py` | The step reader and the step measures of scripts/check_instructions.py: the word lists and patterns, the numbe | 280 | check.sh +3 scripts | no | 1 | 280 | 4 | Vale (custom style), proselint, textlint |
| `scripts/check_instructions_test.py` | Self-test cases of scripts/check_instructions.py (run: python3 scripts/check_instructions.py --test). | 271 | check.sh +3 scripts | yes | 6 | 303 | 8 | Vale (custom style), proselint, textlint |

## Sync, drift, lock, settings

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/bootstrap.sh` | Fill the template placeholders in a new project made from the kit (kit.config.json "kit_repo"). | 138 | check.sh +8 scripts | no | 49 | 337 | 2 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/bootstrap_cli_test.py` | The command line of scripts/bootstrap.sh, tested as a process. | 163 |  +1 scripts | yes | 5 | 179 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/check_lock.py` | The kit lock of a project: `.check.lock` records which kit version the project was synced from and a SHA-256 o | 237 | check.sh +11 scripts | yes | 6 | 257 | 11 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/check_lock_cli_test.py` | The command line of scripts/check_lock.py, tested as a process. | 108 |  +1 scripts | yes | 2 | 110 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/check_settings.py` | The one reader of the code standard and audit settings in `.check`, and the one reader and writer of | 343 | check.sh +21 scripts | yes | 21 | 1377 | 27 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/check_settings_read.py` | The reader of the `code-` and `audit-` lines of `.check`, and the reader and writer of `.check.state.json`: th | 328 | check.sh +3 scripts | no | 6 | 356 | 4 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/check_settings_test.py` | The self-test of scripts/check_settings.py (`python3 scripts/check_settings.py --test`), kept apart so that fi | 416 | check.sh +3 scripts | yes | 14 | 504 | 24 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/drift.py` | Report how a project repo differs from the archimedes_lever baseline. Report only: it never writes. | 317 | check.sh,settings +12 scripts | yes | 21 | 1217 | 11 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/drift_cli_test.py` | The command line of scripts/drift.py, tested as a process. | 92 |  +1 scripts | yes | 2 | 98 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/drift_test.py` | Self-test cases of scripts/drift.py (run by `python3 scripts/drift.py --test`; kept in its own file so drift.p | 319 | check.sh +3 scripts | yes | 3 | 335 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/kit_config.py` | The reader of kit.config.json: the one home of the kit's own addresses (fleet v2 plan DEC 7, 2026-11-23). | 109 | check.sh +5 scripts | yes | 3 | 113 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/kit_package.py` | The kit package (P3, design B): installs the untracked kit scripts of a project from the `archimedes-kit` package at the lock commit and verifies them. Added 2026-11-24. | 174 | check.sh | yes | 0 | 0 | 0 | pipx, pre-commit (hook repo at a tag), copier |
| `scripts/sync_baseline.py` | Sync a project repo to the current kit baseline (the repo that kit.config.json "kit_url" names). | 445 | check.sh +18 scripts | no | 64 | 1669 | 15 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/sync_baseline_cli_test.py` | The command line of scripts/sync_baseline.py, tested as a process. | 148 | check.sh +3 scripts | yes | 4 | 152 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/sync_baseline_repo.py` | The reads of the baseline repo for scripts/sync_baseline.py: git, the baseline folder or clone, the earlier | 150 | check.sh +3 scripts | no | 2 | 150 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/sync_baseline_run.py` | The write side of one run of scripts/sync_baseline.py: the placeholder check, the leftover report, the file writes and the kit lock | 91 | check.sh +3 scripts | no | 1 | 74 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/sync_baseline_stop.py` | The stop of scripts/sync_baseline.py on a project's local edits to kit files: locked, relocked and unlocked files, with a way forward per file | 91 | check.sh +2 scripts | no | 1 | 91 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/sync_merge.py` | The merges of scripts/sync_baseline.py: a sync does not replace these project files, it adds the kit's part to | 260 | check.sh +6 scripts | yes | 7 | 266 | 0 | copier, cruft, pre-commit autoupdate / Renovate |
| `scripts/sync_merge_cli_test.py` | The merges of scripts/sync_merge.py, tested through the command line of scripts/sync_baseline.py (sync_merge.p | 110 |  +1 scripts | yes | 2 | 122 | 0 | copier, cruft, pre-commit autoupdate / Renovate |

## Token log

Lines and jobs of the token log rows re-measured 2026-11-25 (token log follow-ups); the other columns are from the first measurement.

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/token_log.py` | Claude Code Stop hook: log the token use of each API call to the branch claude/token-usage of the private log  | 517 | check.sh +7 scripts | yes | 26 | 2181 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API |
| `scripts/token_log_report.py` | The report of the token log: the price tables and the --report command (estimated cost by week, by source, age | 439 | check.sh +3 scripts | no | 1 | 153 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API |
| `scripts/token_log_rows.py` | The rows of the token log: reads a session log and its subagent logs into one row per API call (message id, tu | 358 | check.sh +4 scripts | yes | 1 | 162 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API |
| `scripts/token_log_test.py` | Self-test of scripts/token_log.py (run by `python3 scripts/token_log.py --test`; kept in its own file so each  | 455 | check.sh +4 scripts | yes | 15 | 876 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API |
| `scripts/token_log_test_parts.py` | Self-test cases of the token log's parts: the rows (agent, agent_id and skill_use columns, bad agent input), t | 417 | check.sh +3 scripts | yes | 7 | 361 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API |
| `scripts/token_log_test_costs.py` | Self-test cases of the /cost and /usage records in the token log: the agents-pane record <TOKEN_LOG_HOME>/cost | 225 | check.sh +1 scripts | yes | 0 | 0 | 0 | Claude Code OpenTelemetry metrics, `/cost`, Anthropic usage API |

## Rule caps and audit

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/bloat_check.py` | Cheap bloat and drift metrics for a project repo, and the audit due date. Report only, unless --record. | 396 | check.sh,hooks,settings +10 scripts | yes | 40 | 2128 | 53 | markdownlint (line caps), wc-based CI step, none known for rule census |
| `scripts/bloat_check_rules.py` | The rule census of scripts/bloat_check.py (`--rules`, `--lint`): the session load, the rule lines of AGENTS.md | 419 | check.sh +3 scripts | yes | 7 | 453 | 17 | markdownlint (line caps), wc-based CI step, none known for rule census |
| `scripts/bloat_check_files.py` | The repo's own files in the bloat check: the tool rows of docs/tools.md (T1), the script lines ratchet (T2), the role word (T6), the debt triggers (T5) and the full `--rules` report | new | check.sh +3 scripts | yes (bloat_check.py --test) | new | new | new | markdownlint (line caps), wc-based CI step, none known for rule census |
| `scripts/bloat_check_skills.py` | The skills check of scripts/bloat_check.py (`python3 scripts/bloat_check.py --skills`; kept in its own file so | 186 | check.sh +6 scripts | no | 10 | 214 | 16 | markdownlint (line caps), wc-based CI step, none known for rule census |
| `scripts/bloat_check_test.py` | Self-test of scripts/bloat_check.py (run by `python3 scripts/bloat_check.py --test`; kept in its own file so t | 323 | check.sh +4 scripts | yes | 20 | 1069 | 27 | markdownlint (line caps), wc-based CI step, none known for rule census |
| `scripts/bloat_check_test_rules.py` | Self-test cases of the rule census of scripts/bloat_check.py: the rule count by place, the caps, the paths | 257 | check.sh +3 scripts | yes | 2 | 267 | 4 | markdownlint (line caps), wc-based CI step, none known for rule census |
| `scripts/bloat_check_timing.py` | The timings of the bloat check: run the timed commands of .check.state.json and compare measured times with th | 110 | check.sh +3 scripts | no | 3 | 116 | 4 | markdownlint (line caps), wc-based CI step, none known for rule census |

## Guards and hooks

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/check.sh` | One check command for the repo (AGENTS.md "Commands": Test): the one front door of every check and guard. | 445 | hooks,CI,settings +62 scripts | yes | 60 | 733 | 40 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `scripts/check_blocks.py` | The block lists of scripts/check.sh that are not content patterns: the git commands and file reads that | 150 | check.sh +8 scripts | yes | 3 | 158 | 4 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `scripts/first_use_check.py` | Session-start check: is this repo set up, and can the personal-data guard check names here? | 254 | check.sh,settings +9 scripts | yes | 16 | 366 | 10 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `scripts/session_checkin.sh` | Session check-in: run at the start and the end of each session. | 153 | check.sh,hooks,settings +6 scripts | yes | 24 | 229 | 29 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `scripts/stop_check.py` | Claude Code Stop hook: block the end of a turn while work is not on GitHub. | 317 | check.sh,settings +5 scripts | yes | 8 | 567 | 23 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `scripts/worker_guard.py` | PreToolUse hook for the worker and reviewer subagents (.claude/agents/): blocks git commands they must never r | 288 | check.sh +3 scripts | yes | 10 | 366 | 18 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `scripts/worker_guard_scan.py` | The --scan mode of scripts/worker_guard.py: finds strings rebuilt to pass the content check and blocked git commands put in shell scripts, in a worker branch or a scratch folder | 238 | worker_guard.py, delegate skill | yes | 1 | 238 | 0 | semgrep (custom rules), bandit, gitleaks (custom rules) |
| `scripts/git-hooks/pre-push` | Git pre-push hook for Claude, any git client, and people. | 265 | check.sh,CI +13 scripts | yes | 23 | 404 | 30 | pre-commit framework, Claude Code permission rules, GitHub rulesets |
| `.claude/skills/verify/measure.mjs` | UI measurement for the verify skill: screenshots at 375 and 1440 px in light and dark, page scroll, WCAG AA text contrast, target size | 0 (outside scripts/) | verify skill | no | - | - | - | Lighthouse CI, axe-core (@axe-core/playwright), pa11y |

## Site and brand

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/build_site.py` | Build the shared parts of the site page (index.html) from README.md, so the README is the one source of truth. | 441 | check.sh +7 scripts | yes | 6 | 785 | 17 | python-markdown / markdown-it-py, MkDocs, Style Dictionary |
| `scripts/build_site_html.py` | HTML parts of the kit's pages: the Markdown-to-HTML builders of scripts/build_site.py (moved here so that file | 233 | check.sh +7 scripts | no | 3 | 241 | 4 | python-markdown / markdown-it-py, MkDocs, Style Dictionary |
| `scripts/fulcrum_palette.py` | Build and check the Fulcrum Minimal design tokens: docs/brand/fulcrum.json is the source, docs/brand/fulcrum.c | 312 | check.sh +2 scripts | yes | 1 | 312 | 4 | python-markdown / markdown-it-py, MkDocs, Style Dictionary |
| `scripts/timeline.py` | Render one or more project logs (docs/LOG.md) as one self-contained HTML timeline page. | 412 | check.sh +6 scripts | yes | 11 | 476 | 18 | python-markdown / markdown-it-py, MkDocs, Style Dictionary |

## Log, fleet, usage

| File | Job | Lines | Callers | Self-test | Commits 30 d | Lines changed | Sync churn | Candidates |
|---|---|---|---|---|---|---|---|---|
| `scripts/fleet_harvest.py` | Read a project's handoff and decisions files in the fleet format, for the fleet page and its format check. | 312 | check.sh +4 scripts | yes | 12 | 1192 | 10 | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest |
| `scripts/fleet_harvest_parse.py` | The fleet format reader: the patterns and parsers that read a project's handoff and docs/DECISIONS.md. | 181 | check.sh +3 scripts | no | 3 | 189 | 4 | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest |
| `scripts/fleet_harvest_test.py` | Self-test cases of scripts/fleet_harvest.py (run by `python3 scripts/fleet_harvest.py --test`; kept in its own | 231 | check.sh +3 scripts | yes | 11 | 269 | 10 | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest |
| `scripts/log_check.py` | Check a project log (docs/LOG.md) against the project log rules (AGENTS.md "Project log" and .claude/skills/pr | 320 | check.sh,settings +4 scripts | yes | 9 | 448 | 16 | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest |
| `scripts/log_check_plan.py` | The T6 (DECISIONS approval quote) and T7 (plan coverage list) checks of scripts/log_check.py, and their self-test cases. | 194 | log_check.py | yes (log_check.py --test) | new | new | new | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest |
| `scripts/skill_use.py` | Count which skills, agent types and tools a set of Claude session records really used. | 220 | check.sh +2 scripts | yes | 4 | 324 | 4 | markdownlint + a schema (e.g. frontmatter), none known for fleet harvest |

## Fleet audit verdicts (2026-11-24)

One line per check of `scripts/check.sh` and for the audit skill: **REC** (a recommendation of the fleet audit), not a
decision; the Maintainer decides each retire or shrink. Evidence and method: docs/reviews/2026-11-24-fleet-audit.md
(all 5 repos read). "Decided" names the dated choice that the line follows.

| Check (check.sh step) | REC | Evidence |
|---|---|---|
| code standard (`code_standard*.py`) | keep, shrink done | P2 (a) moved Python parse, line and size to ruff + pylint; C1 safety, C6, the ratchet have no standard rule (W-A); 0 dead functions, 0 same-body duplicates |
| content check (`check_content*.py`) | keep (decided 9A) | gitleaks with custom rules covers 10 of 11 checks, not `unscanned`, commit metadata, `.check` or the hook (W-B) |
| instructions (`check_instructions*.py`) | keep (decided 10); WARN when no file is listed | Vale 8 of 9 seeded, 54 false positives on 225 real steps (W-B); reads 0 files in RADE and 33-332.Z (no `audit-instructions:` line; audit-the-audit A15) |
| rule caps and pointers, skills well-formed (`bloat_check*.py`) | keep; change the T2 measure | 17 of 25 failed CI runs (2026-11-13 to 11-24): a changed rule line with no conflict-check record; in the kit the session load counts the template NEXT_PROMPT.md, not KIT_HANDOFF.md (~6,100 real tokens, about 600 over the 5,500 cap; A10); no standard tool for a rule census; T2 counts tests and only `scripts/` (audit-the-audit A1, A2) |
| deny rules (`check_blocks.py`) | keep | the one list of blocked git forms for the hook and settings |
| project log, decisions approval quote, plan coverage (`log_check*.py`) | keep | the T6 and T7 checks stop a DECISIONS row with no approval quote |
| fleet format (`fleet_harvest*.py`) | keep | the fleet page reads it; no standard reader |
| python lint (ruff, pylint) | keep | the standard tools that replaced custom Python checks (P2 (a)) |
| shellcheck (WARN) | keep | standard tool (P2 (g)) |
| bandit, gitleaks (full lane; a SKIP line when one is missing) | keep | standard tools; the local run of the scans of `.github/workflows/security.yml`, which skips pull requests in a private repo (2026-11-25) |
| self-tests (each `--test`, `*_cli_test.py`) | keep; shrink done | #158 (merged, 00a0102) merged 4 copies of the CLI test helpers (-105 lines) |
| kit lock (`check_lock.py`), drift (`drift.py`), sync (`sync_baseline*.py`, `sync_merge.py`) | keep until P3 | P3 (a package) can move 13,237 kit-owned lines out of each project; lock and sync change then |
| token log (`token_log*.py`) | keep (decided, plan decision 5) | kit only, 1,566 lines with tests; OpenTelemetry needs a collector (W-C) |
| site and brand (`build_site*.py`, `fulcrum_palette.py`, `timeline.py`) | keep (timeline.py decided; the others measured in P2) | real use; 33-332.Z `site_page.py` imports `fulcrum_palette.contrast` after its PR 77 |
| stop, worker guard, first use, check-in (`stop_check.py`, `worker_guard*.py`, `first_use_check.py`, `session_checkin.sh`) | keep | hooks; no standard tool covers the stop and worker rules |
| check.sh, pre-push (`scripts/check.sh`, `scripts/git-hooks/pre-push`) | keep | the one front door of the checks; the hook runs the fast lane on each push |
| CI content step (`.github/workflows/`) | keep; fix for Dependabot | 6 of 6 Dependabot runs failed with no denylist secret (a setup error, not a defect) |
| settings reader (`check_settings*.py`), kit addresses (`kit_config.py`) | keep | the one reader of `.check` and of kit.config.json (one home) |
| skill use (`skill_use.py`) | keep until 2026-12-08 | the skill-use audit of P2 (j) reads it; decide at that audit |
| bootstrap (`bootstrap.sh`) | keep | first use of a new project; no standard tool fills the placeholders and the lock |
| page measure (`.claude/skills/verify/measure.mjs`) | keep | the verify skill's UI numbers (contrast, targets, scroll) |
| the audit skill (`.claude/skills/audit/SKILL.md`) | shrink the metrics, keep the procedure | 4 of its metrics are not measured or can be gamed (A4, A8, A9 and T2 in A1); proposals in the report |
