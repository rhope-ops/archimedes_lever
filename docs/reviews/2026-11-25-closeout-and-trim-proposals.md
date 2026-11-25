# Close-out lists and context-trim proposals (2026-11-25)

Written 2026-11-25 13:30 America/Chicago by session "Kit · Close-out and context-trim proposals · 2026-11-25"
(session_01PyXpdRt1Kj2iwqZ2uLooet), for "Kit · Fleet coordinator 4", under the approved
[archival plan](2026-11-25-archival-plan.md). **Proposals only.** This report changes no rule, skill, script or plan. Each
AGENTS.md text in Part B is rule text: the Maintainer approves each exact text, or it does not change.

Base: origin/main 9454e6e. Fleet repos: `add_repo` was denied in this session (auto-mode classifier), so fleet states come
only from kit records. Such a row says "not verified".

## Part A: close-out lists

Proposal key: **done** (with evidence) · **verify** (kit records conflict; check in a session that has the fleet repo,
then mark done or move) · **move** (to the named home) · **drop** (with the reason).

New homes named below:

- **Audit-metrics plan**: a new plan `docs/reviews/YYYY-MM-DD-audit-metrics-plan.md`, not written yet. The Maintainer
  approves it. It takes the audit-the-audit rows, with their text copied from
  [2026-11-24-fleet-audit.md](2026-11-24-fleet-audit.md) "Audit the audit".
- **Archive "Open"** / **Archive "Needs the owner"**: the sections of
  [2026-11-24-kit-handoff-archive.md](2026-11-24-kit-handoff-archive.md). They are outside the session load.
- **Project NEXT_PROMPT**: that repo's `docs/NEXT_PROMPT.md`. Not verified here.
- **KIT_HANDOFF "Needs the owner"**: only where the line already exists. No new text goes there.

### A1. Tool-retirement plan ([plan](2026-11-23-tool-retirement-plan.md), [handoff](2026-11-23-tool-retirement-handoff.md), KIT_HANDOFF "Approved plan")

