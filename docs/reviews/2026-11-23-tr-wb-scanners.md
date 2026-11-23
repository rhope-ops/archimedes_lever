# Tool retirement R4, group W-B: scanner trials (content check, instruction check)

Evidence only. This file decides nothing: each "verdict option" is a candidate with its trade-offs, for the Maintainer.
Written 2026-11-23 by a worker session (branch `claude/tr-wb-scanners`) for step R4 of
[2026-11-23-tool-retirement-research-plan.md](2026-11-23-tool-retirement-research-plan.md) (group W-B) and step 2 of
[2026-11-23-tool-retirement-prompt.md](2026-11-23-tool-retirement-prompt.md).

Data rules kept: no word of the name denylist, no secret, no real address or number is in this file. Findings of the
custom tool come masked from the tool itself; findings of the standard tools were reduced to rule, file and line at
run time (gitleaks `--redact`; trufflehog raw fields dropped in memory; detect-secrets hashes dropped). Every seeded
value was assembled at run time in a temporary copy, so none appears in a command or here. Everything is counts per
rule and file:line.

## 1. Setup

### 1.1 Versions and install

| Item | Value |
|---|---|
| gitleaks | v8.30.1 (module github.com/zricethezav/gitleaks/v8; the version the repos' own CI pins), built with Go 1.26.11 |
| trufflehog | v3.100.1 (module github.com/trufflesecurity/trufflehog/v3, built from the module zip), Go 1.26.0; the binary prints `dev` |
| detect-secrets | 1.5.0 (PyPI, in a venv) |
| Vale | v3.28.1 (module github.com/vale-cli/vale/v3), built with Go 1.27.4 |
| Go toolchain | 1.24.7 installed; 1.26.0, 1.26.11, 1.27.4 fetched by `GOTOOLCHAIN=auto` from proxy.golang.org |
| Python / OS | 3.13.18, Linux x86_64, 4 cores, 15 GB |

Install deviation (reported, not hidden): the brief allowed GitHub release binaries. github.com and api.github.com answered
HTTP 403 ("GitHub access to this repository is not enabled for this session") for the three tool repositories, so no
release binary could be fetched. The three Go tools were built from the Go module proxy instead (`go install` or `go build`
of the module zip, `GOPROXY=https://proxy.golang.org`). Same upstream source and tags; the binaries are not the signed
release artifacts, and gitleaks/Vale print no version string (versions above are from `go version -m`). Nothing else
was installed; the 403 was not worked around beyond using the module proxy and PyPI.

### 1.2 Repos, commits and history depth

Same commit for every tool. The four clones were copied to a temporary folder (nothing was written in them); the kit
was cloned from this worktree at the same HEAD. All five repos are complete (not shallow); history scans cover every
commit reachable from HEAD.

| Repo | HEAD | Tracked files | Commits scanned (history depth) | Tier | `skip:` lines | Allow strings | `block:` lines |
|---|---|---|---|---|---|---|---|
| kit | `641023e` | 256 | 570 | minimum | 0 | 0 | 0 |
| RADE | `a99ba73` | 243 | 709 | DoD | 3 | 5 | 0 |
| 90-161.Z | `91ccb0c` | 442 | 1371 | DoD | 10 | 12 | 0 |
| 33-332.Z | `6cbc517` | 157 | 252 | DoD | 2 | 3 | 1 |
| ICF-Source | `02a7ed2d` | 3376 | 2548 | DoD | 9 | 38 | 0 |

Allow-string and skip counts are the repo's `.check` lines (the Maintainer's "allowed although it looks like a
finding" and "not scanned" decisions). The content tool reports 0 or 1 finding per repo with them; most differences
below come from what they hide, so each result is given twice: as configured, and raw (only the `profile:` and
`block:` lines kept: the tier, no allow strings, no skips).

### 1.3 What was run

Custom tool: `scripts/check.sh --content --all` (working tree) and `--range HEAD` (history: commit identity, message,
added lines), kit script of this HEAD, run inside each repo. Three variants: A as configured; B the repo's own
`scripts/check.sh` (own kit version, own local finders in RADE and 90-161.Z); C raw. Raw (C) is the base for overlap.

Standard tools, each in two configurations, working tree (`dir`/`filesystem`) and full history (`git`):

- **default**: the tool's own rules, nothing added. gitleaks with `--config` of `[extend] useDefault = true` (so a repo's own
  `.gitleaks.toml`, present in 90-161.Z, does not apply); trufflehog `--no-verification` (no call to any provider API);
  detect-secrets `scan --all-files` with default plugins and filters.
