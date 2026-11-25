# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"; first use deletes it, and a project uses docs/NEXT_PROMPT.md). At most 40 lines, inside the session-load cap (`.check` counts it); evidence and older items: docs/reviews/. Times: America/Chicago.

Updated: 2026-11-25 16:34 (coordinator 4): fleet audit + archive run done in all 10 repos; kit 13.1.1 in 9 (ICF PR 291 last). Older items: [archive file](reviews/2026-11-24-kit-handoff-archive.md).

## State

- Kit 13.1.1 (640561d) in the fleet ([fleet run](reviews/2026-11-23-fleet-v2-coordinator-state.md), "Coordinator 4"); tags v13.0.0-v13.1.1: the Maintainer (a deny rule blocks agents). T2: baseline 30000 as a ceiling ("cap": true).

## Open

- [Archival plan](reviews/2026-11-25-archival-plan.md) (approved 2026-11-25): phases 1-4 done in the kit and the fleet (2026-11-25, age waits waived by the Maintainer). Follow-up: the archive step misses evidence a plan cites by description (3 wrong deletions, all caught by review). Follow-ups 3: [state](reviews/2026-11-23-fleet-v2-coordinator-state.md).
- Tool retirement and fleet audit: open items in the [close-out list](reviews/2026-11-25-closeout-and-trim-proposals.md). Skill-use audit due 2026-12-08.
- Kit PATCH fixes (a)-(g) and Step 5: archive file, "Open".

## Needs the owner

- Tags, branch deletes, account skills, the 2026-11-21 items: archive file, "Needs the owner".
- Add the Dependabot secret `PII_GUARD_DENYLIST` (steps: archive file, "Dependabot secret"), then re-run the checks of PRs 115 and 116.

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, merges of 44 and 45 made the open 42 conflict in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first (`scripts/bloat_check.py --brief` on a dry-run sync): the highest project is near the 5,500 cap.
