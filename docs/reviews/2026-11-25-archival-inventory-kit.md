# Archival phase 1: kit inventory

Written 2026-11-25 13:08 America/Chicago by the child session "Kit · Archival phase 1 inventory · 2026-11-25" for
"Kit · Fleet coordinator 4". Plan: `docs/reviews/2026-11-25-archival-plan.md` on branch
`claude/coordinator-4-handoff` (approved by the Maintainer 2026-11-25). Read only: this file and its CSV are the only
changes. Measured on main `e69d0ad`, full git history (the clone was shallow; `git fetch --unshallow` gave 957 commits
from 2026-11-11). Nothing was deleted. The retention schedule below is a **DRAFT** for the Maintainer's approval in
phase 2.

Per-file table (290 rows: path, class, bytes, added, last change, live and history references, what check reads it,
open plans that name it, candidate, links from kept files): [2026-11-25-archival-inventory-kit.csv](2026-11-25-archival-inventory-kit.csv).

## Method

- Scope: every tracked file under docs/, .claude/, scripts/, and AGENTS.md, CLAUDE.md, README.md, PREFERENCES.md,
  SECURITY.md, .check, kit.config.json, KIT_VERSION.
- References: a regex search of each file's path, basename (folder name for SKILL.md and README.md), and, for .py, its
  `import` name, across all tracked text files. "Live" = from a file outside docs/reviews/, docs/LOG.md,
  docs/DECISIONS.md and docs/CHANGELOG.md; "history" = from those. Comments count as references (conservative).
- A check reads it: named by a non-test file under scripts/, .github/workflows/, .claude/settings.json, .check,
  .check.state.json or kit.config.json; a `rule-conflict-check:` or `debt-check:` record (read by
  `scripts/bloat_check_rules.py` `conflict_recorded`); `docs/reviews/*-coverage.md` (run by `scripts/check.sh` line 544);
  and the fixed paths DECISIONS.md, LOG.md, NEXT_PROMPT.md, tools.md.
- Open plans: every `docs/reviews/*-plan.md` counts as open unless evidence closes it, plus KIT_HANDOFF.md,
  NEXT_PROMPT.md, the tool-retirement coverage list and the archival plan. Closed with evidence: kit-3.2.0 (CHANGELOG
  3.2.0), session-names (CHANGELOG 4.0.0), skill-use (CHANGELOG 6.0.0, 9 of 9 boxes). 10 plan files count as open.
- Candidate = 0 live references, no check reads it, no open plan names it, and not itself an open plan.
- Limits: the reference search is text only (a computed path is missed); the inventory script is not committed (scratch).

## Baselines (2026-11-25, this container)

| Metric | Value | Command or source |
|---|---|---|
| Tracked files / bytes (whole repo) | 301 / 2,785,052 | `git ls-files \| wc -l`; `git ls-files -z \| xargs -0 cat \| wc -c` |
| In scope: files / bytes | 290 / 2,775,125 | the CSV |
| docs/reviews/: files / bytes | 160 / 962,133 (55% of in-scope files, 35% of bytes) | the CSV |
| Session-load tokens | ~5,484 (cap 5,500; warning 5,000) | `scripts/session_checkin.sh` bloat line |
| T2 script lines / files | 20,621 / 72 | `cat scripts/*.py scripts/*.sh \| wc -l` (= `.check.state.json` baseline) |
| Check-in time | 1.4, 0.9, 1.1 s (n=3; baseline 0.6 s) | `scripts/session_checkin.sh`, wall time |
| Full lane time | 25.4 s wall (n=1; baseline 4.2 s) | `scripts/check.sh`; CHECK PASS 33 passed, 4 skipped, of 37 |
| `bloat_check.py --brief` | 0.32 s (baseline 0.1 s) | wall time |
| Audit time | not recorded as a number; last fleet audit 2026-11-13 (`.check.state.json` "audit") | - |
| Review pace | 162 review files added since 2026-11-11; commits touching reviews: 61 on 11-23, 32 on 11-24, 17 on 11-25 | `git log --diff-filter=A -- docs/reviews` |

The full-lane baseline (4.2 s) is far under this run (25.4 s); `cli_tests self-test` (25.2 s) is not in the baseline
steps. Not diagnosed here (out of scope; the check prints the `.claude/skills/audit/SKILL.md` "A slow run" line).

## Candidate classes

Savings are tree bytes and file count only: archiving review files saves **0** session-load tokens and **0** T2 lines
(neither counts docs/reviews/).

