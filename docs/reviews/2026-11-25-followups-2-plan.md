# Follow-ups 2: plan

Written 2026-11-25 by "Kit · Fleet coordinator 3" (session_01PyXpdUk7tSsbCmQXyLSzEZ). Status: **approved by the
Maintainer, 2026-11-25** (coordinator 3 chat, dialog answer "Approve all 12"). Source: the follow-ups in
[2026-11-23-fleet-v2-coordinator-state.md](2026-11-23-fleet-v2-coordinator-state.md), sections "Coordinator 3".

## Decisions with this plan (the Maintainer, coordinator 3 chat, 2026-11-25)

- Kit #187: merge (security.yml skips pull requests in a private repo); answer "Merge #187". Item 13 below closes its gap.
- SBOMs for RADE and 90-161.Z: "approved" (the coordinator runs the `--output` commands at the prompt).
- Branch deletes: approved; the Maintainer runs them from a Codespace with [2026-11-24-p6-delete.tsv](2026-11-24-p6-delete.tsv).
- 90-161.Z #235 and its round-skill text: approved as written in the dialog ("Approve text").
- Role words: approved for all 3 repos ("Approve all 3"): AGENTS.md only; no-more-beyond and SPAR "the Administrator" to
  "the Maintainer"; SEC-Source "the owner" to "the Maintainer"; possessives the same way.
- Lane C merges in this plan: when the last fresh review has 0 MAJOR and CI is green on the head (as DEC 4).

## Items

| # | Item | Repo | Lane | Owner |
|---|---|---|---|---|
| 1 | ReDoS fix in `build_site_html.py` (CodeQL, seen in 90-161.Z #232) | kit | C | kit child |
| 2 | A named allow for `cyclonedx-py` and `pip-compile` commands in `.claude/settings.json` (the ask rule `Bash(*--output*)` stays for all others) | kit | C | kit child |
| 3 | The approval-quote marker handles a `Date \| Scope \| Decision` table | kit | C | kit child |
| 4 | T6 also matches "the Administrator" | kit | C | kit child |
| 5 | `session_checkin` prints a line in a fresh clone | kit | C | kit child |
| 6 | The SessionStart hook matcher also runs on resume | kit | C | kit child |
| 7 | SECURITY.md stops assuming private reporting is on | kit | C | kit child |
| 8 | `code_standard.py` and `build_site.py` split under 450 lines | kit | C | kit child |
| 9 | The looser cases of #183 (the strict gate against ruff E501) | kit | C | kit child |
| 10 | RADE `Start-SignInSize`: an opt-in that sizes only the PnP sign-in window (or a no-state verb), then an engine release | RADE | C | RADE child |
| 11 | RADE CI: install the pinned packages (`--require-hashes`) and run `pip check` | RADE | C | RADE child |
| 12 | 33-332.Z: the 3 MINOR texts of #118, after the PAM's ISE test | 33-332.Z | B | the next 33-332.Z session |
| 13 | Kit: bandit in the local full lane (closes the #187 gap) | kit | C | kit child |

Out: the worker scan `@(` item (closed by DEC 5).

## Agents, cost and order

- The coordinator (Opus) merges lane C. A kit child (Opus) does items 1-9 and 13 in about 5 pull requests. A RADE child
  (Opus) does items 10 and 11. Item 12 waits for the PAM's ISE test: a line in 33-332.Z docs/NEXT_PROMPT.md.
- About 10 fresh reviews (`reviewer`, Opus). Estimate 5 to 7 hours. The usage limit can stop the work between steps.
- T2 (kit script lines, 20,132): items 1-9 and 13 add code and tests; item 8 moves lines and adds none. A plan total
  over about +400 is drift: tell the Maintainer.
- Rollback: a revert pull request of each merge commit.
