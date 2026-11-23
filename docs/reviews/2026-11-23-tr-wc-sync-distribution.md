# Tool retirement research, group W-C: sync tools vs copier/cruft, token log vs OpenTelemetry, distribution candidates

Date: 2026-11-23 (America/Chicago). Plan step R4, group W-C (docs/reviews/2026-11-23-tool-retirement-research-plan.md). Evidence only: no choice is made here.

## Setup and versions

| Item | Value |
| - | - |
| Kit | this worktree, HEAD 641023e, KIT_VERSION 11.0.1 |
| Projects (read-only; copied to a temp dir before any write) | 33-332.Z and RADE, both pinned at kit 9e3f6fa (`.check.lock`, 69 locked files). The kit changed only docs between 9e3f6fa and 641023e, so both copies already matched the baseline (drift.py: 78 of 79 items "same", only the pin differs). |
| Python / git | 3.13 / 2.43.0 |
| Installed in a temp venv (this container only) | copier 9.19.1, cruft 2.16.0 (with cookiecutter 2.7.1), pre-commit 4.7.0, build 1.6.1, pipx 1.19.0. Also pulled in by the same venv: setuptools (isolated build), actionlint-py 1.7.12.25 (syntax check of the workflow prototype). The system-wide `pip install` failed on a Debian package (argcomplete) and was redone in a venv. |
| Published | nothing (no PyPI, GitHub or registry write). All repos below are temp dirs. |
| Simulated kit changes | S1: one locked script changed (`scripts/log_check.py`, one appended line). S2: one AGENTS.md "Defaults" line plus one skill file (`.claude/skills/deliver/SKILL.md`). |

Locked files by kind (69): 47 scripts, 1 git hook, 1 workflow, 2 brand files, 1 docs/code-standard.md, 16 Claude instruction files (skills, agents, rule-tests), 1 AGENTS.md kit part. Only the first five kinds (52 files) can run from outside the project. The 17 instruction files and the AGENTS.md text must stay in the project repo, because Claude Code reads them from there. This bounds what candidates (a) to (c) below can distribute.

## Trial 1: sync_baseline / sync_merge / drift / check_lock vs copier and cruft

### How the trial was built