| # | Class | Files | Bytes | State | Links to rewrite in kept files |
|---|---|---|---|---|---|
| 1 | Tool-retirement program: `2026-11-23-t*` (plan, research plan, coverage, handoff, prompt, 9 `tr-*` worker reports) | 14 | 427,764 | **Not free:** the plan is open (KIT_HANDOFF "Approved plan" with a `[~` item; coverage list has 1 `later` row; check.sh runs the coverage list) | archive when the plan closes; the `tr-*` reports alone are 350,242 B |
| 2 | Fleet audit 2026-11-24: per-repo reports (`fleet-audit-{kit,icf,33-332,90-161,rade}.md`) | 5 | 192,400 | **Not free:** the parent report is open (KIT_HANDOFF "Open": A1-A9, A12-A14) | 5 (from `2026-11-24-fleet-audit.md`) |
| 3 | Closed plans and finished one-off reviews (table below) | 13 | 71,712 | Free now | 15 (DECISIONS, LOG, CHANGELOG rows and 3 review files) |
| 4 | Skill-test fixtures `2026-11-20-skill-tests/` (folder) | 81 | 27,245 | Free now (28% of the in-scope file count) | 1-3 (skill-use plan, fleet-audit-kit, fleet-audit) |
| 5 | Port notes `2026-11-18-port-notes/` (folder) | 3 | 11,102 | Free now | 2 (DECISIONS.md, fleet-audit.md) |
| 6 | Conflict and debt records (`rule-conflict-check:` / `debt-check:` lines) | 23 | 60,374 | **Read by a check** (the gate searches all of docs/reviews/) | phase 3: decide whether the gate needs records for merged hashes |
| 7 | History docs DECISIONS.md / LOG.md / CHANGELOG.md | 3 | 168,080 | Keep (checks read them; condensing DECISIONS is out of the plan) | - |

Free now (classes 3-5): **97 files, 110,059 bytes** (4.0% of in-scope bytes, 33% of in-scope files). After the two
open items close (classes 1-2): **+19 files, 620,164 bytes**, total 116 files and 730,223 bytes (26% of bytes).

Class 3, one row per file:

| File (docs/reviews/) | Bytes | Kept files that link it |
|---|---|---|
| 2026-11-18-kit-3.2.0-plan.md | 4,184 | DECISIONS.md, LOG.md |
| 2026-11-18-rule-tests-lean.md | 3,789 | LOG.md |
| 2026-11-19-session-names-plan.md | 3,327 | DECISIONS.md |
| 2026-11-20-content-check-speed.md | 3,972 | CHANGELOG.md, LOG.md |
| 2026-11-20-skill-use-analysis.md | 8,911 | 2026-11-23-skill-use-audit.md, CHANGELOG.md, LOG.md |
| 2026-11-20-skill-use-plan.md | 13,495 | 2026-11-20-rule-conflict-skills.md, DECISIONS.md |
| 2026-11-21-fresh-reader.md | 1,998 | - |
| 2026-11-21-instructions-rule-reviews.md | 5,384 | - |
| 2026-11-21-token-log-and-delegation.md | 4,559 | - |
| 2026-11-23-fleet-v2-session-briefs.md | 11,812 | 2026-11-23-fleet-v2-coordinator-state.md |
| 2026-11-23-fleet-v2-step3-rules.md | 4,484 | 2026-11-23-fleet-v2-coordinator-state.md, 2026-11-23-tool-retirement-prompt.md |
| 2026-11-23-p2-aud5-records.md | 2,787 | - |
| 2026-11-23-p2-shellcheck-debt.md | 3,010 (no `debt-check:` line, so the gate does not read it) | DECISIONS.md |

Not candidates (every file has a live reference, a check that reads it, or an open plan): scripts (74), skills (12),
.claude config (5), docs other than reviews (21; `docs/account-skills/` is linked from docs/FILES.md), doc assets (5;
`social-preview.png` 121 KB and `core-mark.svg` 61 KB are linked), instruction files (8).

## Code (scripts/)

Tools in a scratch venv (not a repo dependency): vulture 2.16, coverage 7.17.5, ruff 0.17.6.

- **Coverage** over one `scripts/check.sh` full run (subprocesses traced; CHECK PASS): 10,258 statements, **94%**.
  Most of it comes from self-tests, so it shows "tested", not "used". Under 80%: `kit_package.py` 0% (the kit
  package; fleet repos run it in package mode, so not a kit-only candidate), `check_content.py` 57%,
  `sync_baseline_repo.py` 72%, `skill_use.py` 79%.
