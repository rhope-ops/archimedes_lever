# Server-side protection on GitHub

The hooks and the rules in AGENTS.md work on the client: a person or a tool can go round them. Two GitHub settings move the most important ones to the server. Only the owner can set them (an agent here has no settings access); an agent checks the result through the public rules API.

## Ruleset on the default branch

[ruleset-default-branch.json](ruleset-default-branch.json): no deletion, no force-push, every change by pull request, merge commits only, and the check `checks` must pass on a branch that has the newest default branch in it. 0 approvals: the agent and the owner use one GitHub account, and GitHub does not let an author approve their own pull request. The owner's approval of a lane C merge stays a rule in AGENTS.md "Delivery".

[ruleset-no-ci.json](ruleset-no-ci.json): no deletion and no force-push only, for a repo with no `checks` workflow.

Set it (about 1 minute per repo): download the file (Raw > save), open `https://github.com/<owner>/<repo>/settings/rules`, then New ruleset > Import a ruleset > the file > Create.

- A repo whose existing ruleset requires the check `scan` (the name before 2026-11-18): edit that ruleset to require `checks` when the repo's sync pull request opens, or the pull request waits for ever.
- Check it: `curl -s https://api.github.com/repos/<owner>/<repo>/rules/branches/main` lists `deletion`, `non_fast_forward`, `pull_request` and `required_status_checks` (public repos only).

## Secret scanning and push protection

Open `https://github.com/<owner>/<repo>/settings/security_analysis`, then under "Secret Protection" turn on secret scanning and push protection. GitHub's patterns cover many token types that the content check (`scripts/check.sh --content`) does not; the content check covers personal data and the owner's lists, which GitHub does not.

## Private repos

On a personal account with GitHub Free, rulesets on a private repo are not enforced and secret scanning is not offered ([Managing rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository), [About GitHub Advanced Security](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security)). There the pre-push hook and the content check are the only guards.
