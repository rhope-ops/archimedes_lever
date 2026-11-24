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

Status 2026-11-23 18:24 America/Chicago: steps 1-6 done (session "Kit · Tool retirement P1 finish · 2026-11-23"). Two fresh reviews: 2 MAJOR fixed in b56926b, then no MAJOR. Lane C PR [#137](https://github.com/rhope-ops/archimedes_lever/pull/137) waits for the Maintainer's merge; its body lists the MINOR findings for P2.

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

## P1 result

P1 merged to main at 067726a (2026-11-23, PR [#137](https://github.com/rhope-ops/archimedes_lever/pull/137), the Maintainer's
approval in the coordinator's chat). 4 fresh reviews; the MINOR findings for P2 are in the PR body.

## P2 split (session "Kit · Tool retirement P1 finish · 2026-11-23", 2026-11-23 18:37)

Each item is its own lane C PR (T3), so each can be reverted alone. Shared files have one owner, the main session, in a
join commit per PR: docs/tools.md, .check.state.json, docs/DECISIONS.md, scripts/check.sh, .check.lock, the sync lists in
sync_baseline.py, and scripts/worker_guard.py (it guards the workers).

| Stream | Items | Owner |
|---|---|---|
| Main 0 | T2 MINORs first (the coordinator's order): "the Maintainer: agent wrote" passes, number boundaries, a test; T2 lowers the baseline when lines drop (now the slack stays open) | main session |
| 1 | (a) ruff + pylint config, (g) shellcheck WARN with the fleet list, (e) splits code_standard_ratchet and code_standard_test_gate | worker (Sonnet) |
| 2 | (b) decision 9: 3 matching fixes, (f) ReDoS in build_site_html.py:121, (e) split check_content_scan_settings | worker (Sonnet) |
| 3 | (d) sync stops on a project's local edit of a kit file, (e) split sync_baseline_run | worker (Sonnet) |
| Main | (h) AUD-5 records, (i) AUD-6 worker_guard.py --scan and text S8 | main session |
| Later | (j) skill use (token_log_rows.py, brief line, skill_use.py name) and (e) split token_log_test_report | worker, when a slot is free |
| None | (c) decision 10A: keep check_instructions.py; no code change | - |

Facts at 2026-11-23 18:37: ruff is installed here; pylint, shellcheck and gitleaks are not, and neither CI nor check.sh runs them.
A missing linter must print a SKIP line with the install command, never pass in silence. Fleet repos can be attached
for reading (list_repos). Briefs: the adversarial inputs, a test that fails against the old code, no line squeezing to
meet T2 (report the net count; the Maintainer approves a higher number per PR), commit locally, no stray files.

## P2 status (2026-11-23 20:05 America/Chicago)

| Item | State | T2 baseline (the Maintainer) |
|---|---|---|
| T2 MINORs + downward ratchet | merged, PR 139 | 18159 ("Approve 18159") |
| (f) ReDoS fix | merged, PR 140 | 18195 ("Approve all 5") |
| (e) content split | merged, PR 141 | 18215 ("Approve all 4", 18:59; "The 18:59 batch holds") |
| (e) sync split | merged, PR 143 | 18218 (same batch) |
| (b) two-line marking + keyword/number | merged, PR 144 | 18303 (same batch) |
| (d) sync stop on local edits | branch claude/tr-p2-d3 (local only): d a66c3ab merged with the sync split into the kit-only module sync_baseline_stop.py (6e17870, join e16677f, review 0 MAJOR); +378 lines, so a worker cuts 21 by real cuts | 18660 ("Approve 18660", shortly before 19:33; "Keep 18660, cut 21", shortly after 20:02) |
| (a), (g), (h), (i), (j) | not started | ask each rise on its own |

Merge order is fixed by the numbers: 141, e-sync, b, d. The local branches cannot be pushed before their turn (T2
blocks the push); if this container is lost, rebuild them from the PR bodies and review reports. Decisions of the
Maintainer in P2: `%40` not decoded; build keyword+number on two lines; the sync stops on an unlocked kit file that
differs (an unchanged older kit copy is no stop); relock way out names check.local.sh / .check / a kit change; no lock:
as built. The coordinator relayed a later condition (a retirement before more rises; one number per question): the
Maintainer kept the 18:59 batch; ask each later rise on its own.

**Freeze (the Maintainer, question dialog, 2026-11-23 about 20:15: "Freeze rises, (a) first"; scope: P2).** No T2
baseline rise until item (a) lands with a measured net cut. Map (a) first (which code_standard checks ruff and pylint
replace, exact delete and add counts), show the Maintainer the cut, then build it. d (claude/tr-p2-d3) waits and lands
later inside the freed lines, with its restored test (+360), with no new number. Main is 18303.

**P2 on hold (2026-11-23 21:10 America/Chicago).** Facts measured since the freeze:
- Item (a) cuts nothing. A prototype gave 0 deletable lines, because the checks that stay share the Python parse. The
  Maintainer chose "Build as planned": it is built on the local branch claude/tr-p2-a (b13bc6b, +41 lines) and waits
  under the freeze. Its fresh review found 4 MAJOR findings. 2 are join items: T2, and ruff.toml and .pylintrc are
  missing from COPY_FILES. 2 are code defects to fix before a PR: the lint step ignores code-exclude, code-generated and
  generated blocks; a Python file that does not parse crashes code_standard_docs.py with code-c2: full, where main
  printed a C10 FAIL. Fixing them adds lines (estimate +5 to +15).
- No kit tool is dead (all 47 non-test tools are called and changed). Feature tools measured for retirement:
  timeline.py (-414 to -475), fulcrum_palette.py (-314; reverses the 2026-11-20 decision), build_site.py (-481; RADE and
  33-332.Z use it; reverses the 2026-11-21 decision). The Maintainer chose timeline.py, then a fleet read showed real
  use (icf-source LOG.md and its 2026-11-11 talk slide; no-more-beyond project-log PROJECT.md), and the Maintainer
  chose "Keep it, no retirement".
- So no cut is planned, and the freeze holds (a), d (claude/tr-p2-d3: +351, or +360 with the restored test) and items
  (g), (i), (j), which all add lines. Item (h) (AUD-5 records) adds none.
- Next: the Maintainer chooses another cut or lifts the freeze. The local branches cannot be pushed under T2; rebuild
  from this file and the PR bodies if the container is lost.

## Later phases (plan sections)

- P2: the split above, with the skill-use proposals P1-P4 (audit file
  [2026-11-23-skill-use-audit.md](2026-11-23-skill-use-audit.md)).
- P3: pilot in 33-332.Z; trim its handoff by ~50 tokens first.
- P4-P6 as the plan says. Branch deletes need the Maintainer's OK: `claude/tr-r2a-project-tools` holds a third-party
  name in b765169; merged worker branches.

## Lessons from this session

- Take times from a clock in America/Chicago (`TZ=America/Chicago date`), never from UTC commit times or estimates.
- The T2 ratchet stops a worker push in the middle of a task: join the work locally, then record the new baseline.
- Workers have no Skill tool and slice skills with grep/sed: give each brief the skill text it needs (S4, P2 proposal).
- Two workers worked around guards (chr(64) strings; commands in script files): AUD-6 scans for this in P2.
- `list_events` returns inline results; to measure skill use, ask each session to run `scripts/skill_use.py` itself.
