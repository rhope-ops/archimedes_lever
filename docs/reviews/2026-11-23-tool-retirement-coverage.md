# Tool retirement program: plan coverage list (step 7, rule T7)

DRAFT, not approved. Written 2026-11-23 ~14:45 America/Chicago by session "Kit · Tool retirement · 2026-11-23"
(session_01PyXpdTtcLuv26JT5RFfzye). It needs the Maintainer's approval in this session's own chat before the plan starts.

Sources: FLEET-MASTER-PLAN-v2.md (the Maintainer's Drive, folder Rhope, compiled 2026-11-22; read 2026-11-23) and the
approved prompt [2026-11-23-tool-retirement-prompt.md](2026-11-23-tool-retirement-prompt.md). Rows name items by ID and a
neutral title; they do not quote the source text (it holds personal data and a token).

## Counting rule (what the T7 check counts)

- Master plan items: the 6 DEC lines, the 19 Part 1 checkboxes (1.1-4.3) and the 11 Part 2 checkboxes (P2-1..P2-11).
  Compound Part 2 items are split into sub-rows (a, b, ...); the item counts once, each sub-row gets its own mark.
- Prompt items: steps 1-7 with their named sub-items, the 7 rules, the 2 proof blocks, the plan format and the
  "no new AGENTS.md lines" constraint.
- Not items (evidence only): the master plan's delta table (section 1) and token tables (section 2).
- Marks: **in** (this program does it; the column names the prompt step), **out** (not this program; the reason), **later**
  (wanted, not now; the trigger), **ask** (the Maintainer marks it; REC given). An unmarked or "ask" row blocks the plan.

## A. Master plan decisions (6)

| ID | Item | Mark | Step / reason |
|---|---|---|---|
| DEC-1 | Handover scope: only ICF leaves; retained repos keep org values in one config file | in (constraint) | Steps 3, 6: no trial removes a config home |
| DEC-2 | Role titles Maintainer / Content Approver / Release Manager | in (constraint) | Rule T6 builds on it |
| DEC-3 | Brand: Option A for DoD tools, Fulcrum for the kit | out | UI tokens, not tools; fleet v2 owns it |
| DEC-4 | Remove ExecutionPolicy Bypass (CI only keeps it) | in (constraint) | Steps 3, 6: no generator or pac trial brings it back |
| DEC-5 | DoD security scope excludes ICF-Source | in (constraint) | Step 6: CodeQL, SBOM, hashes not in ICF |
| DEC-6 | Keep the ICF analytics beacon, parameterized | out | Fleet v2 / ICF handover |

## B. Master plan Part 1 (19): fleet v2 owns these

Status source: [2026-11-23-fleet-v2-coordinator-state.md](2026-11-23-fleet-v2-coordinator-state.md) and the fleet v2 plan.
Not verified in this session. Fleet v2 is still open (ICF #248 split, ICF kit 11.0.1 sync).

| ID | Item (short) | Mark | Reason / link to this program |
|---|---|---|---|
| 1.1 | Kit: remove shell=True | out | Fleet v2 (kit 11.0.0) |
| 1.2 | Kit: hygiene files and SAST CI (bandit, gitleaks) | out | Fleet v2; its security.yml is an input to step 2 (gitleaks trial) |
| 1.3 | Kit: role words, kit.config.json | out | Fleet v2 (DEC 2, DEC 7 of fleet v2) |
| 1.4 | Kit: split scripts to 450, unittest discovery | out | Fleet v2; the split lib modules enter the step 1 inventory |
| 1.5 | Kit: Fulcrum v2, CSP in build_site.py | out | Fleet v2 |
| 2.1 | RADE: kit sync, requirements, offline check | out | Fleet v2 |
| 2.2 | RADE: Bypass, TLS, urlopen, XSS, CSP | out | Fleet v2 |
| 2.3 | RADE: apps.json, role words, splits, Option A, engine release | out | Fleet v2 (engine-v36); release tooling enters step 3 |
| 3A.1 | 90-161.Z: kit sync, lock bump, rebuild_all.py | out | Fleet v2; rebuild_all.py and bump_lock.py enter step 3 |
| 3A.2 | 90-161.Z: Bypass, OneDrive paths, SHA256SUMS, XSS | out | Fleet v2 |
| 3A.3 | 90-161.Z: 6 splits, site.config.json, Option A | out | Fleet v2 |
| 3B.1 | 33-332.Z: kit sync, hygiene, PSScriptAnalyzer cache | out | Fleet v2 |
| 3B.2 | 33-332.Z: paste dedup, splits, build_paste_test.py | out | Fleet v2; build_paste.py enters step 3 |
| 3B.3 | 33-332.Z: Option A, CSP, SVG size | out | Fleet v2 |
| 3C.1 | ICF: kit sync, CI split, owner file, beacon config | out | Fleet v2 |
| 3C.2 | ICF: module splits, preload, caching, content_pipeline.py | out | Fleet v2; content_pipeline.py enters step 3 |
| 4.1 | ICF: Option A tokens, CSS partials | out | Fleet v2 Stage 4 |
| 4.2 | ICF: ARIA, focus, release files | out | Fleet v2 Stage 4 |
| 4.3 | ICF: history scan, shadow handover drill | out | Fleet v2 plan B.20: a step for the incoming maintainer |

### B2. Part 1 sub-parts that fleet v2 dropped or left open (no owner now)

| ID | Sub-part | Mark | REC |
|---|---|---|---|
| B2-1 | 1.4 `.kit-manifest.json` (fleet v2 B.5: dropped, check_lock.py extended) | out | Closed by fleet v2 DEC; nothing to do |
| B2-2 | 1.3 move history to docs/archive/ (fleet v2 B.2: not done) | out | Closed by fleet v2 DEC 2 |
| B2-3 | 3C.1 owner file rotation (fleet v2: staged only, ICF #246) | out | ICF handover, not tools |
| B2-4 | 4.3 shadow handover drill (needs the incoming maintainer) | out | ICF handover, not tools |
| B2-5 | 6 kit repos still on kit 10.0.0 (fleet v2 B.21) | later | After the distribution pilot (step 4): catch-up by one version bump |
| B2-6 | ICF preload tags A/B (coordinator state "Needs the Maintainer") | out | Fleet v2 open question |

## C. Master plan Part 2 (11)

| ID | Item (short) | Mark | Step / reason |
|---|---|---|---|
| P2-1 | Installable kit CLI package (pipx) | in | Step 4: the pip/pipx package is a third candidate next to the pre-commit hook repo and the reusable workflow |
| P2-2 | Standard linters and secret scanners | in | Step 2, with 3 added pairs: bash checks vs shellcheck, PowerShell checks vs PSScriptAnalyzer, check_content* vs trufflehog next to gitleaks |
| P2-3a | Authenticode signing of paste bundles | out (proposed) | Needs the Maintainer's certificate; prompt "pending, not in scope yet" |
| P2-3b | Paste truncation sentinel (start/end checksum) | later | A new guard, not a tool retirement |
| P2-4a | Build-time static HTML with a standard Markdown library (90-161.Z, RADE) | in | Step 6 |
| P2-4b | Remove the runtime fetch, offline with connect-src 'none' | in | Step 6, same trial as P2-4a |
| P2-5a | CodeQL | in | Step 6 (kit, RADE, 90-161.Z, 33-332.Z) |
| P2-5b | CycloneDX SBOM | in | Step 6 |
| P2-5c | Hash-pinned Python (pip-compile --generate-hashes) | in | Step 6 |
| P2-6a | TableLayoutPanel or XAML instead of manual pixel math (RADE) | in | Step 6 |
| P2-6b | 125/150/175 % DPI tests in window CI | in | Step 6 |
| P2-7a | pac solution instead of the flow ZIP/XML builders (90-161.Z) | in | Step 6 |
| P2-7b | One versioned module instead of -r1..-r14 file names | in | Step 6 |
| P2-8a | Build-time ==term== markup instead of character offsets (ICF) | in (trial only) | Step 6. Read-only trial until fleet v2 closes; the result is shown to the Maintainer, the incoming maintainer may own the change |
| P2-8b | Split questions and glossary JSON by Block (ICF) | in (trial only) | Step 6, same terms as P2-8a |
| P2-9 | FSRS spaced repetition (ICF) | out (proposed) | Prompt "pending, not in scope yet"; feature, not a tool |
| P2-10a | Installable PWA manifest (ICF) | out (proposed) | Same |
| P2-10b | IndexedDB and JSON backup (ICF) | out (proposed) | Same |
| P2-10c | Exam navigator drawer (ICF) | out (proposed) | Same |
| P2-10d | Shortcut cheat sheet (ICF) | out (proposed) | Same |
| P2-11a | OKLCH colour tokens (fleet) | out (proposed) | Same |
| P2-11b | Static preview.html for visual QA | out (proposed) | Same |

## D. Prompt items

| ID | Item | Mark | Note |
|---|---|---|---|
| S1 | Kit script inventory in docs/tools.md (65 scripts, 17,096 lines: re-measured 2026-11-23 with `find scripts -name '*.py' -o -name '*.sh'` and `wc -l`) | in | docs/tools.md does not exist yet |
| S2a | code_standard.py vs ruff + pylint + radon | in | |
| S2b | check_content* vs gitleaks rules and detect-secrets | in | Plus trufflehog (P2-2) |
| S2c | sync_baseline / sync_merge / drift / check_settings vs copier and cruft | in | |
| S2d | token_log vs Claude Code OpenTelemetry metrics | in | |
| S2e | check_instructions vs Vale | in | |
| S3a | RADE engine lock and release tooling | in | Per-repo decision by the Maintainer |
| S3b | ICF publish_pages.py vs actions/deploy-pages | in (read-only) | No ICF-Source change until fleet v2 closes |
| S3c | 90-161.Z task-script generator | in | |
| S3d | Other project-specific tools (rebuild_all.py, bump_lock.py, build_paste.py, content_pipeline.py, ...) | in | Found by the step 3 inventory |
| S4 | Distribution by version, one pilot, rollback | in | Plus P2-1 candidate |
| S5 | Kit rule bullets 31 -> 28, old/new text, conflict check | in | Re-measured: 31 kit bullets plus 1 project rule |
| S6 | Part 2 standard replacements | in | Rows P2-4..P2-8 |
| S7 | This list | in | Now |
| T1 | Search-first (3 candidates in docs/tools.md) | in | Supersedes step 3 draft R2 |
| T2 | Ratchet on custom script lines | in | |
| T5 | No stricter cap or new rule without a fleet debt list | in | |
| T6 | One role word; approval only in the acting session's chat; DECISIONS quote | in | Supersedes step 3 draft R4 |
| R1 | Split at 80 % of cap (360 of 450) | in | From the step 3 draft |
| R3 | Fresh cross-repo audit at each release or 14 days | in | From the step 3 draft |
| T7 | Plan coverage | in | This list is its first use |
| PR1 | Retirement proof (same defects, mutants, CI green, lines fall) | in | |
| PR2 | Distribution proof (files per kit change, token cost before/after) | in | |
| PF | Plan format (phases, lanes, models, agents, hours, order, rollback, GAPS) | in | |
| NL | No new AGENTS.md lines | in | |

## E. The Maintainer's answers (question dialog in this session, 2026-11-23 ~14:50 America/Chicago)

Scope: this program. Recorded here, not as a DECISIONS row By the Maintainer.

1. The 4 "ask" rows and the 2 drift items (P2-1, P2-2): "Accept all RECs". Marks above are updated.
2. Repo set: "Kit + 4, sec-source later": trials on archimedes_lever, RADE, 90-161.Z, 33-332.Z and ICF-Source; sec-source later.
3. Start time: "After fleet v2 closes". This session stops after this list until the coordinator says fleet v2 is closed.
   No inventory or trial runs before then.

## Still open (block the plan)

1. Rule IDs T3 and T4 (not in the prompt; the cited fleet v2 lessons file is not in this repo or in Drive › Rhope).
   The Maintainer's answer: ask the coordinator session "Kit · Fleet v2 coordinator 2". Asked 2026-11-23.
2. Features out (P2-3a, P2-9, P2-10, P2-11): the prompt file says "pending"; the coordinator relayed "out for now".
3. The Maintainer's approval of the whole list, in this session's chat, after item 1 is answered.

## F. Counts (the T7 check compares these)

| Group | Rows | in | out | later | ask |
|---|---|---|---|---|---|
| A. DEC (6 items) | 6 | 4 | 2 | 0 | 0 |
| B. Part 1 (19 items) | 19 | 0 | 19 | 0 | 0 |
| B2. Part 1 open sub-parts (extra rows, not source items) | 6 | 0 | 5 | 1 | 0 |
| C. Part 2 (11 items, split into sub-rows) | 22 | 13 | 8 | 1 | 0 |
| D. Prompt (25 items) | 25 | 25 | 0 | 0 | 0 |
| **Total** | **78** | **42** | **34** | **2** | **0** |

Source items: 36 master plan items (6 + 19 + 11) + 25 prompt items = 61. Unmarked: 0. Rows "ask": 0.