- Copier template: the kit's 72 distributed files copied as they are (73 with the template AGENTS.md); AGENTS.md became `AGENTS.md.jinja` (7 header placeholders to variables, the `<!-- full -->` and `<!-- starter -->` blocks to `{% if tier %}`); a `copier.yml` (13 lines) and the answers-file template. Built by a 43-line script. Tags v1 (kit 641023e), v2 (S1), v3 (S2), v4 (a file removed and one added), v5 (a deny rule added to settings.json), v6 (kit edits the last Defaults bullet), v7 (kit edits the placeholder comment inside "## Commands").
- Cruft: the same content as a cookiecutter template (29-line build script). Every file but AGENTS.md has to be listed in `_copy_without_render` (73 entries in cookiecutter.json), else jinja would render the 12 files that contain `{{`.
- Adoption of an existing project: Copier with a hand-written `.copier-answers.yml` (`_commit: v1`) committed in the project; cruft with `cruft link --checkout v1`. Both then update from the old tag.
- Quote of the key Copier settings: `_subdirectory: template`, `_templates_suffix: .jinja`, `_envops: {trim_blocks: true, lstrip_blocks: true}` (without trim/lstrip the tier markers left blank lines and AGENTS.md did not render byte for byte like the kit's).
- Check that the template reproduces the kit: render of v1 differs from the kit AGENTS.md only in the 7 header lines (22 diff lines).

### Files changed and conflicts per kit change (clean project, project-owned edits present)

Project-owned parts present in both temp projects: AGENTS.md "Commands" and "Project rules" (project text), `.claude/skills/verify/PROJECT.md` (added by me), and in 33-332.Z its own settings.json (sandbox block, no kit allow list) and extra `.gitignore` line.

| Kit change | sync_baseline.py --apply | copier update | cruft update |
| - | - | - | - |
| S0: docs-only kit change (no kit file) | drift.py shows 1 differing item (the pin); apply not run for S0 | not run | not run |
| S1: 1 locked script | 2 files (script + `.check.lock`), 0 conflicts | 2 (script + answers file), 0 conflicts | 2 (script + `.cruft.json`), 0 conflicts |
| S2: 1 AGENTS.md Defaults line + 1 skill | 3 (AGENTS.md, skill, lock), 0 conflicts | 3 (AGENTS.md, skill, answers), 0 conflicts | 3 (AGENTS.md, skill, `.cruft.json`), 0 conflicts |
| S3: 1 file removed, 1 added in the kit | not run (sync handles removal only for its MOVED_FILES list) | 3 (removed file deleted, new file created, answers) | 3 (same) |
| S4: a deny rule added at the end of settings.json "deny" (project has own settings) | not run (sync merges deny rules as JSON by design) | 2 (settings.json + answers); merged cleanly, JSON still valid | not run |
| S5: kit edits the last bullet of "Defaults" (directly above "## Commands") | not run | 2, 0 conflicts | 2, 0 conflicts |
| S6: kit edits the placeholder comment inside "## Commands" | not run (sync never writes "Commands" or "Project rules") | 2 files, **1 conflict** (inline markers in AGENTS.md "Commands") | 2 files plus an extra `AGENTS.md.rej`, **1 conflict** |

Timing (this machine, wall): sync dry run 0.08 s, sync apply about 0.1 s, drift.py 0.07 s, check_lock --verify 0.05 s; copier update 2.6 s; copier check-update 1.5 s; cruft check 1.1 s.

### A project that edited two kit files itself (RADE copy: one appended line each in log_check.py and deliver/SKILL.md), then S2

| | sync_baseline.py | copier update (v1 to v3) | cruft update (v1 to v3) |
| - | - | - | - |
| Before the update | `check_lock --verify` already FAILs (2 "kit file changed in this project") | no check; the update starts | no check; the update starts |
| Files changed | 4 (AGENTS.md, script, skill, lock) | 4 | 4 |
| Conflicts | 0: the project's edits to kit files were replaced by the baseline copies (shown by `git diff`; no warning that text was lost) | 2 (inline markers in both files, status "UU"); project text kept | 2 (inline markers "U"); the tool still prints "Good work! ... as clean as possible!" |
| Project-owned sections (AGENTS.md "Commands" and "Project rules", 82 lines) | kept; 0 diff lines inside them | kept in S1, S2, S5; changed only when the kit edited text inside them (S6) | same as Copier |
| `PROJECT.md` | kept (not a kit file) | kept (not in the template) | kept |

### Drift and lock: how the checks map

| Kit tool | What it does (measured) | Copier equivalent | Cruft equivalent |
| - | - | - | - |
| `check_lock.py --verify` (hash of each of 69 kit files; gate in check.sh) | Fails at once when a project edits a kit file; names the file | None. A silent merge hides the edit until an update conflicts (see table above) | None as a gate. `cruft diff --exit-code` exits 1 on any difference, but a project with its own settings.json, .gitignore and AGENTS.md sections always differs (3 files for 33-332.Z), so it cannot gate |
| `check_lock.py --status` (version and commit) | one line | `.copier-answers.yml` `_commit` | `.cruft.json` `commit` |
| `drift.py` (per AGENTS.md section: same, changed with %, missing; per file; settings deny rules and hooks) | 79 items in 0.07 s; knows which sections are project-owned | `copier recopy --pretend --overwrite` lists files that differ from the pinned render ("conflict"/"overwrite" lines): 4 files for 33-332.Z (AGENTS.md, answers file, .gitignore, settings.json); no per-section or percent view; project-owned AGENTS.md sections show as a difference | `cruft diff` prints the unified diff against the pinned render: 3 files for 33-332.Z; no section view |
| "Is a newer kit version out?" (check-update) | drift.py shows "pinned vs baseline"; sync dry run | `copier check-update -q`: exit 2 when behind, 0 when current (exit is 0 without `-q`) | `cruft check --checkout TAG`: exit 1 when behind. Without `--checkout` it compared against the template's default branch head and reported "out of date" for a project pinned to a tag |
| `sync_baseline.py` (dry run: diff, no write) | prints the diff; `--apply` writes | `copier update --pretend` printed only "Updating to template version N" (no file list) | `cruft update` has no dry run; `cruft diff` shows the pinned-vs-project diff, not the update |

### What the kit's sync code does that Copier and cruft do not (measured or counted)

| Kit feature | Copier / cruft |
| - | - |
| Owner name replaced in baseline text of all copied files (`the Maintainer` to the owner) | 48 of the 73 template files contain the phrase; each would need a `.jinja` suffix and, in 12 files that contain `{{`, a raw escape. Not built in the trial (both test projects use the default owner). |
| settings.json merged by meaning (kit deny rules and hook entries first, project's own kept, sandbox block added only when missing) | Text 3-way merge. Worked in S4 on a project with its own settings; no test of two edits on the same lines. The kit's `allow` list is not synced by sync_merge; in a template it would be synced and conflict with a project that deleted it (33-332.Z has no `allow` block, and the first `copier recopy --pretend` listed settings.json as different) |
| `.gitignore` line merge, docs/LOG.md Arcs table migration, DoD files only when `dod-security: on`, `docs/FIRST_USE.md` "tuned vs older kit copy", tier starter file deletion (ADVANCED_FILES) | Not covered. Copier's 3-way merge keeps a tuned FIRST_USE.md when unconflicted; the others need jinja conditions or tasks. Not built. |
| The kit lock as a gate | Not covered (see above) |

### Lines of custom code

| Group | Lines | Remains if Copier or cruft is used |
| - | - | - |
| sync_baseline.py, _repo, _run, sync_merge.py | 445 + 150 + 74 + 260 = 929 | Replaced for the file copy; the rows "not covered" above would stay as hooks or tasks (not sized) |
| their tests (sync_baseline_cli_test, sync_merge_cli_test) | 148 + 110 = 258 | follow the code |
| drift.py + drift_test.py + drift_cli_test.py | 317 + 319 + 92 = 728 | No equivalent with section view; only the file-level listing above |
| check_lock.py + check_lock_cli_test.py | 237 + 108 = 345 | Stays (shipped to projects, run by check.sh); no equivalent |
| check_settings.py, check_settings_read.py, check_settings_test.py | 343 + 328 + 416 = 1,087 | Stays. It is the reader of `.check` and `.check.state.json`, not a sync tool; no counterpart in either tool |
| kit_config.py, bootstrap.sh | 109 + 138 | bootstrap.sh is the first-copy path; `copier copy` replaces its file copy only |
| New glue the template needs | 43 (copier build script) + 13 (copier.yml) or 29 (cookiecutter build script) + a 73-entry `_copy_without_render` list | New code that must follow every kit file add or move |

### Verdict options for Trial 1 (no choice made)

| Option | What the numbers support | What it costs |
| - | - | - |
| Keep | Files per change equal Copier and cruft (2 for S1, 3 for S2); the lock gates edits of kit files, which neither tool does; drift has a section view; project-owned sections never conflict because sync never writes them | 1,915 lines kit-side sync plus drift code (929 + 258 + 728) stays maintained |
| Shrink | Copier could take the file copy and the 3-way update (S1 to S5 identical in file count, project edits conflict instead of being replaced). Keep check_lock, drift (reduced), settings merge and the rest | A template build step to keep in step with the kit (43 lines) and a conflict-handling step for projects; 48 files to template for owner names if that feature stays |
| Retire | Not supported by these numbers alone: lock gate, per-section drift, owner rename, settings merge and the other rows above have no equivalent in either tool; a kit edit inside a project-owned section (S6) conflicts in both tools | Would need replacements for each "not covered" row |

Cruft against Copier: cruft needed the 73-entry no-render list, printed "as clean as possible" with conflicts, left a `.rej` file, had no dry run and no tag-aware `check` by default. Copier gave a file-level `--pretend` listing only through `recopy`.

## Trial 2: token_log.py vs Claude Code OpenTelemetry (OTel) metrics

Source: https://code.claude.com/docs/en/monitoring-usage (read as Markdown, 2026-11-23, 1,888 lines). No account change was made. What the docs say; nothing was exported or collected here.

Facts from the page that frame the comparison:
- Telemetry is off until `CLAUDE_CODE_ENABLE_TELEMETRY=1` and exporters (`OTEL_METRICS_EXPORTER`, `OTEL_LOGS_EXPORTER`: console, otlp, prometheus) are set; it needs a collector or a console reader.
- A repository's `.claude/settings.json` and `.claude/settings.local.json` cannot set the exporter variables (the page says Claude Code ignores them there). They come from managed settings, a user shell, or, for cloud sessions, server-managed settings or the cloud environment's variables (any user of that environment can read the variables, so no credential in them).
- The page documents export going forward only; it names no way to read back sessions that ran before telemetry was on. token_log rebuilds every row from the session logs on the next push.
- Metrics: `claude_code.token.usage` (attribute `type`: input, output, cacheRead, cacheCreation), `claude_code.cost.usage` (USD), session, commit, pull request, lines-of-code, active-time counters. Events (logs): `claude_code.api_request` (one per API request) with `cost_usd`, the four token counts, `cache_creation_5m_tokens` and `cache_creation_1h_tokens` (v2.1.300 or later), `request_id`, `speed`, `query_source`, `model`.

| token_log output | Where OTel covers it | Gap |
| - | - | - |
| Row per API call (`message_id`) | `api_request` event, one per request, keyed by `request_id` | `message_id` in token_log is the message id; the page documents `request_id` and `message.uuid` (a transcript id), not that message id. Joining the two is not documented. |
| `timestamp` | `event.timestamp` | none |
| `turn` (prompt counter) | `prompt.id` (UUID per prompt) groups events of one prompt | a UUID, not a running number; order needs `event.sequence` or the timestamp; metrics (not events) do not carry `prompt.id` |
| `session_id` | `session.id`; `ccr.session.id` on cloud sessions | none |
| `repo` | `vcs.repository.url.full` and related, only with `OTEL_METRICS_INCLUDE_REPOSITORY=true`, Claude Code v2.1.269 or later | default is off |
| `model` | `model` attribute | none |
| `source` main / subagent | `query_source` (main, subagent, auxiliary, plugin values) on metrics; on events values like `repl_main_thread`, `compact` or a subagent name | value names differ |
| `agent` (subagent type) | `agent.name` | user-defined agent names (the kit's worker, scout, reviewer are project agent files) are replaced by `custom` unless `OTEL_LOG_TOOL_DETAILS=1` |
| `agent_id` (groups one subagent task) | `agent_id` and `parent_agent_id` on events only (never on metrics) | no per-task view from metrics |
| `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` | `claude_code.token.usage` by `type`; same four as event fields | none documented |
| `cache_write_1h_tokens` | `cache_creation_1h_tokens` on `api_request` (v2.1.300 or later) | not on the token metric (it sums both lifetimes) |
| `speed` | `speed` attribute | none |
| `web_search_requests`, `inference_geo` | not found on the page (searched) | not covered |
| Cost estimate | `claude_code.cost.usage` and `cost_usd` / `cost_usd_micros` computed by Claude Code | token_log prices from its own table (PRICES, dated 2026-11-23, with a 1-hour cache write and a US 1.1 factor assumption); the two numbers were not compared here (no export) |
| `--report`: cost by week (America/Chicago, Monday), by source, agent and model, per subagent task | Not an OTel output; a backend (Prometheus, Grafana and similar) would compute it from the metrics; the per-task part needs events | the report is its own code (token_log_report.py 153 lines) |
| Storage and transport | OTLP to a collector the owner runs or pays for | token_log needs only the repo's own git remote (branch `claude/token-usage`), no collector, installed by the cloud environment's setup script, self-updating (token_log.py 394 + rows 162 + report 153 lines, tests 717) |
| Works for a session with no repo | yes (no repo needed) | token_log does nothing outside a git repo |

Verdict options (no choice): Keep (no collector or account change; row-level history with every price field); Shrink (drop PRICES and the cost report, use `cost_usd`/`claude_code.cost.usage`, keep the CSV rows for rebuild and per-task grouping); Retire (needs a collector, setting the variables in each cloud environment or in managed settings, and accepting the gaps above: the `web_search_requests` and `inference_geo` fields, a message id that does not match, no back-fill). Retire or Shrink also changes the account or environment settings, which this trial did not touch.

## Trial 3: distribution candidates for the shared checks

Common fact (measured): `scripts/check.sh` run from a folder other than the project's (cwd = project) works, because it finds its sibling scripts by its own location: `bash KIT/scripts/check.sh --fast` in a RADE copy gave "CHECK PASS: 10 passed, 3 skipped, of 13". But it first needs `scripts/check.sh` in the project to exist ("is not the top folder of a repo with scripts/check.sh"), and with the project's kit scripts removed (48 locked scripts deleted, stub check.sh kept) the run failed 3 checks: the project's own `scripts/check_content_local.py` imports `check_content_scan` from its own folder, `scripts/check.local.sh` calls `scripts/code_standard.py`, and the content step calls `scripts/check_content.py` there. So none of the three candidates is a drop-in: the kit scripts would need a path variable (for example a `KIT_DIR`), which they do not read today, and a project's own extension files would need it too. I changed no kit file; the prototypes below ran with the project keeping its scripts.

Full lane time on a RADE copy: 227.5 s wall (baseline in `.check.state.json` 51.1 s; the machine was running other jobs; check.local.sh took 226.6 s of it). Fast lane: 15.0 s, 25.3 s and 29.8 s in three runs (also under load).

### Prototype (a): pre-commit hook repo at a tag

Temp repo with `scripts/`, `docs/code-standard.md` (68 files) and `.pre-commit-hooks.yaml`, tags v11.0.1 and v11.0.2. Project file:

```yaml
repos:
  - repo: /tmp/.../hooks      # in real use: the kit's URL
    rev: v11.0.1
    hooks:
      - id: kit-check         # entry: scripts/check.sh --fast, language: script, always_run, stages: [pre-push]
```

Measured: `pre-commit run --hook-stage pre-push --all-files` passed, 15 s (first run 17.6 s with the clone). `pre-commit install --hook-type pre-push` plus a real `git push` to a local bare repo ran the hook and the push went through (hook output "Passed"; git printed a harmless "push negotiation failed" line). Changing `rev` to v11.0.2 re-cloned and ran; `pre-commit autoupdate` moved `rev` itself; moving it back is the rollback.

### Prototype (b): reusable workflow at a tag

Kit side `.github/workflows/kit-check.yml` with `on: workflow_call` (inputs `lane`, `kit-ref`; optional secrets); it checks out the project, then the kit repo at `kit-ref` into `.kit`, then runs `.kit/scripts/check.sh`. Project side:

```yaml
jobs:
  kit:
    if: github.event_name != 'pull_request' || github.event.repository.private == false
    uses: rhope-ops/archimedes_lever/.github/workflows/kit-check.yml@v11.0.1
    with: { kit-ref: v11.0.1 }
    secrets: inherit
```

Measured: both files parse and `actionlint` 1.7.12 reports no finding. It was not run on GitHub (no push), so the GitHub-side behavior below comes from the documentation and my knowledge, not from this trial: a reusable workflow cannot read its own tag, so the tag appears twice (the `uses:` line and `kit-ref`, one file); a private kit repo must allow other private repos to call its workflows (a repository Actions access setting); the called job counts in the caller's minutes.

### Prototype (c): pip or pipx package

`archimedes-kit` 11.0.1: `pyproject.toml` (setuptools), `src/archimedes_kit/scripts/` (the kit's scripts and docs/code-standard.md as package data), and a 20-line `cli.py` that runs the bundled `scripts/check.sh` with the current repo as cwd. Wheel built with `python -m build --wheel`: 328,576 bytes, 74 entries.

Measured: `pipx run --spec dist/archimedes_kit-11.0.1-py3-none-any.whl archimedes-kit check --fast` gave "CHECK PASS: 8 passed, 3 skipped, of 11" (31 s wall under load). With a dead proxy and `PIP_NO_INDEX=1` it still started (0.8 s) because the spec is a local file; after `pipx install` the command ran in 0.08 s. `pipx run --spec git+file:///...@v11.0.1 archimedes-kit` worked from a tagged git repo (3.3 s), which is the route for a private kit with no index. The example in the brief (`pipx run archimedes-kit==11.0.1 check`) needs an index and was not run (nothing published).

### Comparison per candidate

| Question | (a) pre-commit hook repo at a tag | (b) reusable workflow at a tag | (c) pip/pipx package |
| - | - | - | - |
| Files a project keeps | `.pre-commit-config.yaml` (4 lines), the project's own check.local.sh and extension files; a stub or the real scripts/check.sh until check.sh can run without it | one caller workflow (about 10 lines); local run still needs the scripts, so (b) is the CI part only | a version pin (in the hook or a requirements file), the project's own extension files; same check.sh stub need |
| Files changed per kit change (distributed scripts only) | 1 per project (the `rev` line; `pre-commit autoupdate` writes it) | 1 per project (two lines, same file) | 1 per project with a pin; 0 with an unpinned `pipx run` (no pin means no rollback) |
| Files changed per kit change that touches AGENTS.md, skills, agents (17 instruction files) | not distributable: still synced (S2: 3 files per project by the kit's sync, copier or cruft) | same | same |
| Offline / local run | After the first clone into `~/.cache/pre-commit` (tested with a local path only): runs with no network; a first run or a new `rev` needs the clone | None: it runs on GitHub only. Local runs still use the project copy of the scripts | `pipx install` of a version: runs offline; `pipx run` needs the index or git URL on a cold cache; needs Python on the machine (the kit scripts already need python3) |
| How the pre-push hook calls it | `pre-commit install --hook-type pre-push` writes `.git/hooks/pre-push`, but pre-commit refuses to install when `core.hooksPath` is set (message "Cowardly refusing to install hooks with `core.hooksPath` set" in its source), and the kit's hook is installed that way. It also would not do the hook's other checks (fast-forward, identity, own work tree). The kit's hook would have to call `pre-commit run --hook-stage pre-push` itself (not tested) | not a hook; the hook keeps calling the local check.sh | the kit's hook calls `archimedes-kit check --fast` (or `pipx run --spec ... check --fast`) where it calls scripts/check.sh today (not edited here) |
| Actions-minute cost | None by itself (local) | Same as today's check.yml: one job per run, Linux, rounded up to a minute per job as GitHub documents. The measured lane here: 15 to 30 s fast, 227 s full under load (51 s baseline), so about 1 to 4 min per run; at 2,000 min a month that is about 500 to 2,000 runs. A private repo skips the pull-request run today (the "if" line) to save minutes, so (b) changes nothing unless that rule changes | None by itself; if a CI job installs it, it adds the install time (3 s from git, measured) |
| Rollback | Set `rev` to the old tag (1 file) | Set the tag in both places (1 file) | Pin the old version, or `pipx install --force` the old one |
| Other measured or documented points | The hook repo is cloned from the kit URL, so a private kit needs credentials on every machine; Dependabot support for pre-commit `rev` bumps was not checked | The caller cannot read its own tag; a private kit repo needs the Actions access setting | A real index is not available for a private kit (nothing may be published here); the git URL route works with git credentials. Wheel size 0.3 MB |

### Verdict options for distribution (pros and cons, no choice)

| Candidate | Pros | Cons |
| - | - | - |
| (a) pre-commit | Pin and rollback are one line; works locally and offline after the clone; common tool | Conflicts with `core.hooksPath` hook install; the kit's pre-push safety checks are separate; a new tool to install |
| (b) reusable workflow | One file for CI; central change per tag | CI only; no local or offline run; tag in two places; minutes per run; private-repo access setting not tested |
| (c) pip/pipx | Local, offline after install, CLI the hook can call; pin and rollback by version | Python packaging and a git-URL or index path for a private kit; needs a version bump per kit release; extra install step |
| All three | Distribute only the 52 script and doc files; the 17 instruction files and AGENTS.md text still need a sync tool | None is a drop-in until check.sh and the project's extension files can find the kit scripts outside the project |

## Done criteria

- Trial 1: measured (tables above). Cells marked "not run" were not run for time; the reason is in the cell.
- Trial 2: from the official page only; no collector, no export, no account change. The cost comparison of PRICES against `cost_usd` was not measured.
- Trial 3: three prototypes ran locally in temp dirs (workflow: syntax check only); nothing was pushed anywhere except this branch.
- Open: the `git push` hook behavior with a remote kit URL, Dependabot for pre-commit, and GitHub-side reusable-workflow behavior are not verified.
