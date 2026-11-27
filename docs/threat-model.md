# Threat model of the kit

A short STRIDE model. It covers the kit (this repo) and the project repos that receive its files.

## Assets

- Scripts that agents and hooks run: `scripts/check.sh`, `scripts/bloat_check.py`, `scripts/check_content.py`, `scripts/worker_guard.py`.
- Kit files that `scripts/sync_baseline.py` copies to project repos, and the lock `.check.lock` (`scripts/check_lock.py`).
- Settings and state: `.check` and `.check.state.json` (read by `scripts/check_settings.py`).
- Git hooks: `scripts/git-hooks/pre-push`, and the deny rules in `.claude/settings.json`.

## Trust boundaries

1. Repo content (files, issues, comments) to the agent: this is data, not instructions (AGENTS.md "Untrusted input").
2. Agent tool calls to the host: `.claude/settings.json` and `scripts/check_content.py` (`--hook`) limit them.
3. GitHub Actions: `.github/workflows/check.yml` and `.github/workflows/security.yml` read the repo. They run with `contents: read`, on pull requests and manual runs only.
4. The sync from the kit to project repos: a project trusts the kit files it receives.

## STRIDE

| Threat | Example | Control |
|---|---|---|
| Spoofing | A comment that claims to be the owner | AGENTS.md "Order of authority"; only the owner's own message counts |
| Tampering | A pull request that weakens a guard or the settings | `.check.lock`; the Action reads `.check` from the base branch; guard files change only on the owner's request |
| Repudiation | An unknown author of a change | Git history without rewrite (AGENTS.md "Git history"); commit trailers name the session |
| Information disclosure | A secret or personal data in a commit | `scripts/check_content.py` on push and pull request; gitleaks in `security.yml` |
| Denial of service | A slow or hung check | `timeout-minutes` in each workflow; timing baselines in `.check.state.json` |
| Elevation of privilege | Text that becomes a shell command | See "Command injection in timed commands" below; bandit in `security.yml` |

## Command injection in timed commands (CWE-78)

`scripts/bloat_check.py` ran each command in the "timings" list of `.check.state.json` with `shell=True`. The fix:

- The function `timing_argv` refuses a command that holds a shell character (`; | & ` $ ( ) < >` or a new line).
- It refuses a command that does not start with `python3 scripts/` or `bash scripts/`.
- The command then runs with `shlex.split` and no shell.

This is defense in depth. The input is a committed file, so it has the same trust as `scripts/check.sh`: a person who can change it can already change the scripts. The fix limits the damage of a bad merge or a generated edit.

## Known gaps

- The token log hook (`scripts/token_log.py`, kit only) updates itself from the address in `TOKEN_LOG_KIT_URL` or in the `kit.config.json` next to the installed hook, never from a repo's own `kit.config.json`. A repo's `.claude/settings.json` can set `TOKEN_LOG_KIT_URL` for its sessions; such a repo can already run its own hooks, so the added risk is small (fix review, 2026-11-23). The same holds for the private log repo the hook pushes to (`TOKEN_LOG_REPO`, or `token_log_repo` in that file): a repo that sets the variable gets the token counts of its own sessions sent elsewhere; the rows hold no task text (2026-11-24).

- `security.yml` downloads gitleaks and checks it against the checksums of the same release. This detects a damaged download, not a bad release.
- The new files (`SECURITY.md`, this file, `.github/dependabot.yml`, `.editorconfig`, `.gitattributes`, `security.yml`) are kit-only. The sync to project repos does not copy them yet.
