# Tool retirement, step R4, group W-A: custom kit checkers vs standard linters

Date: 2026-11-23. Branch `claude/tr-wa-linters`, from kit commit `641023e`. Evidence only: this file decides nothing (retire, shrink or keep is the Maintainer's call). The plan (`docs/reviews/2026-11-23-tool-retirement-research-plan.md`, row R4, group W-A) and the prompt (`...-tool-retirement-prompt.md`, step 2 and its proof line: the standard tool finds at least the same defects on the same commits, mutant kills equal or higher) are on origin/main, not in the commit this branch starts from; they were read there for those items only. The kit has no mutant counter, so seeded defects stand in for kills (section 4).

## 1. What was measured

| Pair | Custom side | Standard side |
|---|---|---|
| 1 | `scripts/code_standard.py` (+ parts, + the kit's strict gate `code_standard_strict.py` where a repo turns it on), Python files | ruff, pylint (incl. too-many-lines), radon (cc, mi, raw) |
| 2 | Shell files: the same `code_standard.py` shell rules (C1, C2, C3, C4, C5, C6, line). No other bash check exists: no `bash -n` or shellcheck call in any `scripts/*.sh`, `check.sh`, `check.local.sh` or hook of the 5 repos (the two `# shellcheck disable=` comments in `pre-push` and `tests/net_rules_test.sh` are the only mentions) | shellcheck on all shell files |
| 3 | PowerShell files: the same `code_standard.py` PowerShell rules (C1..C6, C10 via pwsh `Parser`, C2 full, line). Also found: RADE `scripts/lint.sh`, 90-161.Z `scripts/lint.sh` and 33-332.Z `tests/Lint.ps1` already run PSScriptAnalyzer (with a `ParseFile` pass in 90-161.Z and 33-332.Z) with a repo `PSScriptAnalyzerSettings.psd1`; so in those repos the standard tool is already a check, next to the custom one. The three settings files differ: RADE's `Severity` includes `ParseError`, the other two list only Error and Warning, and 33-332.Z excludes three more rules (singular nouns, ShouldProcess, unused parameter). The other home-made checks that touch `.sh` or `.ps1` are tests, not linters (RADE `tests/*.sh`, `tests/*.ps1`; 90-161.Z `tests/run.sh`, `tests/ps/`; 33-332.Z `tests/Run-Tests.ps1`); 90-161.Z `tests/check_names.py` checks SharePoint names, not code; icf `scripts/check_project.sh` lints question content, not code. `check.local.sh` of RADE, 90-161.Z, 33-332.Z, icf was read for this; the kit has none | PSScriptAnalyzer (PSSA) |

Repos and commits (same commit for both tools; read-only clones, nothing written in them):

| Repo | HEAD | tracked files in custom scope (py / sh / ps1+psm1) |
|---|---|---|
| kit (this worktree, `archimedes_lever`) | `641023e` | 62 / 4 / 0 |
| RADE | `a99ba73` | 68 / 10 / 39 |
| 90-161.Z | `91ccb0c` | 84 / 8 / 66 |
| 33-332.Z | `6cbc517` | 49 / 4 / 38 |
| icf-source | `02a7ed2d` | 261 / 12 / 0 |

(All five repos carry byte-identical `scripts/code_standard.py`, md5 `19df3bfa...`. Each tool got the same file list: what `code_standard.py` measures, from `git ls-files`, with shebang files without extension, minus its generated files. Also in scope for the custom tool but outside these pairs: JS/MJS files, 1 / 2 / 5 / 1 / 126 in kit / RADE / 90-161.Z / 33-332.Z / icf; no standard tool was run on them.)

Settings in effect for the custom tool: kit `code-c2: full`; RADE, 90-161.Z, 33-332.Z `code-c2: full`, `code-c1-safety: on`, `code-strict-gate: on`, `code-max-line-chars: 200` (plus paste/generated lists in two); icf `code-c2: full`, `code-c1-safety: on`, no strict gate (so no line check there). Caps in all: function 60, file 450, paste file 600.

"Custom counts" below are the raw measurement of `measure()` (all violations that exist now, the ratcheted debt included), taken with a driver that imports each repo's own `code_standard` and prints `measure()`. They are not the pass/fail output of the check, which passes in all 5 repos (`CODE-STANDARD pass`, run once per repo, 0.6 s kit, 3.4 s RADE, 5.4 s 90-161.Z, 2.9 s 33-332.Z, 2.1 s icf).

## 2. Versions and installs

| Package | Version | Source | Note |
|---|---|---|---|
| Python | 3.13.18 | container | |
| ruff | 0.17.6 | `pip install ruff` | used through `python3 -m ruff`; the `ruff` on PATH is 0.16.9 (pre-installed), not used. In 0.17.6 the no-config default rule set is wider than E/F: it reported I, UP, SIM, PLW, RUF, FURB, ISC, B, BLE, TRY, EXE and more |
| pylint | 4.1.4 (astroid 4.3.4) | `pip install pylint` | |
| radon | 6.0.1 | `pip install radon` | pulled mando 0.7.1, mccabe 0.7.0; the same pip run also installed isort 9.0.2, dill 0.4.1, platformdirs 4.14.8, tomlkit 0.15.2 (pylint/ruff dependencies) |
| shellcheck | 0.9.0-1 | `apt-get update`, `apt-get install shellcheck` | |
| PowerShell | 7.4.6 | container (pre-installed) | |
| PSScriptAnalyzer | 1.23.0 | pre-provisioned at `/opt/psmods/PSScriptAnalyzer` (the path both RADE and 90-161.Z `lint.sh` use); not installed by this run | `Install-Module` from the PowerShell Gallery failed: `www.powershellgallery.com` answers 403 through the agent proxy (`github.com` also answers 403, so no release download). The module on disk made the install unnecessary; the version is the one 33-332.Z `tests/Lint.ps1` pins |

Tool settings used (everything here is a trial config, not a repo file; nothing was added to any repo):

```toml
# ruff_mapped.toml  (ruff --no-cache --config ruff_mapped.toml; "default" runs used --isolated, no config)
line-length = 200
[lint]
select = ["E9", "F", "E501", "D100", "D101", "D102", "D103", "D105", "D107", "D417", "PLR0915", "C901"]
[lint.pydocstyle]
convention = "google"
```

```ini
# pylint_mapped.rc  (pylint --rcfile ... --output-format json; "default" runs used an rc with only persistent=no)
[MESSAGES CONTROL]
disable=all
enable=missing-module-docstring,missing-class-docstring,missing-function-docstring,too-many-lines,duplicate-code,too-many-statements,syntax-error,line-too-long
[FORMAT]
max-module-lines=450
max-line-length=200
[BASIC]
no-docstring-rgx=^$
docstring-min-length=-1
```

Extra runs for C2 full:

```toml
# ruff_doc.toml  (ruff --preview --no-cache --config ruff_doc.toml)
line-length = 200
[lint]
select = ["DOC"]
[lint.pydocstyle]
convention = "google"
```

```ini
# pylint_docparams.rc
[MAIN]
persistent=no
load-plugins=pylint.extensions.docparams
[MESSAGES CONTROL]
disable=all
enable=missing-param-doc,missing-return-doc,missing-yield-doc
[DOCPARAMS]
accept-no-param-doc=no
accept-no-return-doc=no
accept-no-yields-doc=no
default-docstring-type=google
```

(The seed run repeated the docparams run with `--accept-no-param-doc=n --accept-no-return-doc=n` on the command line; same result, so the `[DOCPARAMS]` section name was not the cause of what is described under row 7a.) Pylint's `W9013` is `missing-yield-doc`; it is not counted as a parameter message anywhere in this file.

PSSA trial settings (each passed with `Invoke-ScriptAnalyzer -Settings`):

```powershell
# pssa_mapped.psd1
@{ IncludeRules = @('PSProvideCommentHelp')
   Rules = @{ PSProvideCommentHelp = @{ Enable = $true; ExportedOnly = $false; BlockComment = $true; VSCodeSnippetCorrection = $false; Placement = 'before' } } }
# pssa_long.psd1
@{ IncludeRules = @('PSAvoidLongLines')
   Rules = @{ PSAvoidLongLines = @{ Enable = $true; MaximumLineLength = 200 } } }
```

Shellcheck: `-f json1`, no `-s` (the shebang decides), default severity. PSSA: `Invoke-ScriptAnalyzer -Path` per file: (a) default rules, no settings; (b) each repo's own `PSScriptAnalyzerSettings.psd1` (`PSUseCompatibleSyntax` 5.1, Write-Host allowed; Severity as above; the seed run used the 90-161.Z file, and was repeated with the RADE and 33-332.Z files); (c) `IncludeRules PSProvideCommentHelp` with `ExportedOnly = $false`; (d) `IncludeRules PSAvoidLongLines` with `MaximumLineLength = 200`.

How overlap was decided: a custom finding is "also found" when the standard tool reports at the same file and the same function line (up to 3 lines later, for decorators), or, for file-level checks, the same file. Counts of rules are counts of findings (not files), message text is left out. Python overlap uses `path::function` keys from the custom tool mapped to function start lines from its `--report` data.

## 3. Counts per pair and repo

All counts are one run in this container, same commit for both tools. "Custom" counts are per language, from the same measurement. The ruff/pylint "default" columns show how noisy a zero-config run is; the "mapped" columns are the rule sets chosen to match the C-checks (above).

### Pair 1 counts (Python files only; same file list for every tool)

| Repo | py files | custom code_standard (raw debt, by check) | ruff default | ruff mapped | pylint default | pylint mapped |
| --- | --- | --- | --- | --- | --- | --- |
| kit | 62 | 0 | **389** (UP031 115, PLW1510 54, EXE001 36, RUF100 35, I001 34, ISC004 31, +19 more rules) | **28** (C901 14, D101 5, F401 4, PLR0915 1, F402 1, D107 1, E501 1, F841 1) | **3679** (C0301 2977, W0611 118, C0209 114, W1514 70, W1510 54, C0415 51, +36 more rules) | **11** (C0115 5, R0801 3, R0915 1, C0116 1, C0301 1) |
| RADE | 68 | **48** (docs 26, comment 10, safety 8, line 3, length 1) | **602** (UP031 328, PLW1510 56, EXE001 46, I001 43, ISC004 30, FURB167 22, +19 more rules) | **53** (C901 20, F401 10, D103 10, E501 9, PLR0915 2, F402 1, D107 1) | **4129** (C0301 3239, C0209 309, W0611 117, W1510 56, C0415 48, W1514 46, +40 more rules) | **24** (C0116 11, C0301 9, R0915 2, R0801 2) |
| 90-161.Z | 84 | **72** (docs 45, safety 21, line 6) | **608** (UP031 253, EXE001 61, PLW1510 59, I001 53, ISC004 32, FURB167 30, +25 more rules) | **58** (C901 23, E501 21, F401 8, PLR0915 2, D103 2, F402 1, D107 1) | **5122** (C0301 3945, C0321 278, C0209 253, W0611 115, W1514 70, W1510 59, +44 more rules) | **27** (C0301 21, C0116 3, R0915 2, R0801 1) |
| 33-332.Z | 49 | 0 | **347** (UP031 133, PLW1510 44, EXE001 32, I001 30, ISC004 30, FURB167 18, +15 more rules) | **19** (C901 13, F401 3, PLR0915 1, F402 1, D107 1) | **3178** (C0301 2575, C0209 131, W0611 110, C0415 44, W1510 44, W1514 44, +31 more rules) | **4** (R0801 2, R0915 1, C0116 1) |
| icf-source | 261 | **269** (comment 141, safety 60, docs 43, header 17, length 3, file_size 3, duplicate 2) | **1240** (I001 220, RUF100 162, SIM115 142, FURB167 136, UP031 119, EXE001 85, +33 more rules) | **761** (E501 380, D103 153, F401 57, D101 56, C901 49, D102 36, D100 17, PLR0915 4, F841 3, F541 2, F601 2, F402 1, D107 1) | **13336** (C0301 9874, C0321 700, W1514 222, W0611 206, C0116 189, C0413 187, +71 more rules) | **669** (C0301 385, C0116 194, C0115 58, C0114 17, R0801 8, R0915 4, C0302 3) |

### Pair 1 radon

| Repo | cc ranks (functions) | mi ranks (files) | functions > 60 lines (from lineno/endline) | files with loc > 450 |
| --- | --- | --- | --- | --- |
| kit | {'C': 107, 'B': 140, 'A': 431, 'E': 5, 'D': 10} | {'A': 62} | 0 | 0 |
| RADE | {'F': 3, 'D': 10, 'C': 107, 'B': 149, 'A': 351, 'E': 6} | {'A': 68} | 1 | 0 |
| 90-161.Z | {'C': 115, 'B': 177, 'A': 414, 'E': 7, 'D': 13} | {'A': 83, 'C': 1} | 0 | 0 |
| 33-332.Z | {'C': 95, 'B': 126, 'A': 297, 'E': 5, 'D': 7} | {'A': 49} | 0 | 0 |
| icf-source | {'B': 460, 'A': 1555, 'C': 289, 'F': 3, 'D': 66, 'E': 20} | {'A': 256, 'B': 3, 'C': 2} | 3 | 3 |

### Pair 1 overlap per check (custom finding also found by a standard rule at the same file and function line, +3 lines for decorators)

**kit** 

| check | custom | standard rule(s) total | both | custom only | standard only |
| --- | --- | --- | --- | --- | --- |
| C1 header | 0 | D100 0 / C0114 0 | D100 0 / C0114 0 | 0 | 0 |
| C2 comment | 0 | D10x 0 / C0116 1 | ruff 0 / pylint 0 | ruff 0 / pylint 0 | ruff 0 / pylint 1 |
| C3 length (>60 lines) | 0 | PLR0915 1 / R0915 1 / radon-derived 0 | ruff 0 / pylint 0 / radon 0 | ruff 0 / pylint 0 / radon 0 | ruff 1 / pylint 1 / radon 0 |
| C4 file size (>450) | 0 | C0302 0 / radon loc 0 | pylint 0 / radon 0 | pylint 0 / radon 0 | pylint 0 / radon 0 |
| C5 duplicate | 0 functions in 0 py files | R0801 3 findings naming 6 files (module names read from the message text) | files in both 0 | n/a | n/a |
| C2 full (functions > 10 lines) | 0 | pylint W9015 48 / W9011 195; ruff DOC201 171 | W9015 0 / W9011 0 / DOC201 0 | W9015 0 / W9011 0 / DOC201 0 | W9015 48 / W9011 195 / DOC201 171 |
| line > 200 chars (strict gate) | gate off | E501 1 files / C0301 1 files | ruff 0 / pylint 0 | n/a | n/a |
| C1 safety / C6 generated / C10 parse | safety 0 / generated 0 / parse 0 | no rule / no rule / syntax error | - | - | - |

**RADE** 

| check | custom | standard rule(s) total | both | custom only | standard only |
| --- | --- | --- | --- | --- | --- |
| C1 header | 0 | D100 0 / C0114 0 | D100 0 / C0114 0 | 0 | 0 |
| C2 comment | 10 | D10x 10 / C0116 11 | ruff 9 / pylint 9 | ruff 1 / pylint 1 | ruff 1 / pylint 2 |
| C3 length (>60 lines) | 1 | PLR0915 2 / R0915 2 / radon-derived 1 | ruff 1 / pylint 1 / radon 1 | ruff 0 / pylint 0 / radon 0 | ruff 1 / pylint 1 / radon 0 |
| C4 file size (>450) | 0 | C0302 0 / radon loc 0 | pylint 0 / radon 0 | pylint 0 / radon 0 | pylint 0 / radon 0 |
| C5 duplicate | 0 functions in 0 py files | R0801 2 findings naming 4 files (module names read from the message text) | files in both 0 | n/a | n/a |
| C2 full (functions > 10 lines) | 26 | pylint W9015 18 / W9011 205; ruff DOC201 142 | W9015 0 / W9011 24 / DOC201 10 | W9015 26 / W9011 2 / DOC201 16 | W9015 18 / W9011 181 / DOC201 132 |
| line > 200 chars (strict gate) | 3 | E501 3 files / C0301 3 files | ruff 3 / pylint 3 | n/a | n/a |
| C1 safety / C6 generated / C10 parse | safety 8 / generated 0 / parse 0 | no rule / no rule / syntax error | - | - | - |

**90-161.Z** 

| check | custom | standard rule(s) total | both | custom only | standard only |
| --- | --- | --- | --- | --- | --- |
| C1 header | 0 | D100 0 / C0114 0 | D100 0 / C0114 0 | 0 | 0 |
| C2 comment | 0 | D10x 2 / C0116 3 | ruff 0 / pylint 0 | ruff 0 / pylint 0 | ruff 2 / pylint 3 |
| C3 length (>60 lines) | 0 | PLR0915 2 / R0915 2 / radon-derived 0 | ruff 0 / pylint 0 / radon 0 | ruff 0 / pylint 0 / radon 0 | ruff 2 / pylint 2 / radon 0 |
| C4 file size (>450) | 0 | C0302 0 / radon loc 0 | pylint 0 / radon 0 | pylint 0 / radon 0 | pylint 0 / radon 0 |
| C5 duplicate | 0 functions in 0 py files | R0801 1 findings naming 2 files (module names read from the message text) | files in both 0 | n/a | n/a |
| C2 full (functions > 10 lines) | 45 | pylint W9015 24 / W9011 256; ruff DOC201 203 | W9015 2 / W9011 41 / DOC201 33 | W9015 43 / W9011 4 / DOC201 12 | W9015 22 / W9011 215 / DOC201 170 |
| line > 200 chars (strict gate) | 6 | E501 6 files / C0301 6 files | ruff 6 / pylint 6 | n/a | n/a |
| C1 safety / C6 generated / C10 parse | safety 21 / generated 0 / parse 0 | no rule / no rule / syntax error | - | - | - |

**33-332.Z** 

| check | custom | standard rule(s) total | both | custom only | standard only |
| --- | --- | --- | --- | --- | --- |
| C1 header | 0 | D100 0 / C0114 0 | D100 0 / C0114 0 | 0 | 0 |
| C2 comment | 0 | D10x 0 / C0116 1 | ruff 0 / pylint 0 | ruff 0 / pylint 0 | ruff 0 / pylint 1 |
| C3 length (>60 lines) | 0 | PLR0915 1 / R0915 1 / radon-derived 0 | ruff 0 / pylint 0 / radon 0 | ruff 0 / pylint 0 / radon 0 | ruff 1 / pylint 1 / radon 0 |
| C4 file size (>450) | 0 | C0302 0 / radon loc 0 | pylint 0 / radon 0 | pylint 0 / radon 0 | pylint 0 / radon 0 |
| C5 duplicate | 0 functions in 0 py files | R0801 2 findings naming 4 files (module names read from the message text) | files in both 0 | n/a | n/a |
| C2 full (functions > 10 lines) | 0 | pylint W9015 19 / W9011 140; ruff DOC201 107 | W9015 0 / W9011 0 / DOC201 0 | W9015 0 / W9011 0 / DOC201 0 | W9015 19 / W9011 140 / DOC201 107 |
| line > 200 chars (strict gate) | 0 | E501 0 files / C0301 0 files | ruff 0 / pylint 0 | n/a | n/a |
| C1 safety / C6 generated / C10 parse | safety 0 / generated 0 / parse 0 | no rule / no rule / syntax error | - | - | - |

**icf-source** 

| check | custom | standard rule(s) total | both | custom only | standard only |
| --- | --- | --- | --- | --- | --- |
| C1 header | 17 | D100 17 / C0114 17 | D100 17 / C0114 17 | 0 | 0 |
| C2 comment | 141 | D10x 189 / C0116 194 | ruff 138 / pylint 139 | ruff 3 / pylint 2 | ruff 51 / pylint 55 |
| C3 length (>60 lines) | 3 | PLR0915 4 / R0915 4 / radon-derived 3 | ruff 2 / pylint 2 / radon 3 | ruff 1 / pylint 1 / radon 0 | ruff 2 / pylint 2 / radon 0 |
| C4 file size (>450) | 3 | C0302 3 / radon loc 3 | pylint 3 / radon 3 | pylint 0 / radon 0 | pylint 0 / radon 0 |
| C5 duplicate | 2 functions in 2 py files | R0801 8 findings naming 14 files (module names read from the message text) | files in both 0 | n/a | n/a |
| C2 full (functions > 10 lines) | 43 | pylint W9015 50 / W9011 653; ruff DOC201 414 | W9015 0 / W9011 30 / DOC201 4 | W9015 43 / W9011 13 / DOC201 39 | W9015 50 / W9011 623 / DOC201 410 |
| line > 200 chars (strict gate) | gate off | E501 80 files / C0301 83 files | ruff 0 / pylint 0 | n/a | n/a |
| C1 safety / C6 generated / C10 parse | safety 60 / generated 0 / parse 0 | no rule / no rule / syntax error | - | - | - |

### Pair 2 counts (shell files)

| Repo | sh files | custom code_standard (shell files, by check) | shellcheck total (by SC code) | shellcheck by level | files with findings | shellcheck secs |
| --- | --- | --- | --- | --- | --- | --- |
| kit | 4 | 0 | **14** (SC2015 7, SC2046 5, SC2034 1, SC2016 1) | {'info': 8, 'warning': 6} | 3 | 1.29 |
| RADE | 10 | **12** (comment 6, safety 3, line 3) | **242** (SC2015 161, SC2086 19, SC2016 16, SC1010 13, SC2154 12, SC2046 5, SC2012 4, SC1091 3, SC2148 2, SC2002 1, SC2126 1, SC2164 1, +4 more rules) | {'error': 3, 'info': 203, 'warning': 33, 'style': 3} | 9 | 2.24 |
| 90-161.Z | 8 | **13** (comment 8, safety 3, line 2) | **146** (SC2015 84, SC2154 15, SC2086 10, SC2181 6, SC2034 6, SC2128 5, SC2046 5, SC2016 3, SC2148 2, SC2002 2, SC2012 2, SC2164 2, +3 more rules) | {'error': 2, 'info': 101, 'warning': 35, 'style': 8} | 7 | 1.74 |
| 33-332.Z | 4 | 0 | **17** (SC2015 8, SC2046 5, SC2016 2, SC2034 1, SC2164 1) | {'info': 10, 'warning': 7} | 4 | 1.2 |
| icf-source | 12 | **4** (duplicate 4) | **20** (SC2015 11, SC2046 5, SC2054 1, SC2034 1, SC2164 1, SC2016 1) | {'warning': 8, 'info': 12} | 6 | 1.31 |

### Pair 3 counts (PowerShell files)

| Repo | ps files | custom code_standard (PowerShell files, by check) | PSSA default rules (by rule) | PSSA with the repo PSScriptAnalyzerSettings.psd1 | PSSA secs default / settings | PSSA comment help on every function (PSProvideCommentHelp) |
| --- | --- | --- | --- | --- | --- | --- |
| kit | 0 | none (no PowerShell files) | n/a | n/a | n/a | n/a |
| RADE | 39 | **175** (docs 75, comment 45, safety 29, line 25, length 1) | **382** (PSAvoidUsingWriteHost 138, PSAvoidGlobalVars 119, PSAvoidUsingPositionalParameters 80, PSUseDeclaredVarsMoreThanAssignments 20, PSReviewUnusedParameter 12, PSUseShouldProcessForStateChangingFunctions 5, +3 more rules) | **164** (PSAvoidGlobalVars 119, PSUseDeclaredVarsMoreThanAssignments 20, PSReviewUnusedParameter 12, PSUseShouldProcessForStateChangingFunctions 5, PSUseSingularNouns 4, PSAvoidOverwritingBuiltInCmdlets 3, PSAvoidUsingInvokeExpression 1) | 12.26 / 0.97 | 181 |
| 90-161.Z | 66 | **65** (safety 19, docs 19, comment 14, line 13) | **1156** (PSAvoidUsingPositionalParameters 548, PSAvoidGlobalVars 320, PSAvoidUsingWriteHost 221, PSReviewUnusedParameter 17, PSUseShouldProcessForStateChangingFunctions 16, PSProvideCommentHelp 12, +5 more rules) | **368** (PSAvoidGlobalVars 320, PSReviewUnusedParameter 17, PSUseShouldProcessForStateChangingFunctions 16, PSUseSingularNouns 5, PSAvoidOverwritingBuiltInCmdlets 5, PSUseDeclaredVarsMoreThanAssignments 4, PSAvoidUsingInvokeExpression 1) | 16.14 / 1.08 | 324 |
| 33-332.Z | 38 | 0 | **232** (PSAvoidUsingPositionalParameters 91, PSUseSingularNouns 68, PSUseShouldProcessForStateChangingFunctions 27, PSProvideCommentHelp 26, PSReviewUnusedParameter 13, PSAvoidUsingWriteHost 3, +2 more rules) | 0 | 8.79 / 0.39 | 84 |
| icf-source | 0 | none (no PowerShell files) | n/a | n/a | n/a | n/a |

### Times (seconds, one run, this container)

| Repo | custom measure() all langs | ruff def | ruff mapped | radon cc+mi+raw | pylint def | pylint mapped | shellcheck | PSSA default | PSSA settings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kit | 0.45 | 0.19 | 0.05 | 1.43 | 11.87 | 2.39 | 1.29 | n/a | n/a |
| RADE | 3.98 | 0.05 | 0.05 | 1.18 | 11.81 | 2.48 | 2.24 | 12.26 | 0.97 |
| 90-161.Z | 5.58 | 0.05 | 0.04 | 1.49 | 17.03 | 4.08 | 1.74 | 16.14 | 1.08 |
| 33-332.Z | 2.62 | 0.11 | 0.04 | 1.26 | 9.43 | 2.3 | 1.2 | 8.79 | 0.39 |
| icf-source | 2.07 | 0.35 | 0.26 | 4.51 | 43.98 | 8.03 | 1.31 | n/a | n/a |

Reading the tables:

- Pair 1: the standard tools at zero config report 350 to 13,300 findings per repo (mostly style: C0301 at pylint's default 100 columns, UP031, I001, PLW1510), nearly none of which a C-check asks for. Only the mapped sets are comparable. The custom check's own count is small because most repos hold ratcheted debt, not new findings.
- 33-332.Z and kit: custom raw debt is 0 in Python; pylint mapped still reports 4 and 11 (R0915, R0801, C0116/C0115 for classes, 1 C0301), none of them a custom check. See "standard only" in the overlap table.
- Radon does not gate anything by itself: its cc ranks (C or worse: 107 to 378 functions per repo) and mi ranks (A for 62 of 62 kit files; the worst file is rank C in 90-161.Z 1 of 84 and icf 2 of 261) measure complexity and maintainability, which no C-check measures. Function length and file size can be derived from its JSON (`lineno`/`endline`, `loc`) with a short script; that is data, not a check.
- Pair 2: shellcheck's findings are a different class from every shell check of the custom tool. By defect class the overlap is zero; no shellcheck code reports a missing header, a missing function comment, a function or file length, a duplicate or a line length. Per-file overlap was not computed because the defect classes do not meet.
- Pair 3: with each repo's own settings file, PSSA reports 164 (RADE), 368 (90-161.Z) and 0 (33-332.Z) warnings, run per file. RADE's `lint.sh` was not run; it lints the built sample bundle with the same settings (a different scope: not these 39 files), so its result is not comparable with the 164. 119 of the 164 and 320 of the 368 are `PSAvoidGlobalVars`. PSSA default adds Information-level rules (positional parameters) and Write-Host, which the repo setting files switch off or exclude.

## 4. Seeded defects (stand-in for mutant kills)

A temporary repo was made from `git archive HEAD` of the kit, given its own `git init` (outside every real repo), with `.check` extended in the temp copy by `code-c1-safety: on`, `code-strict-gate: on`, `code-max-line-chars: 200` and one `code-generated:` line. The seed files sit in a `seed/` folder, one defect per file, in three languages; each tool ran on the seed files only. Y = the tool reports the seeded defect itself (not an unrelated finding in the same file); the rule that fired is in brackets.

The brief's examples "bare except" and "unquoted variable" are not checks of the custom tool (its checks are C1, C2, C3, C4, C5, C6, C10, the line cap, safety labels and C2 full). They are in the table as separate rows "not a custom check", to show what the standard tool adds. The custom tool also fired `safety` on nearly every seed file only because the seed headers have no `Network:/Writes:/Credentials:` labels; that is a side effect, not a seeded defect, and it is left out of the table.

### Python

| # | Seeded defect (file) | custom | ruff default | ruff mapped | pylint default | pylint mapped | radon |
|---|---|---|---|---|---|---|---|
| 1 | C1 no header comment | Y (header) | N | Y (D100) | Y (C0114) | Y (C0114) | n/a |
| 2 | C2 function without comment | Y (comment) | N | Y (D103) | Y (C0116) | Y (C0116) | n/a |
| 3 | C3 function of 70+ lines | Y (length) | N | Y (PLR0915, counts statements, not lines) | Y (R0915, same) | Y (R0915) | Y as data (`endline - lineno + 1 > 60`; no gate) |
| 4 | C4 file of 751 lines | Y (file_size) | N | N | N (its default cap is 1000) | Y (C0302 with `max-module-lines=450`) | Y as data (raw `loc`; no gate) |
| 5 | C5 same function body in 2 files | Y (duplicate) | N | N | N | N at `min-similarity-lines=4`; Y at 3 (separate run, R0801) | n/a |
| 6 | C10 file that does not parse | Y (parse) | Y (invalid-syntax) | Y | Y (E0001) | Y (E0001) | error entry only |
| 7a | C2 full: function over 10 lines, docstring with no Args section | Y (docs) | N | N for parameters (D417 N); preview DOC201 reports the missing return doc only | N | N for parameters; docparams (separate run) W9011 reports the missing return doc only; parameters are not checked when the docstring has no parameter section | n/a |
| 7b | C2 full: same, Args section names only one of two parameters | Y (docs) | N | Y (D417) | N | N (not in the set); docparams run: Y (W9015) | n/a |
| 8 | C6 generated file without GENERATED | Y (generated) | N | N | N | N | n/a |
| 9 | Line of 230 characters | Y (line) | N | Y (E501) | Y (C0301, also at default 100) | Y (C0301) | n/a |
| 10 | C1 safety: header lacks the 3 labels | Y (safety) | N | N | N | N | n/a |
| x | not a custom check: bare `except`, mutable default argument, unused import | N | Y (E722, B006, F401) | F401 only (E722, B006 not in the mapped set) | Y (W0702, W0102, W0611) | N | n/a |

Python result: the custom tool catches 11 of 11 seeded custom-check defects (rows 1 to 10 with 7a and 7b). Ruff mapped catches 5 (1, 2, 6, 7b, 9) and 1 as a proxy (3); pylint mapped catches 5 (1, 2, 4, 6, 9) and 1 as a proxy (3), 6 with the docparams run (7b); row 5 only with `min-similarity-lines=3`; neither catches 7a, 8 or 10. Both catch a defect class the custom tool does not have (row x). Side effect: the two C2-full seeds share one function body, so the custom tool (and pylint R0801) also reported them as duplicates of each other.

### Shell

| # | Seeded defect (file) | custom | shellcheck |
|---|---|---|---|
| 1 | C1 no header comment | Y (header) | N |
| 2 | C2 function without comment | Y (comment) | N |
| 3 | C3 function of 70+ lines | Y (length) | N |
| 4 | C4 file of 522 lines | Y (file_size) | N |
| 5 | C5 same function body in 2 files | Y (duplicate) | N |
| 6 | Line of 230 characters | Y (line) | N (SC2034 fired, on the unused variable of the seed; not the length) |
| 7 | C1 safety labels missing | Y (safety) | N |
| x | not a custom check: unquoted variable, `cd` without a failure branch, `[ $f == ... ]` | N | Y (SC2086 x3, SC2164 x1) |

Shell result: the custom tool catches 7 of 7; shellcheck 0 of 7, and catches the class the custom tool lacks. (Shell seeds 3 to 5 also fired `comment` on the custom side: the seed's header comment block touches the function, an artifact of the seed layout.)

### PowerShell

| # | Seeded defect (file) | custom | PSSA default | PSSA repo settings | PSSA mapped rule |
|---|---|---|---|---|---|
| 1 | C1 no header comment | Y (header) | N | N | N |
| 2 | C2 function without comment | Y (comment) | N | N | Y (PSProvideCommentHelp, `ExportedOnly = $false`; the default is exported functions only) |
| 3 | C3 function of 70+ lines | Y (length) | N | N | N |
| 4 | C4 file of 654 lines | Y (file_size) | N | N | N |
| 5 | C5 same function body in 2 files | Y (duplicate) | N | N | N |
| 6 | C10 file that does not parse | Y (parse) | Y (ExpectedValueExpression, MissingEndParenthesisInExpression) | RADE file (Severity includes ParseError): Y; 90-161.Z file and 33-332.Z file (Error, Warning only): N | Y (the trial rules report parse errors too) |
| 7 | C2 full: function over 10 lines, no `.PARAMETER` | Y (docs) | N | N | N |
| 8 | Line of 230 characters | Y (line) | N | N | PSAvoidLongLines (`MaximumLineLength = 200`): Y |
| 9 | C1 safety labels missing | Y (safety) | N | N | N |
| x | not a custom check: `Invoke-Expression`, `Write-Host`, unused variable, unapproved verb, plural noun | N | Y (PSAvoidUsingInvokeExpression, PSAvoidUsingWriteHost, PSUseDeclaredVarsMoreThanAssignments, PSUseApprovedVerbs, PSUseSingularNouns) | Y (all but Write-Host, which the 90-161.Z setting file allows) | n/a |

PowerShell result: the custom tool catches 9 of 9; PSSA default 1 of 9 (parse); PSSA with a repo settings file 0 of 9 (90-161.Z, 33-332.Z files) or 1 of 9 (RADE file, parse); with the two trial rules added, 3 of 9 (parse, comment help, line). Seed note: the two C2 seeds have a statement between the header help block and the function, so the header does not count as the function's help.

## 5. Per-pair summary

Definition of Y (the denominator): the checks of `code_standard.py` as its header lists them: C1 header, C1 safety, C2 comment, C2 full, C3 length, C4 file size, C5 duplicate, C6 generated, C10 parse = 9, plus the strict gate's `line` check = 10. For shell, C10 and C2 full do not apply (the tool parses only Python and PowerShell; shell C2 full is the plain C2): Y = 8. The ratchet (`.check.state.json`, the comparison with main, the baseline that can only shrink, `--adopt`) is a capability no standard tool has; it is outside the count, and it is what makes a check usable on a repo with old debt. Grades: Full = every custom finding of that check, measured in the 5 repos and the seeds, was also a finding of a standard rule; Partial = some, or only with a different meaning or a tuned setting; None = no rule.

### Pair 1: code_standard.py (Python) vs ruff + pylint + radon

Standard covers 4 of 10 fully, 4 more partly, 2 not at all.

| Check | Grade | Standard rule and config | What the data shows |
|---|---|---|---|
| C1 header | Full | ruff D100; pylint C0114 | icf 17 of 17 custom findings found by both; 0 extra. Meaning is weaker: only "a docstring exists", not 60 characters or content |
| C2 comment | Partial | ruff D102/D103/D105 (public names only); pylint C0116 with `no-docstring-rgx=^$` | custom 141 (icf) / 10 (RADE): ruff finds 138 / 9, pylint 139 / 9. Missed: nested functions (2), a method of a private class (1), a private function (ruff only, 1). Extra standard findings where the custom check passes (icf): 51 ruff, 55 pylint. Of the 55 pylint ones, 47 have a `#` comment directly above the def or as the first body line and 5 a trailing comment on the def line (read by hand); 3 were not classified. The kit accepts these forms, these rules do not |
| C2 full | Partial | pylint docparams (needs the plugin), ruff preview DOC201/DOC501 | custom 26 / 45 / 43 (RADE, 90-161.Z, icf). docparams missing-return-doc (W9011) overlaps 24 / 41 / 30, missing-param-doc (W9015) 0 / 2 / 0; ruff D417 0 of all; DOC201 overlaps 10 / 33 / 4. Both tools check parameters only when the docstring already has a parameter section: the seed with no Args section is not caught for parameters, the seed with a partial Args section is caught (D417, W9015). Most custom findings in the repos are docstrings with no Args section, hence the near-zero parameter overlap. No 10-line threshold in either: on the clean kit, docparams reports 195 (W9011) + 48 (W9015) functions and DOC201 171 that the custom check accepts |
| C3 length | Partial | proxy only: ruff PLR0915 / pylint R0915 (statements, default max 50); no line-count rule exists | icf custom 3: R0915 finds 2; RADE 1 of 1. Each tool reports 1 to 2 functions the custom check does not (many statements in under 60 lines). Radon JSON gives `endline - lineno + 1`, which finds 3 of 3 and 1 of 1 and 0 extra, but needs a small script to gate |
| C4 file size | Full (pylint) | pylint C0302 with `max-module-lines=450`; ruff has no rule | icf 3 of 3, 0 extra; radon `loc` > 450 also 3 of 3 (data, no gate) |
| C5 duplicate | Partial | pylint R0801 (similar lines across files, not same-body functions) | pylint reports each R0801 on one module, so the files are read from the message text (`==module:[a:b]`): icf custom 2 functions in 2 files; R0801 8 findings naming 14 modules; 0 files shared. Same join: 0 shared in the other four repos. Seed: the identical pair dup_a/dup_b is missed at the default `min-similarity-lines=4`, caught at 3; the two C2-full seeds, which duplicate each other by accident, were reported by both tools. R0801 reports similar lines (also across different functions), the custom check same-body functions, so findings differ in kind |
| C6 generated | None | no rule | seed: not caught |
| C10 parse | Full | ruff invalid-syntax; pylint E0001 | 0 parse failures in all 5 repos in both tools; seed caught by both |
| C1 safety | None | no rule | custom 8 (RADE), 21 (90-161.Z), 60 (icf) |
| line (strict gate) | Full | ruff E501 / pylint C0301 with line length 200 | RADE 3 of 3 files, 90-161.Z 6 of 6 |

Only the custom tool finds: C1 safety, C6 generated, the 10-line-threshold form of C2 full, same-body duplicates as defined, the ratchet. Only the standard tools find: unused imports and variables (F401 at 4 / 10 / 8 / 3 / 57 in kit / RADE / 90-161.Z / 33-332.Z / icf), complexity (C901, radon cc), pylint's R0801 similar lines, missing class docstrings (D101 5 kit, 56 icf), dozens of bug and style classes in the default sets, bare `except`, mutable defaults, maintainability index.

Run time: custom 0.5 to 5.6 s for the whole repo (all languages, includes the pwsh parse); ruff 0.04 to 0.35 s; pylint mapped 2.3 to 8.0 s, pylint default 9.4 to 44.0 s; radon (cc, mi, raw) 1.2 to 4.5 s. Table in section 3.

Config the standard side would need (a trial, measured above; not complete): the two blocks in section 2 (ruff `select` with D100, D101, D102, D103, D105, D107, E501, E9, F, PLR0915; pylint `max-module-lines=450`, `max-line-length=200`, `no-docstring-rgx=^$`, `min-similarity-lines=3` for the seed), and for C2 full `pylint.extensions.docparams` with `accept-no-param-doc=no`. Not reachable by any config: C1 safety, C6, the ratchet, a 60-line function cap (a radon-based script would be needed).

Candidate verdicts (the Maintainer chooses):

| Option | What it means | Trade-offs |
|---|---|---|
| Retire | drop the Python side; use ruff + pylint (+ a radon script for C3) | Loses C1 safety, C6, the ratchet, the same-body duplicate rule, the 10-line C2 full rule and the exact C2 meaning (`#` comments); the repos with debt (RADE, 90-161.Z, icf) have no baseline for ruff/pylint findings, so a first run would fail on 53 / 58 / 761 mapped findings; adds 2 pip tools and a config to keep in sync across 5 repos; gains a maintained rule set, no kit code to own for these rules |
| Shrink to the uncovered part | keep C1 safety, C6, C2 full, C5, C3 and the ratchet; hand C1 header, C4, C10, line (and C2 comment, with a meaning change) to ruff/pylint | Fewer custom lines to own, but two systems must agree on one baseline; the ratchet currently covers only custom findings, so the standard findings need their own ratchet or a clean tree first |
| Keep | no change | Known cost: the custom code (10 files under `scripts/`); no new tools; the standard tools find a different class (bugs) that the custom tool does not claim to find; run time is low |

### Pair 2: shell checks vs shellcheck

The kit has no bash check outside `code_standard.py`'s shell rules. Standard covers 0 of 8 (header, safety, comment, length, file size, duplicate, generated, line); uncovered: all 8. Shellcheck finds a different class: kit 14, RADE 242, 90-161.Z 146, 33-332.Z 17, icf 20 findings; across the 5 repos the top codes are SC2015 (A && B || C), SC2086 (unquoted), SC2046, SC2154, SC2016, with 3 error-level findings in RADE (SC2148 x2 missing shebang, SC2144 x1) and 2 in 90-161.Z (SC2148 x2). The custom shell findings are 0 / 12 / 13 / 0 / 4 (kit / RADE / 90-161.Z / 33-332.Z / icf). Seeds: custom 7 of 7, shellcheck 0 of 7; shellcheck 1 of 1 on the unquoted variable (3 SC2086 plus 1 SC2164).

Run time: shellcheck 1.2 to 2.2 s per repo.

Config the standard side would need: none changes its coverage; shellcheck has no rule for header, comment, length or duplicate. A shellcheck run with `-s bash` and an `.shellcheckrc` for the shared dialect would reduce noise (not tried).

Candidate verdicts:

| Option | Trade-offs |
|---|---|
| Retire the custom shell rules | would remove all 8 checks with no replacement (shellcheck does not cover them); the 3 repos with findings would lose C2 and safety checks on shell |
| Shrink | there is nothing the standard tool can take over from the custom side |
| Keep, and add shellcheck beside it | not a retirement: adds a bug-class check for 4 to 12 files per repo; costs 242 findings to triage in RADE (161 are SC2015, an info-level style code), 146 in 90-161.Z; a baseline or a severity filter (`-S warning`: 33 + 3 in RADE) would be needed |

### Pair 3: PowerShell checks vs PSScriptAnalyzer

Standard covers 2 of 10 fully (C10 parse, line), 2 partly (C2 comment, C2 full), 6 not at all (C1 header, C1 safety, C3, C4, C5, C6). Uncovered: header, safety, function length, file size, duplicate, generated.

| Check | Grade | Standard rule and config | What the data shows |
|---|---|---|---|
| C10 parse | Full, with a condition | the parser errors that PSSA returns (e.g. ExpectedValueExpression) in a default run or with `ParseError` in `Severity` (RADE's file does; the 90-161.Z and 33-332.Z files do not, so those repos add a separate `ParseFile` pass) | 0 parse errors in the 143 files for both tools; seed caught by default PSSA and RADE's file, not by the other two files |
| line | Full | PSAvoidLongLines, `MaximumLineLength = 200` (off by default) | RADE 25 of 25 files, 90-161.Z 13 of 13 (PSSA 15 files, 2 more), 33-332.Z 0 of 0; PSSA adds 351 / 182 line findings (per line, not per file) |
| C2 comment | Partial | PSProvideCommentHelp with `ExportedOnly = $false` (default is exported functions only: 0 of 45 custom RADE findings, 0 of 14 in 90-161.Z) | custom 45 / 14 / 0; with the rule on every function, overlap is 13 of 45 (RADE) and 7 of 14 (90-161.Z); the rule asks for a full help block, so it reports 181 / 324 / 84 findings, 33-332.Z included where the custom check reports 0 |
| C2 full | Partial | the same rule (it checks that help exists, not that each `.PARAMETER` exists) | custom 75 / 19 / 0; overlap 51 of 75 (RADE), 16 of 19 (90-161.Z) with the rule on everywhere. Seed with no `.PARAMETER`: not caught |
| C1 header, C1 safety, C3, C4, C5, C6 | None | no rule | custom counts in section 3 (safety 29 RADE, 19 90-161.Z; length 1 RADE) |

Only the custom tool finds the 6 uncovered checks and the ratchet. Only PSSA finds: global variables (PSAvoidGlobalVars 119 / 320 / 0), Write-Host (138 / 221 / 3 at default), positional parameters, unused variables and parameters, ShouldProcess, singular nouns, `Invoke-Expression` (1 / 1 / 0), and its compatibility rules (5.1 syntax) via the repo settings.

Run time: PSSA default 8.8 to 16.1 s per repo; the settings pass took 0.4 to 1.1 s but ran second in the same pwsh process (module already loaded, rules fewer), so it is not a fair figure for a cold run; the custom tool takes 2.6 to 5.6 s for the whole repo.

Config the standard side would need: the repo `PSScriptAnalyzerSettings.psd1` as it stands (already in RADE, 90-161.Z, 33-332.Z), plus `PSAvoidLongLines` with `MaximumLineLength = 200` and `PSProvideCommentHelp` with `ExportedOnly = $false` (with a different meaning: a help block, not just a comment); nothing exists for header, safety, length, size, duplicate or generated.

Candidate verdicts:

| Option | Trade-offs |
|---|---|
| Retire the PowerShell side | removes the 6 uncovered checks outright and weakens the 2 partly covered ones; the three projects already run PSSA, so the standard tool is not new there, which means it adds nothing for them |
| Shrink | the custom side could drop C10 parse (RADE's settings already report it; 90-161.Z and 33-332.Z run a `ParseFile` pass beside PSSA) and `line` (PSAvoidLongLines), keeping the 6 uncovered checks and C2 as defined; saves the pwsh parse step at the custom side (its run time includes it) at the cost of a new rule and, in two repos, a `ParseError` severity in the PSSA settings file |
| Keep | no change; PSSA and the custom check stay side by side (they already are); no rule overlaps except parse and line |

## 6. Open points and limits

- Overlap is by function line (+3) or file, not by "same defect text"; the two tools use different messages and rule ranges.
- The mapped configs were chosen by this run from the brief's examples and the rule docs; each mapping was checked on the seeds and the 5 repos (table above). Other mappings were not tried (for example ruff `PLR` thresholds, pylint `max-statements`, `min-similarity-lines` other than 3 and 4, shellcheck `-S`/`-e` filters, PSSA custom rules).
- Seeds: one defect per file, one run each; PowerShell comment-help seed 2 is blurred by the seed's own header help block (noted in the table).
- Functions with the same name in nested scopes get a `#2` suffix in the custom key; they were matched by name, so a rare mismatch is possible (3 custom C2 findings had no standard match for nested or private reasons, listed in the C2 row).
- No JS or MJS files were measured with a standard tool (eslint was not in the brief); the custom tool measures 135 of them across the 5 repos.
- `icf-source` has an ignored `scripts/__pycache__/` folder with three files (`check_content_finders`, `check_content_scan`, `check_content_scan_settings`, `.cpython-313.pyc`), all stamped 20:55:01 UTC, 2026-11-23. `code_standard.py` does import `check_content_scan_settings` (through `check_settings`), but every run of this study set `PYTHONDONTWRITEBYTECODE=1`, and 20:55 is earlier than the first run of this study on that repo; the origin is not known, most likely another process. It was left as it is (no writes in clones). Nothing else changed in any clone: `git status --porcelain` is empty for RADE, 90-161.Z, 33-332.Z and the kit worktree, and the HEADs above were read again at the end.
- Work files (configs, drivers, JSON outputs, the seeded repo) are in the session scratchpad, not in the repo; nothing but this file was added to the branch.
