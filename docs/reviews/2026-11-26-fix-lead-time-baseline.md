# Fix lead time: baseline (2026-11-26)

Step 1 of [the faster-fixes plan](2026-11-26-faster-fixes-plan.md). Measured 2026-11-26 about 10:50-11:05 America/Chicago by a general-purpose subagent of the session "Kit · Faster small fixes · 2026-11-26", read-only, from `list_events` timestamps (kinds user, assistant, result; every page). Totals and phase labels only; no message content.

Method: each interval runs from one main-thread event to the next and goes to the phase of the last tool call. A wait of up to 10 min after a turn goes to the phase it waits on (CI: push+checks; reviewer: review). A gap over 10 min with no human message is "idle-external" and is not agent time. Commit + push + check in one call counts as push+checks.

## Sessions (all 2026-11-25)

| Session | Agent min | Largest phase | Reviewer runs | Commits | Handoff edits |
|---|---|---|---|---|---|
| S1 90-161.Z bump_lock fix (PR 248) | 18.2 | push+checks 10.4 (57%) | 3 (2 after merges of main) | 3 | 0 |
| S2 Kit ARCHIVE DUE fix | 5.9 | fix 2.4 (40%) | 1 | 1 | 0 |
| S3 ICF cache walk fix (PR 281) | 40.9 (+3.8 human wait) | push+checks 16.2 (40%) | 5 (4 after fixes, 1 after a conflict) | 5 | 1 |
| S4 90-161.Z lock engine-v39 (PR 239) | 8.6 (+293.5 idle-external) | push+checks 2.9 (34%) | 1 | 1 | 0 |

## Combined (73.6 agent min)

| Phase | Min | % | Tool calls |
|---|---|---|---|
| start | 2.1 | 2.8 | 11 |
| skill-load | 0.2 | 0.2 | 2 |
| fix | 21.2 | 28.8 | 97 |
| push+checks | 30.5 | 41.4 | 48 |
| review | 14.6 | 19.9 | 21 |
| merge+verify | 3.2 | 4.3 | 36 |
| handoff | 0.3 | 0.4 | 6 |
| summary | 1.7 | 2.3 | 0 |

## Other evidence

- 90-161.Z R44 r2 round: about 2 h 30 min; slowest: 7 pushes with an 8-10 min Windows CI job each, 2 failed runs, 4 review rounds (90-161.Z docs/reviews/2026-11-26-r44r2-plan.md line 33).
- 90-161.Z git history since 2026-11-20 (clone depth 50): 6 of 67 merges were handoff-only pull requests.
- Kit check lanes, this clone, 2026-11-26: fast 26.4 s, full 27.8 s.

## What it shows

1. push+checks (41%) and review (20%) are 61% of agent time. 10 reviewer runs for 4 fixes: 6 were repeat reviews after a fix or a merge of main.
2. Start, skill loads and handoff are under 4% together. Cuts there save little time in fix sessions (handoff-only pull requests matter in round work).
3. S3 is 56% of the agent minutes, so the combined shares lean on one session. 4 sessions is a small sample: confidence medium.
