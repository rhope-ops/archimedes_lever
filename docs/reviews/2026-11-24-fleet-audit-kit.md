# Kit audit measurements, 2026-11-24 (read only)

Repo: rhope-ops/archimedes_lever, detached at 6a4b727 (KIT_VERSION 11.0.1). Machine: 4 cores (`nproc` = 4), Linux 6.18 container, python 3.13 (pycache cpython-313). No file in the repo was edited; the only side effect is untracked `scripts/__pycache__/` made by my runs (gitignored? not checked; remove-free).
Scratch scripts (session scratch folder, not kept): kit-work/ (inv.py, dead.py, refs.py, same.py, def.py, census.py, links.py, steps.sh, tt.py; raw check output check1.txt, serial.txt, steps.out).
Caveat on all times: shared container; the same step varied up to 2x between runs (bootstrap_cli_test 18.3 s alone, then 9.7 s under cProfile). Treat times as +-2x; the audit skill asks for the median of 3 only for baselines, which I did not record.
Not measured (reason): Actions minutes (no network, no gh); skill use (no `list_events`, no session records here); mutation kill rate (no tool).

## 1. Step 1: inventory and baseline

### 1.1 Commands and output

`python3 scripts/bloat_check.py --time` (no --record):
- session load: 18,630 bytes, ~4,657 tokens (cap 5,500). AGENTS.md 15,770 B; skill and agent descriptions 2,282 B; docs/NEXT_PROMPT.md 567 B; CLAUDE.md 11 B.
- rules: AGENTS.md 73 lines (cap 200); 28 rule bullets; Project rules 1.
- handoff: docs/NEXT_PROMPT.md 24 lines (budget 40).
- duplicates: 56 lines of 80+ chars in 2+ files (budget 20). Groups: 5 files x 5 lines (cli test helpers: `run`, `py`, `sync` docstring, `sync_baseline` call, `--timezone` args) = the main body; 4 files x 1 (cli test header); 3 files (LOG.md, templates/LOG.md, log_check.py: table header); 3 skill-test grader files (measure.mjs text); bloat_check.py/check_lock.py/check_settings.py argparse line; skills/instructions/SKILL.md vs check_instructions_test.py.
- big files: 0 over 500 KB.
- timings: bloat-brief 0.5 s (baseline 0.1) SLOWER; check 58.9 s (baseline 4.2) SLOWER; checkin 1.0 s (baseline 0.6) SLOWER. Over budget: duplicates, timing bloat-brief, check, checkin.
- "audit not due"; "AUDIT DUE (fleet: no fleet.last_audit date in kit.config.json)".