- **custom**: the same plus rules that mirror the content tool's checks, from one config per tool (sizes in 2.7).
  - gitleaks: 23 `[[rules]]` ported from the kit's regular expressions (RE2 has no look-around, so boundary classes are
    part of the match and the OpenAI rule lacks the "upper-case and digit" look-aheads), a rule allowlist for the reserved
    example addresses, one path-only rule for the `block:` globs, and one rule, generated at run time, for the names and terms.
  - trufflehog: 9 `custom_detectors` (regex + keywords) and one generated for names and terms.
  - detect-secrets: 6 plugin classes (`RegexBasedDetector` subclasses) and `--disable-filter` for two heuristic filters
    (`is_not_alphanumeric_string`, `is_sequential_string`), which otherwise drop digit-only phone, SSN and DoD-ID shapes.
  - Names and terms (the denylist). Mechanism: an environment variable (newline or comma separated) is read at run time
    and turned into one case-insensitive whole-word alternation: a TOML rule printed by a generator for gitleaks, a YAML
    detector for trufflehog, an in-memory regex in the plugin for detect-secrets. The real list was never put into a
    gitleaks or trufflehog config; the trial used 3 invented stand-in words (`STANDIN_DENYLIST`). Only the detect-secrets
    plugin ran with the real `PII_GUARD_DENYLIST` (in memory, output reduced to file and line) to measure the name check
    on the five repos (2.3).

Units of comparison. gitleaks and the content tool: one finding = class + file + line. The kit counts lines with
`str.splitlines()` (it also splits at form feed and a few other marks), the standard tools count `\n`; the kit's line
numbers were converted before comparing. trufflehog (a custom detector reports at most one result per chunk and detector,
with unreliable line numbers; see 2.3) and detect-secrets (one result per distinct value and file) are compared at class + file.
Standard findings in files that git does not track (the `.git` folder samples) were dropped. Times: custom tool times are
serial runs; standard-tool times in 2.2 are a serial pass on an otherwise idle machine; times in other tables ran
beside other jobs and are marked.

## 2. Pair 1: content check vs gitleaks, detect-secrets, trufflehog

### 2.1 The custom tool on the five repos (working tree)

| Repo | A as configured | B own script | C raw total (no `unscanned`) | C raw by kind | C `unscanned` | C after `skip:` lines | C after skips and allow strings (approx.) | Time A, s |
|---|---|---|---|---|---|---|---|---|
| kit | 0 | 0 | 0 | 0 | 0 | 0 | 0 | n/a |
| RADE | 0 | 0 | 27 | milhost 27 | 19 | 27 | 0 | n/a |
| 90-161.Z | 1 | 0 | 136 | email 18, marking 16, milhost 100, phone 2 | 19 | 88 | 1 | n/a |
| 33-332.Z | 0 | 0 | 103 | email 12, marking 17, milhost 73, phone 1 | 1 | 47 | 0 | n/a |
| ICF-Source | 0 | 0 | 28299 | marking 574, milhost 249, name 27463, phone 13 | 158 | 28265 | 0 | n/a |

Judgement of the one finding of variant A (90-161.Z, kind milhost, `docs/reviews/2026-11-12-pii-guard-history.md:17`):
variant B (the repo's own, older script and local finders) passes the same tree, so it is a difference between the kit
script of this HEAD and the repo's script copy, not a new leak. "Approx." means a raw finding is dropped when its line
contains an allow string (the kit compares the exact found value; the line test can only over-suppress).

What the raw numbers show: the tool's output on these repos is dominated by DoD-tier host and marking checks on
published reference text (milhost, marking) and by allow-listed names in ICF's exam data (name: the denylist matches
4 and 5 character words in 1,221 files). The tool finds no secret and no SSN in any repo, raw or configured.

### 2.2 Standard tools, default rules

| Repo | gitleaks tree / history | trufflehog tree / history | detect-secrets tree | Time s (serial): gitleaks / trufflehog / detect-secrets |
|---|---|---|---|---|
| kit | 0 / 0 | 0 / 0 | 7 | n/a / n/a / n/a |
| RADE | 0 / 1 | 0 / 0 | 9 | n/a / n/a / n/a |
| 90-161.Z | 3 / 11 | 4 / 4 | 570 | n/a / n/a / n/a |
| 33-332.Z | 0 / 1 | 0 / 0 | 6 | n/a / n/a / n/a |
| ICF-Source | 2 / 17 | 4 / 17 | 79410 | n/a / n/a / n/a |

