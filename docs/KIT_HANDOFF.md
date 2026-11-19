# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"). Kit only: first use deletes it in a project, which uses docs/NEXT_PROMPT.md. Keep it at 40 lines or fewer; evidence goes in docs/reviews/. Times are America/Chicago.

Updated: 2026-11-19 07:40. Kit owner: the session "Kit · Session names and project tags · 2026-11-19" (kit 4.0.0 plan).

## State

- main: kit 3.2.0 (18896fc, PR 62). Tags (feature releases; the owner makes them): v2.0.0 (7b80101), v3.0.0 (67e7766), v3.1.0 (88185f0); v3.2.0 not made yet. Fleet page: https://claude.ai/artifact/AWtpGxEqCWrjrPa1Afe7qW (private; the kit owner updates its rows). Its "Waiting for you" list (2026-11-19) reads the `needs` field (`[{text, url}]`) of `meta/kit` and of each `repos` row: the session that closes or adds an owner action updates that field.
- All seven repos on 3.2.0 (18896fc; lock pass, 2026-11-18): RADE 112, 90-161.Z 164, 36-3003.Z 10, 65-601.Z 10, SPAR 15, icf-source 141, sec-source 17. Session load after the lane A trims: icf-source ~4,797 (PR 143), sec-source ~4,716 (PR 18); RADE ~4,861.

## Approved plan (the owner, 2026-11-19 07:30): kit 4.0.0, session names

Full text and approved rule text: [reviews/2026-11-19-session-names-plan.md](reviews/2026-11-19-session-names-plan.md). Earlier plan (lean rules, 2026-11-18): done except its step 5 (Open 1); record: [reviews/2026-11-18-lean-rules-sync-plan.md](reviews/2026-11-18-lean-rules-sync-plan.md).

- [x] 0. Plan saved.
- [ ] 1. Kit PR (rule, header line, handoff skill, check-in TITLE and SESSIONS lines, CHANGELOG 4.0.0).
- [ ] 2. Fresh review and rule-conflict check.
- [ ] 3. The owner tags v4.0.0.
- [ ] 4. Nine sync PRs: RADE, 90-161.Z, icf-source, 36-3003.Z, 65-601.Z, sec-source, SPAR, no-more-beyond, transcription_assistant.
- [ ] 5. Fresh review of each sync; merge on green (pre-approved).
- [ ] 6. Backfill PR numbers on the 306 session titles; archive the finished idle sessions.

## Open (in order)

0. Kit fixes for the next PATCH (found by the 3.2.0 reviews; none blocks a repo): (a) the sync swaps "the owner" for each repo's role inside `scripts/check_settings.py`, so `OLD_HEADER_LINES` misses the old "the owner's request" line: exclude that file from the swap or match any role (5 repos got a hand fix in their sync PR); (b) `new_header` stops at a blank line; (c) NITs: the `audit-duplicate-ignore` wording in `bloat_check.py`, the CHANGELOG 3.2.0 row does not name `sync_merge.py`.
1. Step 5 (rulesets, secret scanning: the owner's clicks, docs/github/README.md).

## Needs the owner

- The v3.2.0 tag: https://github.com/rhope-ops/archimedes_lever/releases/new?tag=v3.2.0&target=18896fc5ae5e954eeb0182bc4beae264eee9d541&title=Kit%203.2.0; rulesets and secret scanning.

## Do not

- Do not merge a kit pull request before you list the kit's open pull requests: on 2026-11-18, pull requests 44 and 45 were merged while 42 was open, and 42 then conflicted in about 15 files.
- Do not put a command that holds a denied git pattern in a shell heredoc: the deny rules refuse it. Use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first: after 4.0.0, icf-source (~4,995) and RADE (~4,985) sit at the 5,000 cap; the next kit text needs a cut first.
