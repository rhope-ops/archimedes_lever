# Custom tool retirement program: plan (for the Maintainer's approval)

DRAFT, not approved. Written 2026-11-23 from ~16:45 America/Chicago by session "Kit · Tool retirement · 2026-11-23 · #125".
Nothing is built. Approving this plan approves the exact rule texts in section 3 (AGENTS.md "Rule text"), the
phase lanes, models, agents and hours, and each "REC" marked "(choice)" that you answer.

Inputs (all on branch `claude/tr-research`, to merge with this plan):
[coverage list](2026-11-23-tool-retirement-coverage.md) (85 rows: 51 in, 34 out, approved; ION-1 and AUD-1..5 added),
[research plan](2026-11-23-tool-retirement-research-plan.md),
R1 [kit tools](2026-11-23-tr-r1-kit-tools.md), R2 [project tools](2026-11-23-tr-r2a-project-tools.md) and
[kit 10.0.0 repos](2026-11-23-tr-r2b-kit10-repos.md), R3 [ICF scans](2026-11-23-tr-r3-icf-scans.md),
R4 [linters](2026-11-23-tr-wa-linters.md), [scanners](2026-11-23-tr-wb-scanners.md) (W-B: pending),
[sync and distribution](2026-11-23-tr-wc-sync-distribution.md), [standard replacements](2026-11-23-tr-wd-standard-replacements.md),
R4e [Ion benchmark](2026-11-23-tr-r4e-ion-benchmark.md), R4f [split audit](2026-11-23-tr-r4f-split-audit.md),
the fleet v2 [lessons](2026-11-23-fleet-v2-lessons.md) (5 causes).

## 1. What the research shows (the evidence for each phase)

