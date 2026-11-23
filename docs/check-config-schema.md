# The settings of `.check` and `.check.state.json`

This page lists every key of `.check` and every part of `.check.state.json`. It was made by reading
`scripts/check_settings.py` and the scripts that read the keys. Each reader has a `file:line` mark. The line numbers
are those of the kit at commit `fe62213`; a later split of a script can move them.

## The three files

| File | Who writes it | Who reads it |
|---|---|---|
| `.check` | A person (on the Maintainer's request) | The scripts in the tables below |
| `.check.state.json` | Tools only (sorted keys, indent 1) | `scripts/check_settings.py:359` (`load_state`) |
| `.check.lock` | `scripts/sync_baseline.py` | `scripts/check_lock.py` (not part of this page) |

A `.check` line is `key: value`. A line that starts with `#` is a comment. A line with no known key is an allowed
string for the content check. A key marked "many" can be on more than one line. A key that is not marked "many" on two
lines raises an error (`scripts/check_settings.py:159`, `collect`). A key in capital letters raises an error.

## Keys of the content check

The content check reads these lines (`scripts/check_content_scan.py:221`, `load_allow`).

| Key | Values | Default | Read by | Example |
|---|---|---|---|---|
| `<exact string>` (many) | any text | none | `scripts/check_content_scan.py:347` | `docs.example.org` |
| `skip: <glob>` (many) | a path or glob | none | `scripts/check_content_scan.py:283` (`skipped`) | `skip: ref/**` |
| `block: <glob>` (many) | a path or glob | none | `scripts/check_content_scan.py:288` (`blocked`) | `block: *.xlsx` |
| `profile: dod` | `dod` only; other forms fail the scan | minimum tier | `scripts/check_content_scan.py:190` (`profile_of`) | `profile: dod` |
| `denylist: warn` | `warn` only | a missing name denylist fails | `scripts/check_content_scan.py:204` (`warn_mode`); `scripts/first_use_check.py:95` | `denylist: warn` |
| `content-max-bytes: <n>` | a number from 2000000 to 50000000 | 2000000 | `scripts/check_content_scan.py:154` (`max_bytes_of`) | `content-max-bytes: 5000000` |

Notes:

- `denylist: warn` has no effect when `profile: dod` is on (`scripts/check_content.py:32`).
- A value of `content-max-bytes` below 2000000 or above 50000000 is ignored (`scripts/check_content_scan.py:168`).
- The old file name `.pii-guard` is still read when `.check` is absent (`scripts/check_content_scan.py:221`). If both exist, the scan fails.

## Keys of the project features

| Key | Values | Default | Read by | Example |
|---|---|---|---|---|
| `fleet: on` | `on` | off | `scripts/check.sh:369`; `scripts/fleet_harvest.py:56` | `fleet: on` |
| `dod-security: on\|off` | `on` or `off` | `off` | `scripts/build_site_html.py`, function `dod_security` (see the note below) | `dod-security: on` |

Note on `dod-security`: the key is new in the plan `docs/reviews/2026-11-23-fleet-v2-plan.md`. The file
`scripts/build_site_html.py` does not exist at commit `fe62213`. The `file:line` mark for the reader must be added
after the split of `scripts/build_site.py` lands.

## Keys of the code standard

`scripts/check_settings.py:213` (`code_settings`) reads these lines. The one reader of the settings is
`scripts/code_standard.py:465`. A `code-` change needs a row in `docs/DECISIONS.md` that names `.check`.

| Key | Values | Default | What it does | Example |
|---|---|---|---|---|
| `code-max-file-lines` | whole number, 1 or more | 600 | Longest source file (`scripts/code_standard.py:239`) | `code-max-file-lines: 450` |
| `code-max-function-lines` | whole number, 1 or more | 60 | Longest function (`scripts/code_standard.py:299`) | `code-max-function-lines: 40` |
| `code-max-line-chars` | whole number, 1 or more | off (no line) | Longest line; a project gate enforces it | `code-max-line-chars: 200` |
| `code-include` (many) | glob | `*` | Files that count (`scripts/code_standard.py:162`) | `code-include: scripts/**` |
| `code-exclude` (many) | glob | none | Files that do not count (`scripts/code_standard.py:162`) | `code-exclude: ref/**` |
| `code-generated` (many) | glob | none | Files that need a GENERATED banner (`scripts/code_standard.py:160`) | `code-generated: dist/**` |
| `code-c1-safety` | `on`, `off`, `strict` | `off` | Safety label rule (`scripts/code_standard.py:237`); `strict` needs a project gate | `code-c1-safety: on` |
| `code-c2` | `full`, `lean` | `lean` | Function docs rule (`scripts/code_standard.py:297`) | `code-c2: full` |

The defaults are in `scripts/check_settings.py:65` (`CODE_DEFAULTS`) and `scripts/check_settings.py:67` (`OPT_IN_CAPS`).
An unknown `code-` key raises an error: a typo cannot relax a limit.

## Keys of the audit

`scripts/check_settings.py:293` (`audit_settings`) reads these lines. The reader of the settings is
`scripts/bloat_check.py:104` (`audit_config`). The defaults are in `scripts/check_settings.py:69` (`AUDIT_DEFAULTS`).

| Key | Values | Default | Read by | Example |
|---|---|---|---|---|
| `audit-every-days` | whole number, 1 or more | 14 | `scripts/bloat_check.py:211` | `audit-every-days: 30` |
| `audit-every-commits` | whole number, 1 or more | 300 | `scripts/bloat_check.py:211` | `audit-every-commits: 500` |
| `audit-ignore` (many) | glob | none | `scripts/bloat_check.py:107` (`ignored`) | `audit-ignore: ref/**` |
| `audit-duplicate-ignore` (many) | glob | none | `scripts/bloat_check.py:120` | `audit-duplicate-ignore: docs/templates/**` |
| `audit-start-read` (many) | path | none | `scripts/bloat_check_rules.py:63` | `audit-start-read: docs/map.md` |
| `audit-third-party` (many) | glob of a skill folder or agent file | none | `scripts/bloat_check_rules.py:61`, `scripts/bloat_check_rules.py:382` | `audit-third-party: .claude/skills/pack` |
| `audit-instructions` (many) | glob | none | `scripts/check_instructions.py:123`; `scripts/check.sh:375` | `audit-instructions: README.md` |
| `audit-budget-<name>` | whole number, 0 or more | see the next table | `scripts/bloat_check.py:340`; `scripts/bloat_check_rules.py:372` | `audit-budget-handoff_lines: 30` |

Budget names and defaults (`scripts/check_settings.py:69`):

| Name | Default | Kit cap (a project can lower it, never raise it) |
|---|---|---|
| `session_load_tokens` | 5500 | yes |
| `session_load_warn_tokens` | 5000 | yes |
| `rules_file_lines` | 200 | yes |
| `third_party_tokens` | 1500 | yes |
| `handoff_lines` | 40 | no |
| `file_kb` | 500 | no |
| `duplicate_lines` | 20 | no |
| `rules` | 28 | no |
| `project_rules` | 15 | no |

The kit caps are in `scripts/check_settings.py:76` (`KIT_CAPS`). A value above a kit cap raises an error
(`scripts/check_settings.py:309`).

## Parts of `.check.state.json`

The parts are `code_standard`, `audit` and `timings` (`scripts/check_settings.py:87`). Each part must be a JSON
object. The file is written by `save_part` (`scripts/check_settings.py:385`).

| Part | Shape | Written by | Read by |
|---|---|---|---|
| `code_standard` | `{"debt": {<kind>: {<file>: <value>}}}` | `scripts/code_standard.py:477` (`--init`, `--update` and `--adopt`) | `scripts/code_standard.py:471` |
| `audit` | `{"last_audit": {"date": "YYYY-MM-DD", "commit": "<sha>", "report": "<path>"}}` | The full audit (`.claude/skills/audit/SKILL.md`) | `scripts/bloat_check.py:198` |
| `timings` | `{"<name>": {"cmd": "<command>", "seconds": <number>, "max_slowdown": <number>, "steps": {...}}}` | `scripts/bloat_check.py:319` (`--record`) | `scripts/bloat_check.py:237` |

Notes:

- A part that is not in the file means "not set". A repo with no `code_standard` part has not adopted the code standard.
- `max_slowdown` defaults to 0.25 (`scripts/bloat_check.py:244`).
- `scripts/check_settings.py --migrate` moves the old files `.code-standard.json`, `.bloat-audit.json` and `.pii-guard` into this layout.