Rules that fired (tree, then history): gitleaks `generic-api-key` only (hashes in lock files, `workflowKey` and `beaconToken`
values, a base64 field of a JSON data file); trufflehog `Imagga`, `Box`, `Circle`, `ProtocolsIO` (base64 images, a gzip file, a
SHA-256 field) and in ICF history `NpmToken`, `SnykKey`, `URI`; detect-secrets `Hex High Entropy String`, `Base64 High
Entropy String`, `Secret Keyword`, `AWS Access Key`.

False positives judged from the file:line context (masked, long tokens shown as `<tok>`):

- Every default-rule finding of every standard tool in the tree and in history was judged a false positive: 0 true
  findings in 5 repos. gitleaks: SHA-256 values keyed by file names in `.check.lock` and `scripts/rade.lock.json`,
  a workflow id in a Power Automate JSON file, a version hash in `site/dist/questions.json`, and the public analytics
  beacon identifier in ICF's page code. trufflehog: base64 images, a gzip file, a SHA-256 field, the ICF token-log CSV rows
  (`sessions/*.csv`, first column a hash) and a fake credentialed URL in a test fixture. detect-secrets: commit hashes,
  base64 logos and embedded files, test constants; its 2 `AWS Access Key` hits in 90-161.Z sit inside a long base64 blob.
- Counts judged false positive / total: gitleaks tree 3/3 (90-161.Z) and 2/2 (ICF), history 1/1, 1/1, 11/11, 17/17 (RADE,
  33-332.Z, 90-161.Z, ICF); trufflehog tree 4/4 (90-161.Z) and 4/4 (ICF), history 4/4 and 17/17; detect-secrets tree 7/7
  (kit), 9/9 (RADE), 570/570 (90-161.Z, judged by its 20 rule-and-file groups), 6/6 (33-332.Z), 79,410/79,410 (ICF-Source: 79,403 hex-entropy hits in 302
  files, mostly JSON data with hash fields; 6 base64 hits that are document ids; 1 keyword hit on a sample password label).
- The four repos that run gitleaks in CI (`security.yml`, `detect --no-git`) already avoid the history false positive on
  `.check.lock`; 90-161.Z carries a `.gitleaks.toml` allowlist for its lock file. Both are evidence of the false-positive
  cost of the default rules, not of the tools' recall.

### 2.3 Standard tools with custom rules vs the raw custom tool (working tree)