| Finding | Number | Source |
|---|---|---|
| Kit custom scripts (T2 baseline) | 65 files, 17,096 lines (66 / 17,361 with the pre-push hook) | R1 |
| Kit script churn, last 30 days | 674 commits, 32,874 lines changed; 654 sync commits in 4 projects | R1 |
| Standard linters cover `code_standard.py` | Python 4 full + 4 partial of 10 checks; shell 0 of 8; PowerShell 2 + 2 of 10. Seeded defects: custom 11/11, 7/7, 9/9; standard 5-6/11, 0/7, 1-3/9 | W-A |
| shellcheck finds a defect class the kit does not | 14 / 242 / 146 / 17 / 20 findings (kit / RADE / 90-161.Z / 33-332.Z / ICF) | W-A |
| copier / cruft vs the sync scripts | Same files per change (1-3); they keep a project's edits where sync overwrites them silently; they lack the role-word rename, the settings.json merge and the lock gate. ~1,915 sync and drift lines could go; check_lock and check_settings stay | W-C |
| OpenTelemetry vs token_log | Covers tokens and cost; not web searches, the weekly report or a log with no collector; needs a collector | W-C |
| Distribution (pre-commit / reusable workflow / pipx) | Each gives 1 file per kit change only after `check.sh` reads the kit scripts from the distributed copy (today it runs the project's own copies); 17 instruction files still need a sync | W-C |
| CodeQL | 7 Python findings (4 = one ReDoS in `scripts/build_site_html.py:121`, copied to 4 repos), 1 JS (90-161.Z); no PowerShell support | W-D |
| Paste truncation | Ion: 0 of 700 cuts parse (try wrapper). RADE-built bundles (90-161.Z R41): 49 of 650 cuts parse; the cut at line 13,579 parses (re-checked) and starts the engine | W-D |
| Ion detectors vs Presidio | Ion precision 0.94, recall 0.83; Presidio 0.61 / 0.83. 5 Ion defects (case-sensitive street types, passports as SSN Low, "_" in e-mail, name span over line breaks, middle initial without a dot) | R4e |
| Ion e-signature DoD IDs | 3 layouts give SSN, 7 give no hit (25 layouts tested) | main session, 2026-11-23 |
| Splits made for the 450 cap | 22 judged: 11 cohesive, 9 mixed, 2 arbitrary | R4f |
| Project tools | RADE 18 / 2,391 lines; 90-161.Z 31 / 4,826; 33-332.Z 4 / 789; ICF 209 / 36,183 (73 old review scripts); sec-source 14 / 2,062; kit 10.0.0 repos 84 / 14,499 | R2 |
| Kit 10.0.0 repos | 43 of 54 kit files differ from 11.0.1; transcription_assistant runs 2 Stop hooks (kit and an old copy) | R2b |
| ICF handover | 2 non-noreply addresses in history; ICF-Source cannot have rulesets or secret scanning on its plan; icf settings not checked (attach denied) | R3 |
| Session load after the rule texts | +32 tokens: RADE ~5,445, 90-161.Z ~5,413, 33-332.Z ~5,500, ICF ~5,175 (cap 5,500) | measured on a copy |

## 2. Decisions for the Maintainer (answer each; REC first)

1. **File size cap (AUD-3 against R1).** **DEC: A** (the Maintainer, this session's chat, 2026-11-23 ~17:00 America/Chicago: "1a"; scope: this program). The split audit shows that half of the cap-driven splits are mixed or arbitrary.
   - **REC: A.** File size only warns (C4 of `code_standard.py` becomes WARN); a split is reviewed against its goal (rule C7 below). R1 is not added.
   - B. Keep the 450 fail and add R1: "A hand-written file that passes 80 % of its line cap (360 of 450) is split in the pull request that grows it."
2. **T2 ratchet.** **REC:** keep it as a FAIL (it measures the program's goal, total custom lines, and a split cannot game it). Baseline 17,096 lines (65 files).
3. **Distribution.** **REC:** pip/pipx package (local and offline runs, one pin, works with the existing pre-push hook; pre-commit refuses `core.hooksPath`; a reusable workflow runs only in CI). Pilot: **33-332.Z** (68 kit files, 4 project tools, small). Alternative pilot: SPAR (no project tools: lowest risk, least learning).
4. **Sync scripts.** **REC:** keep `sync_baseline.py` for the 17 instruction files after the pilot, and fix its defect first: it overwrites a project's edits to kit files without a conflict (copier keeps them). Retire copier/cruft as candidates.
5. **token_log.** **REC:** keep (your decision of 2026-11-23 to keep the token log branch; OTel needs a collector and lacks web searches).
6. **shellcheck.** **REC:** add it as a WARN step in the code standard first, with the measured fleet list (rule T5), then fix per repo.
7. **90-161.Z revision files** (75 `-rN` files, 67,606 lines) and **pac solution**. **REC:** not a tool retirement: move superseded revisions to an archive folder in a 90-161.Z session; `pac solution` for the packaging part only (~150 lines), when `pac` can run on a dev machine.
8. **ICF trial items** (`==term==`, Block split, 2 history addresses, no branch protection). **REC:** write them into the ICF handover runbook for the incoming maintainer; no ICF code change in this program.

## 3. Rule texts (exact text for approval)

Result on a copy of AGENTS.md: 76 -> 73 lines, kit rule bullets 31 -> 28 (+1 project rule), session load +128 bytes
(~+32 tokens). No new AGENTS.md line. Three bullets are merged (cuts 1-3); five are extended. Rules a check enforces
get a pointer only; the check's FAIL line states the full rule. Where each prompt rule lives:

| Prompt rule | Home | Enforcing check (trigger) | Defect it prevents |
|---|---|---|---|
| T1 search first | C5 "One home" + check message | `bloat_check.py`: every `scripts/*` file has a docs/tools.md row with 3 named candidates (every push) | new tools instead of existing ones (cause 1) |
| T2 ratchet | C9 "Caps and audit" | `bloat_check.py`: total custom script lines <= baseline in `.check.state.json` (every push) | custom code grows back (causes 1, 3) |
| T5 debt list first | C8 "Lean instructions" (short) + `.claude/skills/rule-change/SKILL.md` (full) | rule-change skill step; audit output before merge | caps stricter than the fleet can meet (cause 3; ICF 21 files) |
| T6 one role word, approval in own chat | C4 hard rule "The Maintainer's approval" | `log_check.py`: a DECISIONS row By the Maintainer quotes the OK of its exact text (push that changes docs/DECISIONS.md) | 3 rows written from dialog answers on 2026-11-23 (cause 4) |
| T7 plan coverage | `.claude/skills/handoff/SKILL.md` (moved out of AGENTS.md for the token cap) | `log_check.py --coverage <file>`: rows marked = rows, no "ask" (before a plan PR) | the Part 2 miss of fleet v2 |
| R1 80 % split | option B of decision 1 only | `code_standard.py` C4 | cap met at sync time |
| R3 fleet audit | C9 "Caps and audit" + audit skill "Fleet" section | `bloat_check.py`: AUDIT DUE (fleet) at a kit tag or 14 days (kit check-in) | drift found only at sync (cause 5) |
| AUD-1 goal per check | C8 + `code_standard.py` C1: a check script's header has a `Prevents:` line | C1 (every push) | checks with no testable goal |
| AUD-2 goal-based review | C7 "Fresh review" | reviewer brief (delegate skill) | splits that only move a number (R4f) |
| AUD-3 outcome metrics | C9 (file size warns) + audit skill (defects per check, mutant kill rate, files per kit change, fix-of-a-fix rate) | audit report | proxies gamed by splits |

Full texts of the skill additions (not rules; shown for review):
- handoff skill, "Plans" step: "A plan made from a source plan first lists every source item as in, out or later, with a count table; the Maintainer approves that list before the plan; `python3 scripts/log_check.py --coverage <file>` fails on an unmarked or 'ask' row or a count mismatch."
- rule-change skill, "Where it belongs": "A new rule, check or stricter cap first lists what it would fail today in every fleet repo, with a fix plan (T5)."

### C1. Decisions (merge with "The Maintainer's decisions" (bullet cut 1))

Old:

```text
- **Decisions.** Make routine decisions yourself. Ask the Content Approver about content approval, and the Maintainer about source authority and what "The Maintainer's approval" names, with all open questions in one round and in the format of the Maintainer's preferences (without them: a question dialog where one exists, 2–4 options each, the recommendation first).
```

Old:

```text
- **The Maintainer's decisions.** Record each one in docs/DECISIONS.md or its canonical document, with its date and scope. A decision binds the task or thing it names; it binds every session only as a line in "Project rules". Before you change an approved design, source or value, search docs/DECISIONS.md for it and ask.
```

New:

```text
- **Decisions.** Make routine decisions yourself. Ask the Content Approver about content approval, and the Maintainer about source authority and what "The Maintainer's approval" names, with all open questions in one round and in the format of the Maintainer's preferences (else a question dialog, 2–4 options, the recommendation first). Record each decision of the Maintainer in docs/DECISIONS.md or its canonical document, with its date and scope: it binds the task or thing it names, and every session only as a line in "Project rules". Before you change an approved design, source or value, search docs/DECISIONS.md for it and ask.
```

### C2. Delivery (absorbs "Host limit" (bullet cut 2))

Old:

```text
- **Delivery.** Deliver every change without being asked: commit, push, open a pull request, then merge it by its lane. Lane A, docs that are not rules: merge when the checks are green. Lane B, code, scripts and checks: merge when the checks are green and the fresh review finds no MAJOR finding. Lane C, rule text, instruction and guard files, a UI or design change the Maintainer has not approved (show a preview first), a MAJOR finding you cannot fix, a self-review, a pull request not opened for this work ("Git history"), and each case in "The Maintainer's approval": ask the Maintainer. Then verify that origin/main has the commit and republish the affected artifacts. Steps: `.claude/skills/deliver/SKILL.md`.
```

Old:

```text
- **Host limit.** A host limit wins over "Delivery" (for example a required branch, or a push or merge the host does not allow without the Maintainer): do the steps it allows, then report each other step as blocked, with its cause and what unblocks it.
```

New:

```text
- **Delivery.** Deliver every change without being asked: commit, push, open a pull request, then merge it by its lane. Lane A, docs that are not rules: merge when the checks are green. Lane B, code, scripts and checks: merge when the checks are green and the fresh review finds no MAJOR finding. Lane C, rule text, instruction and guard files, a UI or design change the Maintainer has not approved (show a preview first), a MAJOR finding you cannot fix, a self-review, a pull request not opened for this work ("Git history"), and each case in "The Maintainer's approval": ask the Maintainer. Then verify that origin/main has the commit and republish the affected artifacts. Steps: `.claude/skills/deliver/SKILL.md`. A host limit wins over the lanes: do the steps it allows and report the rest as blocked, with the cause and what unblocks it.
```

### C3. Delegation (absorbs "Agents" (bullet cut 3))

Old:

```text
- **Delegation.** Delegate only substantial independent work (about 30 minutes or more, and the fresh review) with bounded files and measurable done criteria. Exception: the main session sends searches that span many files, and summaries of long test or log output, to `scout`; it does a lookup with a known target itself. Give parallel agents disjoint files, and check delegated output (diff, touched files, no approval or exemption changes) before you report it as done.
```

Old:

```text
- **Agents.** Before you delegate or run more than one agent: `.claude/skills/delegate/SKILL.md` (agents, model routing, briefs, review and merge).
```

New:

```text
- **Delegation.** Before you delegate or run more than one agent: `.claude/skills/delegate/SKILL.md`. Delegate only substantial independent work (about 30 minutes or more, and the fresh review) with bounded files and measurable done criteria. Exception: the main session sends searches that span many files, and summaries of long test or log output, to `scout`; it does a lookup with a known target itself. Give parallel agents disjoint files, and check delegated output (diff, touched files, no approval or exemption changes) before you report it as done.
```

### C4. The Maintainer's approval (T6 (hard rule))

Old:

```text
- **The Maintainer's approval.** Ask the Maintainer before: a data write, a live or irreversible effect, a cost, a security or privacy risk, and a lane C merge ("Delivery"; a project rule may add a lane C case, never remove one). The Maintainer's own request for that action is the approval; a recommendation is not a decision until the Maintainer approves it.
```

New:

```text
- **The Maintainer's approval.** Ask the Maintainer before: a data write, a live or irreversible effect, a cost, a security or privacy risk, and a lane C merge ("Delivery"; a project rule may add a lane C case, never remove one). The Maintainer's own request for that action is the approval; a recommendation is not a decision until the Maintainer approves it. Only the Maintainer's message in the acting session's chat approves (`scripts/log_check.py`).
```

### C5. One home (T1)

Old:

```text
- **One home.** One fact, rule or value lives in one place; other places link to it. Before you add a file, rule, script, check or doc section, extend or replace an existing one. A change removes what it makes obsolete (code, docs, files, rules) in the same commit.
```

New:

```text
- **One home.** One fact, rule or value lives in one place; other places link to it. Before you add a file, rule, script, check or doc section, extend or replace an existing one (a script: docs/tools.md).. A change removes what it makes obsolete (code, docs, files, rules) in the same commit.
```

### C7. Fresh review (AUD-2)

Old:

```text
- **Fresh review.** For lanes B and C, a fresh reviewer gets only the diff and the brief, not the author's conclusions (a fresh context finds what self-review misses): the `reviewer` subagent where the host has subagents, else a new session, on a model tier no lower than the author's; if neither is possible, review it yourself, call it "self-review" and treat the merge as lane C. The review covers the head commit you merge: a fix made after a review gets its own review.
```

New:

```text
- **Fresh review.** For lanes B and C, a fresh reviewer gets only the diff and the brief, not the author's conclusions (a fresh context finds what self-review misses): the `reviewer` subagent where the host has subagents, else a new session, on a model tier no lower than the author's; if neither is possible, review it yourself, call it "self-review" and treat the merge as lane C. The review covers the head commit you merge: a fix made after a review gets its own review. Review a change made to pass a check against its goal: "only the number moved" is MAJOR.
```

### C8. Lean instructions (T5, AUD-1)

Old:

```text
- **Lean instructions.** Instruction files and host prompts hold rules only, one line per rule (every line costs tokens on every task and can lower adherence); a rule that needs more lines is a procedure. A rule a hook or test enforces becomes a pointer to it; a procedure that only some tasks need becomes a skill.
```

New:

```text
- **Lean instructions.** Instruction files and host prompts hold rules only, one line per rule (every line costs tokens on every task and can lower adherence); a rule that needs more lines is a procedure. A rule a hook or test enforces becomes a pointer to it; a procedure that only some tasks need becomes a skill. A new rule or check names the defect it prevents.
```

### C9. Caps and audit (T2, R3, AUD-3 (option A; R1 as option B))

Old:

```text
- **Caps and audit.** `scripts/bloat_check.py` (run by the check-in and by check.sh) fails when this file passes 200 lines, when the session load passes 5,500 tokens (third-party skills and agents in `.check`: own cap 1,500), or when a skill or agent file states a rule whose home is this file. The full audit runs when the Maintainer asks for it, and a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.
```

New:

```text
- **Caps and audit.** `scripts/bloat_check.py` (run by the check-in and by check.sh) fails when this file passes 200 lines, when the session load passes 5,500 tokens (third-party skills and agents in `.check`: own cap 1,500), when a skill or agent file states a rule whose home is this file, or when custom script lines rise; file size only warns. The full audit runs when the Maintainer asks for it and for all fleet repos at each kit release or after 14 days, and a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.
```


## 4. Phases

Lanes (AGENTS.md "Delivery"): the checks below are run by `check.sh` and the hooks, so they are guard files: lane C
(your merge) unless marked otherwise. Models: workers on the standard tier (Sonnet), reviewers of guards, hooks and
security on the strong tier (Opus), goal-based split reviews on a model other than the author's, the main session on
the strong tier. One PR per retirement (T3). Every phase ends with a fresh review on the head commit.

| Phase | Work | Repos | Lane | Agents (model) | Hours | Rollback |
|---|---|---|---|---|---|---|
| P1 Rules and checks | Section 3 texts in AGENTS.md (kit); checks: T1 tools.md rows, T2 ratchet, R3 AUDIT DUE (fleet), AUD-1 `Prevents:` header, C4 to WARN (decision 1A), T6 and T7 in `log_check.py`; docs/tools.md moves from the R1 review file (kit-only; bootstrap removes it as it removes docs/FILES.md; each project gets its own list); skill texts; the rule conflict check | kit | C | 2 workers (Sonnet, disjoint files: `bloat_check*`+`code_standard*` / `log_check.py`+skills+docs), 2 reviewers (Opus), 1 conflict reviewer (Opus) | ~10 agent-h, ~4 h wall | revert the PR; caps as before |
| P2 Kit shrink and repair | (a) `code_standard.py` Python parse, line and file-size checks move to ruff + pylint config; header, comment, safety, generated, shell and PowerShell checks stay; (b) content check: per W-B (pending); (c) `check_instructions.py`: per W-B (pending); (d) sync: stop on a project's local edit of a kit file (check_lock --verify first); (e) redesign 5 kit splits along the seams in R4f (`sync_baseline_run`, `code_standard_ratchet`, `token_log_test_report`, `code_standard_test_gate`, `check_content_scan_settings`); (f) fix the ReDoS at `build_site_html.py:121`; (g) shellcheck as WARN with the fleet list (decision 6); (h) AUD-5 records for `bloat_check*` and the audit skill | kit | C (checks), B (e, f) | 3 workers (Sonnet), 3 reviewers (Opus; split review on a model other than the author's) | ~16 agent-h, ~6 h wall | revert each PR alone |
| P3 Distribution pilot | pip/pipx package of the kit checks (decision 3); `check.sh` reads the kit scripts from the package; the 17 instruction files stay on sync; pilot in 33-332.Z (first trim ~15 tokens from its own handoff: it sits at the cap) | kit, 33-332.Z | C | 1 worker (Sonnet), 1 reviewer (Opus) | ~7 agent-h | pin back to the vendored copy: one revert commit restores `scripts/` from the last sync |
| P4a RADE | Sentinel in `engine/rade_build.py` `build()` (~line 352: guard 28 lines, covers every engine-built bundle, also 90-161.Z R41); engine release (your step, live); 175 % DPI run (2 lines); CodeQL Python (public repo: free); hash-pinned requirements (6 pins); window layout: keep (already TableLayoutPanel; 42 lines of ink alignment have no standard equivalent) | RADE | C (release), B | 2 workers, 2 reviewers | ~8 agent-h | previous engine tag stays the lock |
| P4b 90-161.Z | Lock bump to the sentinel engine; build-time `go.md` HTML with markdown-it-py (99.3 % word match; card layer ~130 lines; UI change: preview first); CodeQL Python and JS; the hash-pinned manifest exists (9 packages); `-rN` archive and `pac`: decision 7 | 90-161.Z | C (UI), B | 2 workers, 2 reviewers | ~8 agent-h | lock back; page from the previous commit |
| P4c 33-332.Z | Sentinel hash check on top of the try wrapper in `build_paste.py` (your choice: keep the sentinel); CodeQL: not useful (no PowerShell; 0 Python findings) -> keep PSScriptAnalyzer; the 5 Ion defects and the e-signature fix run in a separate Ion session (prompt given 2026-11-23) | 33-332.Z | B | 1 worker, 1 reviewer | ~3 agent-h | revert |
| P4d ICF | Handover runbook entries only (decision 8); `publish_pages.py` keep (it pushes to a second repo with an allowlist, which deploy-pages does not do) | ICF-Source | A | main session | ~1 h | n/a |
| P5 Fleet catch-up and audit | The 6 kit 10.0.0 repos take the kit by the package (after P3); transcription_assistant: remove the 7 old pre-kit copies and the second Stop hook; the first fleet audit (R3) with the outcome metrics (AUD-3); sec-source inventory; 33-332.Z, RADE, 90-161.Z split redesigns found by the audit | 11 repos | C (hooks), B | 3 workers, 2 reviewers, 1 auditor (Opus) | ~14 agent-h | per repo revert |
| P6 Close | Fresh full-history `.7z` export of each changed repo (relayed by the coordinator: your choice in its chat), sent to you in chat (the Drive connector takes ~3.1 MB per call); delete merged and personal-data branches (`claude/tr-r2a-project-tools` holds a third-party name in b765169); session archive list | all | A | main session | ~1 h | n/a |

Totals: ~24 agent runs, ~68 agent-hours, about 4-5 working days with your merges (lane C) as the pacing step.
Order: kit P1 -> P2 -> P3 (pilot) -> RADE P4a (release) -> 90-161.Z P4b and 33-332.Z P4c -> ICF P4d -> P5 -> P6.
Unattended work: the usage limit can stop workers; the main session reports what stopped and resumes it.

## 5. Proof (the prompt's criteria)

| Change | Proof before merge |
|---|---|
| Each retirement or shrink | The standard tool finds at least the same defects on the same commits of the 5 trial repos (W-A, W-B tables as the baseline); the seeded-defect sets of the trials pass (stand-in for mutant kills: GAP 1); CI green; custom script lines fall (`wc -l` in the T2 check) |
| Distribution pilot | Files changed per kit change: before 2 + lock (sync S1) and 3 (S2); target 1 pin + changed instruction files. Token cost per kit change before and after, from the token log (the last 3 kit syncs as the baseline) |
| Sentinel | Cut copies at 10/25/50/75/90/99 % and at each parseable cut point of W-D exit non-zero and run nothing; the full copy runs; on Windows PowerShell 5.1 ISE once (your step) |
| Rule texts | Conflict check record (`docs/reviews/YYYY-MM-DD-rule-conflict.md`), `bloat_check.py --rules` with 28 kit bullets and the session load of each project under 5,500 |
| Split redesigns | Goal-based review (C7): each part has one nameable job; no part receives its parent module |

## 6. GAPS

- **Mutation testing (risk).** No mutation tool in the kit; the prompt's "mutant kill count" cannot be measured. Cost: add `mutmut` (PyPI) as a dev tool, ~3 h for the 3 checkers that are shrunk. Benefit: real kill counts in place of seeded defects. REC: do it in P2 for `code_standard.py` only.
- **Windows-only verification.** ISE paste, WPF, a 175 % window and `pac` cannot run here. Cost: 1 paste step per change for you on a gov device. Benefit: proof on the real host. Risk if skipped: a sentinel that blocks a good paste.
- **JavaScript lint.** 135 JS/MJS files in ICF and 90-161.Z have no linter in the fleet (eslint not trialed). Cost ~2 h trial. Benefit: a defect class nobody checks.
- **Release attestation chain.** The Sigstore root and Rekor inclusion were never verified (host blocked). Cost: allow `tuf-repo-cdn.sigstore.dev` for the RADE release step. Benefit: full release trust.
- **icf deploy repo settings.** Unchecked (attach denied). Cost: one look at Settings by you. Benefit: handover facts complete.

## 7. Not in this plan (from the approved list)

FSRS, the installable PWA, OKLCH and Authenticode signing (your "2yes", 2026-11-23); fleet v2 Part 1 (done by fleet v2);
the ICF 30-minute drill (needs the incoming maintainer).
