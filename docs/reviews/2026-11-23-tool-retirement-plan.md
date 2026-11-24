# Custom tool retirement program: plan (for the Maintainer's approval)

APPROVED by the Maintainer, 2026-11-23 17:12 America/Chicago, in this session's chat (own message: "I approve the plan"): sections 3 and 3b (exact texts), the phases, lanes, models, agents and hours, and decisions 1-10. Written 2026-11-23 from ~16:45 America/Chicago by session "Kit · Tool retirement · 2026-11-23 · #125".
Nothing is built. Approving this plan approves the exact rule texts in section 3 (AGENTS.md "Rule text"), the skill, instruction-file and account texts in section 3b, the
phase lanes, models, agents and hours, and each "REC" marked "(choice)" that you answer.

Inputs (all in this pull request; the research files are copied from their worker branches, not merged):
[coverage list](2026-11-23-tool-retirement-coverage.md) (85 rows: 51 in, 34 out, approved; ION-1 and AUD-1..5 added),
[research plan](2026-11-23-tool-retirement-research-plan.md),
R1 [kit tools](../tools.md), R2 [project tools](2026-11-23-tr-r2a-project-tools.md) and
[kit 10.0.0 repos](2026-11-23-tr-r2b-kit10-repos.md), R3 [ICF scans](2026-11-23-tr-r3-icf-scans.md),
R4 [linters](2026-11-23-tr-wa-linters.md), [scanners](2026-11-23-tr-wb-scanners.md) (W-B: final, d071cb1),
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
| CodeQL | 7 findings: 6 Python (4 = one ReDoS in `scripts/build_site_html.py:121`, copied to 4 repos; 2 in test files) and 1 JS (90-161.Z); no PowerShell support | W-D |
| Paste truncation | Ion: 0 of 700 cuts parse (try wrapper). RADE-built bundles (90-161.Z R41): 49 of 650 cuts parse; the cut at line 13,579 parses (re-checked) and starts the engine | W-D |
| Ion detectors vs Presidio | Ion precision 0.94, recall 0.83; Presidio 0.61 / 0.83. 5 Ion defects (case-sensitive street types, passports as SSN Low, "_" in e-mail, name span over line breaks, middle initial without a dot) | R4e |
| Ion e-signature DoD IDs | 3 layouts give SSN, 7 give no hit (25 layouts tested) | main session, 2026-11-23 |
| Splits made for the 450 cap | 22 judged: 11 cohesive, 9 mixed, 2 arbitrary | R4f |
| Project tools | RADE 18 / 2,391 lines; 90-161.Z 31 / 4,826; 33-332.Z 4 / 789; ICF 209 / 36,183 (73 old review scripts); sec-source 14 / 2,062; kit 10.0.0 repos 84 / 14,499 | R2 |
| Kit 10.0.0 repos | 43 of 54 kit files differ from 11.0.1; transcription_assistant runs 2 Stop hooks (kit and an old copy) | R2b |
| ICF handover | 2 non-noreply addresses in history; ICF-Source cannot have rulesets or secret scanning on its plan; icf settings not checked (attach denied) | R3 |
| Content check vs gitleaks / trufflehog / detect-secrets | With custom rules gitleaks covers 10 of 11 checks, the others 9 of 11; none covers `unscanned`, the commit author and message scan (809 findings in ICF history), the `.check` semantics or the hook mode; default rules give 0 true findings. Seeded: content tool 22 of 23 (the 23rd is exempt by design), gitleaks custom 19, trufflehog 18, detect-secrets 17 | W-B |
| Instruction check vs Vale | 4 of 7 finding kinds match with 0 false positives on 225 real steps; next, cue and long need the step reader (54 false positives without it) | W-B |
| Session load after the rule texts | full tier ~+72 tokens: RADE ~5,485, 90-161.Z ~5,453, ICF ~5,215, **33-332.Z ~5,540 (over the 5,500 cap: it trims ~50 tokens of its own handoff before any sync that carries P1)** | measured on a copy |

## 2. Decisions for the Maintainer (answer each; REC first)

