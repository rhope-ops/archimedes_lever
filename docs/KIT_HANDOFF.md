# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"; first use deletes it, and a project uses docs/NEXT_PROMPT.md). At most 40 lines, inside the session-load cap (`.check` counts it); evidence and older items: docs/reviews/. Times: America/Chicago.

Updated: 2026-11-25 14:40 ("Kit · Closeout R1-R3 and docs"): the tool-retirement plan and the fleet audit are closed; AGENTS.md R1-R3 merged (PR 216). Older items: [archive file](reviews/2026-11-24-kit-handoff-archive.md).

## State

- Kit 12.0.0 (c0fa5f1) in all 10 repos ([plan](reviews/2026-11-25-instructions-80-plan.md)); tag: the Maintainer. T2: baseline 30000 as a ceiling ("cap": true, PR 215).

## Open

- [Archival plan](reviews/2026-11-25-archival-plan.md) (approved 2026-11-25): phase 1 kit inventory. Follow-ups 3: [state](reviews/2026-11-23-fleet-v2-coordinator-state.md).
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
