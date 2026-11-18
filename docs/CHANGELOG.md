# Kit changelog

One line for each kit version that a project must take by a sync (`scripts/sync_baseline.py`, run from the project). The version is the date of the change (`KIT_VERSION`); a project's `.check.lock` records the version it has. Why each change was made: [DECISIONS.md](DECISIONS.md).

| Version | Change | A project must |
|---|---|---|
| 2026.11.18 | One `check`: the personal-data guard is the content check of `scripts/check.sh` (`scripts/check_content*.py`, settings file `.check`, `block:` lines, the owner's terms list, the hook also on Write, Edit and outgoing Bash). Caps: AGENTS.md 200 lines and a session load of 6,000 tokens. One home per rule. Pull-request merge rule. Kit lock `.check.lock`. One config layout: `.check` (every setting a person edits, now also the `code-` and `audit-` lines), `.check.lock`, and `.check.state.json` (what tools write: the code standard debt, the last audit, the time baselines); `.code-standard.json` and `.bloat-audit.json` are replaced. | Sync; run `python3 scripts/check_settings.py --migrate` (it renames `.pii-guard` to `.check`, moves the settings of `.code-standard.json` and `.bloat-audit.json` into `.check` and their state into `.check.state.json`, and deletes the old files); delete `scripts/pii_guard*.py` and `.github/workflows/pii-guard.yml`; optional: add the `CHECK_TERMS` secret. |
