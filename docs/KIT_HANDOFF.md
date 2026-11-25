# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer and inside the session-load cap (`.check` counts it); evidence and older items go in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-25 08:41 (token log session): PRs 200-204 merged; v11.2.0 tagged; setup script on the tag. No tag ruleset: one admin (the Maintainer, 2026-11-25). Older items: [archive file](reviews/2026-11-24-kit-handoff-archive.md); fleet audit [report](reviews/2026-11-24-fleet-audit.md).

## State

- Kit 11.1.0 = a6295509 (tag v11.1.0, made by the Maintainer 2026-11-25). P1-P3, the fleet audit, follow-ups 1-8. 10 fleet repos on 11.1.0. Kit PRs 184-201 go in 11.2.0. T2 20,608.

## Approved plan (the Maintainer, 2026-11-23 17:12): custom tool retirement

Plan and decisions 1-10: [reviews/2026-11-23-tool-retirement-plan.md](reviews/2026-11-23-tool-retirement-plan.md); P2 record: [reviews/2026-11-23-tool-retirement-handoff.md](reviews/2026-11-23-tool-retirement-handoff.md).

- [x] Research and plan. [x] P1 (PR 137). [x] P2. [x] Fleet audit (PRs 158, 159). [x] P3: kit package (kit PRs 164, 168, 169); 33-332.Z pilot in package mode (its PRs 99, 102, 103, 104; 27 of 53 kit scripts from the package). Follow-ups: --kit-install after a branch switch (S7 text), check-in KIT line when the package is missing, MAINTAINER_GUIDE step, bandit in security.yml, 4 MINOR of PR 168. [~] P4: done, except 90-161.Z PR 235 (open for your look) and the SBOM steps (ask rule `*--output*`); RADE CodeQL not started. [x] P5. [~] P6: exports, [branch list](reviews/2026-11-24-p6-branch-list.md); deletes need the Maintainer's OK.

## Open

- Approved plan (the Maintainer, 2026-11-25): instructions at "80%", no "Go on." ([plan](reviews/2026-11-25-instructions-80-plan.md)); phase 1 in work.

- Follow-ups 2: 11 of 13 done ([plan](reviews/2026-11-25-followups-2-plan.md), [state](reviews/2026-11-23-fleet-v2-coordinator-state.md)); 90-161.Z PR 239 held for the Maintainer (state, last section).
- Fleet audit (report, "Open questions"): A10, A11, A15 in PR 160; the other audit-the-audit items (A1-A9, A12-A14) open. Cut proposals 5, 8, 9 and each project's AUDIT DUE wait for that project's own audit (the Maintainer, 2026-11-24). Skill-use audit due 2026-12-08.
- Kit PATCH fixes (a)-(f) and Step 5: archive file, "Open".

## Needs the owner

- Tags, branch deletes, account skills, the 2026-11-21 items: archive file, "Needs the owner".
- Add the Dependabot secret `PII_GUARD_DENYLIST` (steps: archive file, "Dependabot secret"), then re-run the checks of PRs 115 and 116.
- Delete the merged branches `claude/fleet-audit-cli-helpers`, `claude/fleet-audit-report` (kit) and `claude/fleet-audit-site-page-dedup` (33-332.Z).

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first (`scripts/bloat_check.py --brief` on a dry-run sync): at 11.0.1 the highest is 33-332.Z ~5,473 of the 5,500 cap.
