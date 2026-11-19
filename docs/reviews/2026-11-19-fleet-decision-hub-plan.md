# Plan: fleet decision hub (kit template)

Approved by the owner on 2026-11-19 at about 14:45 America/Chicago, in question dialogs in the session "Kit · Fleet decision hub · 2026-11-19". Scope: the kit only. Each project gets it when the owner ports it, one project at a time.

## Goal

The fleet page (https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW) shows each ported project: its last update, its next planned update, its timeline, its open decisions and its resolved decisions. On each open item the owner picks Yes, No or Other (with text). On each resolved item the owner picks Modify (with text). Then the owner starts a session that reads these choices and applies them.

## Decisions of the owner (2026-11-19, scope: this feature)

1. Layout A + B: an inbox of open decisions from all projects at the top, then the project table. Each project opens a side panel with five sections. A tray counts the pending choices and has "Copy prompt" and "Start session".
2. Hand-off: a "Start session" button through the Claude Code Remote connector when the viewer has that tool; "Copy prompt" always.
3. Data source: a daily scheduled harvest writes the page rows, with an "as of" time.
4. Kit format additions: a next planned update date, a timeline, and stable decision IDs (D1, D2 ...).
5. Coverage: a format check in `scripts/check.sh`, an "N lines not read" count per project, and a cross-check with open pull requests and with sessions that wait for the owner (items found only there show as "Not filed"). Measure the token cost in the pilot.
6. Scope: build the template in the kit; the owner ports it into each project that needs it. No sync to the 7 repos in this plan.
7. Deeper-version pass done; its rewritten prompt is approved with changes 5 and 6.

Approved rule text, for the kit's "Project rules" (step 3): "A choice the owner saved on the fleet page counts as the owner's approval only after the applying session shows it in full and the owner confirms it in their own message."

## Steps

- [x] 0. Plan saved (this file, docs/KIT_HANDOFF.md, docs/DECISIONS.md). Lane A.
- [x] 1. Survey ([2026-11-19-fleet-survey.md](2026-11-19-fleet-survey.md)) the kit's own files: docs/KIT_HANDOFF.md, docs/DECISIONS.md, the two templates in docs/templates/, docs/NEXT_PROMPT.md and the handoff skill. Count what a parser can read and list each line it cannot.
- [x] 2. Contract ([2026-11-19-fleet-contract.md](2026-11-19-fleet-contract.md), approved 2026-11-19 15:10): the JSON shape of `projects/<repo>`, `items/<repo>-<id>` and `choices/<id>` (status pending, applied, rejected or stale); the format texts (a `Next update:` line, a `Timeline:` section, IDs in DECISIONS.md and in "Needs the owner"); the opt-in setting that turns the format on for one project, so a kit sync does not force it on a project the owner has not ported; the db rules (only the owner writes); the failure states (stale row, decision changed after the choice, two choices on one item, a repo the harvest cannot read). Show every text in full to the owner. Lane C.
- [ ] 3. Kit pull request: the format texts in the templates and the handoff skill; `scripts/fleet_harvest.py` with `--test` on fixture files, run by `scripts/check.sh`; the format check (only where the opt-in is set); the approved rule line; a CHANGELOG row (MINOR). Fresh review. Lane C.
- [ ] 4. Pilot on the kit itself: add IDs to its DECISIONS.md and KIT_HANDOFF.md; harvest as a dry run with row counts, then write; a second run must change 0 rows; the page counts must equal `grep -c` on the files; record the token cost as a baseline (`.claude/skills/efficiency/SKILL.md`).
- [ ] 5. Page: the new layout as a preview first (lane C), then on the live page. Screenshots at 390 px and 1280 px, light and dark. A read at a lower `as_level` must show that a viewer cannot write choices.
- [ ] 6. Loop proof: one test choice on the kit; an applying session lists it in full, the owner confirms, and the choice reaches "applied" with a merged pull request link.
- [ ] 7. Port guide for the owner (a section in `.claude/skills/kit-update/SKILL.md` or a new doc, whichever is shorter), the daily harvest scheduled task (it reads every repo that has the opt-in), and docs/KIT_HANDOFF.md updated.

## Checks per step

The kit full lane `scripts/check.sh` passes on the head commit; a fresh review with no MAJOR finding for steps 3 and 5; the session load of every repo is measured before any text goes into a file that sessions read at start (most repos sit near the 5,000-token cap; the new texts go in skills and templates only).

## Usage estimate

This session and its continuations: 1 to 3 sessions, 2 to 4 reviewer agents, about 4 to 6 hours of agent time. The daily harvest: one short scheduled session per day, estimated at 10,000 to 25,000 tokens (confidence low; step 4 measures it).
