# Tool retirement, group W-D: trials of the master plan Part 2 standard replacements

Date: 2026-11-23. Program: custom tool retirement (research plan step R4, prompt step 6; coverage rows P2-3b, P2-4a, P2-4b, P2-5a, P2-5b, P2-5c, P2-6a, P2-6b, P2-7a, P2-7b, P2-8a, P2-8b). Evidence only: this file decides nothing. Verdict options are listed with trade-offs for the Maintainer.

All trials ran in a scratch copy of each repo (the repos are read-only; nothing was written to them, nothing was pushed except this file). No secret and no personal data were used.

## Repos and versions

| Repo | HEAD (short SHA) | Role in the trials |
|---|---|---|
| kit (archimedes_lever) | 641023e | trial 1 |
| RADE | a99ba73 | trials 1, 2, 3, 5 |
| 90-161.Z | 91ccb0c | trials 1, 2, 3, 4 |
| 33-332.Z | 6cbc517 | trials 1, 2 |
| ICF-Source | 02a7ed2d | trial 6 (read-only; not in trial 1) |

Packages and tools used (this container only; none added to any repo):

| Tool | Version | Source |
|---|---|---|
| Python | 3.13.18 | preinstalled |
| pip | 26.3 (the container had 24.0 from Debian; `pip install --ignore-installed pip` was needed first) | PyPI |
| cyclonedx-bom (command `cyclonedx-py`) | 9.0.0 (with cyclonedx-python-lib 11.12.0) | PyPI |
| pip-tools (command `pip-compile`) | 7.7.0 | PyPI |
| markdown (python-markdown) | 3.11.3 | PyPI |
| markdown-it-py | 4.3.0 (+ linkify-it-py 2.2.0, mdit-py-plugins 0.7.0) | PyPI |
| bandit (comparison only) | 1.9.4 (the version the repos' own workflows pin) | PyPI |
| CodeQL CLI | 2.27.5 (`codeql-linux64.zip`, 418,509,202 bytes) and the bundle with the query packs (`codeql-bundle-linux64.tar.gz`, 696,138,291 bytes, same release) | github.com release downloads |
| PowerShell | 7.4.6 | preinstalled |
| Node.js / Google Chrome for Testing / playwright (npm) | 22.23.5 / 153.0.8010.12 / 1.63.0 | preinstalled |

Deviations from the brief and the full install list are in "Installs and deviations" at the end of this file.

---

## Trial 1. Supply chain: CodeQL, CycloneDX SBOM, hash-pinned Python (P2-5a, P2-5b, P2-5c)

### What each repo has

| Repo | Python files | Python dependency manifest | Third-party imports found (scan of `import`/`from`) | Existing security workflow |
|---|---|---|---|---|
| kit | 62 | none | none (standard library only) | `security.yml`: bandit 1.9.4 + gitleaks 8.30.1, pull request and manual only |
| RADE | 68 | none | `fontTools` (scripts/build_fonts.py, a build-only script; its docstring says 4.55.3), `jsonschema` (scripts/check_apps.py, check_manifest.py) | `security.yml` (bandit + gitleaks) |
| 90-161.Z | 84 | `requirements.txt` (3 pins: python-docx 1.2.0, pillow 13.0.0, jsonschema 4.26.0), plus `package.json` / `package-lock.json` (3 direct packages docx 9.7.1, jszip 3.10.2, pptxgenjs 3.12.0; 27 locked packages, lockfileVersion 3) | `PIL`, `docx` (both listed), `pdfplumber` (NOT in requirements.txt: a possible gap, not checked further) | `security.yml` (bandit + gitleaks) |
| 33-332.Z | 49 | none | none (standard library only) | `security.yml` (bandit + gitleaks) |

Baseline for comparison: `bandit -r scripts -ll` (medium and higher), as the repos' workflows run it, found 0 results in all four repos (kit 13,917 lines scanned, RADE 11,880, 90-161.Z 14,710, 33-332.Z 11,473).

### (a) CodeQL

Local run: the CodeQL CLI 2.27.5 (CLI-only zip, no query packs) downloaded from a github.com release asset and created the databases. `codeql pack download` is refused by the agent proxy (the `ghcr.io` blob host `pkg-containers.githubusercontent.com` is not on the allowlist) and the CodeQL source archive is refused (403). The query packs came from the second release asset, the bundle `codeql-bundle-linux64.tar.gz` of the github/codeql-action release "latest" (696,138,291 bytes, same CLI release 2.27.5, ships `python-code-scanning.qls`, `javascript-code-scanning.qls`, `actions-code-scanning.qls`). The databases made with the CLI-only zip were analyzed with the bundle (same release number).

Measured with the code-scanning suites (the default suite of the GitHub action), threads=0 (all cores of this container):

| Repo | Language | Database create | Analyze | Findings |
|---|---|---|---|---|
| kit | python | 19 s | 25 s | 1: `py/redos`, scripts/build_site_html.py line 121 (a regular expression that may backtrack exponentially on strings starting with `<table>`) |
| kit | actions | 6 s | 13 s | 0 |
| kit | javascript-typescript | 4 s | 1 s | database creation **fails** (exit 32): "CodeQL detected code written in JavaScript/TypeScript but could not process any of it" (its one .js file is not picked up) |
| RADE | python | 19 s | 26 s | 3: `py/bad-tag-filter` x2 (tests/page_test.py lines 40 and 94: a regular expression does not match upper-case `<SCRIPT>`), `py/redos` x1 (scripts/build_site_html.py line 121, the same line as in the kit) |
| RADE | actions | 7 s | 15 s | 0 |
| RADE | javascript-typescript | 13 s | 45 s | 0 |
| 90-161.Z | python | 16 s | 22 s | 1: `py/redos`, scripts/build_site_html.py line 121 |
| 90-161.Z | actions | 7 s | 16 s | 0 |
| 90-161.Z | javascript-typescript | 14 s | 51 s | 1: `js/bad-tag-filter`, tests/check_go_page.js line 51 (does not match upper-case `<SCRIPT>`) |
| 33-332.Z | python | 11 s | 27 s | 1: `py/redos`, scripts/build_site_html.py line 121 |
| 33-332.Z | actions | 7 s | 15 s | 0 |
| 33-332.Z | javascript-typescript | 4 s | 1 s | database creation fails (exit 32), as the kit |

Reading: 7 findings in all (4 `py/redos` that are one file, `scripts/build_site_html.py`, copied into all four repos; 3 `bad-tag-filter` in test files). Whether each is a real defect was not judged here (the regular expressions run on the repo's own HTML at build time or in tests, not on user input). The bandit baseline (0 results) found none of them: CodeQL finds a different class. In the Actions job a language with no source it can process (kit, 33-332.Z for JavaScript) fails the step, so the matrix must list languages per repo.

Run time: create plus analyze took 40 to 45 s for Python, 59 to 65 s for JavaScript and about 20 s for the workflow YAML; one repo with all its languages in sequence took 63 s (kit) to 126 s (90-161.Z). In GitHub Actions add the action's own start: the CodeQL bundle download and unpack (the bundle is 696 MB; the action caches it per runner image, so the first run is slower), and the job start. The Actions time is an estimate, not a measurement: about 3 to 6 minutes per language job. The two existing jobs (bandit, gitleaks) each have `timeout-minutes: 10`; the same cap fits.

Coverage limit that matters here: CodeQL has no PowerShell support (`codeql resolve languages` of CLI 2.27.5 lists: html, xml, yaml, go, csharp, java, actions, python, swift, rust, csv, properties, ruby, cpp, javascript). The bulk of the code in RADE (39 .ps1/.psm1 files), 90-161.Z (67) and 33-332.Z (38) is PowerShell and stays uncovered. What CodeQL does cover per repo: Python in all four; JavaScript in RADE and 90-161.Z (it fails for kit and 33-332.Z, see the table); the `actions` language (the workflow YAML itself) in all four, 0 findings.

Workflow I would use (not pushed; the action pins must be set to commit SHAs like the repos' other workflows; I did not invent the SHA, set it when adding the file):

```yaml
name: codeql
# CodeQL on Python, JavaScript and the workflow files. Pull requests that change code, and manual runs; never on push (Actions minutes), as security.yml.
on:
  pull_request:
    paths:
      - "**/*.py"
      - "**/*.js"
      - "**/*.mjs"
      - ".github/workflows/**"
  workflow_dispatch:
permissions:
  contents: read
jobs:
  analyze:
    name: analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      security-events: write   # the only write: uploads the SARIF results
    strategy:
      fail-fast: false
      matrix:
        language: [python, javascript-typescript, actions]
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09  # v5.1.0 (the SHA the repos use)
        with:
          persist-credentials: false
      - uses: github/codeql-action/init@<PIN THE COMMIT SHA OF THE v4 RELEASE>
        with:
          languages: ${{ matrix.language }}
          build-mode: none          # Python, JavaScript and actions need no build
      - uses: github/codeql-action/analyze@<SAME SHA>
        with:
          category: "/language:${{ matrix.language }}"
```

Open points for the Maintainer: (1) results upload to the Security tab needs `security-events: write`, which widens a workflow permission (AGENTS.md "Guards and checks": the workflow is a guard file; a change needs the Maintainer's request). (2) Licence: my recollection, not checked in this session, is that code scanning is free for public repos and needs GitHub Code Security (a cost) for private repos; the visibility of each repo was not checked. (3) `paths:` as written skips a pull request that changes no listed file; drop `paths` to run on every pull request. (4) The matrix must be cut per repo: JavaScript fails on kit and 33-332.Z (measured above).

### (b) CycloneDX SBOM

Proof commands (run in the scratch copy):

```
cyclonedx-py requirements 90-161.Z/requirements.txt --of JSON -o sbom-90-161.json
cyclonedx-py requirements <empty file> --of JSON -o sbom-<repo>.json        # for kit, RADE, 33-332.Z
pip-compile --generate-hashes --strip-extras -o req.hashed.txt 90-161.Z/requirements.txt
cyclonedx-py requirements req.hashed.txt --of JSON -o sbom-90-161-full.json
```

| Repo | Components in the SBOM | Note |
|---|---|---|
| kit | 0 | no manifest; standard library only, so a complete SBOM of the Python side is empty |
| RADE | 0 | no manifest, but the code imports `fontTools` and `jsonschema`: an SBOM from a manifest would say 0 while the code needs 2 (+4 transitive) packages |
| 90-161.Z | 3 from `requirements.txt` as written (CycloneDX spec 1.6); 9 from the hash-pinned file (transitive packages included) | the 27 npm lockfile packages are not in it: they need `cyclonedx-npm` (a different tool, not installed or run) |
| 33-332.Z | 0 | no manifest; standard library only |

Not covered by any SBOM here: PowerShell modules (PnP and others the scripts use; no standard SBOM source), the fonts and logos the bundles embed, and the vendored Node packages. `cyclonedx-py environment` would list the installed environment instead, but that lists the container, not the repo.

### (c) pip-tools, `pip-compile --generate-hashes`

| Repo | Input | Pinned packages (lines `name==version`) | Hash lines | Time |
|---|---|---|---|---|
| 90-161.Z | `requirements.txt` | 9: attrs 26.1.0, jsonschema 4.26.0, jsonschema-specifications 2025.9.1, lxml 6.1.3, pillow 13.0.0, python-docx 1.2.0, referencing 0.37.0, rpds-py 2026.9.1, typing-extensions 4.16.0 (3 direct + 6 transitive) | 399 (many wheels per package: one per platform) | 9.5 s; output file 429 lines |
| RADE | none exists. A manifest I inferred from the imports (`fonttools`, `jsonschema`) as a what-if: 6 pins (attrs, fonttools 4.68.0, jsonschema, jsonschema-specifications, referencing, rpds-py) | 6 | not counted | few seconds |
| kit | none, none needed (standard library only) | 0 | 0 | |
| 33-332.Z | none, none needed | 0 | 0 | |

Trade-offs to weigh: a hash-pinned file lists every platform wheel (a long file, 399 hash lines for 9 packages), and the work computer or the cloud image may install a different platform than the one pip-compile ran on (pip-compile pins hashes for all wheels PyPI offers, so that works, but a package without a wheel for that platform falls back to an sdist). pip-compile took the newest versions (fonttools 4.68.0 against 4.55.3 named in RADE's build_fonts.py docstring): a pin file changes what the repo builds with unless the old version is given as a constraint. The 90-161.Z `requirements.txt` comment says the versions come from "the cloud image"; a hashed file would make CI fail on drift instead of silently differing.

### Candidate verdicts (trial 1)

| Item | Retire | Shrink | Keep | Adopt |
|---|---|---|---|---|
| CodeQL | no custom tool replaced (bandit and gitleaks are standard already) | | | Adopt for Python, JavaScript (RADE, 90-161.Z only) and workflow YAML next to bandit: it found 7 results the bandit baseline (0) did not (3 of them in test files; 4 are one copied file); leaves PowerShell uncovered; needs a permission change and, for a private repo, possibly a licence (unchecked) |
| CycloneDX SBOM | | | | Adopt only for 90-161.Z today (3 or 9 components); for kit, 33-332.Z an SBOM would be empty, for RADE it would be wrong until a manifest exists |
| Hash-pinned Python | | | Keep as is for kit and 33-332.Z (nothing to pin) | Adopt for 90-161.Z (replace the hand-pinned 3 lines with a 9-package hashed file); RADE would first need a manifest, which is a new file the repo does not have |

---

## Trial 2. Paste truncation sentinel (P2-3b)

### The bundles

| Bundle | Lines | Bytes | Generator | Existing protection |
|---|---|---|---|---|
| 33-332.Z `paste/Ion-script.txt` | 7,258 | 370,393 | `scripts/build_paste.py` (235 lines; `build()` at line 186) | The whole body sits in `try { ... } finally { ... }` from line 92 to the last line, so a cut anywhere is a parse error. No hash line. |
| 90-161.Z `scripts/gov/paste/90161Z-R41-round-r2.ps1` (same text as the `.txt` copy; 29 embedded files) | 16,250 | 1,434,549 (516,323 gzipped) | RADE engine `engine/rade_build.py` (445 lines), function `build()` ends with `rade_hash.add_line(head + contents(head, body) + body)` (line 352); 90-161.Z `scripts/build_paste_bundles.py` (151 lines) calls it | First line `# @@BUNDLE-HASH <sha256> @@` (docs/specs/bundle-hash.md, engine/rade_hash.py). The bundle checks its own hash in `Get-ScriptCheck` (engine/ps/05-installed.ps1), but that code sits in the engine parts after line 10,000 and "stops nothing" until a work-computer round (spec Q5). |
| RADE repo | no built bundle is committed in RADE itself | | the generator is the one place for all RADE apps | |

### Measurement: what runs if the paste is cut

Method: cut each bundle after line N (N spread over the file), and ask the PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseInput`) whether the prefix is a complete script. A parse-clean prefix runs (in ISE, F5 runs everything that parses); a parse error runs nothing. Script: a 15-line `parsecut.ps1` (run with `pwsh -NoProfile -File parsecut.ps1 <file> <samples>`).

| Bundle | Cut points tried | Parse-clean prefixes (these RUN) | Where |
|---|---|---|---|
| Ion-script.txt | 700 evenly spread + every line 1 to 130 | 0 of 700; in 1..130: lines 83 to 91 only | 83..91 = after the header comment and the three Settings assignments, before `try {`: runs three variable assignments, nothing else |
| 90161Z-R41-round-r2.ps1 (unchanged) | 650 evenly spread | 49 of 650 (7.5 %) | lines 24, 49, 74 (in the `#   line` Contents list: after `$buildId` and `$engineRelease` are assigned), then from line 3,943 on up to line 13,579 (83.6 % of the file); what these prefixes execute is traced below |
| 90161Z-R41-round-r2.ps1 + guard (prototype below) | 650 | 3 of 650 (lines 25, 50, 75: before the start block, in the Contents list) | no cut inside the body or after it runs the body |

What a parse-clean prefix executes (traced with the parser: top-level statements of the prefix, `trace.ps1`):

| Cut at line | Top-level statements | What runs |
|---|---|---|
| 3,943 | 23 | assignments only (no command call) |
| 10,334 | 59 | assignments only |
| 12,549 | 506: 380 assignments, 123 function definitions, 2 `if`, 1 `try` | the assignments and definitions, the bundle reading its own text (line 11,580) and `Get-ScriptCheck` (line 11,615: hash check, display only); no step, no file write |
| 13,579 (the last parse-clean cut found) | 585: 417 assignments, 163 function definitions, 3 `if`, 1 `try`, 1 pipeline | the above, plus `Select-App 0` (line 13,564), `Test-NiprDevice` (line 13,575), `Get-Date`: the engine start begins; no step ran in this prefix as far as the statements show |

So the measured hazard: in 7.5 % of the sampled cuts the text is a valid script that starts to run (up to the engine start at the end of the file) without telling the person that it is cut. What it would do between those cuts was traced for four cuts only; it did not write files in any of the four. A cut between 13,579 and the end, or inside Part 3, was not found parse-clean in the sample. Ion does not have the problem, because of its `try`/`finally`.

### Prototype (temp copy only)

Idea: put the whole body in one script block `$script:PasteBody = { ... }`, and run it (`. $script:PasteBody`, dot-sourced so the scope is the same) only from a block at the very end of the text, after that block has checked the text. The start block stores the expected line count of the whole text; the end block reads the text back (`$PSCommandPath`, else the ISE script pane, as the engine's `$script:selfText` already does), compares the line count and the existing `# @@BUNDLE-HASH` value, and throws before anything runs if they differ. A cut text never reaches the end block.

Start block (6 lines, inserted before the `# ==== Part 1` line; the line count is a fixed-width 6 digits so it does not change the count):

```powershell
# ==== Paste guard, start (GENERATED) ====
# The text below the next line is one script block. It runs only when the guard at the very end of this text has checked
# it. A paste that is cut short never reaches that end: nothing runs, and "Paste check: complete" does not show.
$script:PasteExpectedLines = 016278
Write-Host 'Paste check: started. Wait for the line "Paste check: complete". If it does not show, the paste is cut short: copy the whole text again.'
$script:PasteBody = {
```

End block (22 lines):

```powershell
}
# ==== Paste guard, end (GENERATED) ====
$pgText = ''
try { if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath -PathType Leaf)) { $pgText = [System.IO.File]::ReadAllText($PSCommandPath) } } catch { $null = $_ }
if (-not $pgText) { try { if ($psISE -and $psISE.CurrentFile) { $pgText = [string]$psISE.CurrentFile.Editor.Text } } catch { $null = $_ } }
$pgWhy = ''
if ($pgText) {
  $pgT = $pgText -replace "`r`n", "`n"
  $pgM = [regex]::Match($pgT, '^\s*# @@BUNDLE-HASH ([0-9a-f]{64}) @@\n')
  $pgRest = if ($pgM.Success) { $pgT.Substring($pgM.Length) } else { $pgT }
  $pgRest = ($pgRest -replace '(\n[ \t]*)+\z', '') + "`n"
  $pgLines = $pgRest.Split("`n").Count   # the lines of the whole text: the hash line, then the lines after it
  if ($pgLines -ne $script:PasteExpectedLines) { $pgWhy = 'this text has ' + $pgLines + ' lines, the build wrote ' + $script:PasteExpectedLines }
  elseif ($pgM.Success) {
    $pgSha = [System.Security.Cryptography.SHA256]::Create()
    try { $pgHex = -join @($pgSha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($pgRest)) | ForEach-Object { $_.ToString('x2') }) } finally { $pgSha.Dispose() }
    if ($pgHex -ne $pgM.Groups[1].Value) { $pgWhy = 'the text does not match the hash on its first line' }
  }
} else { Write-Host 'Paste check: this text cannot be read back here; only its end was reached.' }
if ($pgWhy) { throw ('Paste check: STOPPED, nothing ran: ' + $pgWhy + '. Copy the whole text again.') }
Write-Host 'Paste check: complete.'
. $script:PasteBody
```

Added lines: **28** (6 start + 22 end) per bundle. On the real 90-161.Z bundle: 16,250 lines became 16,278; the Contents list line numbers were shifted by 6 (the prototype did it with a regex; the generator must do it from the start block's size: `contents()` in rade_build.py computes `first` from `head`), and the first-line hash was recomputed (the guard text is inside the hashed part).

Where the generator would add it:
- RADE `engine/rade_build.py` `build()`: wrap `body` between start and end blocks before `rade_hash.add_line(...)` (line 352); `contents()` needs the start block's line count in `first`. One place, so every RADE app (90-161.Z and others) gets it.
- 33-332.Z `scripts/build_paste.py` `build()` (line 186): not needed for truncation (its `try`/`finally` is the guard); it has no hash line, so a line-count check alone would need the start/end blocks too.
- The engine's own `Get-ScriptCheck` (05-installed.ps1) and the guard would duplicate the self-text reading; the guard could reuse it or the check could be retired in the guard's favour (a choice for the Maintainer).

### Tests (stub body, `pwsh -NoProfile -File`)

Stub: a 313-line bundle (header hash line, a here-string, a function, 300 lines `Say-It 'body step N'`, a last line `Write-Host 'BODY RAN'`), guarded by the same transform (341 lines). Script `run.sh` runs five copies of the file:

| Copy | Unguarded stub: exit, body lines that ran | Guarded stub: exit, body lines that ran, what shows |
|---|---|---|
| full | 0, 301 | 0, 301; "Paste check: started" then "Paste check: complete." then the body |
| cut at 50 % | 0, 144 (half the body ran) | **1, 0**; PowerShell ParserError (`$script:PasteBody = {` is not closed); nothing ran |
| cut just before the end block | 0, 300 | **0, 0**; only the start line shows, no "complete" line, and nothing ran (exit 0: the file parses; this is the one case that is silent but safe) |
| one trailing space added on line 200 | 0, 301 | **1, 0**; "STOPPED, nothing ran: the text does not match the hash on its first line" |
| one letter changed on line 200 | 0, 300 | **1, 0**; same stop |

Real 90-161.Z bundle: the guarded text parses without error (0 parse errors, as the original); the real body was not run (it writes into a OneDrive path and needs Windows).

Not proven here (needs a Windows ISE round, spec Q5 of docs/specs/bundle-hash.md): that `$psISE.CurrentFile.Editor.Text` in the script pane returns the pasted text, that a body inside a dot-sourced script block behaves the same in ISE (`$script:` scope, here-strings, `$MyInvocation.MyCommand.ScriptBlock` fallback in 05-installed.ps1 differs), and the 1.4 MB parse time in ISE. A throw in ISE shows red text and does not close ISE (a bare `exit` could close it; the prototype throws).

### Candidate verdicts (trial 2)

| Option | Effect | Trade-off |
|---|---|---|
| Adopt the guard in the RADE generator | Closes the window of 7.5 % of sampled cuts (a valid, silent partial start) in 90-161.Z / RADE bundles; one 28-line block for all apps | A change in generated code; needs one Windows round; the cut-before-end case stays silent (no "complete" line is the signal) |
| Shrink: only the wrapper (no read-back, no hash compare) | 12 lines; nothing runs unless the end is reached | No message on a changed (not cut) text; relies on the existing hash check, which stops nothing yet |
| Keep | no work | 49 of 650 cut points of the 90-161.Z bundle are valid scripts that start without a message (traced: up to the engine start, no file write) |
| 33-332.Z | Keep: Ion is protected by its `try`/`finally` (0 of 700 cuts run, except the 3 Settings assignments) | adding a hash line would be a separate feature |

---

## Trial 3. Build-time static HTML (P2-4a, P2-4b)

### Where the client-side Markdown work is

| Repo | Client Markdown parsing | Runtime fetch | CSP `connect-src` today |
|---|---|---|---|
| 90-161.Z | `go.js` (389 lines): `parse()` (lines 264 to 273), `renderBody()` (221 to 258), `inl()` (35 to 40, regex for links, bold, code), `renderSecs()`, `card()`; draws `go.md` (195 lines, 31,349 bytes) as cards | `site.config.json`, `go.md` from raw.githubusercontent.com, and each round script (1.4 MB) for the Copy button (`preload()`) | `'self' https://raw.githubusercontent.com` |
| RADE | none. `index.html` has no Markdown parser; its intro comes from README.md at build time already (`scripts/build_site.py --write`, the `site:intro` markers). | `apps.json`, the manifest, the bundle text and `<bundle>.sha256.json` (for the hash display) | `'self' https://raw.githubusercontent.com` |

Also in 90-161.Z: `scripts/build_readme.py` already renders the same `go.md` to `TASKS.md` at build time (a static copy for computers where github.io is blocked).

### Comparison (same input: the real `go.md`)

Method: run the real `go.js` in node (the repo's own test technique: `vm.runInNewContext` with `window.GO_TEST`) to get the client HTML (53,696 bytes, 5,159 visible words); render the same `go.md` with python-markdown and with markdown-it-py; compare element counts and the visible words (buttons excluded) with `difflib.SequenceMatcher`. Scripts: `client_render.js`, `compare.py` (scratch, not committed).

| Output | h1 | h2 | h3 | p | ol | ul | li | strong | code | a | details | button | div | span |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| client (go.js) | 1 | 0 | 4 | 18 | 8 | 1 | 106 | 51 | 19 | 48 | 3 | 44 | 48 | 96 |
| python-markdown 3.11.3 | 1 | 3 | 0 | 20 | 0 | 1 | 57 | 51 | 19 | 0 | 0 | 0 | 0 | 0 |
| markdown-it-py 4.3.0, CommonMark, `html=False`, `linkify` | 1 | 3 | 0 | 67 | 8 | 1 | 103 | 51 | 19 | 47 | 0 | 0 | 0 | 0 |

Visible words (5,159 in the client):

| Library | Differing word runs | Words in the client that differ | Words in the library that differ | Word-sequence ratio |
|---|---|---|---|---|
| python-markdown | 94 | 63 | 54 | 0.9887 |
| markdown-it-py (html=False, linkify) | 51 | 63 | 7 | 0.9932 |

What the differences are:
- Same words, different structure: the client's cards (`details`/`summary` 3, `h3` 4, `button` 44, `div` 48, `span` 96: state chips, "Done 57 items", folder boxes with a Copy button, file cards with "Open as .txt" and "Copy script") are not Markdown. A library gives h2/h3 headings and lists only. The card layer (about 130 lines of `go.js`: `card`, `renderSecs`, `renderBody`'s folder, file and note rules, `fileCard`) would have to be rewritten as a build script (a markdown-it-py plugin or a post-render pass in Python) or stay in the page; the build-time step then keeps the same custom rules in Python instead of JavaScript.
- python-markdown does not make the nested lists the file uses (3-space indent): `ol` 0 against 8, and it does not link bare URLs without an extension: 0 links against 48.
- `Rounds\<round>` (two places in go.md): standard Markdown reads `\<` as an escape, so markdown-it-py (both `html=True` and `html=False` give the same text, `Rounds<round>`) loses the backslash; the client keeps it. python-markdown loses the `<round>` tag as well (`Rounds\ .`). `html=False` is not what fixes this; it is a hardening option (it keeps raw HTML in go.md out of the page).
- 1 to 2 words per line labels such as "opens:" (colon kept by the library) differ.

### CSP `connect-src 'none'`

Prototype: `build_static.py` renders `go.md` with markdown-it-py into a page with the CSP `default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'` and one external script (the page's own file). Served with `python3 -m http.server`, opened in Chrome 153 through playwright 1.63.0 (`node pw.js <url> <path to playwright>`). Result: the page rendered (1 h1, 103 li, 47 links), the script ran, and a test `fetch()` of the page's own address was **blocked** by the policy ("Connecting to ... violates the following Content Security Policy directive: connect-src 'none'"), as intended. Static page size: 39,321 bytes against 33,100 bytes for today's `index.html` plus the 22,268-byte `go.js` and the fetched `go.md`.

Consequence to weigh: with `connect-src 'none'` the page cannot fetch the round script for its Copy and Open-as-.txt buttons (today `preload()` fetches the 1.4 MB / 516 KB gzipped script from raw.githubusercontent.com, and RADE fetches apps.json, the manifest, the bundle and its hash file). Options: embed the script text in the page (page grows by 1.4 MB per round, and the page needs a rebuild and publish for each round, where today a push of the script is enough), or link to the `.txt` copy and drop the Copy button, or keep `connect-src 'self'` (the script served from the same site, no third-party host: smaller than today's policy but not 'none'). `connect-src 'none'` with go.md only (no script fetch) is possible for the task text alone.

Also: go.md is read at run time so a push to go.md shows after at most 5 minutes (the page says "GitHub can serve a copy up to 5 minutes old"). A static page changes at the publish of the Pages site; whether the Pages build runs on every push to main was not checked here.

### Candidate verdicts (trial 3)

| Repo | Retire | Shrink | Keep | Adopt |
|---|---|---|---|---|
| 90-161.Z `go.js` Markdown parts | | Shrink: a library does the lists, bold, code and links (`inl`, list handling: about 30 of 389 lines); the card layer stays | | Adopt build-time HTML: needs the card layer ported (about 130 lines), a rule for `\<` (escape it as `\\<` in go.md, or keep the text in a code span); `html=False` as a hardening option; saves the runtime fetch of go.md |
| RADE | | | Keep: no client-side Markdown exists; the intro is static already | |
| `connect-src 'none'` | | | | Possible for the task text; not possible while the round script is fetched at run time |

---

## Trial 4. 90-161.Z flows: builders and `pac solution` (P2-7a, P2-7b)

### Counts

| What | Count |
|---|---|
| Builder scripts | 4: `build_flow_package.py` 207 lines, `build_flow_payload.py` 151, `build_flow_solution.py` 435, `build_flow_solution_xml.py` 73 (866 lines) |
| Files under `flow/` | 25 (1.2 MB): 2 packages (.zip), 4 solution zips, 10 + 2 solution defs/test defs (.json), 2 package defs, `provisioning-payload.json`, 3 files of `export-sample/`, 1 README |
| Files with an `-rN` revision suffix (not counting docs/) | 75 files, 67,606 lines: scripts/gov 43, flow/solution/defs 10, samples 7, flow/solution 4, scripts/gov/paste 3, flow/packages 2, flow/solution/test-defs 2, flow/defs 2, scripts/gov/data 1, prompts 1 |
| Revision numbers on disk | r1 12, r2 9, r3 3, r4 6, r5 10, r6 4, r7 3, r8 2, r10 1, r11 7, r12 3, r14 15 |
| Base names with two revisions on disk at once | 0 (73 base names for 75 files; the older revision is deleted when a new one is built) |

Proof: `python3 revfiles.py 90-161.Z` (a 30-line scratch script); the builder line counts with `wc -l`.

### `pac solution` (official docs)

Source: Microsoft Learn, "pac solution" reference (`https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution`, fetched 2026-11-23). Commands listed there: add-license, add-reference, add-solution-component, check, clone, create-settings, delete, export, import, init, list, online-version, pack, publish, sync, unpack, upgrade, version. `pac solution pack --zipfile <zip> --folder <dir>` packs a folder of component files into a solution ZIP (SolutionPackager); it reads `Other\Solution.xml` and `Other\Customizations.xml` (legacy XML layout) or `solutions/*/solution.yml` (YAML layout, CLI 2.4.1 or later); it does not make those files from a flow definition. `unpack` is the reverse. `clone` makes a solution project from a solution in an environment (needs a signed-in environment). `init` makes an empty solution project from a publisher name and prefix. pac is **not installed** here and was not installed (the brief). Not tried: `dotnet`, the NuGet tool and `pac` on Windows; nothing about pac below was run.

### Map: builder step to pac command

| Builder step | Where | pac equivalent |
|---|---|---|
| Read flow def JSON, check action description length (over 256 characters fails) | `build_flow_solution.py` `load`, `check_action_descriptions` | none (domain check) |
| Make the workflow JSON of each flow (connection references, parameters, triggers, actions, run-token rewrite for a manual flow) | `workflow_json`, `run_token`, `json_name` | none: pac packs files you already have; the flow definition JSON stays authored here (or exported once with `pac solution export`/`unpack`) |
| Make `customizations.xml` and `solution.xml` (publisher, platform version, root components) | `build_flow_solution_xml.py` 73 lines, `workflow_entries`, `connection_reference_xml`, `env_definition_files` (about 60 lines) | partly: `pac solution init` writes a project with `Other/Solution.xml`; `pac solution clone`/`unpack` write real ones from an environment. The values the builder copies by hand from the R18 export (platform 9.2.26101.188, option prefix 89127) would come from a real export instead; needs a signed-in environment or a committed unpacked export |
| Environment variable definitions, connection reference XML | `env_definition_files`, `connection_reference_xml` | none to generate (hand-made files in the unpacked layout; the repo's notes say the first attempts failed on exactly these, R16 to R18) |
| Zip the files deterministically (fixed timestamps, stored, uuid5 IDs, CRLF text, `--check` compares with the committed zip) | `zip_solution`, `exported_text`, `guid`, `flow_guid` | `pac solution pack` makes a zip; whether its output is byte-identical between runs (timestamps, ordering) was not tested, so the repo's `--check` (compare committed zip with a fresh build) may need a different test (compare unpacked files) |
| Import test: a test solution for each test def (one harmless flow) | `test_jobs`, `test_variant` | `pac solution import` (needs an environment and a login) |
| Legacy "Import Package (Legacy)" zip (manifest.json + `Microsoft.Flow/flows/<id>/definition.json`, apisMap, connectionsMap) | `build_flow_package.py` (207 lines) | no equivalent on the `pac solution` page I read (it lists Dataverse solution commands only); I did not read the rest of the pac reference, so another `pac` command group may cover the legacy flow package: **unverified** |
| SharePoint provisioning payload (lists, fields, views, MERGE requests from `schemas/lists/*.json`) | `build_flow_payload.py` (151 lines) | **no equivalent** (a domain generator, not a packaging step) |
| Version number in the file name (`-r5`) | all builders, the `-rN` rule | `pac solution version` / `online-version` set the solution version inside `Solution.xml` (4-part version, today `1.0.0.1`); the file name itself stays a repo convention |

Summary of the map: of 866 builder lines, the XML/zip packaging part (about 130 to 180 lines: `build_flow_solution_xml.py`, `workflow_entries`, `connection_reference_xml`, `env_definition_files`, `zip_solution`, `exported_text`) maps to `init`/`pack` plus committed unpacked files; the flow definition and the connection pieces (about 300 lines) and the two other builders (358 lines) have no pac equivalent.

### One versioned module instead of `-r1`..`-r14` names (P2-7b)

75 files carry a suffix; the suffix is also inside the file (for example `Get-PartPath` builds `90161Z-T22-<name>-<Rev>.ps1`, and the bundle contents list names each file) and in doc and test references. A single versioned module would put a version in one manifest (a `.psd1` `ModuleVersion`) and the git history would hold older revisions. Not trialled in code (it changes how the work computer receives files: the bundle writes 29 named files). What the count says: 67,606 lines sit in suffixed files; 0 base names exist twice, so the suffix does not preserve history on disk, it only names the current one.

### Candidate verdicts (trial 4)

| Item | Retire | Shrink | Keep | Adopt |
|---|---|---|---|---|
| `build_flow_package.py` (legacy zip) | | | Keep: no pac equivalent; retire only if the legacy import path is dropped | |
| `build_flow_payload.py` | | | Keep (domain generator) | |
| `build_flow_solution.py` + `_xml.py` | | Shrink to the flow-definition part (about 300 lines) if the unpacked solution folder is committed and `pac solution pack` makes the zip | | Adopt `pac solution pack` for the zip only after a Windows or dotnet run proves a byte-stable zip and an accepted import |
| `-rN` file names | Retire the suffix in file names and put the version in one manifest | | Keep (the suffix names which file a round used) | |

Trade-offs: pac is a .NET tool (install route and platform support not checked here: **unverified**). Which commands need a signed-in environment: from the docs page, `clone`, `export`, `import`, `list`, `delete`, `publish`, `sync`, `online-version`, `upgrade` act on an environment; `pack`, `unpack`, `init`, `version` and `add-reference` read or write local files (my reading of the descriptions, not run). Nothing in the repo today needs a login to build.

---

## Trial 5. RADE window layout (P2-6a, P2-6b)

### Size and content of `engine/ps/window/05-alignment.ps1`

| Measure | Value |
|---|---|
| Lines | 406 (104 comment lines, 300 code lines) |
| Definitions (`$ui.<Name> = { ... }`) | 36 |
| `& $ui.Sc` (scale a pixel value) calls | 43 |
| `[math]::` calls (Max, Min, Round, Ceiling) | 35 |
| Mentions of `Margin` | 31; `New-Object System.Windows.Forms.Padding` 8 |
| `PreferredSize` 4, `MaximumSize` 3, `DrawToBitmap` 1 | |
| The window folder in total | 11 files, 1,910 lines |

Layout computations, grouped by what they do (lines by definition, from the 36 definitions):

| Group | Definitions | Lines | What it computes |
|---|---|---|---|
| Ink alignment: put the first drawn pixel of each text on one left edge | FitEdges, FitStepEdge, FitHead, RuleW, HeadPair, LeftIn | 42 | A label draws its text after a padding of about 1/6 em, so each control's left margin is set to (edge minus the measured ink start); the ink is measured by drawing the control into a bitmap (`DrawToBitmap`) and finding the first changed column |
| Row midpoint: parts of a row share one vertical midpoint | BarTop, LabelH, AlignTick, AlignRow, RowParts, AlignRows | 35 | top margins from the tallest part; half-pixel rounding |
| Width fit and wrap | FitBar, SentFonts, Raw, BreakAll, FitSent, FitRow, Apart | 60 | the bar takes the room beside the title (60 to 200 px at 100 %), long text breaks or ends in "...", rows wrap |
| Card inside the window, options | Squeeze, Rows, OptPlan, PaintOpt, FillOpts | 94 | shrink spacing to keep a card inside the window; plan and paint the option buttons |
| Measure, scale, self-check, card setup | Measure, Scale, ScaleKeep, LogScale, ScaleLines, LayLine, Show, ScriptWarn, SetRange, SetCard, ToFront, Say1 | 162 | the layout self-check (`$ui.Check`: no cut text, no overlap) and its SCALE line; set a card |
| Header comment | | 13 | |

Important fact for the mapping: the window is **Windows Forms** (System.Windows.Forms, Windows PowerShell 5.1), and it **already uses** `TableLayoutPanel` (cards: 03-card.ps1, 04-record-parts.ps1, 02-fixed-parts.ps1) and `FlowLayoutPanel`, with `AutoScaleMode = 'Dpi'` and `AutoScaleDimensions 96, 96` (01-setup.ps1 line 59). 05-alignment.ps1 is the pixel correction on top of those panels, not a layout built from nothing.

### Map to TableLayoutPanel and to WPF XAML

| Computation | TableLayoutPanel / WinForms | WPF XAML |
|---|---|---|
| Row midpoint (AlignTick, AlignRow(s), BarTop, LabelH: 35 lines) | A cell with `Anchor = Left` (no Top/Bottom) centres its control vertically in the cell; a row `SizeType.AutoSize`. Replaces the top-margin arithmetic where all parts live in one table row | `Grid` row with `VerticalAlignment="Center"` (one line per child) |
| Width fit and wrap (FitBar, FitSent, FitRow, BreakAll, Apart: 60 lines) | Column `SizeType.Percent` / `AutoSize` and `MaximumSize` for wrap; "bar takes the room that is left" is a `Percent` column with `MinimumSize` | `Grid` star columns (`*`), `MinWidth`, `TextWrapping="Wrap"`, `TextTrimming="CharacterEllipsis"` (the "..." rule is built in) |
| Card inside the window (Squeeze, OptPlan: 94 lines) | `AutoScroll` on the card panel, or Dock Fill with a table | `ScrollViewer` or `Viewbox` |
| Scale (Scale*, LogScale: 35 lines) | Already `AutoScaleMode Dpi`; `$ui.Sc` stays for values set in code; per-monitor awareness is a process setting (01-setup.ps1 calls `SetProcessDPIAware` and thread DPI context by P/Invoke) | Units are device-independent (96 per inch): no `Sc` calls; per-monitor DPI awareness is a process setting too (the host's manifest), which PowerShell and ISE decide, not the script |
| Ink alignment (FitEdges, FitHead, RuleW: 42 lines) | **No equivalent.** The padding is how GDI text draws a label; `UseCompatibleTextRendering`/`TextRenderer` flags (NoPadding) change it but the glyph's own side bearing remains; the file's comments record that a formula and a with/without-NoPadding measure both missed by 3 to 6 px (R24) | No 1/6 em text padding in WPF (`TextBlock` has none), so most of the correction goes away; the glyph side bearing is still there. Not measured here |
| Self-check (`$ui.Check`, LayLine, Show: about 40 lines inside the 162) | stays (it is a test of layout, in any toolkit) | stays, or UI Automation / render-to-bitmap compare |

Not tried: a rewrite or a prototype on Windows (nothing here can draw a Windows Forms or a WPF window). WPF under Windows PowerShell 5.1 needs an STA thread (ISE runs STA) and `Add-Type -AssemblyName PresentationFramework`; the existing bundle, the window tests and the 29-file write all assume WinForms. A WPF window is a rewrite of the window folder (1,910 lines), not of 05-alignment.ps1 alone.

### A 125 / 150 / 175 % DPI test the window CI could run (no build needed)

What exists already: the Windows job `.github/workflows/window.yml` runs `python tests/window_real.py window-out`, which draws each card of the sample bundle in the real window (windows-latest, Windows PowerShell 5.1), runs the layout self-check, and keeps one PNG per card. `tests/window_real.py` already has the runs `device150-half` (956 x 1081), `device125-full` and `device200-full`, made by a swap in the test copy: `device(k)` sets `AutoScaleDimensions` to `(96/k, 96/k)` so the form scales by k on the 96 dpi runner and sets `$ui.Dpi = $d * k`. Pass = "WIN closed=True", no "LAYOUT " line, a "SCALE" line, and no card scrolls except at the smallest size.

What a 175 % step needs: **one run line and one tuple**. In the `RUNS` list add `("device175-full", 0, "done", "0", "", False)`, and in the prefix loop (line 257) add `("device175-", device(1.75))`. The job would then cover 125, 150, 175 (and 200) %. Nothing else (no new script, no build). Cost: one more run of the driver in the 15-minute job (the time of one existing run was not measured here).

Limits to state: the swap simulates scaling by changing the form's scale factor and the engine's dpi value on a 96 dpi screen; it does not change the Windows display scaling, so it does not test per-monitor DPI changes (a window dragged between screens), real font hinting at 175 %, or how ISE's own DPI awareness affects the window. A real-scaling run would need the runner's display scaling changed (registry value and a new session), which was not tried and which I do not know to work on a hosted runner. A 175 % case also needs a size choice for the window ("" lets the engine pick), which is the Maintainer's design choice.

### Candidate verdicts (trial 5)

| Item | Retire | Shrink | Keep | Adopt |
|---|---|---|---|---|
| `05-alignment.ps1` | | Shrink: move the midpoint and width rules (about 95 lines of 406) into TableLayoutPanel cell settings in 03-card.ps1; keep the ink alignment (42), scale and the self-check | Keep as is (every rule records a measured defect of a real work-computer round) | WPF rewrite: removes most of the file, but replaces all 1,910 lines of the window and needs a new proof on the work computer |
| 175 % test | | | | Adopt: one `RUNS` line and one tuple in `tests/window_real.py` (a test file; the workflow file stays unchanged) |

---

## Trial 6. ICF-Source (read-only; trial only; P2-8a, P2-8b)

The repo is read-only: all reads and the prototype ran in a scratch copy of the built files. The incoming maintainer may own any change.

Note on names: there is no `questions.json` or `glossary.json` in `data/`; both are built outputs in `site/dist/`, made by `scripts/build_site_bank.py` (443 lines) and `scripts/build_glossary*.py` (403 + 62 + 209 + 275 lines) from the sources under `data/questions/` and `data/glossary/`.

### Raw character-offset spans

| What | Value |
|---|---|
| `site/dist/questions.json` | 1,979,688 bytes (359,619 gzipped), 1,357 questions |
| `site/dist/glossary.json` | 1,414,230 bytes (258,629 gzipped) |
| Spans in `questions.json` | **1,485** objects `{text, start, end}` in `questions[].keywords[]`, all in the stem, in all 1,357 questions (82,540 bytes of JSON in the file's own compact form; 98,824 with the `"keywords":` key), per block: B1 350, B2 329, B3 250, B4 253, B5 303 |
| Spans in `glossary.json` | 8,911 triples `[start, end, termSlug]` in `questionLinks`: stem 1,278, answers 3,927, rationales 3,706 (489,688 bytes; 1,333 questions have a link). These are produced by the build (`build_glossary_links.py` and the matcher), not authored: they are derived from the question text |
| Authored source of the keyword spans | `data/questions/**`: 49 JSON files hold 2,624 `{text,start,end}` objects (13,121,137 bytes of source JSON): exam 1,344, hard 542, b1 181, b2 169, b5 146, b3 120, root unit files 122. More span objects sit in revision, publication and quality files: across all of `data/` and `config/` 160 JSON files contain 10,301 objects with `start` and `end` |
| Integrity of the 1,485 keyword spans | 0 spans where `stem[start:end]` differs from `text`; 0 overlapping spans; 0 characters above U+FFFF (so Python and JavaScript string offsets are the same); 0 stems, answers or rationales that already contain `==` (no clash with the markup) |

Rationale and answer text sometimes sits in `textDictionary` (`{"$text": 0}` references); the prototype resolves them.

### Prototype: `==term==` markup to the same spans

Files: `proto.py` in scratch. The build step: scan the marked text with `==(.+?)==`, drop the markers, and record `{text, start, end}` with `start` = length of the clean text so far. To test it I generated the marked text from the existing spans (insert `==` around `stem[start:end]`) and rebuilt the spans from the markup, then compared with the originals.

| Test | Result |
|---|---|
| 20 sample questions (every 67th question: `B1-U2-Q015` to `B5-H-U6-Q040`), 23 spans | 0 questions differ, 0 spans differ (`text`, `start` and `end` all equal) |
| All 1,357 questions (1,485 spans) | 0 differ |
| Size effect | the keyword JSON arrays (82,540 bytes in the built file) leave the source; the markup adds 5,940 characters (4 per span) to the stems |

Example of the marked stem: "An airman carries his laptop ... tied to ==one central distribution system==. Each room's unit ==broadcasts the ...".

What this proves and does not: the markup and the offsets carry the same information for the current text, so the conversion is lossless. It does not prove the real build change: the source files and the revision-patch scripts (`apply_revision.py`, `apply_revision_edits.py`, `new_bank_*`, `build_exam_bank*`, `build_hard_bank.py`, the audit and quality scripts: 12 scripts mention `keywords`) would all read and write marked text instead of offsets, and an edit that changes a stem today must move offsets by hand or by script; the markup removes that. Glossary links are derived already, so for P2-8a only the 1,485 keyword spans are authored offsets.

### Block (B1 to B5) split: size estimate

Sizes, measured with the files' own compact serialization (`json.dumps(separators=(',', ':'), ensure_ascii=False)` reproduces `glossary.json` exactly and `questions.json` to 1 byte; the parts below add up to the file sizes: questions 1,966,350 + 13,323 other keys; glossary parts 1,414,110 of 1,414,230):

| Block | Questions | Question bytes | Keyword bytes | Glossary `questionLinks` | `answerTerms` | `questionEntry` | Glossary per-block total |
|---|---|---|---|---|---|---|---|
| B1 | 282 | 393,118 | 18,889 | 94,142 | 18,607 | 7,676 | 120,425 |
| B2 | 295 | 418,641 | 17,609 | 89,465 | 14,743 | 8,756 | 112,964 |
| B3 | 248 | 364,163 | 14,789 | 102,856 | 27,017 | 6,289 | 136,162 |
| B4 | 252 | 373,432 | 14,202 | 104,630 | 26,005 | 6,171 | 136,806 |
| B5 | 280 | 416,995 | 17,051 | 98,594 | 28,599 | 7,572 | 134,765 |

Not per block: `questions.json` outside the questions array 13,323 bytes (blocks, examForms, textDictionary, hardMode); `glossary.json` shared parts 772,985 bytes (698 entries 757,333, acronyms 13,743, docs 1,833; the entries carry excerpts from all five blocks: B1 300, B2 304, B3 237, B4 234, B5 288 excerpt records).

Estimate of the split (from these numbers, nothing was built): five question files of about 0.36 to 0.42 MB each (about 65 to 76 KB gzipped each, taking the whole file's ratio of 18 %) with a shared 13 KB part; the glossary stays one shared file of about 0.77 MB plus five per-block link files of about 0.11 to 0.14 MB (links + answerTerms + questionEntry). A learner who opens one block would fetch about 0.4 MB instead of 2.0 MB of questions (and the glossary parts still have to be fetched for the glossary view). Code touched: 60 files mention `questions.json` and 32 mention `glossary.json` (scripts, tests and `site/dist` modules, such as `data-load.mjs`, which fetches `./glossary.json` at line 61), so the split is a loader and a test change across about 60 files, not a data change alone. Cross-block features (the exam forms, the hard bank, the glossary's cross-block entries, any cache list of the site) were not traced here.

Open choice for the Maintainer on what P2-8a targets: the prototype covers the **1,485 keyword spans** (authored, `==text==` can carry them). The **8,911 glossary link triples** carry a term slug that `==text==` cannot hold, and they are derived by the build already; they are a different set (a `==text|slug==` markup, or leaving them derived, or a matcher change).

### Candidate verdicts (trial 6)

| Item | Retire | Shrink | Keep | Adopt |
|---|---|---|---|---|
| Offsets in the question source (P2-8a) | | | Keep (works, 0 integrity errors today) | Adopt `==term==` in the source with a build step that derives the 1,485 spans: lossless on all 1,357 questions; the risk is the 12 scripts and the revision files (10,301 span objects) that read offsets; covers the 1,485 keyword spans only, not the 8,911 link triples (see the open choice above) |
| Glossary link triples | Retire as stored data only if the build derives them in the browser (not tried); today they are already derived at build time | | Keep (8,911 triples, derived) | |
| Block split (P2-8b) | | | Keep one file: 1.98 MB (360 KB gzipped) loads once | Adopt a split for load size: about 0.4 MB per block; costs a loader and test change across about 60 files |

The ICF-Source work is trial only: the result is for the Maintainer; the incoming maintainer may own the change.

---

## Proof commands (summary)

```
# trial 1
pip install --ignore-installed pip cyclonedx-bom pip-tools markdown markdown-it-py
cyclonedx-py requirements 90-161.Z/requirements.txt --of JSON -o sbom.json
pip-compile --generate-hashes --strip-extras -o req.hashed.txt 90-161.Z/requirements.txt
curl -L -o codeql.zip https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip
codeql database create db --language=python --source-root=<repo copy>      # 11 to 19 s per repo
codeql pack download codeql/python-queries                                   # refused by the proxy
curl -L -o bundle.tgz https://github.com/github/codeql-action/releases/latest/download/codeql-bundle-linux64.tar.gz   # worked
codeql database analyze db-<repo> python-code-scanning.qls --format=sarif-latest --output=res.sarif   # 22 to 27 s per repo
bandit -r <repo>/scripts -ll                                                 # 0 results in all four
# trial 2
pwsh -NoProfile -File parsecut.ps1 <bundle> 650        # parse-clean prefixes
python3 guard.py <bundle> <guarded>                    # adds 28 lines, re-hashes
bash run.sh <guarded stub>                             # full, 50 %, cut before end, 2 tampered copies
# trial 3
node client_render.js go.js go.md > client.html ; python3 compare.py go.md client.html
python3 build_static.py go.md site ; node pw.js http://127.0.0.1:8765/index.html <playwright path>
# trial 4
python3 revfiles.py 90-161.Z ; wc -l scripts/build_flow_*.py
# trial 5
grep and count in engine/ps/window/05-alignment.ps1; read tests/window_real.py RUNS and device()
# trial 6
python3 spans.py icf ; python3 proto.py icf ; python3 src.py icf
```

The scratch scripts (`parsecut.ps1`, `guard.py`, `run.sh`, `client_render.js`, `compare.py`, `build_static.py`, `pw.js`, `revfiles.py`, `spans.py`, `proto.py`, `src.py`) are not in the repo (this file is the only allowed file); each is 15 to 110 lines and can be added on request.

## Limits of these trials

- CodeQL: findings and local run times are measured (Python, JavaScript, actions); the run time in GitHub Actions is an estimate. Each finding was listed, not judged. The query packs came from the codeql-action bundle (a first attempt with the CLI-only zip and `codeql pack download` failed on the proxy).
- Windows-only behaviour (ISE script pane text, the real 90-161.Z bundle running, a 175 % window, WPF, `pac`): not run; the container has PowerShell 7.4.6 on Linux only.
- The guard was proven on a stub body and by parsing the real bundle; the real bundle body was not run.
- pac commands were read from the docs only.
- The ICF prototype used the built `site/dist` files; the source files under `data/questions/` were counted but not rewritten.

## Installs and deviations

Installs beyond the brief's list (cyclonedx-bom, pip-tools, markdown/markdown-it-py, CodeQL CLI), all in this container, none in any repo:
- `bandit` 1.9.4 (a comparison baseline; its dependencies PyYAML 6.0.3, rich 15.0.0, stevedore 5.10.0, Pygments 2.21.0 came with it), `linkify-it-py` 2.2.0 and `mdit-py-plugins` 0.7.0 (the markdown-it-py link rule), the CodeQL bundle `codeql-bundle-linux64.tar.gz` (696,138,291 bytes, release 2.27.5, ships the query packs), Google Chrome and playwright (already installed in the image, not installed by me).
- `pip download playwright` (a try to see if the Python package could be had) wrote two wheel files into this worktree's top folder (`greenlet-3.5.6-*.whl`, `playwright-1.65.2-*.whl`); they were not installed and I deleted both before the commit. The committed diff holds only this file.
- Full output of the first install (`pip install --ignore-installed pip cyclonedx-bom pip-tools markdown markdown-it-py`): arrow 1.4.0, attrs 26.1.0, boolean.py 5.0, build 1.6.1, chardet 7.7.0, click 8.5.0, cyclonedx-bom 9.0.0, cyclonedx-python-lib 11.12.0, defusedxml 0.7.1, fqdn 1.6.0, idna 3.19, isoduration 20.11.0, jsonpointer 3.12, jsonschema 4.26.0, jsonschema-specifications 2025.9.1, lark 1.3.1, license-expression 30.4.4, lxml 6.1.3, markdown 3.11.3, markdown-it-py 4.3.0, mdurl 0.1.2, packageurl-python 0.17.6, packaging 26.3, pip 26.3, pip-requirements-parser 32.0.1, pip-tools 7.7.0, py-serializable 2.2.0, pyparsing 3.3.3, pyproject_hooks 1.3.3, python-dateutil 2.9.0.post0, referencing 0.37.0, rfc3339-validator 0.1.4, rfc3986-validator 0.1.1, rfc3987-syntax 1.1.0, rpds-py 2026.6.3, setuptools 84.2.1, six 1.17.0, sortedcontainers 2.4.0, tzdata 2026.6, uri-template 1.3.0, webcolors 25.10.0, wheel 0.48.0. pip warned that conan 2.32.0 requires python-dateutil below 3 and an installed python-dateutil 4.0.0 conflicts; the install itself ended with python-dateutil 2.9.0.post0. Pip 24.0 (Debian) could not be uninstalled in place, hence `--ignore-installed`.
- Network use: github.com release assets (CodeQL CLI zip, CodeQL bundle), learn.microsoft.com (the `pac solution` page), PyPI (packages). Requests refused by the proxy: the GitHub API, the CodeQL source archive, `ghcr.io` blobs.

Claims taken from recall and not verified in this session (each is marked in the text where used): the CodeQL licence rule for private repos; whether a Pages build runs on every push to main; pac install route and platform support; which pac command groups beyond `pac solution` exist.
