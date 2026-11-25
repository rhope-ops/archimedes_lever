# Kit follow-ups 1-8: plan

Written 2026-11-24 19:24 America/Chicago by "Kit · Fleet coordinator 3 · 2026-11-24" (session_01PyXpdUk7tSsbCmQXyLSzEZ).
Source: the 8 kit follow-ups in [2026-11-23-fleet-v2-coordinator-state.md](2026-11-23-fleet-v2-coordinator-state.md),
section "Coordinator 2: P3 package-mode rollout closed". Status: **approved by the Maintainer as written, 2026-11-24 19:30
America/Chicago** (coordinator 3 chat, "Approve as written"), with the answers below.

## Decisions for this plan (the Maintainer, coordinator 3 chat, 2026-11-24; scope: this plan only)

- DEC 3: plan all 8 follow-ups first; the Maintainer approves the plan before step 1.
- DEC 4: advance OK for the lane C merges of follow-ups 1-8, when the last fresh review has 0 MAJOR and CI is green on
  the merged head (ICF-Source: the full lane on the head). A tag and a release are not merges: ask for each.
- T2: no ask per rise in this plan ("i despise being asked to raise it over and over. just get it done."). Keep code
  small; show the running total at each merge; a plan total past about +400 lines is drift: tell the Maintainer.
- Step 7: all 4 projects ("Yes, all 4 projects").
- ICF-Source name item: leave it as is; `.check` allows it on purpose ("Leave it as is"). Item closed.
- DEC 5 (later, same chat): item 3: "Close it, keep the scan" (PR 181 closed: every safe rule fixed 1 of 11 lines).
- DEC 6 (later, same chat): "Yes, release 11.1.0" (KIT_VERSION, CHANGELOG row, tag v11.1.0; step 7 locks to the tag).

## Source items

Mark: in (this plan), out, later, ask (the Maintainer decides before the step).

| # | Source item | Fact found (2026-11-24) | Mark | Step |
|---|---|---|---|---|
| 1 | `code_standard.py --update` drops Python line debt that ruff/pylint still fail on | Not reproduced yet. `check()` saves the measurement as the new baseline; the kit itself has no debt (`.check.state.json`), so the case is in a project baseline | in | 1 |
| 2 | Approval-quote marker: the check says a sync adds it, no sync does | `sync_baseline.py:183-204` adds it only below a `## Decisions` heading; with no heading it adds nothing and prints nothing | in | 2 |
| 3 | worker_guard_scan flags PowerShell `@(` as an at sign | `worker_guard_scan.py:70`; a first fix weakened the scan and was dropped | out (DEC 5) | 3 |
| 4 | `--kit-install` runs pip outside a venv (PEP 668) | `check.sh:272` installs into the system Python; this container does not enforce PEP 668 (pip prints a WARNING only), so the test needs an EXTERNALLY-MANAGED marker | in | 1 |
| 5 | Delegate skill does not name the reviewer delete block (kit #174) | `.claude/skills/delegate/SKILL.md:18` names the worker blocks only | in | 4 |
| 6 | kit-update SKILL.md and the check.sh comment disagree about the setup script; "fail closed" is not STE | SKILL.md:44 (the setup script may not run again) against check.sh:268 (the setup script uses it); `.claude/settings.json:109` | in | 4 |
| 7 | No CHANGELOG row for "Python line cap moves to ruff/pylint"; main untagged after 11.0.1 | docs/CHANGELOG.md | in (row); ask (tag) | 5, 6 |
| 8 | RADE and ICF-Source lack kit #174; session loads near the cap | Load numbers from the hand-off, not measured again: RADE 5,475, 33-332.Z 5,484, 90-161.Z 5,462 of 5,500 | in (all 4 projects) | 7 |

## Steps

1. **PR 1 (lane C: scripts the hooks run), items 1 and 4.** Item 1: reproduce first in a temporary copy of a project
   with Python line debt (with and without ruff and pylint), then choose the fix and write a test that fails before it.
   Item 4: a test with an EXTERNALLY-MANAGED marker; `--kit-install` then installs where pip allows it, and the
   SessionStart hook and `archimedes-kit --verify` find that install. Reviewer: strong tier.
2. **PR 2 (lane C), item 2.** A DECISIONS file with no `## Decisions` heading: the sync prints one line that names the
   manual step, and the T6 message names the case. A test for both.
3. **PR 3 (lane C), item 3.** A test that a PowerShell array `@(` is not a finding, and that an at sign built at run
   time (joined value, `chr(64)`, a decode) still is. The fix changes only the check of the joined value. Reviewer:
   strong tier; the brief names the dropped first try.
4. **PR 4 (lane C: skills and settings), items 5 and 6.** The delegate skill names the `reviewer` delete block;
   check.sh:268 and kit-update SKILL.md say the same about the setup script; the session-start FAIL line in STE. Before
   the merge, measure the session load of the kit and of the 4 projects (`bloat_check.py --brief` on a dry-run sync);
   the PR adds no net tokens.
5. **PR 5 (lane A), item 7.** CHANGELOG rows for "Python line cap moves to ruff/pylint" and for PRs 1-4.
6. **Ask the Release Manager:** tag main as a kit release (REC: 11.1.0, because package mode is a new feature).
7. **Item 8: lock bumps** to the new kit main or tag, with each project's session load measured first: RADE and
   ICF-Source, 33-332.Z and 90-161.Z. Lane C, covered by DEC 4.
8. Update docs/KIT_HANDOFF.md and the coordinator state doc; show the running T2 totals at each merge.

## Limits, cost and agents

- T2 (tracked script lines): the kit is at 20,025. PRs 1-3 add code and tests (estimate +100 to +200).
- Agents: the coordinator writes the code (main session); one `reviewer` subagent per PR: 6 kit and docs reviews plus
  2 to 4 project reviews (strong tier for PRs 1 and 3, the author's tier for the others). No workers. Estimate 4 to 5
  hours. The usage limit can stop the work between steps; the state is in this file and on each PR.
- Rollback: a revert PR of each merge commit (never a reset); a project lock bump is reverted in that project.

## Out of scope

- ICF-Source name item: closed, left as is (the Maintainer, 2026-11-24).
- 33-332.Z Ion PRs #60/#61: stay paused (the Maintainer's request).