`python3 scripts/bloat_check.py --rules`: AGENTS.md 73 lines, ~4,657 tokens, 28 rule bullets, Project rules 1; scripts 19,228 lines in scripts/*.py and *.sh (baseline 19,228); RULES PASS.
`python3 scripts/bloat_check.py --lint`: `LINT: 0 flag(s) in 29 rule lines (warn only)`. Flags: near-duplicate 0, vague 0, untested 0.
`python3 scripts/bloat_check.py --skills`: WARN audit/SKILL.md 151 lines (over 150); WARN deliver/SKILL.md description does not start with "Use when" or "Use before"; `SKILLS PASS: 11 skills, 2 warnings`.
`nproc`: 4.

### 1.2 `scripts/check.sh` runs

| Run | Command | Result line |
|---|---|---|
| full, parallel (as the hook and CI run it) | `scripts/check.sh` | `TIME  full lane 64.2 s wall; slowest: cli_tests self-test 64.0 s, code_standard self-test 34.6 s, check_content self-test 34.3 s`; `CHECK PASS: 33 passed, 3 skipped, of 36` |
| full, serial | `CHECK_SERIAL=1 scripts/check.sh` | `TIME  full lane 108.2 s wall; slowest: cli_tests self-test 40.6 s, code_standard self-test 15.2 s, check_content self-test 15.0 s`; `CHECK PASS: 33 passed, 3 skipped, of 36` |
| fast (no change vs origin/main in my tree) | `scripts/check.sh --fast` | `TIME  fast lane 1.7 s wall; slowest: code standard 1.1 s, content check 0.5 s, rule caps and pointers 0.4 s`; `CHECK PASS: 9 passed, 4 skipped, of 13` |

The 3 SKIPs of the full lane: python lint (ruff or pylint missing), shellcheck (missing), project checks (no check.local.sh). So the lint steps were not run here: unmeasured.
Baseline compare line (WARN, never fails): `check 64.2 s (baseline 4.2 s, +1429%)` and 15 steps over baseline. The baseline in `.check.state.json` is from a lane with 14 timed steps; the lane now has 36 (33 run). The baseline is stale, not a measured regression of one step (serial run: stop_check 4.5 s vs 1.6 s baseline, check_content 15.0 vs 4.1, check.sh self-test 10.3 vs 3.2).
Last audit baseline (docs/reviews/2026-11-13-bloat-audit.md): check 2.9 s -> 3.0 s, start read 3,740 -> 3,799 tokens, 37 -> 39 files / 246 -> 255 KB. Now: 64.2 s (x21), 4,657 tokens (+24% vs 3,740), 283 files / 2.39 MB (x7.3 files, x9.4 size) in 11 days.

### 1.3 Session load per start-read file (bytes / 4; `python3 inv.py`, `bloat_check --time`)

| File | Bytes | ~Tokens | Counted by bloat_check |
|---|---|---|---|
| AGENTS.md | 15,770 | 3,942 | yes |
| skill + agent descriptions (11 skills, 3 agents) | 2,282 | 570 | yes |
| docs/NEXT_PROMPT.md (the unfilled template) | 567 | 141 | yes |
| CLAUDE.md | 11 | 2 | yes |
| **bloat_check total** | 18,630 | **4,657** | |
| docs/KIT_HANDOFF.md (the kit's real handoff, AGENTS.md:17) | 6,114 | 1,528 | **no** |
| SessionStart output: first_use_check.py 719 B + session_checkin.sh 1,149 B (`| wc -c`) | 1,868 | 467 | no (hook output; skill says to count it) |
| .claude/settings.json (not read into context) | 3,727 | 931 | no |
Not start-read in the kit: docs/DECISIONS.md 76,175 B (19,043 tokens; no start-read file tells agents to read it: AGENTS.md:19 says "on demand, not at start"), PREFERENCES.md 21,549 B, README.md 26,948 B, docs/LOG.md 42,677 B.
Finding (drift, see 2.2 item 2): with KIT_HANDOFF.md the kit's load is ~4,657 - 141 + 1,528 = ~6,044 tokens, over the 5,500 cap, and the skill (audit Step 1.4) says to count the handoff. Command: arithmetic on the sizes above; `grep -n "NEXT_PROMPT\|KIT_HANDOFF" scripts/bloat_check*.py` shows START_READ = AGENTS.md, CLAUDE.md, docs/NEXT_PROMPT.md at scripts/bloat_check_rules.py:30 and the handoff read at scripts/bloat_check.py:311; KIT_HANDOFF appears in no bloat_check code.

### 1.4 Tracked files

`git ls-files | wc -l` = 283 files, 2,388,352 bytes (2.28 MiB). By folder (`inv.py`): scripts 72 files 1,053,806 B; docs/reviews 145 files 698,586 B; docs (rest) 31 files 460,867 B; .claude 17 files 100,143 B; root 15 files 70,126 B; .github 3 files 4,824 B.
Largest: docs/assets/social-preview.png 121,262 B; docs/DECISIONS.md 76,175; docs/reviews/2026-11-23-tr-r2a-project-tools.md 73,487; tr-wb-scanners 64,641; docs/assets/core-mark.svg 61,252; tr-wd-standard-replacements 56,155; docs/LOG.md 42,677; tr-r4e-ion-benchmark 42,615; tr-wa-linters 42,092; tool-retirement-plan 41,926; scripts/check.sh 39,373 (533 lines); tr-r2b-kit10-repos 33,387.
Tool-retirement files (14 files `docs/reviews/2026-11-23-tr-*` and `tool-retirement*`): 427,764 B = 17.9% of all tracked bytes, all created 2026-11-23.
Last change: all files changed within the last 14 days (repo history starts 2026-11-10/11), so "no change in 90+ days" matches 0 files.
Files with no reference from any other tracked file (basename or stem match, `python3 inv.py`): 71, all in docs/reviews:
- 62 of them are single-line grader files in `docs/reviews/2026-11-20-skill-tests/*/*/graders/NN-*.md` (81 files, 27,245 B in that folder in total; the 19 that are referenced are the other files).
- 9 review files: 2026-11-16-rule-conflict-3.md, 2026-11-18-rule-conflict-2.0.0.md, 2026-11-18-rule-conflict-3.0.0.md, 2026-11-20-rule-conflict-skills.md, 2026-11-21-fresh-reader.md, 2026-11-21-instructions-rule-reviews.md, 2026-11-21-rule-conflict-scout-narrow.md, 2026-11-21-token-log-and-delegation.md, 2026-11-23-p2-aud5-records.md.
Caveat: AGENTS.md "Rules for the auditor" says no caller does not prove unused; graders are read by the skill-test runner by folder, not by name. No file outside docs/reviews is unreferenced.

## 2. Rule census (Step 2 item 14)

Command: `python3 census.py` (per bullet: log mentions in docs/LOG.md, rows in docs/DECISIONS.md, review files naming `"<label>"`, rule-tests scenarios naming the label) plus a read of the text and of docs/reviews/2026-11-18-rule-tests-lean.md, docs/LOG.md rows 34-79.
Bullets: Hard rules 8, Defaults 20, Project rules 1 = 29 (bloat_check counts 28 + 1; `--lint` sees 29 lines). Last audit count: the 2026-11-13 report gives no bullet count; CHANGELOG 2026.11.19 says "28 rule bullets", so 28 -> 28 (+1 project rule).
Rule-test record: only 2 runs, docs/reviews/2026-11-13-rule-tests.md and 2026-11-18-rule-tests-lean.md (10 pass, 1 not valid; scenario 22 unfixed per its "To do"; scenarios 1-20 not rerun in fresh top-level sessions). Kit rule text changed since (11.0.0, 10.0.0 "Instructions people follow", "Fleet choices"). A pass there shows the text can produce the behavior, not that the rule changed an outcome.

| # | Section | Label (AGENTS.md line) | Chars | Class | Evidence |
|---|---|---|---|---|---|
| 1 | Hard | Git history (25) | 660 | enforced | scripts/git-hooks/pre-push, deny rules in .claude/settings.json (34 deny entries), `check_blocks.py --settings` (check.sh:433); LOG #45, #59 |
| 2 | Hard | Secrets and personal data (26) | 760 | enforced | check_content.py in pre-push and PreToolUse hook (settings.json), check.sh:469 "content check" |
| 3 | Hard | Guards and checks (27) | 608 | enforced in part | `.check.lock` + check_lock.py --verify (project only; the kit has no lock), check_blocks --settings; LOG #77 (two workers worked around a guard) |
| 4 | Hard | Untrusted input (28) | 354 | evidence | rule-tests scenario 3 / 25: 2026-11-18 pass; LOG #? mention 1; no hook |
| 5 | Hard | The Maintainer's approval (29) | 360 | evidence | LOG #74 (fix opened without checking the approval), DECISIONS approval-quote check `log_check.py --decisions` (check.sh:453) covers decision rows only |
| 6 | Hard | True reports (30) | 183 | no evidence | 0 log rows, 0 decision rows; scenario 8 not in the 2026-11-18 run |
| 7 | Hard | Instructions people follow (31) | 882 | enforced | check_instructions.py (check.sh:480, PreToolUse hook on Write/Edit), 4 DECISIONS rows |
| 8 | Hard | Rule text (32) | 374 | enforced in part | `bloat_check --rules --gate` (check.sh:428), `log_check --decisions`; LOG #42; 7 review files |
| 9 | Default | Start of session (38) | 451 | enforced | SessionStart hook first_use_check.py + session_checkin.sh |
| 10 | Default | Decisions (39) | 656 | evidence | LOG #42; scenarios 2, 26 pass 2026-11-18; 2 DECISIONS rows |
| 11 | Default | Assumptions (40) | 198 | no evidence | 0 log, 0 decision rows, 0 review files; scenario 7 not in the 2026-11-18 run |
| 12 | Default | Maintainer changes (41) | 428 | evidence | scenario 12 pass 2026-11-18; 1 DECISIONS row |
| 13 | Default | Delivery (42) | 942 | procedure (skill deliver) + evidence | LOG #34, #38 (merged unseen commits), 9 DECISIONS rows; longest rule |
| 14 | Default | Checks (43) | 393 | enforced | pre-push `--cached` stamp, check.sh |
| 15 | Default | Fresh review (44) | 563 | evidence | LOG #34, #38; 6 review files |
| 16 | Default | Verification (45) | 275 | procedure (skill verify) | pointer to two skills |
| 17 | Default | Skills (46) | 392 | evidence | LOG #66 (4 Skill calls in 12 sessions) |
| 18 | Default | Reporting (47) | 463 | evidence (weak) | LOG #54; 3 DECISIONS rows |
| 19 | Default | Handoff (48) | 536 | procedure (skill handoff) + enforced cap | `bloat_check` handoff budget (40 lines), fleet_harvest --check |
| 20 | Default | One home (49) | 488 | enforced in part | bloat_check duplicates (56 vs budget 20: over) |
| 21 | Default | Lean instructions (50) | 398 | enforced | bloat_check caps (200 lines, 5,500 tokens), `--lint`; LOG #44 |
| 22 | Default | Caps and audit (52) | 656 | enforced | `bloat_check --rules`, check.sh:428-430; 7 DECISIONS rows |
| 23 | Default | Project log (53) | 397 | enforced + procedure | log_check.py (check.sh:444), skill project-log |
| 24 | Default | Agents (54) | 147 | procedure (pointer to skill delegate) | pointer only |
| 25 | Default | Delegation (56) | 472 | evidence | LOG #? 2 mentions, 7 DECISIONS rows |
| 26 | Default | Unattended work (57) | 199 | no evidence | 0 log, 0 decision rows (DECISIONS 2026-11-16 keeps it as a line), scenario 30 not run |
| 27 | Default | Access (58) | 358 | no evidence of change | scenario 31 pass 2026-11-18 (text can produce it); 0 log, 0 decision rows; model does a minimal dependency without the rule: candidate |
| 28 | Default | Kit files (59) | 463 | enforced | check_lock.py, `.check.lock`, drift.py |
| 29 | Project | Fleet choices (73) | 235 | no evidence | 0 log rows; DECISIONS 2026-11-19 row (line 52) is the hub decision, not this rule; scenario 34 never run |

Counts per class (one primary class per rule; mixed rules take the first class named in the table):
- enforced by a hook or test: 9 (rows 1, 2, 7, 9, 14, 21, 22, 23, 28).
- enforced in part (a pointer fits only the enforced half): 3 (rows 3, 8, 20).
- a procedure (a skill holds the steps): 4 (rows 13, 16, 19, 24).
- model does it without the rule: 0 proven (no "before" run exists; rule-tests-lean.md says "no before run on the old rules"); candidate row 27 (Access), counted under no evidence.
- evidence it changed an outcome: 8 (rows 4, 5, 10, 12, 15, 17, 18, 25; row 18 weak).
- no evidence: 5 (rows 6, 11, 26, 27, 29).
Sum: 9 + 3 + 4 + 0 + 8 + 5 = 29.
Limits of the evidence column: "LOG #n" is a row number in docs/LOG.md; "log=0" counts the label text in LOG.md, DECISIONS.md and review files only, so a rule that shaped work without being named there shows as no evidence (a false negative is possible). Row 4 cites rule-tests only: LOG.md has 1 text mention of the label, row number not read.
Candidate actions with trade-offs: (a) rows 6, 11, 26, 27, 29: retire, or keep with a review date; retiring a Hard rule (6) needs the Maintainer's text approval (AGENTS.md "Rule text"); the 2026-11-16 DECISIONS row chose to keep Unattended work as a line. (b) rows 3, 8, 20: shorten each to a pointer plus the unenforced half; saves ~150 tokens in total, risk: the guard-file clause is the part nothing enforces. (c) No rule shortens without the Maintainer's approval of the exact text.

## 3. Step 2 items 1-21

### Item 1 Duplication
| What | Where | Evidence | Cost | Candidate fix | Risk |
|---|---|---|---|---|---|
| cli-test helpers `run`, `py`, `new_repo`, `sync` copied in 5 files | scripts/bootstrap_cli_test.py:26-45, check_lock_cli_test.py:33, drift_cli_test.py:32, sync_baseline_cli_test.py:36, sync_merge_cli_test.py:35 | bloat `--time`: 56 duplicate lines (budget 20); `same.py`: `new_repo` and `sync` bodies equal in 5 files each | ~30 lines x 5; budget exceeded by 36 lines | one shared `cli_test_support.py` imported by the 5; | the self-test split was made for the 450-line cap (LOG #76); a shared module is a new file (needs a docs/tools.md row, check.sh deps list) |
| Two script inventories | docs/FILES.md (76 lines; basenames missing for 9 of 70 scripts: bloat_check_files.py, bootstrap_cli_test.py, check_blocks.py, check_lock.py, check_lock_cli_test.py, check_settings_test.py, drift_cli_test.py, sync_baseline_cli_test.py, sync_merge_cli_test.py) and docs/tools.md (150 lines, 0 missing) | python check in 1.4 session | two homes for "what each script does" (AGENTS.md "One home") | merge into one; tools.md carries lines/callers/candidates and is research input (its own line 4) | tools.md is the retirement plan's input and bootstrap deletes it; FILES.md is synced to projects |
| pip pins of ruff/pylint/shellcheck-py in 3 places | scripts/check.sh:163,166,406,423; .github/workflows/check.yml:24; ruff.toml:2 | `grep -rn "ruff==0.17.6"` | version change = 4 edits in 3 files | one pins file read by both | check.sh and the workflow are guard files (Maintainer's request only) |
| 3 kit-skill table headers / log header in 3 files | docs/LOG.md, docs/templates/LOG.md, scripts/log_check.py | bloat duplicates group | 1 line x 3 | none needed (template and checker must match) | low |
| 62 one-line grader files | docs/reviews/2026-11-20-skill-tests/*/graders | 62 unreferenced files, 8 duplicate lines "kit measure script passes" x3 | 27 KB, 81 files | one table per scenario | graders are input of a skill test runner not in the repo (unknown) |

### Item 2 Drift
| What | Where | Evidence | Cost | Fix | Risk |
|---|---|---|---|---|---|
| KIT_HANDOFF says kit 10.0.0, fleet on 10.0.0, "after 10.0.0 the highest is ~5,352" | docs/KIT_HANDOFF.md:10, :38 vs KIT_VERSION = 11.0.1, docs/CHANGELOG.md:7-8 (11.0.0 and 11.0.1 exist) | `cat KIT_VERSION` | a session reads the wrong state; handoff 6,114 B | update by the owner of the handoff (not by this audit) | handoff is a status file |
| Session-load measure skips the kit's own handoff | AGENTS.md:17 names docs/KIT_HANDOFF.md; scripts/bloat_check_rules.py:30 START_READ has docs/NEXT_PROMPT.md only | 4,657 reported vs ~6,044 with the handoff (1.3) | cap 5,500 reported as 85% used; real use 110% | count `docs/KIT_HANDOFF.md` when it exists, or shrink the handoff to <= ~600 B... (needs the Maintainer: either option changes a cap meaning) | guard script change = Maintainer's request |
| tools.md totals stale | docs/tools.md:31 "66 files 17,361 lines" vs 70 files 19,228 lines (`.check.state.json` script_lines) | state file | the T2 ratchet baseline candidate (line 33) differs from the real baseline | re-measure | none |
| Timing baselines | .check.state.json timings.check 4.2 s (14 steps) vs 64.2 s (36 steps) | check.sh WARN line | the WARN line is always on, so a real regression would not stand out | re-record 3 runs (audit skill "Record a baseline"); a slower baseline needs the Maintainer | needs approval |
| fleet.last_audit missing | kit.config.json (3 keys) vs bloat `--time` "AUDIT DUE (fleet...)" | output | fleet audit not tracked | audit skill: write the date after this audit | none |
| Last audit commit not in this clone | .check.state.json audit.last_audit.commit eab8b98: `git rev-list eab8b98..HEAD` = "Invalid revision" | the "300 commits" due test cannot be computed here (HEAD has 757 commits) | audit due date uses the date only | none |

### Item 3 Dead code (code references only)
Commands: `dead.py` (AST: every def/class/module constant, 1,137 names in scripts/*.py, word count across scripts/*.py, *.sh, hooks, workflows, settings.json); `refs.py` (each script: callers among scripts, hook, workflows, settings, skills, agents).
- Names used once (definition only): 78, all false positives: unittest test classes and `test_*` methods (73 in *_cli_test.py and *_test.py: found by discovery) and 3 `HTMLParser` overrides (`handle_starttag`, `handle_endtag`, `handle_data`, scripts/check_instructions_steps.py:150,174,191). So: **0 dead functions, classes or constants** in non-test code by name count.
- Defined in non-test code and referenced only from a test: 1: `scripts/bloat_check.py:110 DEFAULTS = check_settings.AUDIT_DEFAULTS`; only user is scripts/bloat_check_test.py:328. Cost 1 line. Fix: test reads `check_settings.AUDIT_DEFAULTS`. Risk: none.
- Scripts with no caller other than a test or doc: 0 (every script has a caller in check.sh, a hook, a workflow, settings.json, another script, or a skill). Command: `refs.py`, no row flagged.
- Scripts whose only repo caller is check.sh's self-test line: `scripts/token_log.py` and its 4 parts (`rg token_log` in .claude/settings.json = 0). By docs/FILES.md:58 the cloud setup script installs it from main (outside the repo): "nothing calls it" would be wrong. Cost: 5 files 1,426 lines; `token_log self-test` 9.5 s alone (of ~120 s serial). Candidate: the tool-retirement plan family "Token log" (docs/tools.md:26) already lists it.
- Flags: `bloat_check.py` has 10 flags; all appear in docs or check.sh (--strict, --brief, --record used by skills). Not exhaustively measured for other scripts.
- Shell: no function in check.sh unused (`on_main`, `touched`, `extension`, `selftest`, `skip`, `run`, `clean`, `now`, `secs` each called; read of scripts/check.sh).

### Item 4 Stale docs
- docs/KIT_HANDOFF.md:10, :38 (kit 10.0.0); "Open" list items from plans of 2026-11-18/20/21 (lines ~22-31: "Plan 2026-11-20 done", tags v4.1.0/v5.0.0/v5.0.1 not made yet, kit branches to delete). 38 lines but longest line 1,063 chars; 6,114 B. Candidate: move done plans to docs/reviews, keep <= 15 lines.
- docs/tools.md:3 "Measured 2026-11-23 ~15:30 on kit main 641023e"; totals now off (see item 2).
- .claude/rule-tests.md scenario 22 flagged "not valid" on 2026-11-18, not fixed (rule-tests-lean.md "To do").
- Broken relative links: 0 of 91 (`links.py`, README, AGENTS, docs/*.md, docs/reviews, skills).
- TODO/FIXME > 30 days: 0 (grep over scripts, docs, .claude; the only hit is README.md:46 prose).
- docs/reviews: 63 top-level entries, 145 files, 698,586 B; none older than 90 days (history starts 2026-11-10); "superseded revisions": rule-conflict series (e.g. 2026-11-16-rule-conflict.md, -2, -3, -4; 2026-11-18-rule-conflict.md, -2, -2.0.0, -3.0.0): 12 files; candidate: single index (AGENTS.md audit item 16 says to archive after 90 days: not yet due).

### Item 5 Layered wrappers (call chains, times)
Times from `steps.out` (each step alone, serial, one run) and `check1.txt`.

Fast lane, a push of a branch (hook-run):
```
git push
 -> scripts/git-hooks/pre-push (bash; own_tree, check, check_identity: several git calls)   ~0.1 s est. (not isolated)
     -> bash scripts/check.sh --cached --fast --no-content     1.7 s wall (measured `--fast`)
         -> git rev-parse, merge-base, diff x3
         -> 9 parallel steps: code standard 1.1 s, rule caps 0.4 s, skills 0.1, deny 0.04, log 0.04,
            decisions 0.09, coverage 0.08, instructions 0.17 (+ content check skipped by --no-content)
         -> python3 scripts/bloat_check.py --compare ...   0.06 s
     -> python3 scripts/check_content.py --all --push --require-denylist   0.3 s (`--all`: 0.29 s)
     -> python3 scripts/bloat_check.py --compare push-guard=...   0.06 s
 -> chain to a pre-existing hook in .git/hooks
