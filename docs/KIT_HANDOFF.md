# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer and inside the session-load cap (`.check` counts it); evidence and older items go in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-24 22:20 by "Kit · Fleet coordinator 3 · 2026-11-24": P4a, P4c done (engine-v38), P4b waits for R42, P6 branch list made: [state](reviews/2026-11-23-fleet-v2-coordinator-state.md) last section. Older items: [reviews/2026-11-24-kit-handoff-archive.md](reviews/2026-11-24-kit-handoff-archive.md); fleet audit report: [reviews/2026-11-24-fleet-audit.md](reviews/2026-11-24-fleet-audit.md).

## State

- Kit 11.1.0 (tag v11.1.0; v11.0.1 9e3f6fa): P1-P3, the fleet audit, follow-ups 1-8 (plan in docs/reviews). 4 fleet repos lock 11.1.0 (2026-11-24). Script lines (T2) 20,023.

## Approved plan (the Maintainer, 2026-11-23 17:12): custom tool retirement

Plan and decisions 1-10: [reviews/2026-11-23-tool-retirement-plan.md](reviews/2026-11-23-tool-retirement-plan.md); P2 record: [reviews/2026-11-23-tool-retirement-handoff.md](reviews/2026-11-23-tool-retirement-handoff.md).

- [x] Research and plan. [x] P1 (PR 137). [x] P2. [x] Fleet audit (PRs 158, 159). [x] P3: kit package (kit PRs 164, 168, 169); 33-332.Z pilot in package mode (its PRs 99, 102, 103, 104; 27 of 53 kit scripts from the package). Follow-ups: --kit-install after a branch switch (S7 text), check-in KIT line when the package is missing, MAINTAINER_GUIDE step, bandit in security.yml, 4 MINOR of PR 168. [~] P4: RADE engine-v38 and 33-332.Z done, ICF runbook done; RADE SBOM/CodeQL blocked; 90-161.Z after R42. [x] P5. [~] P6: exports, [branch list](reviews/2026-11-24-p6-branch-list.md); deletes need the Maintainer's OK.

## Open

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
