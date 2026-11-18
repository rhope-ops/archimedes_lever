---
name: deliver
description: Use when a change in this repo is ready to commit, push, merge or publish, when a push or a merge is blocked, when you clean up branches or change a GitHub Actions workflow, and before you report repo work as done. Gives the delivery steps, the two check lanes, blocked steps and branch clean-up.
---

# Deliver a change

AGENTS.md "Delivery" and "Checks" point here. The rules are there; this file holds the steps.

## Steps

1. Commit on a branch (the branch the host requires, else `claude/<topic>`), with a noreply identity.
2. Push. The pre-push hook runs the fast lane; do not run it by hand first.
3. Open a pull request for the branch (one per branch). When the work is ready to merge: run the full lane one time on the head commit (`scripts/check.sh`), and get the fresh review on that head commit when AGENTS.md "Delegation" requires one.
4. Merge the pull request with a merge commit when AGENTS.md "Delivery" allows it. If the base moved, update the branch by merge first.
5. Verify: `git fetch origin main && git merge-base --is-ancestor <commit> origin/main`.
6. Republish the affected artifacts. Delete previews after they ship.
7. Clean up branches (below). Report with the states kept apart: done, published, verified.

## Check lanes

| Lane | Command | Runs | When |
|---|---|---|---|
| Fast | `scripts/check.sh --fast` | Rule caps and pointers; self-tests only of the kit scripts that changed against origin/main; the project log check; the content check; `scripts/check.local.sh --fast` | The pre-push hook, on each push |
| Full | `scripts/check.sh` | Everything: all self-tests and `scripts/check.local.sh` with no argument | Before a merge (step 3), and the pull-request Action |

- Steps of a lane run in parallel. Each run ends with a `TIME` line (the wall time and the 3 slowest steps) and a line that compares the times with their baselines. A `WARN  slower than the baseline` line (full tier) starts the `efficiency` skill; it never fails the lane.
- A passing step can print `WARN` lines (rule lint). When rule lines changed, the full lane fails until the conflict check of `.claude/skills/rule-change/SKILL.md` has a record.
- `scripts/check.local.sh` gets `--fast` as its first argument in the fast lane. A fast project lane must still check each changed file in full and that generated files are not stale. A script that ignores the argument runs everything, which is slow but safe.
- A lane that passed on a clean tree leaves a stamp in `.git/`; the hook skips a repeat run on the same commit. Never write the stamp by hand.
- The fast lane can miss a defect in a file that did not change. The full lane before the merge is the gate: never merge on a fast-lane pass.

## No project tests yet

While `scripts/check.local.sh` does not exist (check.sh says SKIP project checks), the kit checks and the fresh review are the only gate. At the first code change, propose a `scripts/check.local.sh` that runs this project's tests or a smoke test.

## Blocked steps and host limits

- If permissions block a step, give the exact commands to paste, one code block for each command.
- When the content check blocks a push: `.claude/skills/personal-data/SKILL.md`.

## Branch clean-up

Delete a remote branch when all its work is on main (`git merge-base --is-ancestor origin/<branch> origin/main`), stale ones included. Never delete one with unmerged work: list it for the owner with a recommendation.

## GitHub Actions

Private repos share 2,000 Actions minutes a month. Trigger workflows on `pull_request` and `workflow_dispatch` only, never on `push`. Agents run the lanes in their own workspace before they report; CI is a second check, not the first. Public repos run Actions free.

## Unattended work

- A scheduled task needs a prompt that stands alone and permission to commit, push, merge its pull request and republish without a person.
- Background work stops at the usage limit. Say when that can interrupt it.