Format: matched / only-custom / only-standard-custom-rules (the custom tool's raw findings, minus `unscanned`). "Only-standard"
counts only findings of the added rules; default-rule findings are in 2.2.

| Repo | Custom raw findings | gitleaks | trufflehog | detect-secrets |
|---|---|---|---|---|
| kit | 0 | 0 / 0 / 1 (finding) | 0 / 0 / 2 (file) | 0 / 0 / 1 (file) |
| RADE | 27 | 26 / 0 / 0 (finding) | 11 / 0 / 0 (file) | 11 / 0 / 0 (file) |
| 90-161.Z | 136 | 130 / 0 / 20 (finding) | 42 / 0 / 4 (file) | 42 / 0 / 0 (file) |
| 33-332.Z | 103 | 99 / 0 / 17 (finding) | 14 / 0 / 0 (file) | 14 / 0 / 0 (file) |
| ICF-Source | 28299 | 734 / 11 / 169 (finding) | 0 / 265 / 0 (file) | 264 / 1 / 1624 (file) |

Reading it:

- gitleaks with ported rules reproduced every raw finding of the content tool in the 5 repos (only-custom 0 where it ran),
  at line level. Its only-standard findings are explained by 3 differences, none a leak: (a) a `.mil` host inside a mail
  address (the kit counts the address once; gitleaks fires on the address rule and the host rule); (b) gitleaks decodes
  percent-encoded text, so `%40` in a URL became an address (2 findings in 33-332.Z, false positives); (c) a marking phrase
  split over two lines ("FOR OFFICIAL" / "USE ONLY"): the kit is per line, gitleaks matches across the break (judged real marks, 3+3).
- trufflehog custom detectors: each detector yields at most one result per chunk, whatever the number of matches, and the
  line numbers of custom results are not reliable (in a 19-line seeded file the results sat on lines 6, 14, 14 and 18).
  It finds at least one hit in every file that the content tool flags (file level: only-custom 0), but its counts are lower
  bounds, so a count compare is not valid.
- detect-secrets plugins: found the matching files for the classes it has; the dedupe per value and file lowers the counts, and its
  only-custom entries are repeated values (the same host many times in a file) rather than missed files in the cases checked.
- Name check on real data: see the table below. The stand-in rules of gitleaks and trufflehog were not measured on real names
  by design (1.3); name findings are left out of the overlap counts above for every tool.

| Repo | Content tool raw name findings | in files | detect-secrets plugin (real list, in memory): files | files matched | only-custom files | only-standard files |
|---|---|---|---|---|---|---|
| kit | 0 | 0 | 0 | 0 | 0 | 0 |
| RADE | 0 | 0 | 0 | 0 | 0 | 0 |
| 90-161.Z | 0 | 0 | 0 | 0 | 0 | 0 |
| 33-332.Z | 0 | 0 | 0 | 0 | 0 | 0 |
| ICF-Source | 27463 | 1221 | 1226 | 1219 | 2 | 7 |

Only ICF-Source has any raw name finding (4 and 5 character words in 1,221 files; all suppressed by that repo's allow strings: 0 as
configured). The four other repos have none, so the name check is untested on real data there.

### 2.4 History (full depth)

| Repo | Commits | Custom `--range HEAD` as configured | by kind | Custom raw | gitleaks git (custom rules) | trufflehog git (custom rules) | gitleaks vs raw, class+file: M/OC/OS | trufflehog vs raw, class+file: M/OC/OS |
|---|---|---|---|---|---|---|---|---|
| kit | 570 | 0 | 0 | 0 | 3 (1 files) | 6 (1 files) | 0 / 0 / 1 | 0 / 0 / 1 |
| RADE | 709 | 0 | 0 | 61 | 65 (14 files) | 48 (13 files) | 13 / 0 / 0 | 13 / 0 / 0 |
| 90-161.Z | 1371 | 9 | milhost 8, name 1 | 307 | 334 (76 files) | 317 (71 files) | 79 / 4 / 0 | 67 / 16 / 9 |
| 33-332.Z | 252 | 0 | 0 | 185 | 199 (17 files) | 180 (17 files) | 19 / 2 / 1 | 19 / 2 / 1 |
| ICF-Source | 2548 | 1150 | email 379, marking 1, name 770 | 50006 | 0 (0 files) | 2881 (294 files) | 0 / 1818 / 0 | 294 / 1524 / 16 |

History-only checks of the content tool that no standard tool has: the commit author and committer identity, the commit
message, and a changed file that cannot be read (kind `unscanned`). In ICF the as-configured history run reports
1,155 findings: 789 in commit author and committer lines (373 non-reserved addresses, in 194 commits; 416 denylist names),
20 denylist names in commit messages, and 346 in added lines. gitleaks and trufflehog scan patches only, so the 809 findings in
commit identity and messages are only-custom (probed on a seeded commit message and a seeded author address: neither tool reports them).

### 2.5 Seeded defects (temporary copy of 33-332.Z with its own `.git`)

23 invented items were planted and committed in the copy (18 lines in one file, one blocked file name, one binary file, one
key added in one commit and deleted in the next, a commit message and a commit author). The custom tool ran with
stand-in word lists in place of the real lists (`PII_GUARD_DENYLIST`, `CHECK_TERMS` set for that process only). Y = the
tool reports the item; "-" = not reported; n/a = the tool does not scan that place. The 5 items the brief asked for are
S01 (address), S03 (phone), S04 (AWS-style key), S05 (GitHub-style token), S19 (blocked file name).

| Item | Kind | Custom: tree | Custom: history | gitleaks default | gitleaks custom rules | trufflehog default | trufflehog custom | detect-secrets default | detect-secrets custom |
|---|---|---|---|---|---|---|---|---|---|
| S01-email-real-shape | email | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S02-email-example-invalid | email-reserved | - | - | - | - | - | - | - | - |
| S03-phone | phone | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S04-aws-key | secret | Y | same as tree (history output has no line) | Y | Y | - | Y | Y | Y |
| S05-github-token | secret | Y | same as tree (history output has no line) | Y | Y | Y | Y | Y | Y |
| S06-ssn | id | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S07-name-standin | name | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S08-term-standin | term | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S09-milhost | milhost | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S10-marking | marking | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S11-dodid | dodid | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S12-slack | secret | Y | same as tree (history output has no line) | - | Y | - | Y | Y | Y |
| S13-stripe | secret | Y | same as tree (history output has no line) | Y | Y | Y | Y | Y | Y |
| S14-privkey | secret | Y | same as tree (history output has no line) | - | Y | - | Y | Y | Y |
| S15-google | secret | Y | same as tree (history output has no line) | Y | Y | - | Y | - | Y |
| S16-anthropic | secret | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S17-gitlab | secret | Y | same as tree (history output has no line) | Y | Y | Y | Y | Y | Y |
| S18-openai | secret | Y | same as tree (history output has no line) | - | Y | - | Y | - | Y |
| S19-blocked-file | blocked | Y | Y | - | Y | - | - | - | - |
| S20-unscanned-binary | unscanned | Y | Y | - | - | - | - | - | - |
| S21-history-only-aws | secret | n/a | - | Y | Y | - | Y | n/a | n/a |
| S22-email-in-commit-message | email | n/a | Y | - | - | - | - | n/a | n/a |
| S23-email-as-commit-author | email | n/a | Y | - | - | - | - | n/a | n/a |

How to read the table. Standard-tool columns for S01-S18 come from one file per item (a neutral line, the item, a neutral line),
because trufflehog reports one custom result per chunk and detector and unreliable lines when several items sit in one file;
in the single shared file trufflehog's custom detectors reported only the first hit of each detector (S12, S14, S15, S16, S18 were
not reported there although each is found alone). The custom tool's columns come from the shared file.
Notes per item:

- S02 (`.invalid` address, the example in the brief): not reported by the custom tool by design (its `ALLOWED_EMAIL` exempts
  example.com/.org/.net and the reserved TLDs .example, .invalid, .test, .localhost). The brief expected a catch; S01, a
  non-reserved invented address, is the item that tests the email check. Mismatch listed in section 4.
- S07 and S08 (name and term, stand-in words): the standard tools reach them only through the generated rule; S08 uses the
  same mechanism as S07 (a second list for terms was not set up).
- S04 (AWS-style key): gitleaks default reports it under `generic-api-key`, not `aws-access-token`; trufflehog default does
  not report an access key id without its secret key; detect-secrets default reports it.
- S19 (blocked file name `PIIScan-*`, from the repo's own `block:` line): only a gitleaks path-only rule caught it, in `dir` and
  `git` mode. trufflehog and detect-secrets have no rule type for a file name. The seed file first did not enter the
  tracked set because the repo's `.gitignore` also lists `PIIScan-*`; it had to be added with `git add -f`. The content tool
  tests tracked, pushed and named files, so an ignored file never reaches it.
- S20 (binary file, DoD `unscanned` check): no standard tool reports it; gitleaks, trufflehog and detect-secrets skip binary files silently.
- S21 (key added then deleted): found by both history modes (gitleaks, trufflehog) and the custom `--range`; the working-tree scans cannot.
- S22, S23 (address in a commit message, in a commit author): only the custom tool.

### 2.6 Coverage of the custom checks

Y = 11 checks of the content tool (its docstring list: email, phone, id, secret, name, term, blocked, milhost, marking,
dodid, unscanned). Two more behaviours are listed apart: commit identity and message scanning, and the settings semantics.
"Covered" = the seeded item of that check was reported (single-file test, 2.5) and the real-repo overlap in 2.3 held.

| Check | Default rules only (best of the three) | gitleaks + custom rules | trufflehog + custom detectors | detect-secrets + plugin |
|---|---|---|---|---|
| email | no (0 of 1 seeded) | yes | yes | yes |
| phone | no | yes | yes | yes (2 filters off) |
| id (SSN shapes) | no | yes | yes | yes (2 filters off) |
| secret (10 token shapes; 9 seeded) | partial: gitleaks 5 of 9 (aws via generic rule, github, gitlab, google, stripe), detect-secrets 6 of 9, trufflehog 3 of 9 | yes, 9 of 9 | yes, 9 of 9 (one result per chunk and detector) | yes, 9 of 9 via plugin |
| name (denylist) | no | yes (generated rule) | yes (generated detector) | yes (plugin; ran with the real list) |
| term | no | yes (same mechanism) | yes | yes |
| blocked (`block:` file names) | no | yes (path-only rule) | no | no |
| milhost (DoD) | no | yes | yes | yes |
| marking (DoD) | no | yes (phrase may cross lines) | yes | yes |
| dodid (DoD) | no | yes | yes | yes (2 filters off) |
| unscanned (DoD) | no | no | no | no |

Count: with custom rules, gitleaks covers 10 of 11 checks, trufflehog 9 of 11 (not blocked, not unscanned), detect-secrets 9 of 11
(not blocked, not unscanned). With default rules only, 1 of 11 is covered in part (secret: gitleaks 5 of 9 seeded shapes, detect-secrets 6 of 9,
trufflehog 3 of 9 in the seeded run). Uncovered by every standard tool: unscanned (binary or oversize file in the DoD tier);
commit author, committer and message scanning; the `.check` semantics (exact-string allow list, `skip:` and `block:` globs in
one file, tier lines, read from the base branch in the Action); the PreToolUse hook mode (`--hook`, scanning a tool call's input);
masked output by design. `gitleaks stdin` could cover the `--stdin` mode; it was not tried.

### 2.7 Standard-tool configuration needed, and size

| Tool | Config written for the trial | Size | Still needed to match the custom tool | Run time s (serial, working tree): kit / RADE / 90-161.Z / 33-332.Z / ICF |
|---|---|---|---|---|
| content tool (custom) | scripts/check_content*.py (+ finders, hook, scan, settings) | 1,457 lines (tests 1,220) | - | n/a / n/a / n/a / n/a / n/a |
| gitleaks custom rules | one TOML file + generator for names | 99 + 13 lines | per-repo allowlist generated from `skip:` globs and allow strings (path and regex allowlists); block globs to path rules; a tier switch (DoD rules on or off); `--redact`; run in two modes (`dir`, `git`) | n/a / n/a / n/a / n/a / n/a |
| trufflehog custom detectors | one YAML file + generator | 39 + 11 lines | `--no-verification` and `--results` flags; `--exclude-paths` file for skips; no exact-string allow list (only regex excludes per detector); JSON post-filter to drop raw secrets before they reach a log | n/a / n/a / n/a / n/a / n/a |
| detect-secrets plugin | one plugin file | 73 lines | a baseline file for allowed values (its audit step), `--exclude-files` for skips, 2 filters disabled; plugin file must be on the scan path; not a history tool | n/a / n/a / n/a / n/a / 1215 (run beside other jobs) |

Times for detect-secrets are with default plugins. ICF: default plugins 1,215 s (beside other jobs); the plugin-only run (all default plugins off, used for the ICF overlap and name check) 252 s.
Run times for the history modes (beside other jobs): gitleaks git default 4-30 s for the four small repos, 652 s for ICF;
trufflehog git default 6-8 s and 43 s; content tool `--range HEAD` as configured 5-40 s and 597 s for ICF (raw: 359 s).

### 2.8 Candidate verdict options for the content check (not decided)

The research plan fixes the proof (same defects found, mutants killed equal or higher, CI green, custom lines fall). This trial
measured defect overlap only; mutant counts were not measured.

| Option | What it means here | Trade-offs from the evidence |
|---|---|---|
| Retire | gitleaks (custom rules) replaces the content tool | Loses 1 of 11 checks outright (unscanned) and the history identity and message scan (809 findings in ICF history: 789 in author and committer lines, 20 in messages), the hook mode, the base-branch settings read and the `.check` semantics unless rebuilt as config and glue. Gains a maintained engine, `git` mode, decoding of encoded text, a path rule for blocked files. The glue (generator, allowlist builder, redaction wrapper, two modes) is code that stays. The RE2 port had to drop the look-around of 3 rules (phone boundaries, milhost, OpenAI), which changes their edge cases. |
| Shrink | keep a small custom tool for what no tool covers; run gitleaks (default + custom rules) for patterns | Custom part would be: names and terms from outside the repo (or the generator), `unscanned`, commit identity and message scan, `.check` semantics, the hook. Two scanners to run and two outputs to keep apart; default gitleaks rules add 0 true findings and 51 false positives in history (30 gitleaks, 21 trufflehog default rules) unless allowlisted. |
| Keep | no change | No false positives on 5 repos as configured; one engine, masked output, tested hook. Cost: 1,457 lines plus 1,220 lines of tests, and every new secret shape is hand-written; in these repos trufflehog and detect-secrets found nothing the custom tool misses; their default rules add provider-specific shapes the custom list lacks, with the false positives of 2.2. |

Pair-1 facts that bear on any option: detect-secrets and trufflehog custom detectors need workarounds (filters off; one result per
chunk) that make them weaker bases than gitleaks; gitleaks and the repos' CI already share version 8.30.1; none of the default
rules found a true secret in these five repos or their history.

## 3. Pair 2: instruction check vs Vale

### 3.1 Setup

The kit tool reads the files named by `audit-instructions:` lines in `.check`; Vale ran on exactly those files. Style `STE`
(9 rules, 104 lines of YAML, `.vale.ini` 7 lines) written for the trial: one rule per finding kind of the kit tool (long step and
long sentence, actions, pointer, vague, wait, next, cue) plus a passive-voice rule. Rules are `occurrence` (word counts),
`existence` with token lists copied from the kit's lists, and `existence` with negative look-ahead for the absence checks (next, cue,
wait). Vale's package sync (styles such as write-good or Microsoft) pulls from GitHub, which was blocked, and Vale ships no
ASD-STE100 style, so nothing was reused. `IgnoredScopes = code, tt, strong, b`.

### 3.2 Real files

| Repo | Files in scope | Steps the kit tool read | Kit tool findings | Vale alerts on those steps (by rule) | Vale alerts outside steps | Vale time s | Note |
|---|---|---|---|---|---|---|---|
| kit | `README.md`, `docs/MAINTAINER_RUNBOOK.md`, `docs/check-config-schema.md`, `docs/github/README.md` | 133 | 0 | 40 (Cue 19, Next 19, Passive 2) | 90 | 0.07 |  |
| RADE | none | - | - | - | - | - | empty cell: the repo's `.check` has no `audit-instructions:` line |
| 90-161.Z | `TASKS.md`, `go.md`, `scripts/paste_bundles.json` | 92 | 0 | 18 (Cue 8, Long 2, Next 8) | 292 | 0.38 | scripts/paste_bundles.json is in the list; Vale has no reader for it |
| 33-332.Z | none | - | - | - | - | - | empty cell: the repo's `.check` has no `audit-instructions:` line |
| ICF-Source | none | - | - | - | - | - | empty cell: the repo's `.check` has no `audit-instructions:` line |

Kit tool run time on all five repos: 0.09-0.16 s each. Kit tool result on the 4 files of the kit and the 3 of 90-161.Z: 0 findings.

Judgement of Vale's alerts on steps (file:line context):

- Next and cue: 54 of the 58 are on a lead-in item ("do these actions:") or one of its numbered sub-actions. The kit tool reads the
  lead-in together with its actions and exempts sub-actions from these two checks; Vale sees each list item alone, so all 54 are
  false positives of the same cause. On plain steps both tools agree: 0 alerts.
- Passive (kit README lines 235 and 239: "is written"): correct reports of passive voice; the kit tool has no passive check (so these
  are only-standard true positives of the style, not misses of the kit tool).
- Long (90-161.Z `TASKS.md:60`, `go.md:53`, 25 words): false positives of tokenization: the kit counts a quoted phrase as one word
  (19 words); Vale counts its words.
- Pointer: 2 false positives in the first version ("you see the list"), removed by a look-behind in the style (the kit excludes the
  "you see ..." span). Counts above are after that fix.
- Outside steps: Vale's `list` scope matches every list item and its sentence scope every sentence, so it alerts on prose and
  bullet lists the kit tool never reads (kit 90, 90-161.Z 292 alerts). There is no ordered-list-only or "procedure" scope in Vale; the
  kit tool decides a list is a procedure when half its items start with an action verb.
- Judged: 0 of the kit tool's "0 findings" were shown wrong by Vale (no true alert on a plain step); Vale produced 54 false
  positives, 2 tokenization false positives and 2 passive-voice reports on the 225 steps read.

### 3.3 Seeded defects

10 steps in a temporary file: step 1 clean, steps 2 to 10 one defect each (including passive voice and a missing screen name,
which the brief named and the kit tool does not check). Lines are those of `instr.md` (step n on line n+2).

| Step (line) | Seeded defect | Kit tool | Vale + STE style |
|---|---|---|---|
| 1 (3) | clean control | no finding | no alert |
| 2 (4) | two actions in one step | actions | actions |
| 3 (5) | passive voice ("is opened by the program") | not checked | passive |
| 4 (6) | no exact screen name ("a new window") | not caught (no check) | not caught (no rule written) |
| 5 (7) | sentence over 20 words | long (+ actions) | long (+ actions) |
| 6 (8) | pointer ("step 2") | pointer | pointer |
| 7 (9) | vague word ("some") | vague | vague |
| 8 (10) | wait without the state to wait for | wait | wait |
| 9 (11) | no next state | next | next |
| 10 (12) | no cue | cue | cue |

Result: the kit tool catches 7 of the 9 seeded defects (all 7 of its own kinds); Vale with the written style catches 8 of 9 (the same 7 plus passive).
Neither catches the missing screen name. An HTML `<ol>` copy of three steps gave the same two alerts in both tools (HTML works in both).

### 3.4 Coverage of the custom checks

| Kit check | Vale rule type used | Seeded | On real steps |
|---|---|---|---|
| long (step 60 words, sentence 20) | occurrence, scope list / sentence | yes | 2 false positives (quoted text counted as words); step-length rule fires only outside steps |
| actions (two actions in a step) | existence, regex on verb lists | yes | 0 alerts, agrees |
| pointer | existence, token list + look-behind | yes | 0 after the fix, agrees |
| vague | existence, token list | yes | 0 on steps, agrees |
| wait (names a wait, not the state) | existence with look-ahead | yes | 0 on steps, agrees |
| next (no "you see ...") | existence with look-ahead (absence) | yes | false positives on every lead-in and sub-action (38 + 16 with cue) |
| cue (no wait / go on / note) | existence with look-ahead (absence) | yes | same |

Count: 7 of 7 finding kinds fire in the seeded test; 4 of 7 (actions, pointer, vague, wait) match the kit tool without false positives on
225 real steps; 3 of 7 (long, next, cue) need what Vale lacks. Uncovered logic (not a finding kind): which lists are procedures,
lead-in and sub-action handling, "quoted text is one word", the `check_instructions_local.py` extension hook, the HTML reader (works in
Vale through its own HTML parser), the PreToolUse hook that blocks an edit until the instructions skill was loaded, and the
`audit-instructions:` file selection (Vale needs a glob list in `.vale.ini` instead).

### 3.5 Candidate verdict options for the instruction check (not decided)

| Option | Trade-offs from the evidence |
|---|---|
| Retire | The 7 kinds are expressible (104 lines of YAML). Loses procedure detection, lead-in handling and quote handling, so Next and Cue would flood (54 false positives on 225 steps) unless lists are tagged some other way; loses the hook and the `.check` file selection. Gains passive voice and any future Vale style for free. The kit tool's 590 lines (tests 271) go. |
| Shrink | Keep the step reader (procedure and lead-in logic) and send its steps to Vale, or keep only next, cue and long in code and move actions, pointer, vague, wait, passive to Vale. Two tools for one check; a style to maintain (word lists copied from the kit would live in the style). |
| Keep | 0 findings on 225 real steps and 7 of 9 seeded; no false positive; passive voice and screen-name checks not covered by either tool as is. |

## 4. Open points and limits

- Install: GitHub release downloads were blocked (HTTP 403), so the binaries were built from the Go module proxy; versions are tags, not
  signed release assets (1.1).
- Brief item S02: the sample address in the brief uses a reserved TLD that the custom tool exempts by design, so it is not a
  defect for it. S01 uses a non-reserved invented domain instead. The Maintainer may want that exemption listed as a difference.
- Stand-in lists: the real denylist and terms were not put into gitleaks, trufflehog or Vale config. The name and term checks are
  proved by mechanism with invented words (S07, S08); on real data only the detect-secrets plugin used the real list (in memory).
  `CHECK_TERMS` is not set in this environment, so the term check had no real entries to measure.
- trufflehog custom detectors: one result per chunk and detector, and unreliable lines; comparison is at file level.
- Mutant kill counts were not measured for either custom tool (the plan's proof asks for them).
- Raw (C) runs replace each repo's `.check` with its tier and block lines in a temporary copy; every `.check` file finding was
  dropped from the comparison. The "after skips and allow strings" columns are approximations (line contains an allow string).
- The repos' own gitleaks workflows scan the working tree only; this trial also scanned history. For ICF the detect-secrets "custom"
  column is the plugin-only run (default plugins off); a full run with default plugins and the two filters off was stopped after
  more than 20 minutes because its default-plugin part adds only entropy false positives (79,410 in the default run).
- Judgements of false positives are from masked context only; no value was decoded or tried.