- **ruff F401/F841** (6): `timeline.py:27` unused `import json`; `token_log_test_parts.py:21` unused `tool_result`;
  `token_log_test_parts.py:346` unused `root`; `check_settings_test.py:24` unused `audit_from_old`;
  `bloat_check.py:100` `import bloat_check_files` (used for its side effect per the comment; verify);
  `check_content.py:110` `warn_mode` (re-export; verify).
- **vulture** (12 at 60%+): 9 false positives (unittest classes `*Cli`/`ApplyOwner`, HTMLParser `handle_*` methods,
  shlex `whitespace_split`); real: `bloat_check.py:310` unused `s_lines`, `code_standard_test.py:115` `if True:`.
- Savings: under 10 lines of T2. No dead script file found: each of the 74 has a live reference and a check that runs it.

## Rules and skills: triggers in 30 days

The 30-day window cannot be observed: the history starts 2026-11-11 (14 days). Sources reached and not reached:

| Source | Reached | Result |
|---|---|---|
| `.claude/rule-tests.md` + run records (`2026-11-13-rule-tests.md`, `2026-11-18-rule-tests-lean.md`) | yes | 36 scenarios; **16 with no recorded run**: 6, 13-20, 29, 30, 32-36 (scenario numbers may have shifted since 11-18) |
| `python3 scripts/bloat_check.py --lint` | yes | 0 flags in 29 rule lines (no untested rule label) |
| Skill-use audits 2026-11-20 (12 sessions) and 2026-11-23 (7 sessions, 90 logs) | yes (as reports) | 0 full loads: **handoff** (4 slices), **data-change** (0/0), personal-data (4 slices), project-log (1 after the count); account skills **turn-summary 0, ship 0** |
| This session's log (`scripts/skill_use.py`) | yes | 0 skill loads, 1 slice (audit) |
| Token log repo `rhope-ops/token-logs` | **no**: `add_repo` (read) was denied by the permission classifier | - |
| Other sessions' transcripts | **no**: `list_events` returns inline and is not saved to files (the 2026-11-23 audit, method 2) | - |

No rule or skill is a removal candidate on this data: a skill with 0 loads in 2 samples (handoff, data-change) also
has rules that name it. The 2026-11-23 audit's P4 already plans the measured re-run (due 2026-12-08, KIT_HANDOFF).

## Retention schedule (approved by the Maintainer, 2026-11-25, as written)

| File class | Rule | Reason | Exceptions |
|---|---|---|---|
| Plan file (`*-plan.md`) | Archive 7 days after it closes (release row in CHANGELOG, or every step checked and KIT_HANDOFF no longer lists it) | DECISIONS rows keep the decisions; git keeps the text | a plan that a kept DECISIONS row quotes as its source: rewrite the link to the index row |
| Plan evidence (worker reports, coverage list, briefs, prompts, plan handoff) | Archive with its plan | evidence of a closed plan | a coverage list stays while check.sh runs it |
| Audit reports (per-repo and parent) | Archive when the parent's open questions close, or at the next audit of the same scope | the next audit replaces it | the last audit named in `.check.state.json` "audit" |
| Test fixtures and one-off notes (folders) | Archive 14 days after they are added, unless a live file links them | used once | - |
| Conflict and debt records | Keep until phase 3 decides whether the gate needs records for merged hashes | a check reads them | - |
| Handoff archives (`*-kit-handoff-archive.md`) | Keep the newest; archive the older ones | KIT_HANDOFF links the newest | - |
| DECISIONS, LOG, CHANGELOG, scripts, skills, instruction files, docs outside reviews | Keep | live or read by checks | - |

## ARCHIVE DUE thresholds (approved by the Maintainer, 2026-11-25, as written)

From the pace (162 review files in 14 days, about 12 a day; 960 KB of reviews):

- `ARCHIVE DUE` when the archivable set (closed per the schedule above, and the candidate test of this report) reaches
  **20 files or 200 KB**, whichever comes first. Today: 97 files and 110 KB are free, so the line would print now.
- Also when docs/reviews/ passes **200 files or 1 MB** in total (today 160 files and 962 KB), to catch plans that
  stay open.

## Blocks and open points

- `add_repo rhope-ops/token-logs` (read): denied by the permission classifier. Not run another way. Unblocks: the
  Maintainer allows it, or attaches the repo to the session.
- Session transcripts of other sessions: no file export (see the 2026-11-23 audit, method 2).
- For phase 2: whether the conflict-check gate needs records for hashes already on main (class 6, 60 KB);
  `fleet-audit.md` open questions (class 2, 192 KB); the tool-retirement plan close (class 1, 428 KB).