1. **File size cap (AUD-3 against R1).** **DEC: A** (the Maintainer, this session's chat, 2026-11-23 16:47 America/Chicago: "1a"; scope: this program). The split audit shows that half of the cap-driven splits are mixed or arbitrary.
   - **REC: A.** File size only warns (C4 of `code_standard.py` becomes WARN); a split is reviewed against its goal (rule C7 below). R1 is not added.
   - B. Keep the 450 fail and add R1: "A hand-written file that passes 80 % of its line cap (360 of 450) is split in the pull request that grows it."
2. **T2 ratchet.** A. **REC:** FAIL on the total of custom script lines, baseline 17,096 (65 files); only you approve a higher number. B. WARN only, as AUD-3 asks for line counts. A total cannot be gamed by a split, so A keeps AUD-3's intent.
3. **Distribution.** **REC:** pip/pipx package (local and offline runs, one pin, works with the existing pre-push hook; pre-commit refuses `core.hooksPath`; a reusable workflow runs only in CI). Pilot: **33-332.Z** (68 kit files, 4 project tools, small). Alternative pilot: SPAR (no project tools: lowest risk, least learning).
4. **Sync scripts.** A. **REC:** keep `sync_baseline.py` for the 17 instruction files after the pilot, and fix its defect first: it overwrites a project's edits to kit files without a conflict (copier keeps them). B. Move to copier (keeps project edits; ~1,915 lines go; the role-word rename, settings merge and lock gate stay custom).
5. **token_log.** **REC:** keep (your decision of 2026-11-23 to keep the token log branch; OTel needs a collector and lacks web searches).
6. **shellcheck.** **REC:** add it as a WARN step in the code standard first, with the measured fleet list (rule T5), then fix per repo.
7. **90-161.Z revision files** (75 `-rN` files, 67,606 lines; 0 base names with two revisions on disk, so nothing is superseded) and **pac solution**. A. **REC:** keep the `-rN` names (each is the current revision a person pastes; a versioned module changes the paste path: a later 90-161.Z decision); `pac solution` for the packaging part only (~130-180 lines), when `pac` can run on a dev machine. B. Versioned module now (one module, version in the file header).
8. **ICF trial items** (`==term==`, Block split, 2 history addresses, no branch protection). **REC:** write them into the ICF handover runbook for the incoming maintainer; no ICF code change in this program.
9. **Content check (W-B).** A. **REC:** keep `check_content*`; gitleaks stays the CI second net (it already runs in `security.yml`); W-B's final report: gitleaks with the ported rules matched all 1,137 content-tool findings, found 43 more (matching differences: a split address, `%40` in a URL, a phrase over two lines) and missed 0; the kit gains those 3 matching fixes. B. Shrink to the parts no tool covers and run gitleaks with generated custom rules (two scanners, two outputs).
10. **Instruction check (W-B).** A. **REC:** keep `check_instructions.py` (0 false positives, the step reader is the value). B. Shrink: keep the step reader, send steps to Vale for actions, pointer, vague and wait.

**DEC 2-10 and the pilot:** the Maintainer accepted every REC of decisions 2-10 ("Accept all RECs") and chose the pilot **33-332.Z** (question dialog in this session, 2026-11-23 17:09 America/Chicago; scope: this program). Open: the Maintainer's approval of the whole plan, with its rule texts.

## 3. Rule texts (exact text for approval)

Result on a copy of AGENTS.md: 76 -> 73 lines, kit rule bullets 31 -> 28 (+1 project rule), kit AGENTS.md +321 bytes
A project gets +291 bytes (~72 tokens) in the full tier and +103 bytes (~25 tokens) in the starter tier: C9 sits in the `<!-- full -->` block, and C11 and C12 sit in "Project rules", which a sync does not touch. No new AGENTS.md line. Three bullets are merged (cuts 1-3: "The Maintainer's decisions" into "Decisions", "Host limit" into "Delivery", "README" into "One home"); three are extended (C7, C8, C9; C9 also takes T1, because `bloat_check.py` exists only in the full tier); three role-word texts change (C10-C12). C4-C6 are not used. No changed bullet adds a starter-tier pointer to an advanced file (the old ones stay: README's `scripts/bloat_check.py`, Delegation's `scout`). T6 gets no AGENTS.md pointer (token cap); its check's FAIL line states the rule. Rules a check enforces
get a pointer only; the check's FAIL line states the full rule. Where each prompt rule lives:

| Prompt rule | Home | Enforcing check (trigger) | Defect it prevents |
|---|---|---|---|
| T1 search first | C9 "Caps and audit" ("or a script has no docs/tools.md row") + check message | `bloat_check.py`: every tool file the repo owns (any folder; kit-locked files are listed in the kit's own docs/tools.md) has a docs/tools.md row with 3 candidates searched, or "none known" with the search terms (every push) | new tools instead of existing ones (cause 1) |
| T2 ratchet | C9 "Caps and audit" ("their approved baseline") | `bloat_check.py`: total custom script lines <= the baseline; a higher baseline needs a DECISIONS row By the Maintainer with the number (every push) | custom code grows back (causes 1, 3) |
| T5 debt list first | C8 "Lean instructions" | `bloat_check.py --rules`: a pull request that adds a rule line, a check entry point in `check.sh` or a stricter cap in `KIT_CAPS` fails without a `docs/reviews/*-debt.md` record that names its hash (like the conflict-check record) | caps stricter than the fleet can meet (cause 3; ICF 21 files) |
| T6 one role word, approval channels | no new text: the hard rule "The Maintainer's approval" already says "The Maintainer's own request for that action is the approval", "Maintainer changes" names the other channels, and "Rule text" covers approval of shown texts; the role word changes in C10, C11, C12 ("Owner"/"the owner" -> "the Maintainer") | `log_check.py`: a new DECISIONS row (dated after the kit release that adds this check) By the Maintainer quotes the approval of its exact text; `bloat_check.py`: no other role word in kit-synced text (every push) | 3 rows written from dialog answers on 2026-11-23 (cause 4) |
| T7 plan coverage | `.claude/skills/handoff/SKILL.md` (moved out of AGENTS.md for the token cap) | `log_check.py --coverage <file>`: rows marked = rows, no "ask" (before a plan PR) | the Part 2 miss of fleet v2 |
| R1 80 % split | not added (decision 1 = A) | none | (cap met at sync time: handled by the goal-based review, C7) |
| R3 fleet audit | C9 "Caps and audit" + audit skill "Fleet" section | `bloat_check.py`: AUDIT DUE (fleet) at a kit tag or 14 days (kit check-in) | drift found only at sync (cause 5) |
| AUD-1 goal per check | C8 + `code_standard.py` C1: a check script's header has a `Prevents:` line | C1 (every push) | checks with no testable goal |
| AUD-2 goal-based review | C7 "Fresh review" | reviewer brief (delegate skill) | splits that only move a number (R4f) |
| AUD-3 outcome metrics | C9 (file size warns) + audit skill (defects per check, mutant kill rate, files per kit change, fix-of-a-fix rate) | audit report | proxies gamed by splits |

**Change against the prompt's T6 text (disclosed):** the prompt says "an approval counts only in the acting session's own chat". That text conflicts with "Maintainer changes" (briefs from a session the Maintainer started), "Rule text" (one approval covers every text a plan or a pull request shows in full) and the plan-continuation rule in "Handoff". So the plan adds no approval text (an earlier draft, C4, did and caused these conflicts); the check enforces the DECISIONS quote. C10-C12 also reverse two DECISIONS rows: row 13 (2026-11-21: the exception stays "the Owner's own message") and row 108 (2026-11-23: "Not changed: ... the kit's own Project rules"); C11 changes the recorded approver of "Fleet choices" from "the owner" to "the Maintainer" (the same person, the new role word).

**T5 fleet debt of the new checks** (measured 2026-11-23; P1 makes each one FAIL in the kit and WARN in projects until its debt is 0):

| Check | Kit debt | Project debt |
|---|---|---|
| T1 tools.md rows | 65 scripts (kit docs/tools.md) | RADE 18, 90-161.Z 31, 33-332.Z 4, ICF 209 (73 of them old review scripts), sec-source 14, kit 10.0.0 repos 84 |
| T2 ratchet | 0 (baseline = today) | 0 |
| T6 DECISIONS quote | 0 (new rows only) | 0 |
| T7 coverage | 0 (this list: 85 rows, 0 ask) | 0 |
| AUD-1 `Prevents:` header | 47 of 47 check entry points (0 have it) | counted in P1 per repo |
| T6 role word | 13 lines in 3 files of the sync copy set; 50 lines in 10 tracked files outside docs/ (reviewer's count, 2026-11-23). Some must keep the literal: `scripts/sync_baseline.py:116-117`, test values in `sync_baseline_cli_test.py`, dated attributions. P1 renames only the others, so the check needs an allow list of those lines | each project's own text, counted in P1 |
| R3 fleet AUDIT DUE | 1 (no fleet audit yet: P5) | n/a |

Also changed in P1 so no reference breaks: `.claude/rule-tests.md` line 26 (Section "Host limit" -> "Delivery"), lines 46 and 48 ("The Maintainer's decisions" -> "Decisions"), and the cites of the "README" label in `scripts/bloat_check.py:50`, `scripts/bloat_check_rules.py:11,296,331` and `scripts/bloat_check_test_rules.py:128` (C3 removes that label). The T5 debt record names the hash of the changed rule lines as `bloat_check.py --rules` prints it (the same hash as the conflict record).

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
- **Decisions.** Make routine decisions yourself. Ask the Content Approver about content approval, and the Maintainer about source authority and what "The Maintainer's approval" names, with all open questions in one round and in the format of the Maintainer's preferences (else a question dialog where one exists, 2–4 options each, the recommendation first). Record each decision of the Maintainer in docs/DECISIONS.md or its canonical document, with its date and scope: it binds the task or thing it names, and every session only as a line in "Project rules". Before you change an approved design, source or value, search docs/DECISIONS.md for it and ask.
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
- **Delivery.** Deliver every change without being asked: commit, push, open a pull request, then merge it by its lane. Lane A, docs that are not rules: merge when the checks are green. Lane B, code, scripts and checks: merge when the checks are green and the fresh review finds no MAJOR finding. Lane C, rule text, instruction and guard files, a UI or design change the Maintainer has not approved (show a preview first), a MAJOR finding you cannot fix, a self-review, a pull request not opened for this work ("Git history"), and each case in "The Maintainer's approval": ask the Maintainer. Then verify that origin/main has the commit and republish the affected artifacts. Steps: `.claude/skills/deliver/SKILL.md`. A host limit (for example a required branch, or a push or merge the host does not allow without the Maintainer) wins over "Delivery": do the steps it allows and report the rest as blocked, with the cause and what unblocks it.
```

### C3. One home (absorbs "README" (bullet cut 3))

Old:

```text
- **One home.** One fact, rule or value lives in one place; other places link to it. Before you add a file, rule, script, check or doc section, extend or replace an existing one. A change removes what it makes obsolete (code, docs, files, rules) in the same commit.
```

Old:

```text
- **README.** A change that alters what the project is, does, or how to install, run or use it updates README.md in the same pull request; README.md opens with the "Purpose" line of this file. Enforced in part: `scripts/bloat_check.py`.
```

New:

```text
- **One home.** One fact, rule or value lives in one place; other places link to it. Before you add a file, rule, script, check or doc section, extend or replace an existing one. A change removes what it makes obsolete (code, docs, files, rules) in the same commit. A change that alters what the project is, does, or how to install, run or use it updates README.md in the same pull request; README.md opens with the "Purpose" line of this file. Enforced in part: `scripts/bloat_check.py`.
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
- **Lean instructions.** Instruction files and host prompts hold rules only, one line per rule (every line costs tokens on every task and can lower adherence); a rule that needs more lines is a procedure. A rule a hook or test enforces becomes a pointer to it; a procedure that only some tasks need becomes a skill. A new rule, check or stricter cap names its defect and first lists its fleet debt.
```

### C10. Instructions people follow (T6 one role word (hard rule))

Old:

```text
- **Instructions people follow.** Write every instruction a person reads and acts on (pages, READMEs, go.md, window cards, hand steps, messages) in ASD-STE100 Simplified Technical English, unless the Owner's own message says otherwise for that text. Each step holds one action, or the numbered actions that are all on one screen; it names the exact thing on the screen and the exact text to type, says what the person sees next, and says whether to wait, go on or note a value (show the value again where it is needed; never make the person remember it). Show each step on the screen where the action happens, at the time it is needed (in chat: the step names the screen where the action happens). Enforced: `.claude/skills/instructions/SKILL.md` before any such text is written or changed, `scripts/check_instructions.py` on every push, and a fresh-reader test before release.
```

New:

```text
- **Instructions people follow.** Write every instruction a person reads and acts on (pages, READMEs, go.md, window cards, hand steps, messages) in ASD-STE100 Simplified Technical English, unless the Maintainer's own message says otherwise for that text. Each step holds one action, or the numbered actions that are all on one screen; it names the exact thing on the screen and the exact text to type, says what the person sees next, and says whether to wait, go on or note a value (show the value again where it is needed; never make the person remember it). Show each step on the screen where the action happens, at the time it is needed (in chat: the step names the screen where the action happens). Enforced: `.claude/skills/instructions/SKILL.md` before any such text is written or changed, `scripts/check_instructions.py` on every push, and a fresh-reader test before release.
```

### C11. Fleet choices (T6 one role word (project rule))

Old:

```text
- **Fleet choices.** A choice the owner saved on the fleet page counts as the owner's approval only after the applying session shows it in full and the owner confirms it in their own message (the owner, 2026-11-19).
```

New:

```text
- **Fleet choices.** A choice the Maintainer saved on the fleet page counts as the Maintainer's approval only after the applying session shows it in full and the Maintainer confirms it in their own message (the Maintainer, 2026-11-19).
```

### C9. Caps and audit (T1, T2, R3, AUD-3 (decision 1 = A))

Old:

```text
- **Caps and audit.** `scripts/bloat_check.py` (run by the check-in and by check.sh) fails when this file passes 200 lines, when the session load passes 5,500 tokens (third-party skills and agents in `.check`: own cap 1,500), or when a skill or agent file states a rule whose home is this file. The full audit runs when the Maintainer asks for it, and a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.
```

New:

```text
- **Caps and audit.** `scripts/bloat_check.py` (run by the check-in and by check.sh) fails when this file passes 200 lines, when the session load passes 5,500 tokens (third-party skills and agents in `.check`: own cap 1,500), when a skill or agent file states a rule whose home is this file, or when custom script lines pass their approved baseline or a script has no docs/tools.md row; file size only warns. The full audit runs when the Maintainer asks for it and for all fleet repos at each kit release or 14 days after the last one, and a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.
```

### C12. Project rules comment (T6 one role word (kit comment, not a rule))

Old:

```text
<!-- This project's own rules: one line each, at most 15 (full tier: scripts/bloat_check.py checks the cap). Add, change or remove a line only with the owner's approval of its exact text; date it, for example "(the owner, 2026-11-09)". Mark a rule that nothing may relax "(cannot be changed)". -->
```

New:

```text
<!-- This project's own rules: one line each, at most 15 (full tier: scripts/bloat_check.py checks the cap). Add, change or remove a line only with the Maintainer's approval of its exact text; date it, for example "(the Maintainer, 2026-11-09)". Mark a rule that nothing may relax "(cannot be changed)". -->
```

## 3b. Changes to skills, other instruction files and your account preferences

Exact texts for approval with this plan. They land in P1 (kit, lane C), then reach the projects by their kit sync.
Skill texts are procedures, not rules: they add no AGENTS.md line and no session-load token (only skill names and
descriptions load at start; no description changes).

### Skills (kit `.claude/skills/`)

| ID | File, place | Change (exact text) | Why (evidence) |
|---|---|---|---|
| S1 | `handoff/SKILL.md`, "Write a handoff", the "Approved plan" item (line 16), appended | "A plan made from a source plan first lists every source item as in, out or later, with a count table; the Maintainer approves that list before the plan; `python3 scripts/log_check.py --coverage <file>` fails on an unmarked or \"ask\" row or a count mismatch (T7)." | T7: fleet v2 left out the master plan's Part 2 with no question (lessons file, section 3) |
| S2 | `rule-change/SKILL.md`, "Where it belongs", new last paragraph | "Before a new rule, check or stricter cap: list what it would fail today in every fleet repo, with a fix plan, in `docs/reviews/YYYY-MM-DD-<topic>-debt.md`, with the line `debt-check: <hash>` for the hash that `python3 scripts/bloat_check.py --rules` prints (T5)." | T5: the 450 cap met 21 ICF files (the plan said 3) |
| S3 | `audit/SKILL.md`, new section "## Fleet audit" before "## Rules for the auditor" | "At each kit release, or 14 days after the last fleet audit (AUDIT DUE (fleet) at the kit check-in), run the full audit for every fleet repo in a fresh session. Report per repo: kit version and lock state, caps, open branches, kit lag; and the outcome metrics: defects found per check in the last 30 days, mutant kill rate where measured, files changed per kit change, and fix-of-a-fix rate (commits that fix a commit of the last 7 days). File size and file counts are warnings only. Write the date to `fleet.last_audit` in kit.config.json. Each check, and this skill, gets a retire / shrink / keep line in docs/tools.md." | R3, AUD-3, AUD-5; split audit: 11 of 22 splits mixed or arbitrary |
| S4 | `delegate/SKILL.md`, "Brief", two new bullets after "No design decisions" | "- \"A blocked command or a blocked check stops the task: report it; do not run it another way and do not change the text to pass.\"" and "- For a change made to pass a check: the design goal, not the metric (AGENTS.md \"Fresh review\")." | 2 guard workarounds on 2026-11-23 (R4e rebuilt e-mail strings with `chr(64)`; W-B wrapped commands in script files); AUD-2 |
| S5 | `deliver/SKILL.md`, "Merge lanes", new bullet under the table | "- A script that `scripts/check.sh`, `scripts/check.local.sh` or a hook runs, and a workflow file, is a guard file: lane C." | the plan's first and second reviews found 3 lane errors of this kind |
| S6 | `personal-data/SKILL.md`, "When it blocks", new bullet | "- A block on invented test data: describe the pattern in words (for example \"a 9-digit SSN with dashes\"); never rebuild the string to pass the check." | R4e incident, 2026-11-23 |
| S8 | `delegate/SKILL.md`, "Review and merge", step 3, appended; the same line in the body of `.claude/agents/reviewer.md` | "Any workaround of a guard (a string rebuilt to pass the content check, a command wrapped in a file to pass the worker guard), in the diff or in scratch output, is a MAJOR finding." | AUD-6b, added 2026-11-23 ~17:15 (the Maintainer: "Approve as shown"); 2 workarounds on 2026-11-23 |
| S7 | `kit-update/SKILL.md`, "Sync steps" | the pilot's steps (package pin plus the sync of the 17 instruction files): exact text in the P3 pull request, approved by your lane C merge | P3 (decision 3) |

### Other instruction files (kit)

| ID | File | Change (exact text) |
|---|---|---|
| F1 | `.claude/rule-tests.md` | line 26, Section column: "Host limit" -> "Delivery"; lines 46 and 48: "The Maintainer's decisions" -> "Decisions" (C1, C2 remove those labels) |
| F2 | `scripts/bloat_check.py:50`, `scripts/bloat_check_rules.py:11,296,331`, `scripts/bloat_check_test_rules.py:128` | the label "README" -> "One home" (C3 removes it) |
| F3 | Kit-synced text with the old role word | "the owner" / "Owner's" -> "the Maintainer" / "Maintainer's" (13 lines in 3 files of the sync copy set; 50 lines in 10 tracked files outside docs/), except `scripts/sync_baseline.py:116-117`, the test values in `scripts/sync_baseline_cli_test.py` and dated attributions such as "(the owner, 2026-11-13)" |
| F4 | `CLAUDE.md`, `.claude/agents/*.md`, `docs/host-prompts.md` | no change (checked: no removed label, no old role word) |
| F5 | Projects | each project's AGENTS.md gets section 3 by its sync; 33-332.Z first trims ~50 tokens of its own `docs/NEXT_PROMPT.md` (it would be at ~5,540 of 5,500) |

### Your account preferences (source: kit `PREFERENCES.md`; you paste them into your account)

Each extends an existing line; each also gets a row in `PREFERENCES.md` "Why each rule exists". `PREFERENCES.md` keeps
its dated "the owner" attributions (history; F3 excludes them).

| ID | Line it extends ("How to work" / "Reporting") | Text added at the end of that line | Why (evidence) |
|---|---|---|---|
| A1 | "Plan mode only for: ... continue it without a new review." | "A plan made from a source plan first marks every source item in, out or later, for my approval." | T7 outside a repo too (fleet v2 Part 2 miss) |
| A2 | "In a repo, its AGENTS.md sets delivery, git, review and delegation. ..." | "A brief tells each agent that a blocked command or check stops its task: it reports the block and never runs the step another way." | 2 guard workarounds by workers on 2026-11-23 |
| A3 | "For each number from data, give the query or command and its as-of time. ..." | "Take each date and time from a clock or a commit, never from memory." | 2026-11-23: 6 times in review files were estimates, up to 75 minutes off, one in the future |


## 4. Phases

Lanes (AGENTS.md "Delivery"): the checks below are run by `check.sh` and the hooks, so they are guard files: lane C
(your merge) unless marked otherwise. Models: workers on the standard tier (Sonnet), reviewers of guards, hooks and
security on the strong tier (Opus), goal-based split reviews on a model other than the author's, the main session on
the strong tier. One PR per retirement (T3). Every phase ends with a fresh review on the head commit.

| Phase | Work | Repos | Lane | Agents (model) | Hours | Rollback |
|---|---|---|---|---|---|---|
| P1 Rules and checks | Section 3 texts in AGENTS.md (kit); checks: T1 tools.md rows, T2 ratchet, R3 AUDIT DUE (fleet), AUD-1 `Prevents:` header, `code_standard.py` C4 to WARN (decision 1A), T6 and T7 in `log_check.py`; docs/tools.md moves from the R1 review file (kit-only; bootstrap removes it as it removes docs/FILES.md; each project gets its own list); skill texts; the rule conflict check | kit | C | 2 workers (Sonnet, disjoint files: `bloat_check*`+`code_standard*` / `log_check.py`+skills+docs), 2 reviewers (Opus), 1 conflict reviewer (Opus) | ~10 agent-h, ~4 h wall | revert the PR; caps as before |
| P2 Kit shrink and repair | (a) `code_standard.py` Python parse, line and file-size checks move to ruff + pylint config; header, comment, safety, generated, shell and PowerShell checks stay; (b) content check: decision 9; (c) `check_instructions.py`: decision 10; (d) sync: stop on a project's local edit of a kit file (check_lock --verify first); (e) redesign 5 kit splits along the seams in R4f (`sync_baseline_run`, `code_standard_ratchet`, `token_log_test_report`, `code_standard_test_gate`, `check_content_scan_settings`); (f) fix the ReDoS at `build_site_html.py:121`; (g) shellcheck as WARN with the fleet list (decision 6); (h) AUD-5 records for `bloat_check*` and the audit skill; (i) AUD-6: `scripts/worker_guard.py --scan <dir or diff>` finds strings rebuilt to pass the content check (`chr()`, escapes, joins or encodings that build `@` or a blocked word) and commands wrapped in a file to pass the worker guard; the delegate skill runs it on each worker branch and scratch folder before the review; first run on the 2026-11-23 scratch folders (debt: 2 known cases); text S8; (j) skill use (the Maintainer, 17:23): the token log's Stop hook also counts Skill-tool calls and Reads and shell slices of SKILL.md files per session (`scripts/token_log_rows.py`), a delegate brief line "Read each skill you need in full with the Read tool, never by grep or sed.", the false skill name fixed in `scripts/skill_use.py`, and a fleet-wide skill-use audit 14 days after the token-log change (docs/reviews/2026-11-23-skill-use-audit.md) | kit | C | 3 workers (Sonnet), 3 reviewers (Opus; split review on a model other than the author's) | ~16 agent-h, ~6 h wall | revert each PR alone |
| P3 Distribution pilot | pip/pipx package of the kit checks (decision 3); `check.sh` reads the kit scripts from the package; the 17 instruction files stay on sync; pilot in 33-332.Z (first trim ~50 tokens from its own handoff: it would be at ~5,539) | kit, 33-332.Z | C | 1 worker (Sonnet), 1 reviewer (Opus) | ~7 agent-h | pin back to the vendored copy: one revert commit restores `scripts/` from the last sync |
| P4a RADE | Sentinel in `engine/rade_build.py` `build()` (~line 352: guard 28 lines, covers every engine-built bundle, also 90-161.Z R41); engine release (your step, live); 175 % DPI run (2 lines; 125, 150 and 200 % runs exist); CodeQL Python workflow (a workflow file: guard; public repo: free; needs `security-events: write`); hash-pinned requirements (6 pins) and its CycloneDX SBOM; window layout: keep (already TableLayoutPanel; 42 lines of ink alignment have no standard equivalent); build-time Markdown: none needed (RADE's intro is already static) | RADE | C | 2 workers, 2 reviewers | ~8 agent-h | previous engine tag stays the lock |
| P4b 90-161.Z | Lock bump to the sentinel engine; build-time `go.md` HTML with markdown-it-py (99.3 % word match; card layer ~130 lines; UI change: preview first); CSP `connect-src 'none'` for the task text, with one allowed source for the Copy button's 1.4 MB script fetch (W-D; a deviation from coverage row P2-4b, which says `connect-src 'none'`: the Copy button needs that one fetch); CodeQL Python and JS workflow (guard); CycloneDX SBOM from the hash-pinned manifest (9 packages); `-rN` and `pac`: decision 7 | 90-161.Z | C | 2 workers, 2 reviewers | ~8 agent-h | lock back; page from the previous commit |
| P4c 33-332.Z | Sentinel hash check on top of the try wrapper in `build_paste.py` (run by `check.local.sh`, so a guard file) (your choice: keep the sentinel); CodeQL: low value (no PowerShell; 1 Python finding, the shared ReDoS, fixed in the kit by P2 f) -> keep PSScriptAnalyzer; the 5 Ion defects and the e-signature fix run in a separate Ion session (prompt given 2026-11-23) | 33-332.Z | C | 1 worker, 1 reviewer | ~3 agent-h | revert |
| P4d ICF | Handover runbook entries only (decision 8); `publish_pages.py` keep (it pushes to a second repo with an allowlist, which deploy-pages does not do); `content_pipeline.py` keep (handover tool, has a test) | ICF-Source | A | main session | ~1 h | n/a |
| P5 Fleet catch-up and audit | The 6 kit 10.0.0 repos take the kit by the package (after P3); transcription_assistant: remove the 7 old pre-kit copies and the second Stop hook; the first fleet audit (R3) with the outcome metrics (AUD-3); sec-source inventory; 33-332.Z, RADE, 90-161.Z split redesigns found by the audit | 11 repos | C (hooks), B | 3 workers, 2 reviewers, 1 auditor (Opus) | ~14 agent-h | per repo revert |
| P6 Close | Fresh full-history `.7z` export of each changed repo (relayed by the coordinator: your choice in its chat; the ICF export holds the 2 history addresses, so it stays private), sent to you in chat (the Drive connector takes ~3.1 MB per call); a list of branches to delete (merged ones, and `claude/tr-r2a-project-tools`, which holds a third-party name in b765169): deleted only with your approval (irreversible); session archive list | all | A (C for deletes) | main session | ~1 h | n/a |

Totals: ~29 agent runs (5 + 6 + 2 + 4 + 4 + 2 + 0 + 6), ~68 agent-hours, about 4-5 working days with your merges (lane C) as the pacing step.
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

- **Mutation testing (risk).** No mutation tool in the kit; the prompt's "mutant kill count" cannot be measured. Cost: add `mutmut` (PyPI) as a dev tool, ~3 h for the 3 checkers that are shrunk. Benefit: real kill counts in place of seeded defects. REC: do it in P2 for `code_standard.py` only, with the mutmut version pinned at P2 start and listed in the PR.
- **Windows-only verification.** ISE paste, WPF, a 175 % window and `pac` cannot run here. Cost: 1 paste step per change for you on a gov device. Benefit: proof on the real host. Risk if skipped: a sentinel that blocks a good paste.
- **JavaScript lint.** 135 JS/MJS files in ICF and 90-161.Z have no linter in the fleet (eslint not trialed). Cost ~2 h trial. Benefit: a defect class nobody checks.
- **Release attestation chain.** The Sigstore root and Rekor inclusion were never verified (host blocked). Cost: allow `tuf-repo-cdn.sigstore.dev` for the RADE release step. Benefit: full release trust.
- **icf deploy repo settings.** Unchecked (attach denied). Cost: one look at Settings by you. Benefit: handover facts complete.

## 7. Project tool records (prompt step 3: retire / shrink / keep)

| Tool | Record | Evidence |
|---|---|---|
| RADE `engine_files.py` + `release.yml` (engine lock and release) | keep | the release already uses `actions/attest-build-provenance`; no standard tool writes the 42-file lock (R2a) |
| RADE `engine/rade_*.py` build | keep; gains the sentinel (P4a) | no standard tool builds a paste bundle (R2a, W-D) |
| 90-161.Z `build_task_scripts.py` (task-script generator) | keep | ModuleBuilder / PS2EXE do not give paste text (R2a) |
| 90-161.Z `rebuild_all.py` | keep (shrink to a Make target later if the builders shrink) | R2a |
| 90-161.Z `bump_lock.py` | keep | Renovate and Dependabot cannot update a hash set (R2a) |
| 90-161.Z flow builders (866 lines) | shrink the packaging part with `pac solution` (decision 7) | W-D |
| 33-332.Z `build_paste.py` | keep; gains the sentinel hash check (P4c) | R2a, W-D |
| ICF `publish_pages.py`, `content_pipeline.py` | keep (P4d) | R2a |
| ICF 73 old review scripts (6,725 lines) | retire: move out of the tracked tree or delete in an ICF session (incoming maintainer's choice) | R2a |
| transcription_assistant 7 pre-kit copies | retire (P5) | R2b |
| sec-source 14 tools (2,062 lines) | inventory only; records in P5 | R2a |

## 8. Not in this plan (from the approved list)

FSRS, the installable PWA, OKLCH and Authenticode signing (your "2yes", 2026-11-23); fleet v2 Part 1 (done by fleet v2);
the ICF 30-minute drill (needs the incoming maintainer).