```
A full-lane push to main is the same with `check.sh --cached` (no --fast): cached when a full run passed on the same commit with a clean tree (check.sh:240-246), else 64.2 s.

Full lane (by hand before merge, CI, or main push):
```
scripts/check.sh (bash, 533 lines; 140 lines of it are its own self-test)
 -> 36 steps, all started in the background (4 cores):
    20 kit self-tests: python3 scripts/X.py --test (serial times: stop_check 2.0, worker_guard 0.2, log_check 0.1, check_settings 0.3,
       bloat_check 1.2, token_log 9.5, code_standard 18.7, code_standard_strict 0.8, timeline 0.1, check_content 16.1,
       check_instructions 0.5, skill_use 0.1, fleet_harvest 0.4, check_blocks 0.1, check_lock 0.3, fulcrum_palette 0.2,
       build_site 0.3, first_use_check 0.5, drift 2.3, kit_config 0.05)  = 54.0 s
    pre-push self-test 2.1 s, session_checkin self-test 0.7 s
    cli_tests: python3 -m unittest discover (5 files, 48 tests, each runs sync_baseline/bootstrap/drift/check_lock/sync_merge as subprocesses)  44.5 s
    check.sh self-test: bash scripts/check.sh --test (runs check.sh ~50 times in temp repos; inner CHECK_IN_TEST stops recursion)  13.9 s
    10 plain checks: code standard 0.7, rule caps --gate 0.2, skills 0.1, deny 0.04, project log 0.04, decisions 0.09,
       coverage 0.08, content 0.4, instructions 0.2   = ~1.9 s
 -> bloat_check.py --compare (0.06 s)