| # | Open item | True state (evidence) | Proposal |
|---|---|---|---|
| T1 | P3 follow-up: `--kit-install` after a branch switch (S7 text) | Done: the S7 text in kit PR 168 (merged 2026-11-24); kit #173 SessionStart hook runs `--kit-install` when the verify fails (`.claude/skills/kit-update/SKILL.md:44`) | done |
| T2 | P3 follow-up: check-in KIT line when the package is missing | Done: `scripts/session_checkin.sh:64-70` prints `KIT: N kit scripts ... are missing` (follow-ups 2 item 5) | done |
| T3 | P3 follow-up: "MAINTAINER_GUIDE step" | Not verified: no `docs/MAINTAINER_GUIDE.md`; `docs/MAINTAINER_RUNBOOK.md` has no package or `--kit-install` step; no record says what the step is. The package installs by itself (SessionStart hook, kit #173) | drop: no source names the step. If the Maintainer knows it: move to Archive "Open" as PATCH item (g) |
| T4 | P3 follow-up: bandit in security.yml | Done: `.github/workflows/security.yml:2,11`; local full lane too (follow-ups 2 item 13) | done |
| T5 | P3 follow-up: "4 MINOR of PR 168" | Not verified: PR 168 has no comments; no repo file lists the 4 findings (searched docs/ and the last 40 commits) | drop: no list exists, and a MINOR finding does not block. Coordinator 4: keep it only if your chat has the list |
| T6 | P4b: 90-161.Z PR 235 (go.md build-time HTML) | Records conflict: KIT_HANDOFF:15 says "open for your look"; [coordinator state](2026-11-23-fleet-v2-coordinator-state.md):236 lists #235 as merged (follow-ups 2, 2026-11-25 04:20-06:20); [follow-ups 2 plan](2026-11-25-followups-2-plan.md):12 says the Maintainer approved it | verify |
| T7 | P4: SBOM steps (ask rule `*--output*`) | Records conflict: KIT_HANDOFF:15 says open; coordinator state:234,236 says RADE #184 SBOM and 90-161.Z #238 pins and SBOM are merged; the ask rule stays (follow-ups 2 item 2 dropped: the Maintainer approves each run) | verify |
| T8 | P4a: RADE CodeQL | Records conflict: KIT_HANDOFF:15 says "not started"; coordinator state:204 says "#182 CodeQL Python merged (c5ba723)" | verify |
| T9 | P4b: 90-161.Z #239 (lock engine-v39) | Done per two kit records: KIT_HANDOFF:5 and coordinator state:250 (70c72e3). Fleet repo not verified | done (record) |
| T10 | P4c: 33-332.Z, the 3 MINOR texts of #118 after the PAM's ISE test | Not verified; [follow-ups 2 plan](2026-11-25-followups-2-plan.md) item 12 puts it in 33-332.Z NEXT_PROMPT. Note: coordinator state:243 says 33-332.Z has session load 5,504 > 5,500 with that line (local branch, not pushed) | move: 33-332.Z NEXT_PROMPT, after the Part B AGENTS.md cuts free room there |
| T11 | P6: full-history exports | Done per record: coordinator state:213-214 (10 exports sent in chat). The kit export "follows this commit": not verified | done (record); the Maintainer confirms receipt of the kit export |
| T12 | P6: delete the kit's CONTAINED branches (11) | Open: approved 2026-11-25 (followups-2 plan:13, "the Maintainer runs them from a Codespace"). `git ls-remote` at 2026-11-25 ~13:25: 11 of 11 still on origin ([delete list](2026-11-24-p6-delete.tsv)) | move: KIT_HANDOFF "Needs the owner" (line 27, "branch deletes", already there) |
| T13 | P6: delete the CONTAINED branches of the 10 fleet repos (101) | Not verified (no fleet access) | move: same line as T12 |
| T14 | P6: session archive list | Open, a step for the Maintainer: the list is in coordinator state:219-223; not verified which sessions are archived | move: Archive "Needs the owner" |
| T15 | KIT_HANDOFF:29: delete `claude/fleet-audit-cli-helpers`, `claude/fleet-audit-report` (kit), `claude/fleet-audit-site-page-dedup` (33-332.Z) | Kit: both gone (`git ls-remote` 0 rows, ~13:25). 33-332.Z: in the P6 delete list (1 row), so T13 covers it | drop the line (Part B K4) |

### A2. Fleet audit ([report](2026-11-24-fleet-audit.md) "Open questions"; KIT_HANDOFF "Open")

| # | Open item | True state (evidence) | Proposal |
|---|---|---|---|
| F1 | Cut 5: ICF-Source one-off scripts (-912) | Decided: it waits for that project's own audit (the Maintainer, 2026-11-24; KIT_HANDOFF:22). Not verified in ICF-Source | move: ICF-Source NEXT_PROMPT (audit item) |
| F2 | Cut 8: 90-161.Z `measure_pdf.py` (-58) | Same decision; not verified | move: 90-161.Z NEXT_PROMPT |
| F3 | Cut 9: RADE `Split-Sentence` (about -20; needs an engine release) | Same decision; not verified | move: RADE NEXT_PROMPT |
| F4 | Question 3: Dependabot content-step failure | Open: KIT_HANDOFF:28 asks the Maintainer to add the secret `PII_GUARD_DENYLIST` (steps: Archive "Dependabot secret"); not verified (a secret cannot be read) | move: KIT_HANDOFF "Needs the owner" (line 28, already there) |
| F5 | Question 4: record measurements as each project's audit? | Decided: leave each project's AUDIT DUE for its own audit (the Maintainer, 2026-11-24; KIT_HANDOFF:22) | done (decision) |
| A1 | T2 counts test files with code | Open: `cat scripts/*.py scripts/*.sh \| wc -l` (`.check.state.json` "script_lines" command) still counts tests and code as one number | move: audit-metrics plan |
| A2 | A blanket T2 ceiling stays open | Practice covers it: each later row names one PR and one number, and the 20000 row has the scope "P2 only" and was replaced (DECISIONS:38 "Replaces: The P2 allowance up to 20000 lines (P2 only)"). Later blanket allowances name their plan too (kit follow-ups plan, "no ask per rise in this plan") | drop: the scope column already ends each allowance with its plan; no check is needed |
| A3 | File splits made to pass the size cap | Open: no "seam" question in `.claude/agents/reviewer.md` or the delegate skill (grep: 0) | move: audit-metrics plan (keep [R4f](2026-11-23-tr-r4f-split-audit.md) as evidence) |
| A4 | Fix-of-a-fix rate by `git blame` | Open: `.claude/skills/audit/SKILL.md:61` still counts "commits that fix a commit of the last 7 days" by subject | move: audit-metrics plan |
| A5 | Duplicate functions (same body) beside the line count | Open: nothing built | move: audit-metrics plan (low priority) |
| A6 | Rule count by sentence, not by bullet | Open: nothing built. The bullet count is a guide that only warns (`.claude/skills/rule-change/SKILL.md:68`), and the conflict check reads each changed rule line whatever the count | drop: merging bullets cannot hide a rule change from the conflict check |
| A7 | Session load as a typical session reads it (skill use) | Open: needs the skill-use counts of P2 (j); the fleet re-run is due 2026-12-08 | move: audit-metrics plan, after 2026-12-08 |
| A8 | `fleet.last_audit` after a partial audit | Open: `scripts/bloat_check.py:204-218` reads one date, with no list of the repos that the audit covered | move: audit-metrics plan |
| A9 | Defects per check from local runs; mutation kills | Open: check.sh writes no FAIL log (grep `.jsonl`: 0); mutmut is not a dependency (the Maintainer chooses) | move: audit-metrics plan |
| A12 | Duplicate count includes generated files; not reproducible | Open: the file-group printing and the generated-block skip came in #156 (2026-11-24 05:45), before the audit (#159, 08:55), so they do not close it. The ICF glob is a guard change in ICF-Source `.check` | move: audit-metrics plan (kit part); ICF-Source NEXT_PROMPT (the `audit-duplicate-ignore:` glob) |
| A13 | `bootstrap.sh` leaves kit review subfolders in new projects | Open: `scripts/bootstrap.sh:109` is still `find docs/reviews -maxdepth 1 -name '20*.md' -delete`; 2 subfolders exist (`2026-11-18-port-notes/`, `2026-11-20-skill-tests/`) | move: Archive "Open" as PATCH item (h) (lane C: a guard script) |
| A14 | No rule-test run records | Open: the last records are [2026-11-13-rule-tests.md](2026-11-13-rule-tests.md) and [2026-11-18-rule-tests-lean.md](2026-11-18-rule-tests-lean.md) | move: audit-metrics plan |

### Counts (32 rows)

| Proposal | Rows | Which |
|---|---|---|
| done | 6 | T1, T2, T4, F5 (evidence in the kit repo); T9, T11 (kit records only) |
| verify | 3 | T6, T7, T8 (kit records conflict) |
| move | 18 | T10, T12, T13, T14, F1-F4, A1, A3, A4, A5, A7, A8, A9, A12, A13, A14 |
| drop | 5 | T3, T5, T15, A2, A6 |

Moves add no session load: every new home is outside the start-read files. The 2 KIT_HANDOFF lines that T12, T13 and F4 use exist already.

### Files that become archivable when both close

Sizes: `wc -c` on the tree at 9454e6e, 2026-11-25 ~13:30. "Both close" means: the verify rows are done, the move rows sit in
their new homes, the audit-metrics plan exists, and the branch deletes are done.

| File | Bytes | Archivable |
|---|---|---|
| 2026-11-23-tool-retirement-handoff.md | 10,930 | yes |
| 2026-11-23-tool-retirement-prompt.md | 6,110 | yes |
| 2026-11-23-tool-retirement-research-plan.md | 3,231 | yes |
| 2026-11-23-tr-r2a-project-tools.md | 73,487 | yes |
| 2026-11-23-tr-r2b-kit10-repos.md | 33,387 | yes |
| 2026-11-23-tr-r3-icf-scans.md | 2,510 | yes |
| 2026-11-23-tr-r4e-ion-benchmark.md | 42,615 | yes |
| 2026-11-23-tr-wa-linters.md | 42,092 | yes |
| 2026-11-23-tr-wb-scanners.md | 64,641 | yes |
| 2026-11-23-tr-wc-sync-distribution.md | 29,186 | yes |
| 2026-11-23-tr-wd-standard-replacements.md | 56,155 | yes |
| 2026-11-23-p2-aud5-records.md | 2,787 | yes |
| 2026-11-24-fleet-audit-33-332.md | 38,625 | yes |
| 2026-11-24-fleet-audit-90-161.md | 27,774 | yes |
| 2026-11-24-fleet-audit-icf.md | 45,219 | yes |
| 2026-11-24-fleet-audit-kit.md | 43,454 | yes |
| 2026-11-24-fleet-audit-rade.md | 37,328 | yes |
| 2026-11-24-p6-branch-list.md | 7,178 | yes, after the deletes |
| 2026-11-24-p6-delete.tsv | 8,448 | yes, after the deletes |
| **Subtotal** | **575,157** | 19 files |
| 2026-11-23-tool-retirement-plan.md | 41,926 | no, until the links go: DECISIONS:64 and `scripts/bloat_check_files.py:5` name it |
| 2026-11-23-tool-retirement-coverage.md | 15,325 | no: `scripts/check.sh:557` runs the coverage check on each `*-coverage.md` |
| 2026-11-23-p1-debt.md, 2026-11-23-rule-conflict-p1.md | 4,181 + 4,048 | no: hash records that a check reads |
| 2026-11-23-p2-shellcheck-debt.md | 3,010 | no: DECISIONS names it |
| 2026-11-23-skill-use-audit.md | 7,460 | no: the 2026-12-08 re-run uses it |
| 2026-11-23-tr-r4f-split-audit.md | 6,169 | no: A3 evidence (audit-metrics plan) |
| 2026-11-24-fleet-audit.md | 21,669 | no: `docs/tools.md:159` and docs/LOG.md link it; the audit-metrics plan copies its A rows |
| **Exceptions** | **103,788** | 8 files |

Archiving the 19 files also removes 0 duplicate lines. The 5 AGENTS.md duplicates are in the plan file, which stays.

## Part B: context-trim proposals

### B1. Session load today, by part

Method: the same count as `scripts/bloat_check_rules.py` `start_read()` (bytes / 4). The start-read files are AGENTS.md,
CLAUDE.md, docs/NEXT_PROMPT.md and, from `.check` `audit-start-read:`, docs/KIT_HANDOFF.md. Each skill and agent counts
only its frontmatter `name` and `description`. `python3 scripts/bloat_check.py --brief` at 9454e6e: **~5,471 of 5,500**
(headroom 29; warning line 5,000).

| Part | Bytes | ~Tokens |
|---|---|---|
| AGENTS.md (all) | 15,923 | 3,980 |
| · title and header lines | 530 | 132 |
| · Order of authority | 672 | 168 |
| · Hard rules | 4,644 | 1,161 |
| · Defaults | 9,112 | 2,278 |
| · Commands | 402 | 100 |
| · Project rules (with its comment) | 563 | 140 |
| CLAUDE.md | 11 | 2 |
| docs/NEXT_PROMPT.md (the project template; kit sessions read KIT_HANDOFF.md) | 567 | 141 |
| docs/KIT_HANDOFF.md | 3,291 | 822 |
| Skill and agent descriptions (14) | 2,092 | 523 |
| **Total** | **21,884** | **5,471** |

Descriptions (bytes of name + description): deliver 183, kit-update 182, handoff 175, personal-data 173, rule-change 172,
audit 172, verify 143, scout 137, instructions 133, reviewer 127, delegate 125, data-change 125, worker 123,
project-log 122.

Largest AGENTS.md lines (~tokens): Instructions people follow 259, Delivery 235, Secrets and personal data 190, Git
history 165, Decisions 164, Caps and audit 164. KIT_HANDOFF: line 15 (the plan line) 159.

### B2. Result by tier (measured)

Each tier was applied to a copy of the tree (`git archive HEAD`), and `bloat_check.py --brief` ran on the copy.

| Tier | Cuts | Session load | Saved | Headroom |
|---|---|---|---|---|
| 0: today | none | 5,471 | 0 | 29 |
| 1: handoff only | K1-K8 | 5,091 | 380 | 409 |
| 2: + one description | + D2 | 5,084 | 387 | 416 |
| 3: + AGENTS.md rule text | + R1-R4 | **4,957** | **514** | **543** |
| R1-R4 alone (every fleet repo) | R1-R4 | 5,344 | 127 | 156 |

**The target of 500 tokens of headroom needs tier 3.** Tier 3 needs the Maintainer's approval of each exact R text.
Tiers 1-2 give 416 and miss the target. The R cuts are the only ones that also help the fleet repos (AGENTS.md is the
same kit text there). 33-332.Z needs them: its load is 5,504 > 5,500 with one pending handoff line (coordinator state:243).

K1 and K2 are **conditional on Part A**: they remove the plan lines from KIT_HANDOFF, so each open item must first have
the home that Part A names. Part A moves add no start-read text.

### B3. Proposals

| ID | File | Change | ~Tokens saved | Risk | Approval |
|---|---|---|---|---|---|
| R1 | AGENTS.md "Caps and audit" | The list of what bloat_check fails on becomes a pointer; the check-in prints each cap (values: `scripts/check_settings_read.py:38`) | 70 | Medium. The text loses: the numbers 200 / 5,500 / 1,500 (the check-in prints the first two at each start); "a script has no docs/tools.md row" (the agent learns it only when the check fails); "file size only warns"; the AUDIT DUE trigger "each kit release or 14 days" (the check-in prints AUDIT DUE). "Lean instructions" supports the pointer form for a rule a check enforces | Maintainer: exact text |
| R2 | AGENTS.md "Project rules" comment | Shorter comment; points to the rule-change skill | 36 | Low. The approval of the exact text stays in the hard rule "Rule text"; the "(cannot be changed)" mark stays in the "Hard rules" intro. The comment is kit text, not a rule (plan C12), but it is a kit file: lane C | Maintainer: exact text |
| R3 | AGENTS.md "Start of session" | Drop the list of output-line names | 13 | Low. The output lines name themselves; a new check-in line no longer needs a rule edit | Maintainer: exact text |
| R4 | AGENTS.md "Secrets and personal data" | The pull-request scope becomes a pointer to `.github/workflows/check.yml` (its lines 15 and 39 hold the public-repo and `.check` conditions) | 6 | Low. Small saving: approve only together with R1-R3 | Maintainer: exact text |
| K1 | KIT_HANDOFF "Approved plan" section | Remove it (the plan and P2 links stay in the plan file, DECISIONS:64 and the close-out list) | 234 | Low, if Part A is accepted. Conditional | coordinator / lane A |
| K2 | KIT_HANDOFF "Open", fleet audit line | One pointer line to this file | 28 | Low; conditional. The "each project's AUDIT DUE" decision moves with F5 | lane A |
| K3 | KIT_HANDOFF "State" | The stale 11.1.0 line becomes the current 12.0.0 line (T2 20,694 from `.check.state.json`) | 14 | Low | lane A |
| K3b | KIT_HANDOFF "Open" | Remove the 12.0.0 line (K3 moves it to "State") | 28 | Low | lane A |
| K4 | KIT_HANDOFF "Needs the owner" | Remove the fleet-audit branch line (T15) | 37 | Low: the kit branches are gone; the 33-332.Z one is in the P6 delete list | lane A |
| K5 | KIT_HANDOFF "Updated" | Drop the fleet audit report link (K2 points to its successor) | 14 | Low | lane A |
| K6 | KIT_HANDOFF "Do not" | Drop the stale number (5,473 at 11.0.1; the newest record is 5,504) | 4 | Low: the rule (measure every repo first) stays | lane A |
| K7 | KIT_HANDOFF intro | Same facts, shorter | 9 | Low | lane A |
| K8 | KIT_HANDOFF "Do not" | Same incident, shorter | 8 | Low | lane A |
| D2 | deliver skill description | Shorter trigger | 7 | Medium: "before a turn ends" with no "work not on origin" can load the skill at more turn ends (more reads, not fewer triggers) | lane C (a `.claude/` file) |

Tested and left out: the scout and handoff descriptions (0-1 token each); the hard rule "Instructions people follow"
(259 tokens: its text was approved today with kit 12.0.0, so a cut now would reopen that decision).

Optional, not counted above: **O1**. The kit counts docs/NEXT_PROMPT.md (141 tokens), but kit sessions read
KIT_HANDOFF.md ("Order of authority"; A10). Not counting the template in the kit would add 141 tokens of headroom. Risk:
this changes a check (`scripts/bloat_check_rules.py:30` or `.check`, lane C). A fresh review must confirm that it
corrects the measure and does not only move the number (AGENTS.md "Fresh review"). No decision yet: LOG row 81 records
the miss, and DECISIONS has no row.

Duplicate lines: this report quotes about 8 lines of AGENTS.md and KIT_HANDOFF.md word for word, so `bloat_check.py`
reports more duplicate lines (51 at 9454e6e; report only, check.sh does not fail on it). The count falls again when the
cuts land or this file is archived.

### B4. Exact texts

Each old text was found exactly once in its file at 9454e6e. Line breaks in KIT_HANDOFF blocks are part of the text.

R1   AGENTS.md                        found=1 saved~70
R2   AGENTS.md                        found=1 saved~36
R3   AGENTS.md                        found=1 saved~13
K1   docs/KIT_HANDOFF.md              found=1 saved~234
K2   docs/KIT_HANDOFF.md              found=1 saved~28
K3   docs/KIT_HANDOFF.md              found=1 saved~14
K3b  docs/KIT_HANDOFF.md              found=1 saved~28
K4   docs/KIT_HANDOFF.md              found=1 saved~37
K5   docs/KIT_HANDOFF.md              found=1 saved~14
K6   docs/KIT_HANDOFF.md              found=1 saved~4
K7   docs/KIT_HANDOFF.md              found=1 saved~9
K8   docs/KIT_HANDOFF.md              found=1 saved~8
D1   .claude/agents/scout.md          found=1 saved~1
D2   .claude/skills/deliver/SKILL.md  found=1 saved~7
D3   .claude/skills/handoff/SKILL.md  found=1 saved~0
R4   AGENTS.md                        found=1 saved~6
total (no D3) 509
#### R1 (AGENTS.md)

Old:

```text
- **Caps and audit.** `scripts/bloat_check.py` (run by the check-in and by check.sh) fails when this file passes 200 lines, when the session load passes 5,500 tokens (third-party skills and agents in `.check`: own cap 1,500), when a skill or agent file states a rule whose home is this file, or when custom script lines pass their approved baseline or a script has no docs/tools.md row; file size only warns. The full audit runs when the Maintainer asks for it; at each kit release or 14 days after the last fleet audit the check-in reports AUDIT DUE (fleet) and you ask; a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.
```

New:

```text
- **Caps and audit.** `scripts/bloat_check.py` (run by the check-in and by check.sh) enforces the caps, the single home of each rule and the script-line baseline; the check-in prints each cap and AUDIT DUE. The full audit runs when the Maintainer asks for it; on AUDIT DUE (fleet) you ask; a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.
```

#### R2 (AGENTS.md)

Old:

```text
<!-- This project's own rules: one line each, at most 15 (full tier: scripts/bloat_check.py checks the cap). Add, change or remove a line only with the Maintainer's approval of its exact text; date it, for example "(the Maintainer, 2026-11-09)". Mark a rule that nothing may relax "(cannot be changed)". -->
```

New:

```text
<!-- This project's own rules: one line each, at most 15, each dated, for example "(the Maintainer, 2026-11-09)". Steps: .claude/skills/rule-change/SKILL.md. -->
```

#### R3 (AGENTS.md)

Old:

```text
do what their output lines say (FIRST USE, KIT, DENYLIST, AUDIT DUE, TITLE, SESSIONS) and report
```

New:

```text
do what their output lines say and report
```

#### R4 (AGENTS.md)

Old:

```text
on every push, and on every pull request in a public repo, in a repo that has the settings file `.check`, and, in every repo, as a PreToolUse hook
```

New:

```text
on every push, in the pull-request Action (where: `.github/workflows/check.yml`) and, in every repo, as a PreToolUse hook
```

#### K1 (docs/KIT_HANDOFF.md)

Old:

```text
## Approved plan (the Maintainer, 2026-11-23 17:12): custom tool retirement

Plan and decisions 1-10: [reviews/2026-11-23-tool-retirement-plan.md](reviews/2026-11-23-tool-retirement-plan.md); P2 record: [reviews/2026-11-23-tool-retirement-handoff.md](reviews/2026-11-23-tool-retirement-handoff.md).

- [x] Research and plan. [x] P1 (PR 137). [x] P2. [x] Fleet audit (PRs 158, 159). [x] P3: kit package (kit PRs 164, 168, 169); 33-332.Z pilot in package mode (its PRs 99, 102, 103, 104; 27 of 53 kit scripts from the package). Follow-ups: --kit-install after a branch switch (S7 text), check-in KIT line when the package is missing, MAINTAINER_GUIDE step, bandit in security.yml, 4 MINOR of PR 168. [~] P4: done, except 90-161.Z PR 235 (open for your look) and the SBOM steps (ask rule `*--output*`); RADE CodeQL not started. [x] P5. [~] P6: exports, [branch list](reviews/2026-11-24-p6-branch-list.md); deletes need the Maintainer's OK.
```

New:

```text
(nothing: the text goes)
```

#### K2 (docs/KIT_HANDOFF.md)

Old:

```text
- Fleet audit (report, "Open questions"): A10, A11, A15 in PR 160; the other audit-the-audit items (A1-A9, A12-A14) open. Cut proposals 5, 8, 9 and each project's AUDIT DUE wait for that project's own audit (the Maintainer, 2026-11-24). Skill-use audit due 2026-12-08.
```

New:

```text
- Tool retirement and fleet audit: open items in the [close-out list](reviews/2026-11-25-closeout-and-trim-proposals.md). Skill-use audit due 2026-12-08.
```

#### K3 (docs/KIT_HANDOFF.md)

Old:

```text
- Kit 11.1.0 = a6295509 (tag v11.1.0, made by the Maintainer 2026-11-25). P1-P3, the fleet audit, follow-ups 1-8. 10 fleet repos on 11.1.0. Kit PRs 184-201 go in 11.2.0. T2 20,608.
```

New:

```text
- Kit 12.0.0 (c0fa5f1) in all 10 repos ([plan](reviews/2026-11-25-instructions-80-plan.md)); tag: the Maintainer. T2 20,694.
```

#### K3b (docs/KIT_HANDOFF.md)

Old:

```text
- Kit 12.0.0 (c0fa5f1) in all 10 repos ([plan](reviews/2026-11-25-instructions-80-plan.md)); tag: the Maintainer.
```

New:

```text
(nothing: the text goes)
```

#### K4 (docs/KIT_HANDOFF.md)

Old:

```text
- Delete the merged branches `claude/fleet-audit-cli-helpers`, `claude/fleet-audit-report` (kit) and `claude/fleet-audit-site-page-dedup` (33-332.Z).
```

New:

```text
(nothing: the text goes)
```

#### K5 (docs/KIT_HANDOFF.md)

Old:

```text
Updated: 2026-11-25 13:15 (coordinator 4): 90-161.Z #239 merged (70c72e3). Older items: [archive file](reviews/2026-11-24-kit-handoff-archive.md); fleet audit [report](reviews/2026-11-24-fleet-audit.md).
```

New:

```text
Updated: 2026-11-25 13:15 (coordinator 4): 90-161.Z #239 merged (70c72e3). Older items: [archive file](reviews/2026-11-24-kit-handoff-archive.md).
```

#### K6 (docs/KIT_HANDOFF.md)

Old:

```text
 at 11.0.1 the highest is 33-332.Z ~5,473 of the 5,500 cap.
```

New:

```text
 the highest project is near the 5,500 cap.
```

#### K7 (docs/KIT_HANDOFF.md)

Old:

```text
The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer and inside the session-load cap (`.check` counts it); evidence and older items go in docs/reviews/. Times are America/Chicago.
```

New:

```text
The kit's own handoff (AGENTS.md "Handoff"; first use deletes it, and a project uses docs/NEXT_PROMPT.md). At most 40 lines, inside the session-load cap (`.check` counts it); evidence and older items: docs/reviews/. Times: America/Chicago.
```

#### K8 (docs/KIT_HANDOFF.md)

Old:

```text
on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
```

New:

```text
on 2026-11-18, merges of 44 and 45 made the open 42 conflict in about 15 files.
```

#### D2 (.claude/skills/deliver/SKILL.md)

Old:

```text
before a turn ends with work not on origin; and before you report repo work done.
```

New:

```text
and before a turn ends or you report repo work done.
```
