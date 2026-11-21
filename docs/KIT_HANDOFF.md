# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-21 17:10 by session "Kit · Fleet cleanup 10.1.0 · 2026-11-21". Before: "Kit · Project Studies and fleet sync" (PRs 103, 105 merged; PR 107 closed: the owner keeps "the Owner's"), "Kit · Instructions hard rule" (PRs 104, 108; 7 README steps name claude.ai screens that are not verified: reviews/2026-11-21-fresh-reader.md).

## State

- main: kit 10.0.0 (f397b52; main 160c81e). Tags on origin: v1.0.0–v3.2.0, v4.0.0, v6.1.1, v6.2.0, v7.0.0, v8.0.0, v10.0.0. Missing (MINOR or MAJOR only get a tag): v4.1.0 (4135536), v5.0.0 (24c2391), v6.0.0 (43ad952), v8.1.0 (a94284e), v9.0.0 (a620a7f).
- Fleet on 10.0.0 (merged 2026-11-21): RADE 165, 33-332.Z 48, ICF-Source 240, SEC-Source 27, SPAR 19, 36-3003.Z 14, 65-601.Z 14, no-more-beyond 66, transcription_assistant 8. 90-161.Z on 9.0.0; its sync is PR 216 of its own session (K2). Session load (cap 5,500): 33-332.Z ~5,352, ICF ~5,322, RADE ~5,278, TA ~5,250, SEC ~5,210, NMB ~5,178.
- Branch `claude/token-usage` is a data branch (`scripts/token_log.py` writes one CSV per session): never delete it.

## Approved plan (the owner, 2026-11-21 17:05): fleet cleanup, kit 10.1.0

Full text, owner decisions and the approved Delegation rule text: [reviews/2026-11-21-fleet-cleanup-10-1-0-plan.md](reviews/2026-11-21-fleet-cleanup-10-1-0-plan.md).

- [x] 1. Plan saved. Paused by the owner 2026-11-21 17:15 (7-day usage limit; no work on overage): continue at step 2 after the reset, 2026-11-23 05:00.
- [ ] 2. Kit PR 10.1.0: placeholder false positive; backlog (a)(b)(c)(d)(f) below; token_log timestamp crash and `tokens()` docstring; Delegation text and skill sentence; 9c record; session-load trim; CHANGELOG; review; lane C merge.
- [ ] 3. Sync 10.1.0 to the 9 repos on 10.0.0 (plan approval covers green merges with no MAJOR finding).
- [ ] 4. TA audit (report only).
- [ ] 5. Tag links to the owner. [ ] 6. Handoff; message K2 (90-161.Z).

## Open

- Backlog from the 3.2.0 reviews: (a) the sync swaps the role inside `scripts/check_settings.py`, so `OLD_HEADER_LINES` misses the old "the owner's request" line; (b) `new_header` stops at a blank line; (c) NITs: `audit-duplicate-ignore` wording in `bloat_check.py`, the CHANGELOG 3.2.0 row does not name `sync_merge.py`; (d) `fix_hooks` keeps an old `tools/git-hooks` path, so the content check is skipped; (f) first use keeps the kit's "Project rules" lines (reviews/2026-11-19-rule-conflict-fleet.md finding 4); (e) 90-161.Z commit 50421f2 is unpushed (its pre-push needs pwsh).
- Other kit follow-ups: `scripts/check.sh` and `fleet_harvest.py` cite a kit-only review file; `skill_use.py` is slow on 200,000 unmatched brackets.
- Fleet hub plan (2026-11-19, [record](reviews/2026-11-19-fleet-decision-hub-plan.md)): all done except step 6, loop proof after the owner ports a first project.

## Needs the owner

- Per repo: `audit-instructions:` lines in `.check`; 33-332.Z README does not open with its Purpose line (warning).
- Rulesets and secret scanning (docs/github/README.md). Account skills to save (files from 2026-11-20): `pages-and-tools`, `ship`, `turn-summary`, `roadmap-update`, `stakeholder-update`; 2 preference lines.

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first (`scripts/bloat_check.py --brief` on a dry-run sync).
