# Plan: kit 4.0.0 (planned as 3.3.0), session names (approved by the owner, 2026-11-19)

Approved in the session "Kit · Session names and project tags · 2026-11-19" (dialog answers, 2026-11-19 about 07:30 America/Chicago). Scope: the kit and every repo that takes kit syncs.

## Approved decisions

- Title form: `<Short name> · <Task, 2-6 words> · YYYY-MM-DD` (start date, the header's time zone), tag `project:<short name in lower case>`.
- PR number: ` · #<number>` at the end, from the first pull request the session opens.
- Auto-archive: a session archives itself when its pull requests are merged and nothing waits on the owner.
- Extras: the resume prompt names the next session's title; the check-in prints a SESSIONS line so the agent lists this project's sessions that wait on the owner.
- Approved rule text (AGENTS.md "Defaults", new line):

  - **Session names.** Title each cloud session `<Short name> · <Task, 2-6 words> · YYYY-MM-DD` (start date, header's time zone) with the tag `project:<short name>`; when its first pull request opens, add ` · #<number>`; archive the session when its pull requests are merged and nothing waits on the owner. Child sessions follow the same form. `scripts/session_checkin.sh` prints the TITLE line; steps: `.claude/skills/handoff/SKILL.md`.

- Changed (the owner, 2026-11-19, after the session-load measure): the line above is not added; it would put RADE (~4,976) and icf-source (~4,986) over the 5,000 cap. Instead "Start of session" lists the output lines `TITLE, SESSIONS`, the check-in prints them, and the handoff skill section "Session names" holds the rule in full. Version: 4.0.0 (a changed kit rule text is MAJOR by docs/CHANGELOG.md), not 3.3.0.
- Approved header line (AGENTS.md header, new): `- Short name: {{SHORT_NAME}}` (for example RADE, ICF, SEC2).
- Merges: pre-approved when the full check passes and the fresh review finds no MAJOR; stop and ask on a MAJOR or a failure.
- Sync targets: RADE, 90-161.Z, icf-source (ICF), 36-3003.Z, 65-601.Z, sec-source (SEC2), SPAR, no-more-beyond (NMB), transcription_assistant (TA).
- Backfill: add PR numbers to the existing 306 session titles (from each session's summary; confidence medium).
- Archive now: the finished idle sessions with nothing waiting on the owner.

## Steps

1. Kit PR (4.0.0): the rule pointer, the header line (`{{SHORT_NAME}}` filled by bootstrap.sh, sync_baseline.py `--short-name`, drift.py), the handoff skill section, TITLE and SESSIONS lines in session_checkin.sh with self-tests, CHANGELOG 4.0.0, a DECISIONS row. Measure the session load of every repo first (KIT_HANDOFF "Do not").
2. Fresh review and rule-conflict check (reviewer agents, Opus).
3. The owner tags v4.0.0.
4. Nine sync PRs (worker agents, Sonnet), each sets its short name.
5. Fresh review of each sync (reviewer, Opus); merge on green.
6. Backfill PR numbers on the existing titles; archive the finished idle sessions.

## Changes after approval (the owner, 2026-11-19)

- Add to 4.0.0: sessions coordinate when one repo has several open pull requests (deliver skill step 5).
- Auto-archive approval: one line in the owner's account preferences (no repo tokens), not a rule line.
- NMB and TA: not on the kit layout; full conversion approved (a first sync each, like sec-source PR 15 and icf-source PR 135).
