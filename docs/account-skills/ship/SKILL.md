---
name: ship
description: Use only in a Git repository that has no delivery skill of its own (no `.claude/skills/deliver/SKILL.md`) when work is ready to commit, push, open a pull request or merge, and before you report that work as done. Gives the safe steps from a new branch to merged and clean, the merge lanes by risk, and the report. In a repository with a `deliver` skill, use that skill and not this one.
---

# Ship

The user's procedure to take work in a Git repository from "changed" to "merged and clean". The user does not want to approve each step. They want the same safe sequence each time, and a short report at the end.

A repository's own rules win. If it has `.claude/skills/deliver/SKILL.md`, stop here: load that skill and follow it and its AGENTS.md "Delivery"; this skill adds nothing there. In another repository with an AGENTS.md or other delivery rules, read them first and follow them where they differ. Use the steps below for what they do not cover.

## Limits in every repository

These hold even where a repository says nothing. The user's preferences no longer list them; this skill is their home.

- No direct commit, push or merge to the default branch. No push with `--no-verify`.
- No force-push, history rewrite, reset, clean or stash to make a branch look synchronized. Update a branch by merge.
- No deletion of a branch that has unmerged work.

## 1. Start

- Start new work on a new branch from the latest default branch. Fetch first, so the branch does not start from stale history. When the host names the branch to use, use that one.
- Batch related changes into one branch and one pull request.

## 2. Check

- Run the repository's tests and checks yourself (look in AGENTS.md, the README, the CI configuration and the package scripts for the command). Record the command and its result: it is the proof that the work is done.
- If the repository has no check that you can run, say so, do not report the work as verified, and recommend the smallest check that would prove this change.
- Before each commit and before the pull request: scan the diff, the commit message and the pull request text for personal data and secrets. Run the repository's content check or personal-data guard where it has one.

## 3. Push and open the pull request

- Push the branch and open a pull request. This is the user's standing request; do not ask first.
- Use the headings of the repository's pull request template, if it has one.
- Name the merge lane (step 4) in the pull request text, and put there the summary lines that apply: Proof, Drift, Applied, Assumptions, PII, Delegated.
- Give the user the pull request link.

## 4. Merge by lane

Before a merge, list the repository's open pull requests: work of another session can come first or conflict. If the base branch moved, merge it into your branch and run the checks again.

| Lane | What the pull request holds | Merge |
|---|---|---|
| A | Docs that are not rules | When the checks pass |
| B | Code, scripts, checks and tests | When the checks pass and a fresh review (a reviewer that gets only the diff and the brief, on a model tier no lower than the author's) finds no MAJOR finding |
| C | Rule or instruction files; guard files (hooks, CI, settings); a UI change the user has not seen; a live or irreversible effect, or a merge that deploys; a data write; a security change; a MAJOR finding; a self-review only; a repository with no check; a conflict with another session's work | Ask the user in one question: the pull request link, the check result and the review result |

Take the highest lane that any file or effect of the pull request falls in; in doubt, take the higher one. Merge with a merge commit. A review covers the head commit you merge: a fix after the review gets its own review.

## 5. After the merge

- Verify that the default branch has the commit (`git fetch` and `git merge-base --is-ancestor <commit> origin/<default branch>`).
- Delete the branch on GitHub if the repository does not delete it automatically, and confirm the merge and the deletion.
- Report: the pull request link, the check result (CI, or the local command and its result), the review result if a review ran, and one line that summarises the change.

## 6. Clean up old branches

- Delete old remote branches that you or the user created, if their work is already on the default branch (merged, or no changes of their own).
- Keep each branch that has unmerged work. List it for the user with a recommendation (finish, open a pull request, or delete after their approval).
