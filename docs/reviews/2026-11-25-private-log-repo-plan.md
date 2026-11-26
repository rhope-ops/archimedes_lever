# Plan: private project logs in a git repo

Approved by the Maintainer on 2026-11-25 (America/Chicago), in session "Kit · Private log repo". Scope: the private project log of each public project.

## Problem

Sessions that another session starts with `create_session` get no Claude Docs tools, so they cannot write the private log docs (FIRST_USE answer 12A). They fall back to "Paste into: project log", and the Maintainer pastes. Evidence: the RADE session of 2026-11-25 had 25 tools and no `mcp__Claude_Docs__*`. The RADE, SPAR, 65-601.Z and 36-3003.Z log docs were last updated on 2026-11-14, and 33-332.Z on 2026-11-20, while sessions worked on those projects until 2026-11-25.

## Decisions (the Maintainer, 2026-11-25)

- The logs move to a private git repo (option A).
- They go in the existing private repo `rhope-ops/token-logs`, folder `project-logs/<short name>/LOG.md`.
- The branch is `claude/project-logs`. Sessions push rows straight to it, with no pull request.

## Steps

1. Attach `token-logs` with push access, then run a test push. Done: commit 812f152.
2. Copy the 6 log docs (RADE, SPAR, 65-601.Z, 36-3003.Z, 33-332.Z, 90-161.Z) into `project-logs/<short name>/LOG.md`, in the kit table format.
3. Kit PR (lane C): change the project-log skill, the AGENTS.md "Project log" line and FIRST_USE answer 12A. The Maintainer approves the exact rule text before the merge.
4. One PR per project: the "Project log" line in its Project rules points to the repo path.
5. Add a "Moved to ..." line at the top of each old doc.
6. Verify (a seeded session writes one row) and report.