```
Sum of step times alone: ~120 s; serial run 108.2 s; parallel wall 64.2 s (cli_tests alone = the critical path: step wall 64.0 s while it takes 44.5 s alone; 36 processes on 4 cores).
Findings:
| What | Where | Evidence | Fix | Risk |
|---|---|---|---|---|
| Same check run twice by two tools | scripts/check.sh:395-396 (ruff E501 and pylint line-too-long on the same files) and :398-399 (ruff parse E9 and pylint syntax) | ruff.toml:4 `select = ["E9"]` only; pylint `--disable=all --enable=line-too-long` | keep one linter for parse and one for line length | not measured: both linters absent here (SKIP) |
| code_standard.py started 4 times per lane when the linters exist | check.sh:377 ("code standard", 0.7 s), :389 two calls (`--python-files all`, `--python-files line`), :413 `--shell-files` | 4 x 0.7 s alone; python start itself 0.014 s, so the cost is its file scan | one call writes all 3 lists | guard file |
| Self-test layering: check.sh self-test runs check.sh | check.sh:62-220 (158 lines, 40+ `ok` cases) | 13.9 s alone = 12% of serial time | keep (it proves the lane logic); but its fake kit scripts duplicate step logic | high if cut |
| `check_content` self-test also scans: content check (0.4 s) plus self-test 16.1 s plus pre-push re-scan `--all` (0.3 s) | check.sh:469, pre-push:236-244 | `--no-content` avoids the second scan inside the hook | already collapsed by `--no-content` | n/a |
| Config over config | `.check` -> check_settings.py -> `.check.state.json`; code-standard settings read by 4 scripts (check_settings*.py are listed as deps of 6 self-tests in check.sh:307-349) | dep list repeats `scripts/check_settings.py scripts/check_settings_read.py scripts/build_site_html.py scripts/check_content_scan_settings.py scripts/check_content_scan_words.py` in 7 selftest lines | one named dep group | `build_site_html.py` as a dep of settings tests is odd: not explained |

### Item 6 Performance (slowest operation = full lane, then its slowest step = cli_tests)
Top 3 costs of `cli_tests self-test` (`tt.py`, per-test timer, 48 tests, total 48.1 s, `python3 -m cProfile -m unittest` on bootstrap_cli_test):
1. `sync_baseline_cli_test.py`: 23.4 s alone for 25 tests (49% of the step); slowest test 1.96 s (`test_unchanged_older_kit_copy_is_no_stop`).
2. `bootstrap_cli_test.py`: 18.3 s alone (cold) / 9.7 s (warm) for 9 tests; top tests 3.30, 2.85, 2.84, 2.67, 2.64, 2.12 s. cProfile: 61 `subprocess.run` calls = 7.86 s of 9.74 s (81%); each test builds a kit copy (`kit_copy`: `git ls-files`, copy ~283 files, `git add -A`, commit) = ~0.65 s.
3. The three smaller files: check_lock 2.9 s, drift 2.2 s, sync_merge 2.4 s = 7.4 s, each repeating `new_repo` + `sync`.
Series work that shares no state (candidates for parallel): the 5 cli test files (shared nothing, own temp repos): in series inside one `unittest discover` process = 48 s; in parallel the longest is sync_baseline_cli_test (23.4 s). That would take the full lane's critical path from ~44.5 s (alone) toward ~23 s; with 36 steps on 4 cores total CPU is ~120 s / 4 = 30 s lower bound. Process starts: each step = 1 python3 or bash start (14 ms for `python3 -c pass`); the 48 cli tests start ~61 x 5 / 9 ... measured 61 subprocess runs in bootstrap alone; ~250 est. over 5 files (not measured).
Same step run per change: by hand full lane x1 (64.2 s) + pre-push on main `--cached` (0 s if stamp valid) + CI full lane x1 per PR (public repo) + fast lane per branch push (1.7 s each). The content scan runs `--all` in the by-hand full lane (0.4 s), in pre-push (0.3 s) and in CI (`--range`).
Hot spot already known: session-start hook cost: first_use_check 0.06 s, check-in 1.0 s.

### Item 7 Dependencies
- No requirements file, no package manifest. Third-party Python imports in scripts/*.py: 0 (AST walk of every Import/ImportFrom against `sys.stdlib_module_names` and the scripts' own module names).
- Pinned tools: ruff 0.17.6, pylint 4.1.4, shellcheck-py 0.9.0.6, bandit 1.9.4, gitleaks 8.30.1. Two linters for one job: ruff and pylint both do parse and line length (check.sh:395-399); ruff.toml selects only E9. Overlap secret scanning: gitleaks (security.yml:44) vs check_content secret finders (decision 9A, tool-retirement-plan.md:52 keeps gitleaks as the second net). bandit vs nothing.
- Vendored copies: docs/assets/core-mark.svg 61,252 B and social-preview.png 121,262 B are brand assets (generated? social-preview.png from social-preview.html: not verified).

### Item 8 Repository weight
2,388,352 B tracked, 0 files over 500 KB (bloat `--time`). Largest: social-preview.png 121 KB; DECISIONS.md 76 KB (grows 134 rows); tool-retirement files 428 KB (14 files). `.git` size not measured (a `git count-objects` form is blocked in my sandbox). No logs, no caches tracked (`find ... *.bak *~ *_old* *_v2* tmp* debug*` = 0 hits).

### Item 9 CI and automation
| Workflow | Event | Runs | Note |
|---|---|---|---|
| .github/workflows/check.yml ("checks") | pull_request (only when repo is public: `if:` at line 15), workflow_dispatch; never on push | 1 job: checkout (fetch-depth 0), `pip install ruff pylint shellcheck-py`, `scripts/check.sh` (full lane, content step skipped by GITHUB_ACTIONS), content check with PR base `.check` (`--range BASE..HEAD`) | the local full lane is the by-hand gate too: same 64 s run twice per PR. Runner time not measured (no gh) |
| .github/workflows/security.yml | pull_request, workflow_dispatch | 2 jobs: bandit (setup-python 3.12, pip install bandit==1.9.4, `bandit -r scripts/ -ll`), gitleaks (download 8.30.1 + checksum, `detect --no-git`) | 2 more runner starts per PR; gitleaks overlaps check_content (decision kept it) |
Per PR: 3 runner starts. Hooks (local): PreToolUse x2 (check.sh --hook 0.06 s on every Bash/Write/Edit/... call; check_instructions --hook 0.05 s on Write/Edit), Stop (stop_check 0.06 s), SessionStart (first_use_check 0.06 s). Pre-push as above. No scheduled workflows.
Candidate: drop check.yml's duplicate content step? (no: it uses base-branch settings on purpose, comment at check.yml:30-31). Risk high; guard files.

### Item 10 Process bloat
- Release tags by hand: v4.1.0, v5.0.0, v5.0.1, v8.1.0, v9.0.0 not made (docs/KIT_HANDOFF.md:7, 25-31); kit branches to delete by hand (`claude/content-check-speed`, `claude/kit-handoff-6-0-0`, KIT_HANDOFF "Needs the owner"). Candidate: a release script, or drop the old tags (Release Manager).
- Fleet sync: one PR per project per kit release (9 repos on 10.0.0; docs/CHANGELOG.md).
- docs/templates/ has 2 files (DECISIONS.md, LOG.md) both used; no always-empty section measured.

### Item 11 Tech-debt register: see section 6.

### Item 12 Instruction bloat
Command: `bloat_check --lint` = 0 flags (near-duplicate, vague, untested all 0) in 29 rule lines. AGENTS.md 15,770 B / 73 lines. Longest rules (chars): Delivery 942, Instructions people follow 882, Secrets 760, Git history 660, Caps and audit 656, Decisions 656. The Delivery line spans lanes A, B, C, host limit (5 sentences). Rules that already name their enforcement and could be pointers: Git history ("Enforced: ..." ~200 chars), Secrets (~320 chars of "Enforced"), Instructions people follow (~200 chars). Candidate: move "Enforced:" clauses to docs; saves ~700 B = ~175 tokens; risk: "A rule a hook enforces becomes a pointer" is already AGENTS.md:50; any change is proposal (instruction file, lane C).
`audit/SKILL.md` is 17,347 B (151 lines) and 3.8 times the average skill; loaded on audit and slow-run triggers.

### Item 13 Context cost
- Load per session ~4,657 tokens counted (85% of cap), ~6,044 with the kit handoff (1.3). Hook output ~467 tokens per session start (1,868 B). Skill descriptions 2,282 B (570 tokens).
- No start-read file imports DECISIONS.md (CLAUDE.md = `@AGENTS.md` only, 11 B). OK: AGENTS.md:19.
- Reference text in start-read: AGENTS.md has 2 lines marked `<!-- full -->` (52-55) that the starter tier drops.
- KIT_HANDOFF.md longest line 1,063 chars; 6,114 B; candidate trim to <= ~2 KB by moving done plans to docs/reviews.

### Item 14 Rule census: see section 2.

### Item 15 Cross-host duplication
Not measurable here: no access to the claude.ai Project, account preferences or memory. In repo: PREFERENCES.md (21,549 B) is the account text source (README.md:23); AGENTS.md:15 says personal preferences rank 3. docs/host-prompts.md is 10 lines. Overlap AGENTS.md vs PREFERENCES.md not measured by me: unmeasured.

### Item 16 Handoff and memory rot
docs/NEXT_PROMPT.md: 24 lines (template with {{...}}: kit uses KIT_HANDOFF). docs/KIT_HANDOFF.md: 38 lines (budget 40) but 6,114 B and 1,063-char lines; stale as in item 2. docs/reviews 63 entries; none older than 90 days; archive by index not due. Memory files: not accessible.

### Item 17 Agent-made helpers
`find` for `*_old*`, `*_v2*`, `*_new*`, `*.bak`, `*~`, `*.orig`, `tmp*`, `debug*`: 0 files. Wrappers by cap-splitting: 22 splits of the 450-line cap rated by a fresh reviewer: 11 cohesive, 9 mixed, 2 arbitrary (LOG #76). Suffix families: `bloat_check*` 7 files, `check_content*` 9 files, `code_standard*` 10, `token_log*` 5; 21 `*_test*` files = 5,954 of 19,228 script lines (31%).

### Item 18 Defensive layering in scripts/*.py (AST, non-test files, `def.py`)
- 117 `try` blocks, 116 handlers; 19 handlers catch `Exception`/`BaseException`/bare (all Exception or BaseException; 0 bare `except:`); 48 handlers are "silent" (body only `pass`, `continue` or `return` of a constant/empty container).
- Broad AND silent: 3: scripts/first_use_check.py:145 (`except Exception` -> `return ""`, comment says Windows pipe), scripts/sync_merge.py:226 (`except Exception: return False` around `zoneinfo.ZoneInfo(name)`; narrower `ZoneInfoNotFoundError, ValueError, ImportError` would do), scripts/sync_baseline_repo.py:104 (`except Exception` around `zoneinfo.ZoneInfo(zone)`, falls back to UTC: a reasoned fallback, but the same zoneinfo probe is written twice, here and at sync_merge.py:222-226).
- Fail-closed broad catches with a reason in the comment (keep): check_content_hook.py:136, check_content_finders.py:342, code_standard.py:116, check_instructions.py:175,262,270, build_site.py:108,187,209. Fail-open broad catch at first_use_check.py:255 ("a session-start hook must never break the session": reasoned).
- Highest try density: token_log.py 8, first_use_check.py 7, stop_check.py 7, token_log_rows.py 7, build_site.py 6, check_instructions.py 6.
- `subprocess.run(check=True)` 7 uses; check=False/absent elsewhere (returncode read).
- Shell: `|| true` x6 (bootstrap.sh 1, session_checkin.sh 3, check.sh 2), `2>/dev/null` x34 (check.sh 11, pre-push 13, checkin 7, bootstrap 3), `|| return` x11.
- Duplicate checks one layer up: `check_lock.py:208` and `check_blocks.py:93` define the same 3-line `ok(label, good)` (item 4 list).
Candidate: narrow the 3 broad+silent handlers; no behavior change expected; guard files (first_use_check is run by a hook) need the Maintainer's request.

### Item 19 Hooks and tools
Hook run time (single run, this machine): PreToolUse `check.sh --hook` ~0.06 s per matching tool call (matcher covers Bash, Write, Edit, NotebookEdit, SendMessage, Agent, Task, Artifact*, WebFetch, WebSearch, many MCP tools); `check_instructions.py --hook` 0.05 s on Write/Edit/MultiEdit/NotebookEdit; Stop `stop_check.py` 0.06 s (timeout 30 s); SessionStart `first_use_check.py` 0.06 s + check-in 1.0 s. Per-session cost small; per-turn cost = N tool calls x 0.06-0.11 s. Permission entries: allow 14, ask 2, deny 34 (`json`); sandbox excludedCommands 2. Skills 11, agents 3. Skill use: **not measured** (`scripts/skill_use.py` needs saved session records: none here); LOG #66 had 4 Skill-tool calls in 12 sessions on 2026-11-20, and docs/reviews/2026-11-23-skill-use-audit.md (item 3 "no fleet-wide record", LOG #79) says no record exists. MCP servers: not listed in the kit.

### Item 20 Delegation overhead
Not measured from records. In repo: .claude/skills/delegate/SKILL.md 6,247 B; agents 3 (reviewer 1,727 B, scout 689 B, worker 1,499 B); AGENTS.md "Delegation" 472 chars + "Agents" 147 + skill. rule-tests scenario 29 untested since 2026-11-13. LOG #77 (two workers worked around a guard).

### Item 21 Output verbosity
DECISIONS.md: 134 lines, 76,175 B, longest row 2,357 chars (`awk` on rows); LOG.md 107 lines 42,677 B; KIT_HANDOFF.md longest line 1,063 chars; tool-retirement trials 14 files 428 KB (a trial file up to 73 KB). Candidate: cap a decisions row at ~600 chars with the rest in docs/reviews; risk: decision rows are the record (AGENTS.md:19).

## 4. Same-body Python functions (`same.py`: scripts/*.py, functions with a body of 2+ lines, docstring dropped, compared by `ast.dump`)
3 groups, 12 functions:
1. `new_repo(path)`: scripts/bootstrap_cli_test.py:36, scripts/check_lock_cli_test.py:33, scripts/drift_cli_test.py:32, scripts/sync_baseline_cli_test.py:36, scripts/sync_merge_cli_test.py:35 (5 places).
2. `sync(path)`: scripts/bootstrap_cli_test.py:42, scripts/check_lock_cli_test.py:39, scripts/drift_cli_test.py:38, scripts/sync_baseline_cli_test.py:42, scripts/sync_merge_cli_test.py:41 (5 places; equal bodies with the same call to `py("sync_baseline.py", ...)`).
3. `ok(label, good)` (3 lines): scripts/check_blocks.py:93 and scripts/check_lock.py:208.
Also in the same 5 files: `run` and `py` one-liners (below the 2-line floor) repeat; `git(...)` wrappers exist under 8 different bodies (bloat_check_rules.py:45, check_content_scan.py:155, check_content_test_blocks.py:93, code_standard.py:359, stop_check.py:33, sync_baseline_repo.py:26, token_log.py:97, worker_guard_scan.py:143), not equal bodies.

## 5. Step 3: key assumptions

| # | Assumption | Used at | Source | Conf. |
|---|---|---|---|---|
| A1 | Session load = bytes/4 tokens of AGENTS.md, CLAUDE.md, NEXT_PROMPT.md, descriptions; cap 5,500 | scripts/bloat_check_rules.py:30; AGENTS.md:52 | DECISIONS 2026-11-21 (docs/DECISIONS.md:36); bytes/4 is an estimate, not a tokenizer; kit handoff left out (item 2) | medium |
| A2 | A private repo needs no PR Action (Actions minutes); the pre-push hook is its gate | .github/workflows/check.yml:15 (`if:`), AGENTS.md:43 | LOG #51, check.yml comment line 6 (Maintainer 2026-11-18) | high for decision; medium that every project runs the hook (hook is per clone, `core.hooksPath` set by a session) |
| A3 | The pre-push hook is installed in every clone (hooksPath set by check-in or a SessionStart hook) | scripts/git-hooks/pre-push:2-3, AGENTS.md:25 | the hook's header; LOG #45 (a push with `--git-dir` ran no check) | medium |
| A4 | bash >= 4 for EPOCHREALTIME, with a whole-second fallback for bash 3 | scripts/check.sh:248-251 | comment only; no test runs bash 3 | medium |
| A5 | GNU `date +%N` exists for push-guard timing; else the compare is skipped | scripts/git-hooks/pre-push:243-249 | code (the `case "$g0" in *N\|'')` branch); no test on macOS | medium |
| A6 | ruff 0.17.6, pylint 4.1.4, shellcheck-py 0.9.0.6, bandit 1.9.4 exist on PyPI and behave as pinned | check.sh:163,166,406,423; check.yml:24; security.yml:21 | none recorded; not run here (SKIP) | low (not verified in this audit) |
| A7 | Deny rules in settings.json stop destructive git forms; an agent cannot sidestep with `git -C`, `--git-dir`, heredocs | .claude/settings.json deny (34 entries); AGENTS.md:25 | check_blocks self-test (33 steps pass), LOG #45; DECISIONS 2026-11-23 "do not put a command with a denied git pattern in a heredoc" (KIT_HANDOFF:36) shows a hole class | medium |
| A8 | Skills load when their description matches the step | AGENTS.md:46 | LOG #66: 4 Skill-tool calls in 12 sessions; skill-use plan 2026-11-20; no fleet record (LOG #79) | low |
| A9 | A subagent pass in rule-tests shows the rule text works | .claude/rule-tests.md; docs/reviews/2026-11-18-rule-tests-lean.md "limits" | the report states "not a fresh top-level session", "no before run" | medium; stale (item below) |
| A10 | The hook timeout (PreToolUse 10 s, Stop 30 s, SessionStart 15 s) stays above hook run time | .claude/settings.json hooks | measured: 0.06 s each; check-in 1.0 s runs outside a hook | high |
Also checked: the fleet has 9 repos on kit 10.0.0 (KIT_HANDOFF:10) | stale: KIT_VERSION 11.0.1 | no live check (no network).
Untraced (no source): A6; A4 and A5 rest on code comments only.
Stale (true when written, not now): (1) `.check.state.json` timings.check 4.2 s / 14 steps (lane now 36 steps, 64.2 s); (2) docs/KIT_HANDOFF.md:10,38 kit 10.0.0 and "highest ~5,352 of 5,500"; (3) docs/tools.md:31 66 files / 17,361 lines vs 70 / 19,228; (4) rule-tests last run 2026-11-18 vs kit 11.0.1 text; (5) kit.config.json has no `fleet.last_audit`; (6) audit commit eab8b98 not in this clone.
Counts for the report table: high 2 (A2 decision, A10) -> I rate: high 2, medium 6 (A1, A3, A4, A5, A7, A9), low 2 (A6, A8), untraced 1 (A6, also counted low; so untraced-only = 0 beyond A6).
Questions for the Maintainer (2-3 options, REC first), not resolved by me:
- Q1 Kit session load: (a) count KIT_HANDOFF.md in the load and shrink it (REC; trade-off: a guard script change plus a handoff rewrite), (b) leave the measure and accept ~6,044 real tokens (breaks the 5,500 cap meaning), (c) raise the cap (affects 9 repos).
- Q2 Baseline: (a) re-record `timings` over 3 full runs now (needs Maintainer approval because it is slower: 4.2 -> ~64 s), (b) make the cli tests parallel first then record, (c) keep the warning on.

## 6. Tech-debt register (accepted, not fixed; owner = role; review date = proposal)
Review-date rule: next audit (the audit skill: every 14 days) = 2026-12-08, or the date shown.

| # | Item | Evidence | Owner (role) | Review date |
|---|---|---|---|---|
| D1 | Timing baselines stale (check 4.2 s vs 64.2 s; 15 steps WARN every run) | .check.state.json, check1.txt | Maintainer | 2026-12-08 |
| D2 | Session-load measure omits docs/KIT_HANDOFF.md (~1,528 tokens) | scripts/bloat_check_rules.py:30 | Maintainer | 2026-12-08 |
| D3 | 56 duplicate lines vs budget 20 (cli test helpers x5) | bloat `--time` | Maintainer | 2026-12-08 |
| D4 | docs/KIT_HANDOFF.md stale (kit 10.0.0; done plans; 1,063-char lines) | KIT_HANDOFF:10,38 | Maintainer | 2026-12-08 |
| D5 | ruff, pylint, shellcheck steps SKIP here; not measured; two linters for one check | check1.txt SKIP lines; check.sh:395-399 | Maintainer | 2026-12-08 |
| D6 | check.sh 533 lines (C4 WARN >450) incl. 158-line self-test | check1.txt WARN | Maintainer | tool-retirement P2 |
| D7 | Tags not made: v4.1.0, v5.0.0, v5.0.1, v8.1.0, v9.0.0; kit branches to delete | KIT_HANDOFF:7,25-31 | Release Manager | 2026-12-08 |
| D8 | Rule tests not rerun since 2026-11-18; scenario 22 invalid; 5 rules with no evidence (rows 6, 11, 26, 27, 29) | docs/reviews/2026-11-18-rule-tests-lean.md | Maintainer | 2026-12-08 |
| D9 | `fleet.last_audit` unset in kit.config.json; fleet audit due | bloat `--time` output | Maintainer | after this audit |
| D10 | Skills: audit/SKILL.md 151 lines (limit 150); deliver description not "Use when" | `--skills` WARN x2 | Maintainer | 2026-12-08 |
| D11 | 3 broad-and-silent exception handlers | first_use_check.py:145, sync_merge.py:226, sync_baseline_repo.py:104 | Maintainer | 2026-12-08 |
| D12 | FILES.md lacks 9 scripts; tools.md is the other inventory | item 1 | Maintainer | 2026-12-08 |
| D13 | Tool retirement P2-P6 open (kit shrink, pilot, fleet, exports) | KIT_HANDOFF:12-16 | Maintainer | per plan |
| D14 | Skill use unmeasured (no session records) | LOG #79 | Maintainer | 2026-12-08 |

## Report table inputs
| Measure | Before (2026-11-13 audit) | Now (2026-11-24) | Budget |
|---|---|---|---|
| Start read (~tokens) | 3,740 | 4,657 counted (~6,044 with KIT_HANDOFF) | 5,500 cap |
| Rule bullets: AGENTS.md / Project rules | 28 / 0 | 28 / 1 | AGENTS.md 200 lines (73 used); project rules cap 15 |
| Check lanes: fast / full (s), slowest step | - / 3.0 | 1.7 / 64.2 (serial 108.2); slowest cli_tests 64.0 (44.5 alone) | baseline 4.2 s |
| Duplicate lines (80+, 2+ files) | 2 | 56 | 20 |
| Tracked files / size | 39 / 255 KB | 283 / 2,388,352 B | - |
| Big files | 0 | 0 over 500 KB | 500 KB |
| Timing: bloat-brief / checkin / check | 0.1 / 0.9-1.1 / 3.0 | 0.5 / 1.0 / 58.9 (`--time`), 64.2 (check.sh) | +25% of baseline 0.1 / 0.6 / 4.2 |
| Key assumptions high / medium / low / untraced | 3 / 3 / 1 / 0 | 2 / 6 / 2 / 0 (A6 counted low) | - |
