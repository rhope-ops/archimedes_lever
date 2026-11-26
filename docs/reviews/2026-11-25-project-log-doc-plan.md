# Plan: sessions write the private project log doc

Approved by the Maintainer on 2026-11-25 (America/Chicago), in session "Kit · Private log repo". Scope: the private project log of each public project.

## Problem

Sessions asked the Maintainer to paste each log row. Evidence: the RADE session of 2026-11-25 had the Claude Docs tools connected (its `init` events) and never called one; its last turn said "this repo is public, so the row goes in your private log doc. Paste into: project log". The RADE, SPAR, 65-601.Z and 36-3003.Z log docs were last updated on 2026-11-14, and 33-332.Z on 2026-11-20, while sessions worked on those projects until 2026-11-25.

Cause (medium confidence, 1 session): the rule's fallback ("If you cannot write to the log, ... Paste into") made the paste the easy path, and no skill step said how to add a row to a doc.

## Test in a session that another session started (2026-11-25)

| Path | Result |
|---|---|
| Private repo `rhope-ops/token-logs` | `add_repo` denied by the auto-mode classifier ("Unauthorized Access"); passed only after the Maintainer approved in chat |
| Claude Docs | tools loaded; a test doc made and a row appended with `update`; both rows read back |

## Decisions (the Maintainer, 2026-11-25)

- First: move the logs to a private repo. Withdrawn after the test above.
- Final: the logs stay in their Claude docs; the rule and skill make sessions write the doc first.
- Remove the test doc, the test branch and the repo copies.

## Steps

1. Test both paths in a session that another session started. Done.
2. Kit PR 225 (lane C): AGENTS.md "Project log" and the project-log skill section "A log in a Claude doc". The Maintainer approves the exact rule text before the merge.
3. Cleanup: test doc deleted. The branches `claude/log-write-test` and `claude/project-logs` in `rhope-ops/token-logs`: the delete push was refused (HTTP 403); the Maintainer deletes them.
4. Each project takes kit 14.0.0 at its next sync; no project change is needed (their "Project log" lines already name a doc).
