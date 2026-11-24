# Tool retirement: handoff at the P1 stopping point

Written 2026-11-23 18:12 America/Chicago by session "Kit · Tool retirement · 2026-11-23 · #125", at the Maintainer's
request ("I want a stopping point and for you to start newly with your side sessions as needed"). The approved plan is
[2026-11-23-tool-retirement-plan.md](2026-11-23-tool-retirement-plan.md) (approved 2026-11-23 17:12). Continue it from
the first open step; no new plan review or approval is needed.

## State

| Item | State |
|---|---|
| Research R1-R4f, plan, coverage list (86 rows), skill-use audit | on main (PRs 125, 127, 131, 132, 133, 134) |
| PR 135 (skill-use audit, 7th session) | open, lane A, merge when green |
| P1 rules and checks | built on branch `claude/tr-p1` at 2161319; no PR yet; fast lane on push: 32 passed, 2 skipped, of 34 |
| P2-P6 | not started |

P1 on the branch: AGENTS.md 73 lines, 28 kit bullets (C9 text approved 17:37); skills S1-S6 (S3 text approved 17:37);
PREFERENCES.md F3 and A1-A3; docs/tools.md (with a Candidates column); log_check.py and log_check_plan.py (T6, T7);
new scripts/bloat_check_files.py (T1, T2, T5, T6); code_standard C4 warns, AUD-1 FAILs in the kit; 47 `Prevents:`
lines; check.sh steps; sync_baseline.py marker; DECISIONS rows (plan approval with Replaces, C9/S3, AUD-1 FAIL, T2
17878, T2 18142); .check.state.json `script_lines` 18142; debt record docs/reviews/2026-11-23-p1-debt.md
(debt-check 0abd68228388); rule-conflict record docs/reviews/2026-11-23-rule-conflict-p1.md (rule-conflict-check
0abd68228388).

## P1: open steps (in order)

1. Fix the date of the T2 18142 row in docs/DECISIONS.md on `claude/tr-p1`: it says 2026-11-24 (UTC); the Maintainer
   approved it on 2026-11-23 ~18:10 America/Chicago.
2. Verify the T1 first-cell match (W3 item 1: T1 must match only the first cell of a docs/tools.md row). It has no
   separate commit; test it, or build it.
3. Run `scripts/check.sh` (full lane) on the head.
4. Fresh review (strong model, `reviewer` agent) of the changes since 8338bf8: W3, W4, the joins, the
   "Prevents: unclear" gaming gap (timeline.py, token_log*.py) and the weak `Prevents:` lines in skill_use, drift and
   fleet. Fix each MAJOR finding; a fix gets its own review.
5. If a rule line changed after 0abd68228388, run the rule-conflict check again and update its record.
6. Open the P1 PR (lane C) and ask the Maintainer to merge.

## Later phases (plan sections)

- P2: items (a)-(j), with the skill-use proposals P1-P4 (audit file
  [2026-11-23-skill-use-audit.md](2026-11-23-skill-use-audit.md)) and AUD-6 (worker_guard.py --scan).
- P3: pilot in 33-332.Z; trim its handoff by ~50 tokens first.
- P4-P6 as the plan says. Branch deletes need the Maintainer's OK: `claude/tr-r2a-project-tools` holds a third-party
  name in b765169; merged worker branches.

## Lessons from this session

- Take times from a clock in America/Chicago (`TZ=America/Chicago date`), never from UTC commit times or estimates.
- The T2 ratchet stops a worker push in the middle of a task: join the work locally, then record the new baseline.
- Workers have no Skill tool and slice skills with grep/sed: give each brief the skill text it needs (S4, P2 proposal).
- Two workers worked around guards (chr(64) strings; commands in script files): AUD-6 scans for this in P2.
- `list_events` returns inline results; to measure skill use, ask each session to run `scripts/skill_use.py` itself.
