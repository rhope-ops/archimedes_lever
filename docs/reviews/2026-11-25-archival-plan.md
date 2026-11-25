# Archival: plan

Written 2026-11-25 by "Kit · Fleet coordinator 4" (session_01PyXpdUztPNnbLW6RN6Kenb). Status: **approved by the
Maintainer, 2026-11-25** (coordinator 4 chat, dialog answers: "Run deeper-version", scope "all 3", method
"Delete + index (Recommended)", design "Approve (Recommended)").

## Decisions (the Maintainer, 2026-11-25; scope: this plan)

- Scope: docs, rules and instructions, and code (all 3).
- Method: delete from the tree; one index row per file links its last commit (git keeps the file).
- Home: a section of `.claude/skills/audit/SKILL.md` (the audit identifies candidates; extends item 16). No separate
  function and no new AGENTS.md line (session load 5,493 of 5,500 tokens).
- Trigger: dynamic, not monthly. The check-in prints `ARCHIVE DUE` at a volume threshold (example: 20 closed review
  files or 200 KB since the last archive); closing a plan marks its review files. Thresholds are set in the phase 2
  schedule.
- Pace that sets the trigger: 160 review files added in the 14 days to 2026-11-25 (`git log --diff-filter=A`), 212 commits.

## Why the tool-retirement plan removed little

It asked "can a standard tool replace this custom script?" (2026-11-23 plan, sections 2 and 7): mostly no, so keep.
Archival asks "does anything still use or need this?": age, references and use.

## Prompt (from deeper-version, approved)

Phase 1, Inventory (read only, kit first, then each fleet repo): for every file under docs/, .claude/, scripts/ and the
instruction files, record size, last-change date, inbound references (git grep of its path across the repo, .claude/,
.github/workflows/, hooks), and whether a check reads it (conflict records, *-debt.md, hash records, baseline and
approval-quote rows in DECISIONS.md). Code: vulture and coverage.py over one scripts/check.sh full run, plus ruff
F401/F841. Rules and skills: from .claude/rule-tests.md and session transcripts or token logs, rules and skill sections
that never triggered in 30 days. Baselines: bytes, session-load tokens, T2 lines, file count, check-in and audit times.

Phase 2, Retention schedule (the Maintainer approves): one row per file class (keep / archive after N days / archive
when closed), reason, exceptions (open approved plans, files a check reads, current DECISIONS rows), the candidate list
with sizes and savings, and the ARCHIVE DUE thresholds. Stop for approval.

Phase 3, Tooling: extend audit item 16, the KIT_HANDOFF archive pattern and bloat_check into a dry-run-by-default
archive step that deletes approved candidates and writes the index rows (path, last commit link, date, reason); add the
ARCHIVE DUE check-in line. A rule-text change only with the Maintainer's exact approval.

Phase 4, Kit pilot, then the fleet as one kit release: one PR per class. Each PR proves check.sh green, 0 broken
links, every index row resolves (`git cat-file -e <sha>:<path>`), before and after numbers, a fresh review, and one
restore drill.

Done: schedule approved, kit pilot merged with the proofs, fleet release planned (models, agents, hours) for approval.

## Steps

- [x] Phase 1 kit inventory ([report](2026-11-25-archival-inventory-kit.md), PR 210). [ ] Phase 1 fleet.
  [x] Phase 2 schedule approved (the Maintainer, 2026-11-25, dialog "Approve (Recommended)"): the report's DRAFT
  retention schedule and ARCHIVE DUE thresholds as written. Also approved the same day: phase 3 adds measured
  context-trim proposals (each rule text needs the Maintainer's approval of its text), and close-out lists for the
  tool-retirement plan and the fleet audit (nothing closes without the Maintainer's approval).
  [x] Phase 3 (PRs 214, 217). [~] Phase 4 kit pilot: the Maintainer, 2026-11-25 ~15:00 CST, own message "do it now
  and audit the entire fleet since it keeps whining": the age waits are waived for this run (all other exceptions
  stay); session "Kit · Archive run now (pilot)" (session_01PyXpdV79gVD4nA6ayeYn3k).
  [x] Fleet release plan approved (the Maintainer, 2026-11-25, dialogs "Approve, Sonnet" and "You make it
  (Recommended)"): [ ] kit 13.0.0 (MAJOR: R1-R3 rule text; the coordinator makes the tag v13.0.0); [ ] one Sonnet
  session per fleet repo (33-332.Z, 90-161.Z, RADE, ICF-Source, SEC-Source, SPAR, TA, no-more-beyond, 36-3003.Z,
  65-601.Z): kit sync, full audit (`.claude/skills/audit/SKILL.md`), the archive step with the same waiver; lane C
  sync merges after green checks and a fresh review with 0 MAJOR. About 12 agent-hours, 2-3 h wall.
- Left out: a scheduled monthly run (replaced by the dynamic trigger); condensing DECISIONS rows (changes the record).
