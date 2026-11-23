# Tool retirement R4, group W-B: scanner trials (content check, instruction check)

Evidence only. This file decides nothing: each "verdict option" is a candidate with its trade-offs, for the Maintainer.
Written 2026-11-23 by a worker session (branch `claude/tr-wb-scanners`) for step R4 of
`docs/reviews/2026-11-23-tool-retirement-research-plan.md` (group W-B; that file is not in this branch's checkout, so it is named, not linked) and step 2 of
[2026-11-23-tool-retirement-prompt.md](2026-11-23-tool-retirement-prompt.md).

Data rules kept: no word of the name denylist, no secret, no real address or number is in this file. Findings of the
custom tool come masked from the tool itself; findings of the standard tools were reduced to rule, file and line at
run time (gitleaks `--redact`; trufflehog raw fields dropped in memory; detect-secrets hashes dropped). Every seeded
value was assembled at run time in a temporary copy, so none appears in a command or here. Everything is counts per
rule and file:line.

## Summary of results

Details and the evidence for each line are in sections 2 and 3. No verdict is chosen; options are in 2.8 and 3.5.

- **Pair 1 coverage of the content tool's 11 checks** (email, phone, id, secret, name, term, blocked, milhost, marking, dodid, unscanned):
  gitleaks with custom rules 10 of 11, trufflehog with custom detectors 9 of 11, detect-secrets with a plugin 9 of 11.
  Uncovered by every standard tool: `unscanned` (binary or oversize file), commit author, committer and message scanning, the `.check`
  allow/skip semantics, the PreToolUse hook. Only gitleaks covers `blocked` (a path-only rule). With default rules only, none of the 11 is fully covered (secrets partly).
  Thin evidence: the five repos hold raw findings of only 4 checks (email, phone, milhost, marking; name in ICF-Source). For id, secret, term, blocked and dodid the
  "covered" rests on seeded items only; `unscanned` has real hits in the content tool and none in any standard tool.
- **Seeded items (23 planted)**: the content tool reports 22 (S02, a reserved-domain address, is exempt by design). Of those 22: gitleaks with custom rules 19,
  trufflehog with custom detectors 18, detect-secrets with plugin 17; default rules only: gitleaks 6, trufflehog 3, detect-secrets 6.
- **Real repos, working tree, gitleaks with ported rules vs the content tool raw (names left out)**: matched 1137, only-custom 0, only-standard 43 (all explained in 2.3).
  As configured (with each repo's allow strings and skips) the content tool reports 0 findings on 4 repos and 1 on 90-161.Z (variant A; its own script copy reports 0).
- **Default rules, all 5 repos**: gitleaks 5 tree and 30 history findings, trufflehog 8 and 21, detect-secrets 80002 tree; every group viewed was a false positive (2.2); 0 true findings.
- **Run time, working tree, serial**: content tool 0.2 / 0.4 / 0.7 / 0.4 / 6.5 s (kit / RADE / 90-161.Z / 33-332.Z / ICF); gitleaks default 0.5 / 0.5 / 2.3 / 0.7 / 22.7 s; trufflehog default 1.6 / 1.4 / 1.9 / 1.3 / 8.5 s.
- **Pair 2**: the kit tool reads 225 steps in 6 Markdown files of 2 repos (a seventh file, a JSON bundle, holds 0 steps; 3 repos have no `audit-instructions:` line) and reports 0 findings. Seeded: kit tool 7 of 9 defects,
  Vale with a written 9-rule style 8 of 9 (adds passive voice); neither catches a missing screen name. All 7 finding kinds fire in Vale in the seeded file, but on the real steps
  Vale alerts 58 times (54 false positives on lead-in and sub-action items, 2 quote-counting, 2 passive-voice reports) and on 382 more places outside the steps the kit tool reads.

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
was cloned from this worktree at the same HEAD. The four project clones are complete (not shallow). Inside this worktree git
reports a shallow repository and 234 commits; a clone of the same HEAD walks 570 commits, and the content tool's own line says
"570 commit(s)"; the 570 are used. History scans cover every commit reachable from HEAD.

| Repo | HEAD | Tracked files | Commits scanned (history depth) | Tier | `skip:` lines | Allow strings | `block:` lines |
|---|---|---|---|---|---|---|---|
| kit | `641023e` | 256 | 570 | minimum | 0 | 0 | 0 |
| RADE | `a99ba73` | 243 | 709 | DoD | 3 | 5 | 0 |
| 90-161.Z | `91ccb0c` | 442 | 1371 | DoD | 10 | 12 | 0 |
| 33-332.Z | `6cbc517` | 157 | 252 | DoD | 2 | 3 | 1 |
| ICF-Source | `02a7ed2d` | 3376 | 2548 | DoD | 9 | 38 | 0 |

Allow-string and skip counts are the repo's `.check` lines (the Maintainer's "allowed although it looks like a
finding" and "not scanned" decisions). The content tool reports 0 or 1 finding per repo with them; most differences
below come from what they hide, so each result is given twice: as configured, and raw (only the `profile:`, `block:` and `content-max-bytes:` lines kept:
the tier, the blocked names and the size limit; no allow strings, no skips).

### 1.3 What was run

Custom tool: `scripts/check.sh --content --all` (working tree) and `--range HEAD` (history: commit identity, message,
added lines), kit script of this HEAD, run inside each repo. Three variants: A as configured; B the repo's own
`scripts/check.sh` (own kit version, own local finders in RADE and 90-161.Z); C raw. Raw (C) is the base for overlap.

Standard tools, each in two configurations, working tree (`dir`/`filesystem`) and full history (`git`):

- **default**: the tool's own rules, nothing added. gitleaks with `--config` of `[extend] useDefault = true` (so a repo's own
  `.gitleaks.toml`, present in 90-161.Z, does not apply); trufflehog `--no-verification` (no call to any provider API);
  detect-secrets `scan --all-files` with default plugins and filters.
- **custom**: the same plus rules that mirror the content tool's checks, from one config per tool (sizes in 2.7).
  - gitleaks: 24 `[[rules]]` ported from the kit's regular expressions (RE2 has no look-around, so boundary classes are
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
Standard findings in files that git does not track were dropped (listed in section 4). Times: the content tool's times
and the working-tree times of the standard tools in 2.2 and 2.7 come from serial passes on an otherwise idle machine; times of
history runs and of ICF detect-secrets ran beside other jobs and are marked.

## 2. Pair 1: content check vs gitleaks, detect-secrets, trufflehog

### 2.1 The custom tool on the five repos (working tree)

| Repo | A as configured | B own script | C raw total (no `unscanned`) | C raw by kind | C `unscanned` | C after `skip:` lines | C after skips and allow strings (approx.) | Time A, s |
|---|---|---|---|---|---|---|---|---|
| kit | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.2 |
| RADE | 0 | 0 | 27 | milhost 27 | 19 | 27 | 0 | 0.4 |
| 90-161.Z | 1 | 0 | 136 | email 18, marking 16, milhost 100, phone 2 | 19 | 88 | 1 | 0.7 |
| 33-332.Z | 0 | 0 | 103 | email 12, marking 17, milhost 73, phone 1 | 1 | 47 | 0 | 0.4 |
| ICF-Source | 0 | 0 | 32415 | marking 711, milhost 261, name 31430, phone 13 | 151 | 32331 | 0 | 6.5 |

The one finding of variant A (90-161.Z, kind milhost, `docs/reviews/2026-11-12-pii-guard-history.md:17`): variant B (the repo's own
`scripts/check.sh` and local finders) passes the same tree. A and B differ in script version or local finders; the cause was not traced.
"Approx." means a raw finding is dropped when its line contains an allow string (the kit compares the exact found value;
the line test can only over-suppress).

What the raw numbers show: the tool's output on these repos is dominated by DoD-tier host and marking checks on
published reference text (milhost, marking) and by allow-listed names in ICF's exam data (name: the denylist matches
4 and 5 character words in 1,228 files). The tool finds no secret and no SSN in any repo, raw or configured.

### 2.2 Standard tools, default rules

| Repo | gitleaks tree (by rule) | gitleaks history | trufflehog tree | trufflehog history | detect-secrets tree | Time s, tree, serial: gitleaks / trufflehog / detect-secrets |
|---|---|---|---|---|---|---|
| kit | 0 | 0 | 0 | 0 | Hex High Entropy String 7 | 0.5 / 1.6 / 2.2 |
| RADE | 0 | generic-api-key 1 | 0 | 0 | Base64 High Entropy String 1, Hex High Entropy String 8 | 0.5 / 1.4 / 2.6 |
| 90-161.Z | generic-api-key 3 | generic-api-key 11 | Imagga 4 | Box 1, Imagga 3 | AWS Access Key 2, Base64 High Entropy String 414, Hex High Entropy String 154 | 2.3 / 1.9 / 13.7 |
| 33-332.Z | 0 | generic-api-key 1 | 0 | 0 | Hex High Entropy String 4, Secret Keyword 2 | 0.7 / 1.3 / 3.2 |
| ICF-Source | generic-api-key 2 | generic-api-key 17 | Box 1, Circle 2, ProtocolsIO 1 | Box 2, Circle 2, NpmToken 8, ProtocolsIO 1, SnykKey 1, URI 3 | Base64 High Entropy String 6, Hex High Entropy String 79403, Secret Keyword 1 | 22.7 / 8.5 / n/a |

Rule meanings: gitleaks `generic-api-key` is its catch-all for a key-like value next to a key-like name; trufflehog `Imagga`, `Box`,
`Circle`, `ProtocolsIO`, `NpmToken`, `SnykKey`, `URI` are provider detectors that match a bare token shape; detect-secrets `Hex`/`Base64 High
Entropy String` are entropy tests, `Secret Keyword` a name test. ICF detect-secrets time: 1,215 s, run beside other jobs (not in the serial pass).

False positives judged from the file:line context (masked, long tokens shown as `<tok>`). What was looked at, exactly:

- gitleaks: every finding group (rule + file) of every repo, tree and history, was viewed: 3 + 2 tree and 1 + 1 + 11 + 17 history
  findings; all judged false positives (hash values keyed by file names in `.check.lock` and `scripts/rade.lock.json`; a workflow id in a
  Power Automate JSON file; a version hash in `site/dist/questions.json`; the analytics beacon identifier in ICF's page code, a value
  the repo ships in public page source on purpose (a Maintainer decision recorded in the coverage list), so judged not a secret).
- trufflehog: every group viewed: 4 + 4 tree and 4 + 17 history findings; all judged false positives (base64 images, a gzip file,
  a SHA-256 field; ICF token-log CSV rows whose first column is a hash; a fake credentialed URL in a test fixture).
- detect-secrets: kit 7, RADE 9, 33-332.Z 6 and 90-161.Z 570 findings (20 groups): every group viewed, all false positives (commit and
  step hashes, base64 logos and embedded files, `svg` fields, test constants; the 2 `AWS Access Key` hits sit on lines that are one long
  base64 blob). ICF 79,410 findings in 303 groups: the 45 largest groups (62,157 findings, 78 %) and all 7 non-hex hits were viewed
  (JSON hash and id maps, hash fields, a sample password label); the other 258 groups (17,253 findings) were classified by the shape of
  their first line only (JSON field, inline token, other), not read one by one.
- Result: 0 true findings in the 5 repos and their history from any default rule, among all viewed groups; the unviewed ICF groups are assumed the same.
- Seen at repo level: the four repos that run gitleaks in CI (`security.yml`, `detect --no-git`) avoid the history false positive on
  `.check.lock` by scanning the working tree only; 90-161.Z carries a `.gitleaks.toml` allowlist for its lock file. That is the
  maintenance cost of the default rules, not a measure of recall.

### 2.3 Standard tools with custom rules vs the raw custom tool (working tree)

Base: the content tool's raw findings without `name` (the real denylist is not in the standard tools' config; see the name table below),
without `unscanned`. gitleaks compares distinct class + file + line; trufflehog and detect-secrets compare distinct class + file. M = matched,
OC = only-custom (raw finding with no standard finding), OS = only-standard (a finding of an added rule with no raw finding). M + OC equals the
distinct base of the comparison. Default-rule findings are in 2.2.

| Repo | Raw findings | distinct class+line | distinct class+file | gitleaks M / OC / OS (class+line) | trufflehog M / OC / OS (class+file) | detect-secrets M / OC / OS (class+file) |
|---|---|---|---|---|---|---|
| kit | 0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| RADE | 27 | 26 | 11 | 26 / 0 / 0 | 11 / 0 / 0 | 11 / 0 / 0 |
| 90-161.Z | 136 | 130 | 42 | 130 / 0 / 20 | 42 / 0 / 5 | 42 / 0 / 0 |
| 33-332.Z | 103 | 99 | 14 | 99 / 0 / 17 | 14 / 0 / 0 | 14 / 0 / 0 |
| ICF-Source | 985 | 882 | 275 | 882 / 0 / 6 | 275 / 0 / 4 | 275 / 0 / 0 |

Findings of the added rules, by class (tree; whole counts, not overlap). detect-secrets `default plugins` = entropy and provider hits that
run with the plugin and the two filters off (so they are higher than in 2.2); for ICF detect-secrets ran with the default plugins off.
trufflehog counts are lower bounds (one result per chunk and detector).

| Repo | gitleaks | trufflehog | detect-secrets |
|---|---|---|---|
| kit | 0 | 0 | default rules 9 |
| RADE | milhost 32 | milhost 24 | default rules 12, dod(milhost+marking+dodid) 12 |
| 90-161.Z | default rules 3, email 18, marking 18, milhost 124, phone 3 | default rules 4, email 17, marking 27, milhost 101, phone 2 | default rules 1191, dod(milhost+marking+dodid) 66, email 11, phone 2 |
| 33-332.Z | email 14, marking 22, milhost 91, phone 2 | email 12, marking 22, milhost 73, phone 1 | default rules 19, dod(milhost+marking+dodid) 26, email 5, phone 1 |
| ICF-Source | default rules 2, dodid 1, marking 864, milhost 305, phone 17 | default rules 4, marking 706, milhost 236, phone 13 | default rules 1, dod(milhost+marking+dodid) 439, phone 14 |

Reading it (every item below was checked in the data above; the examples were viewed in masked context):

- gitleaks with ported rules: only-custom findings are listed per repo in the table above; where OC is not 0 the cause is named below.
  Only-standard findings fall into these groups: (a) a host in the military domain inside a mail address (the kit counts the address once,
  gitleaks fires on the address rule and the host rule); (b) gitleaks decodes percent-encoded text, so `%40` in a URL became an address
  (2 findings in 33-332.Z, false positives); (c) a marking phrase split over two lines ("FOR OFFICIAL" / "USE ONLY" and similar): the kit
  reads per line, gitleaks matches across the break (judged real marks); (d) a keyword and a number on two lines (the kit reads per line).
  The `.check` file itself was dropped from the comparison. A first raw run for ICF-Source dropped that repo's `content-max-bytes: 8000000` line, so the kit
  left 23 large files unscanned and 167 more only-standard findings appeared; the raw variant now keeps that option line and those findings are gone.
- gitleaks only-standard causes found per repo (counts of findings, one per rule hit, so they can exceed the distinct class+line OS of the table when
  two rules hit one line; each cause was classified by the line context; the trufflehog and detect-secrets OS were not classified):
  - kit: none.
  - RADE: none.
  - 90-161.Z: 18 x milhost inside a mail address (kit counts the address once); 2 x marking phrase split over two lines (kit reads per line).
  - 33-332.Z: 12 x milhost inside a mail address (kit counts the address once); 3 x marking phrase split over two lines (kit reads per line); 2 x email made by percent-decoding %40 in a URL.
  - ICF-Source: 4 x marking phrase split over two lines (kit reads per line); 1 x keyword and number on different lines (kit reads per line); 1 x other dodid.
  - Unexplained: ICF-Source `k-dodid site/dist/migrations.json:1` (a single-line JSON file; not traced further).
  Only-custom is 0 in every repo for gitleaks (every raw finding that is not a name was reproduced at line level); an earlier run with an
  incomplete port (no "TOP SECRET" line pattern) had 11 only-custom marking findings in ICF-Source; the port was completed and rerun.
- trufflehog custom detectors: each detector yields at most one result per chunk, whatever the number of matches, and the line numbers
  of custom results are not reliable (in a 19-line seeded file the results sat on lines 6, 14, 14 and 18). Its OC is counted per file, so
  a file with one hit counts as matched even when the kit finds more lines there.
- detect-secrets plugins: one result per distinct value and file, so repeated values collapse; compared per file for that reason.
- Port completeness. The gitleaks, trufflehog and detect-secrets configs carry all 10 secret shapes, the email and phone shapes, the SSN
  shapes, the milhost shapes, all 9 marking patterns (including the single-word and "TOP SECRET" line patterns) and both DoD ID forms
  (keyword then number, number then keyword). RE2 (gitleaks, trufflehog) has no look-around, so 3 rules (phone boundaries, milhost, OpenAI)
  differ at the edges. The DoD checks are switched off for the kit (minimum tier) the way the content tool does it.

Name check on real data (the content tool's `name` findings against the detect-secrets plugin that read the real denylist in memory; file level):

| Repo | Content tool raw name findings | in files | detect-secrets plugin: files | files matched | only-custom files | only-standard files |
|---|---|---|---|---|---|---|
| kit | 0 | 0 | 0 | 0 | 0 | 0 |
| RADE | 0 | 0 | 0 | 0 | 0 | 0 |
| 90-161.Z | 0 | 0 | 0 | 0 | 0 | 0 |
| 33-332.Z | 0 | 0 | 0 | 0 | 0 | 0 |
| ICF-Source | 31430 | 1228 | 1226 | 1226 | 2 | 0 |

Only ICF-Source has any raw name finding (4 and 5 character words; all suppressed by that repo's allow strings: 0 as configured). The four
other repos have none, so the name check is untested on real data there. The stand-in rules of gitleaks and trufflehog were not run on real
names by design (1.3).

### 2.4 History (full depth)

| Repo | Commits | Custom `--range HEAD` as configured: all findings (added-line findings by kind, names left out) | Custom raw: added-line findings, no names, no metadata | gitleaks git, custom rules, by class | trufflehog git, custom rules, by class | gitleaks vs raw (class+file) M / OC / OS | trufflehog vs raw (class+file) M / OC / OS |
|---|---|---|---|---|---|---|---|
| kit | 570 | 0 (no added-line findings) | 0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| RADE | 709 | 0 (no added-line findings) | 61 | default rules 1, milhost 64 | milhost 48 | 13 / 0 / 0 | 13 / 0 / 0 |
| 90-161.Z | 1371 | 9 (milhost 7) | 298 | default rules 11, email 18, marking 33, milhost 269, phone 3 | default rules 4, email 19, marking 63, milhost 244, phone 2 | 79 / 2 / 0 | 67 / 14 / 16 |
| 33-332.Z | 252 | 0 (no added-line findings) | 175 | default rules 1, email 14, marking 22, milhost 160, phone 2 | email 12, marking 19, milhost 148, phone 1 | 19 / 0 / 1 | 19 / 0 / 1 |
| ICF-Source | 2548 | 1150 (email 6, marking 1) | 2638 | default rules 17, dodid 72, email 6, marking 5902, milhost 854, phone 21 | default rules 17, email 349, marking 1951, milhost 585, phone 18 | 305 / 0 / 2 | 305 / 0 / 7 |

Overlap columns leave out names (no real list in the standard tools) and the commit-metadata findings, which no standard tool can produce; those
are counted apart: raw metadata findings per repo:

| Repo | Commit identity and message findings, as configured | raw | Raw name findings in added lines (not compared) |
|---|---|---|---|
| kit | 0 | 0 | 0 |
| RADE | 0 | 0 | 0 |
| 90-161.Z | message milhost 1 | message milhost 8 | 1 |
| 33-332.Z | 0 | message milhost 6 | 0 |
| ICF-Source | author/committer email 373, author/committer name 416, message name 20 | author/committer email 373, author/committer name 1060, message marking 1, message milhost 3, message name 347 | 52681 |

History-only checks of the content tool that no standard tool has: commit author and committer identity, commit message, and a changed file that
cannot be read (kind `unscanned`). In ICF the as-configured run reports 1,155 findings: 789 in author and committer lines (373 non-reserved
addresses in 194 commits; 416 denylist names), 20 denylist names in commit messages and 346 in added lines. gitleaks and trufflehog scan patches
only (probed on a seeded commit message and a seeded author address: neither tool reports them).

History differences not explained (class+file pairs, working-tree-style comparison on the added lines of every commit; `.check` left out):
- kit: none.
- RADE: none.
- 90-161.Z: gitleaks OC 2, trufflehog OC 14, trufflehog OS 16.
- 33-332.Z: gitleaks OS 1, trufflehog OS 1.
- ICF-Source: gitleaks OS 2, trufflehog OS 7.
  Not classified, except one check: the 2 gitleaks OC pairs in 90-161.Z (kind milhost) are in two files that a later commit deleted. The trufflehog OC pairs
  (14 in 90-161.Z) were not traced; a size or chunk limit of its git mode is one possible cause, unverified.

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
| S21-history-only-aws | secret | n/a | Y | Y | Y | - | Y | n/a | n/a |
| S22-email-in-commit-message | email | n/a | Y | - | - | - | - | n/a | n/a |
| S23-email-as-commit-author | email | n/a | Y | - | - | - | - | n/a | n/a |

Count: the custom tool reports 22 of the 23 items (S02 is exempt by design). Of those 22: gitleaks default 6, gitleaks with custom rules 19,
trufflehog default 3, trufflehog with custom detectors 18, detect-secrets default 6, detect-secrets with plugin 17 (detect-secrets does not read history).

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
- S04 (AWS-style key): gitleaks default reports it under `generic-api-key`, not `aws-access-token`; trufflehog default did not report it
  (cause not checked); detect-secrets default reports it.
- S19 (blocked file name `PIIScan-*`, from the repo's own `block:` line): only a gitleaks path-only rule caught it, in `dir` and
  `git` mode. trufflehog and detect-secrets have no rule type for a file name. The seed file first did not enter the
  tracked set because the repo's `.gitignore` also lists `PIIScan-*`; it had to be added with `git add -f`. The content tool
  tests tracked, pushed and named files, so an ignored file never reaches it.
- S20 (binary file, DoD `unscanned` check): no standard tool reports it. The tools do not skip all binary content (gitleaks reported hits in `.pyc` files,
  trufflehog in pack files and a `.gz`), but none of the three reports a file it cannot scan: there is no finding like `unscanned`.
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

How thin each "yes" is. The five repos hold raw findings of only four checks: email, phone, milhost and marking (plus name in ICF-Source, which only
the detect-secrets plugin could read with the real list). For id, secret, term, blocked, dodid and unscanned every cell rests on one seeded item (two to nine
for the secret shapes), not on real data. Of the 9 marking patterns three were seeded (the form with two slashes S10, a one-word line S24, a two-word line S25);
the others (phrases, FOUO, NOFORN, the `SECRET` plus two slashes form) rest on real hits whose pattern the masked output does not name, or on nothing: NOFORN and the
`SECRET` plus two slashes form are "ported, not tested" for every standard tool. Both DoD ID forms were seeded (S11, S26).
S24 to S26 (extra single-file seeds): the content tool and all three standard tools with custom rules report all three. The trufflehog phone rule merges the
kit's five phone patterns into one pattern, so it is an approximation, not a port.

### 2.7 Standard-tool configuration needed, and size

| Tool | Config written for the trial | Size | Still needed to match the custom tool | Run time s (serial, working tree): kit / RADE / 90-161.Z / 33-332.Z / ICF |
|---|---|---|---|---|
| content tool (custom) | scripts/check_content*.py (+ finders, hook, scan, settings) | 1,457 lines (tests 1,220) | - | 0.2 / 0.4 / 0.7 / 0.4 / 6.5 |
| gitleaks custom rules | one TOML file + generator for names | 103 + 17 lines | per-repo allowlist generated from `skip:` globs and allow strings (path and regex allowlists); block globs to path rules; a tier switch (DoD rules on or off); `--redact`; run in two modes (`dir`, `git`) | 0.8 / 1.4 / 5.2 / 1.8 / 62.5 |
| trufflehog custom detectors | one YAML file + generator | 39 + 15 lines | `--no-verification` (and `--no-update`, which exists in `trufflehog --help` and was not passed in these runs) and `--results` flags; `--exclude-paths` file for skips; no exact-string allow list (only regex excludes per detector); JSON post-filter to drop raw secrets before they reach a log | 2.5 / 2.1 / 5.1 / 2.2 / 39.3 |
| detect-secrets plugin | one plugin file | 77 lines | a baseline file for allowed values (its audit step), `--exclude-files` for skips, 2 filters disabled; plugin file must be on the scan path; not a history tool | 2.2 / 2.6 / 13.7 / 3.2 / 1215 (run beside other jobs) |

Times for detect-secrets are with default plugins. ICF: default plugins 1,215 s (beside other jobs); the plugin-only run (all default plugins off, used for the ICF overlap and name check) 132 s on an idle machine.
Run times for the history modes (beside other jobs): gitleaks git default 4-30 s for the four small repos, 652 s for ICF;
trufflehog git default 6-8 s and 43 s; content tool `--range HEAD` as configured 5-40 s and 597 s for ICF (raw: 359 s).

### 2.8 Candidate verdict options for the content check (not decided)

The prompt ("Proof required for every retirement") fixes the proof: same defects found, mutants killed equal or higher, CI green, custom lines fall. This trial
measured defect overlap only; mutant counts were not measured.

| Option | What it means here | Trade-offs from the evidence |
|---|---|---|
| Retire | gitleaks (custom rules) replaces the content tool | Loses 1 of 11 checks outright (unscanned) and the history identity and message scan (809 findings in ICF history: 789 in author and committer lines, 20 in messages), the hook mode, the base-branch settings read and the `.check` semantics unless rebuilt as config and glue. Gains a maintained engine, `git` mode, decoding of encoded text, a path rule for blocked files. The glue (generator, allowlist builder, redaction wrapper, two modes) is code that stays. The RE2 port had to drop the look-around of 3 rules (phone boundaries, milhost, OpenAI), which changes their edge cases. |
| Shrink | keep a small custom tool for what no tool covers; run gitleaks (default + custom rules) for patterns | Custom part would be: names and terms from outside the repo (or the generator), `unscanned`, commit identity and message scan, `.check` semantics, the hook. Two scanners to run and two outputs to keep apart; default gitleaks rules add 0 true findings and 51 false positives in history (30 gitleaks, 21 trufflehog default rules) unless allowlisted. |
| Keep | no change | As configured: 0 findings on 4 of 5 repos and 1 on one repo with variant A (variant B: 0); one engine, masked output, tested hook. Cost: 1,457 lines plus 1,220 lines of tests, and every new secret shape is hand-written; in these repos trufflehog and detect-secrets found nothing the custom tool misses; their default rules add provider-specific shapes the custom list lacks, with the false positives of 2.2. |

Pair-1 facts that bear on any option: gitleaks needed no workaround for the ported rules; trufflehog custom detectors report one result per chunk and
detector; detect-secrets needed two heuristic filters switched off for the digit-only shapes and reports one result per value and file; gitleaks and the
repos' CI already share version 8.30.1; none of the default rules found a true secret in these five repos or their history.

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
- Pointer: 4 false positives in the first version (2 in the kit, 2 in 90-161.Z) ("you see the list"), removed by a look-behind in the style (the kit excludes the
  "you see ..." span). Counts above are after that fix.
- Outside steps: Vale's `list` scope matches every list item and its sentence scope every sentence, so it alerts on prose and
  bullet lists the kit tool never reads (kit 90, 90-161.Z 292 alerts). There is no ordered-list-only or "procedure" scope in Vale; the
  kit tool decides a list is a procedure when half its items start with an action verb.
  Outside-step alerts by rule: kit STE.Cue 28, STE.Long 35, STE.Next 24, STE.Passive 1, STE.Pointer 1, STE.Vague 1; 90-161.Z STE.Cue 28, STE.Long 146, STE.LongStep 44, STE.Next 28, STE.Passive 36, STE.Pointer 6, STE.Vague 4.
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

Real files test false positives only: neither tool has a true defect to find in them (the kit tool reports 0), so recall rests on one seeded
instance per kind.
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
- Mutant kill counts were not measured for either custom tool (the prompt's proof asks for them).
- Raw (C) runs replace each repo's `.check` with its tier and block lines in a temporary copy; every `.check` file finding was
  dropped from the comparison. The "after skips and allow strings" columns are approximations (line contains an allow string).
- The repos' own gitleaks workflows scan the working tree only; this trial also scanned history. For ICF the detect-secrets "custom"
  column is the plugin-only run (default plugins off); a full run with default plugins and the two filters off was stopped before it finished
  (not needed: its default-plugin part only adds entropy hits, 79,410 in the default run).
- The first gitleaks history run on ICF-Source with the completed rules was killed by the kernel for lack of memory after 648 s (other jobs ran at the
  same time, and the wrapper then wrote an empty result file; the wrapper was changed so that a failed scan leaves no result file). The run was repeated alone:
  it finished; its figures are in 2.4. An earlier complete run with the rules before the last port fixes found 6,848 findings.
- Judgements of false positives are from masked context only; no value was decoded or tried.
- Findings dropped as not tracked by git: gitleaks 5 hits in `scripts/__pycache__/*.pyc` per repo (byte-compiled files that variant B's own run created in the
  temporary copies); trufflehog 1 to 16 hits in `.git/objects/pack/*` (its filesystem mode reads the pack files). Nothing else was dropped.
- Harness deviation to accept: the worktree guard refused commands whose text named the tool ("gitleaks") or git in a form it could not verify, so each run was put
  in a script file under the session scratchpad and started from there; the scripts do exactly the steps described in section 1.3.

## Appendix: configuration and commands used

These are the files and commands that produced the numbers above. They contain no real word list: the name and term rules are
generated at run time from an environment variable (the trial used three invented words in `STANDIN_DENYLIST`).

### Commands (working tree and history)

```text
gitleaks dir <repo>  --config <generated.toml> --redact --no-banner --exit-code 0 -f json -r <report.json>
gitleaks git <repo>  --config <generated.toml> --redact --no-banner --exit-code 0 -f json -r <report.json> --log-opts=--all
trufflehog filesystem <repo>        --json --no-verification --no-color [--config <generated.yaml>]   (output parsed in memory; raw fields dropped)
trufflehog git file://<repo>        --json --no-verification --no-color [--config <generated.yaml>]
detect-secrets scan --all-files --exclude-files '^\.git/' [-p ds_plugin_k.py --disable-filter detect_secrets.filters.heuristic.is_not_alphanumeric_string
                      --disable-filter detect_secrets.filters.heuristic.is_sequential_string]   (run inside the repo; hashes dropped)
vale --config .vale.ini --output=JSON <the files named by the audit-instructions lines>
scripts/check.sh --content --all | --range HEAD | FILE...           (content tool)      python3 scripts/check_instructions.py   (instruction tool)
```

Generated at run time from an environment variable: for gitleaks and trufflehog `generator.py static-file > generated-file` appends one rule built from the list;
`KTIER=minimum` removes the milhost, marking and dodid rules (the content tool's minimum tier). The generators are listed below.

### gitleaks: rules (static part)

```toml
title = "kit content check parity (static part)"

[extend]
useDefault = true

# check: email (kit EMAIL + ALLOWED_EMAIL)
[[rules]]
id = "k-email"
description = "mail address"
regex = '''[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'''
[[rules.allowlists]]
regexTarget = "match"
regexes = ['''(?i)(@users\.noreply\.github\.com$|^no-?reply@|@example\.(com|org|net)$|\.(example|invalid|test|localhost)$)''']

# check: phone (the five kit patterns; RE2 has no look-around, so a boundary class is part of the match)
[[rules]]
id = "k-phone-a"
description = "US phone NNN-NNN-NNNN"
regex = '''(?:^|[^\w./-])\(?\d{3}\)?[-. ]\d{3}[-.]\d{4}(?:$|[^\w-])'''
[[rules]]
id = "k-phone-b"
description = "US phone (NNN) NNN-NNNN"
regex = '''(?:^|[^\w./-])\(\d{3}\) ?\d{3}[-. ]\d{4}(?:$|[^\w-])'''
[[rules]]
id = "k-phone-intl"
description = "+country phone"
regex = '''(?:^|[^\w+])\+\d{1,3}[ -]\(?\d{1,4}\)?[ -]\d{2,4}[ -]\d{3,4}(?:$|[^\w-])'''
[[rules]]
id = "k-phone-kw"
description = "phone after a keyword"
regex = '''(?i)\b(?:phone|tel|cell|mobile|fax|call)\b\D{0,20}?(\+?1?[ .-]?\d{3}[ .-]?\d{3}[ .-]?\d{4})\b'''
[[rules]]
id = "k-phone-e164"
description = "+1NNNNNNNNNN"
regex = '''(?:^|[^\w+])\+1\d{10}\b'''

# check: id
[[rules]]
id = "k-ssn"
description = "SSN shape"
regex = '''(?:^|[^\w-])\d{3}-\d{2}-\d{4}(?:$|[^\w-])'''
[[rules]]
id = "k-ssn-kw"
description = "SSN keyword then 9 digits"
regex = '''(?i)\b(?:SSN|social security)\b\D{0,20}?(\d{3}[ -]?\d{2}[ -]?\d{4})\b'''

# check: secret (kit SECRET list; gitleaks defaults cover most of these too, the k- copies show what the defaults miss)
[[rules]]
id = "k-secret-github"
regex = '''\bgh[pousr]_[A-Za-z0-9]{36,}\b'''
[[rules]]
id = "k-secret-github-pat"
regex = '''\bgithub_pat_[A-Za-z0-9_]{60,}\b'''
[[rules]]
id = "k-secret-gitlab"
regex = '''\bglpat-[A-Za-z0-9_-]{20,}'''
[[rules]]
id = "k-secret-aws"
regex = '''\b(?:AKIA|ASIA)[0-9A-Z]{16}\b'''
[[rules]]
id = "k-secret-anthropic"
regex = '''\bsk-ant-[A-Za-z0-9_-]{20,}'''
[[rules]]
id = "k-secret-openai"
# kit: lookaheads need an upper-case letter and a digit; RE2 cannot, so this copy is looser
regex = '''\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}'''
[[rules]]
id = "k-secret-google"
regex = '''\bAIza[0-9A-Za-z_-]{35}(?:[^0-9A-Za-z_-]|$)'''
[[rules]]
id = "k-secret-slack"
regex = '''\bxox[abposr]-[A-Za-z0-9-]{10,}'''
[[rules]]
id = "k-secret-stripe"
regex = '''\b[rs]k_live_[0-9A-Za-z]{24,}'''
[[rules]]
id = "k-secret-privkey"
regex = '''-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----'''

# DoD tier checks: milhost, marking, dodid
[[rules]]
id = "k-milhost"
regex = '''(?i)(?:^|[^A-Za-z0-9-])(?:(?:[a-z0-9-]+\.)+mil(?:[^A-Za-z0-9.-]|\.[^A-Za-z0-9]|$)|(?:[a-z0-9-]+\.)*sharepoint-mil\.us\b|(?:[a-z0-9-]+\.)*dod\.teams\.microsoft\.us\b)'''
[[rules]]
id = "k-marking-cui"
regex = '''\bCUI//|(?i:\bcontrolled\s+unclassified\s+information\b)|\bFOUO\b|(?i:\bfor\s+official\s+use\s+only\b)|\bNOFORN\b|(?i:\b(?:SECRET|CONFIDENTIAL|UNCLASSIFIED)//)'''
[[rules]]
id = "k-marking-line"
description = "classification word alone on its line"
regex = '''(?m)^[^A-Za-z0-9\n]*(?:CUI|SECRET|CONFIDENTIAL|UNCLASSIFIED)[^A-Za-z0-9\n]*$'''
[[rules]]
id = "k-marking-top"
description = "TOP SECRET alone on its line, any case"
regex = '''(?mi)^[^A-Za-z0-9\n]*TOP\s+SECRET[^A-Za-z0-9\n]*$'''
[[rules]]
id = "k-dodid"
regex = '''(?i)(?:(?:DOD[\s_-]*ID|EDIPI|CAC)\D{0,20}?(\d{10})(?:\D|$)|(?:^|\D)(\d{10})\D{0,20}?(?:DOD[\s_-]*ID|EDIPI|CAC))'''

# check: blocked (path-only rule; the glob of the repo's `block:` line becomes this regex at run time)
[[rules]]
id = "k-blocked-file"
description = "file name that the settings file blocks (here: the one block line of 33-332.Z)"
path = '''(^|/)PIIScan-[^/]*$'''
```

### gitleaks: generator of the name and term rule and of the tier switch

```python
#!/usr/bin/env python3
"""Print a gitleaks config: the static file plus one rule built at run time from the environment variable STANDIN_DENYLIST
(newline or comma separated words). Mechanism for the name check: env var -> regex -> config on stdout (a pipe or a
short-lived temp file). In this trial the variable holds invented stand-in words, never the real denylist."""
import os
import re
import sys

txt = open(sys.argv[1]).read()
if os.environ.get("KTIER") == "minimum":  # the minimum tier does not run the DoD checks
    blocks = re.split(r"(?m)^(?=\[\[rules\]\]\n)", txt)
    txt = "".join(b for b in blocks if not re.match(r'\[\[rules\]\]\nid = "k-(milhost|marking|dodid)', b))
print(txt)
words = [w.strip() for w in re.split(r"[\n,]", os.environ.get("STANDIN_DENYLIST", "")) if w.strip()]
if words:
    rx = r"(?i)(?:^|[^A-Za-z0-9])(" + "|".join(re.escape(w) for w in words) + r")(?:[^A-Za-z0-9]|$)"
    print('[[rules]]\nid = "k-name"\ndescription = "word of the name denylist"\nregex = \'\'\'' + rx + "'''")
```

### trufflehog: custom detectors (static part)

```yaml
detectors:
  - name: k-email
    keywords: ["@"]
    regex:
      m: '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
    exclude_regexes_match:
      - '(?i)(@users\.noreply\.github\.com$|^no-?reply@|@example\.(com|org|net)$|\.(example|invalid|test|localhost)$)'
  - name: k-phone
    keywords: ["-", ".", "(", "+", "phone", "tel", "cell", "mobile", "fax", "call"]
    regex:
      m: '(?:\(\d{3}\)\s?|\b\d{3}[-.])\d{3}[-. ]?\d{4}\b|\+\d{1,3}[ -]\(?\d{1,4}\)?[ -]\d{2,4}[ -]\d{3,4}\b|\+1\d{10}\b|(?i)\b(?:phone|tel|cell|mobile|fax|call)\b\D{0,20}?\+?1?[ .-]?\d{3}[ .-]?\d{3}[ .-]?\d{4}\b'
  - name: k-ssn
    keywords: ["-", "ssn", "social"]
    regex:
      m: '\b\d{3}-\d{2}-\d{4}\b|(?i)\b(?:SSN|social security)\b\D{0,20}?\d{3}[ -]?\d{2}[ -]?\d{4}\b'
  - name: k-secret-aws
    keywords: ["AKIA", "ASIA"]
    regex:
      m: '\b(?:AKIA|ASIA)[0-9A-Z]{16}\b'
  - name: k-secret-github
    keywords: ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"]
    regex:
      m: '\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{60,}\b'
  - name: k-secret-misc
    keywords: ["glpat-", "sk-", "AIza", "xox", "_live_", "PRIVATE KEY"]
    regex:
      m: '\bglpat-[A-Za-z0-9_-]{20,}|\bsk-ant-[A-Za-z0-9_-]{20,}|\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}|\bAIza[0-9A-Za-z_-]{35}|\bxox[abposr]-[A-Za-z0-9-]{10,}|\b[rs]k_live_[0-9A-Za-z]{24,}|-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----'
  - name: k-milhost
    keywords: [".mil", "sharepoint-mil", "dod.teams"]
    regex:
      m: '(?i)\b(?:[a-z0-9-]+\.)+mil\b|(?:[a-z0-9-]+\.)*sharepoint-mil\.us\b|(?:[a-z0-9-]+\.)*dod\.teams\.microsoft\.us\b'
  - name: k-marking
    keywords: ["cui", "fouo", "noforn", "controlled unclassified", "official use", "secret", "confidential", "unclassified"]
    regex:
      m: '\bCUI//|(?i:controlled\s+unclassified\s+information)|\bFOUO\b|(?i:for\s+official\s+use\s+only)|\bNOFORN\b|(?i:\b(?:SECRET|CONFIDENTIAL|UNCLASSIFIED)//)|(?m:^[^A-Za-z0-9\n]*(?:CUI|SECRET|CONFIDENTIAL|UNCLASSIFIED)[^A-Za-z0-9\n]*$)|(?mi:^[^A-Za-z0-9\n]*TOP\s+SECRET[^A-Za-z0-9\n]*$)'
  - name: k-dodid
    keywords: ["dod", "edipi", "cac"]
    regex:
      m: '(?i)(?:DOD[\s_-]*ID|EDIPI|CAC)\D{0,20}?\d{10}\b|\b\d{10}\b\D{0,20}?(?:DOD[\s_-]*ID|EDIPI|CAC)'
```

### trufflehog: generator

```python
#!/usr/bin/env python3
"""Print a trufflehog config: the static detectors plus one detector built at run time from STANDIN_DENYLIST."""
import os
import re
import sys

txt = open(sys.argv[1]).read()
if os.environ.get("KTIER") == "minimum":  # the minimum tier does not run the DoD checks
    blocks = re.split(r"(?m)^(?=  - name: )", txt)
    txt = "".join(b for b in blocks if not re.match(r"  - name: k-(milhost|marking|dodid)", b))
print(txt)
words = [w.strip() for w in re.split(r"[\n,]", os.environ.get("STANDIN_DENYLIST", "")) if w.strip()]
if words:
    rx = r"(?i)\b(?:" + "|".join(re.escape(w) for w in words) + r")\b"
    print("  - name: k-name\n    keywords: [" + ", ".join('"' + w.lower() + '"' for w in words) + "]\n    regex:\n      m: '" + rx.replace("'", "''") + "'")
```

### detect-secrets: plugin file

```python
"""detect-secrets custom plugins that mirror the kit's content-check finders.
No word list is written here: KDenylist reads the names from the environment variable named in KDENY_ENV at run time
(default PII_GUARD_DENYLIST), keeps them in memory, and never prints them.
"""
import os
import re

from detect_secrets.plugins.base import RegexBasedDetector

ALLOWED_EMAIL = re.compile(
    r"(?i)(@users\.noreply\.github\.com$|^(no-?reply)@|@example\.(com|org|net)$|\.(example|invalid|test|localhost)$)")


class KEmail(RegexBasedDetector):
    secret_type = "k-email"
    denylist = [re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")]

    def analyze_string(self, string):
        for rx in self.denylist:
            for m in rx.finditer(string):
                if not ALLOWED_EMAIL.search(m.group()):
                    yield m.group()


class KPhone(RegexBasedDetector):
    secret_type = "k-phone"
    denylist = [
        re.compile(r"(?<![\w./-])\(?\d{3}\)?[-. ]\d{3}[-.]\d{4}(?![\w-])"),
        re.compile(r"(?<![\w./-])\(\d{3}\) ?\d{3}[-. ]\d{4}(?![\w-])"),
        re.compile(r"(?<![\w+])\+\d{1,3}[ -]\(?\d{1,4}\)?[ -]\d{2,4}[ -]\d{3,4}(?![\w-])"),
        re.compile(r"(?i)\b(?:phone|tel|cell|mobile|fax|call)\b\D{0,20}?(\+?1?[ .-]?\d{3}[ .-]?\d{3}[ .-]?\d{4})\b"),
        re.compile(r"(?<![\w+])\+1\d{10}\b"),
    ]


class KSsn(RegexBasedDetector):
    secret_type = "k-ssn"
    denylist = [re.compile(r"(?<![\w-])\d{3}-\d{2}-\d{4}(?![\w-])"),
                re.compile(r"(?i)\b(?:SSN|social security)\b\D{0,20}?(\d{3}[ -]?\d{2}[ -]?\d{4})\b")]


class KSecret(RegexBasedDetector):
    secret_type = "k-secret"
    denylist = [re.compile(r) for r in (
        r"\bgh[pousr]_[A-Za-z0-9]{36,}\b", r"\bgithub_pat_[A-Za-z0-9_]{60,}\b", r"\bglpat-[A-Za-z0-9_-]{20,}",
        r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", r"\bsk-ant-[A-Za-z0-9_-]{20,}",
        r"\bsk-(?:proj-|svcacct-)?(?=[A-Za-z0-9_-]*[A-Z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{32,}",
        r"\bAIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])", r"\bxox[abposr]-[A-Za-z0-9-]{10,}", r"\b[rs]k_live_[0-9A-Za-z]{24,}",
        r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")]


class KDod(RegexBasedDetector):
    secret_type = "k-dod"
    denylist = [re.compile(r) for r in (
        r"(?i)(?<![A-Za-z0-9-])(?<![A-Za-z0-9-]\.)(?:(?:[a-z0-9-]+\.)+mil(?![A-Za-z0-9-]|\.[A-Za-z0-9])|(?:[a-z0-9-]+\.)*sharepoint-mil\.us\b|(?:[a-z0-9-]+\.)*dod\.teams\.microsoft\.us\b)",
        r"\bCUI//", r"(?i)\bcontrolled\s+unclassified\s+information\b", r"\bFOUO\b", r"(?i)\bfor\s+official\s+use\s+only\b",
        r"\bNOFORN\b", r"(?i)\b(?:SECRET|CONFIDENTIAL|UNCLASSIFIED)//",
        r"^[^A-Za-z0-9]*(?:CUI|SECRET|CONFIDENTIAL|UNCLASSIFIED)[^A-Za-z0-9]*$", r"(?i)^[^A-Za-z0-9]*TOP\s+SECRET[^A-Za-z0-9]*$",
        r"(?i)(?<![A-Za-z])(?:DOD[\s_-]*ID|EDIPI|CAC)(?![A-Za-z])\D{0,20}?(\d{10})(?!\d)",
        r"(?i)(?<!\d)(\d{10})(?!\d)\D{0,20}?(?<![A-Za-z])(?:DOD[\s_-]*ID|EDIPI|CAC)(?![A-Za-z])")]
    if os.environ.get("KTIER") == "minimum":  # the minimum tier does not run the DoD checks
        denylist = []


class KDenylist(RegexBasedDetector):
    """The name and term checks: words from an environment variable, whole-word, any case."""
    secret_type = "k-name"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        words = [w.strip() for w in re.split(r"[\n,]", os.environ.get(os.environ.get("KDENY_ENV", "PII_GUARD_DENYLIST"), ""))
                 if w.strip() and not w.strip().startswith("#")]
        self._rx = re.compile(r"(?i)(?<![A-Za-z0-9])(" + "|".join(re.escape(w) for w in words) + r")(?![A-Za-z0-9])") if words else None

    @property
    def denylist(self):
        return [self._rx] if self._rx else []
```

### Vale: `.vale.ini` (path of the styles folder shortened)

```ini
StylesPath = styles
MinAlertLevel = suggestion
IgnoredScopes = code, tt, strong, b
SkippedScopes = script, style, pre, figure

[*.md]
BasedOnStyles = STE
```

### Vale: style rule `STE/Actions.yml`

```yaml
extends: existence
message: "actions: two actions in one step"
level: error
scope: list
ignorecase: true
raw:
  - '(?:^|[.!?]\s+)(?:accept|add|allow|approve|attach|change|check|choose|clear|click|close|collapse|connect|copy|delete|deny|disconnect|double-click|download|drag|drop|edit|enter|expand|fill|find|go|insert|install|log|look|move|open|paste|plug|press|pull|push|put|read|refresh|reject|reload|remove|rename|replace|restart|restore|right-click|run|save|scroll|select|send|set|sign|start|stop|submit|switch|tap|turn|type|unplug|upload|use)\b[^.!?;]*?(?:\s+then\s+|;\s*|,\s+and\s+|\s+and\s+)(?:accept|add|allow|approve|attach|change|check|choose|clear|click|close|collapse|connect|copy|delete|deny|disconnect|double-click|download|drag|drop|edit|enter|expand|fill|find|go|insert|install|log|look|move|open|paste|plug|press|pull|push|put|read|refresh|reject|reload|remove|rename|replace|restart|restore|right-click|run|save|scroll|select|send|set|sign|start|stop|submit|switch|tap|turn|type|unplug|upload|use)\b'
```

### Vale: style rule `STE/Cue.yml`

```yaml
extends: existence
message: "cue: the step does not say whether to wait, go on or note a value"
level: error
scope: list
ignorecase: true
raw:
  - '^(?![\s\S]*\b(?:wait|go on|continue|next step|write down|note (?:the|down|this|it)|done|finished|complete|stop|do not go on)\b)[\s\S]+$'
```

### Vale: style rule `STE/Long.yml`

```yaml
extends: occurrence
message: "long: a sentence has more than 20 words (ASD-STE100 5.1)"
level: error
scope: sentence
max: 20
token: '\b[A-Za-z0-9][A-Za-z0-9''’-]*\b'
```

### Vale: style rule `STE/LongStep.yml`

```yaml
extends: occurrence
message: "long: the step has more than 60 words"
level: error
scope: list
max: 60
token: '\b[A-Za-z0-9][A-Za-z0-9''’-]*\b'
```

### Vale: style rule `STE/Next.yml`

```yaml
extends: existence
message: "next: the step does not say what the person sees next"
level: error
scope: list
ignorecase: true
raw:
  - '^(?![\s\S]*\b(?:you (?:now |will )?(?:see|get|hear)|(?:shows|opens|appears|closes|changes|turns|loads|starts|stops|ends|displays|disappears|goes away|comes up|is shown|are shown|is open|is closed))\b)[\s\S]+$'
```

### Vale: style rule `STE/Passive.yml`

```yaml
extends: existence
message: "passive: '%s' (ASD-STE100 5.x: use the active voice in a procedure)"
level: error
scope: list
ignorecase: true
tokens:
  - '\b(?:am|is|are|was|were|be|been|being)\s+(?:\w+ed|made|done|shown|given|taken|seen|written|chosen|known|run|set|put|left|sent|kept)\b'
```

### Vale: style rule `STE/Pointer.yml`

```yaml
extends: existence
message: "pointer: '%s' points to another file, step or section"
level: error
scope: list
ignorecase: true
tokens:
  - '(?<!you )see (?:step|section|chapter|above|below|page|the (?:previous|next|following|section|file|table|list|readme|docs?|guide))'
  - 'steps? \d+'
  - '(?:as|shown|described|listed|mentioned|explained|given) (?:above|below|earlier|before|previously)'
  - '(?:previous|preceding|earlier) (?:steps?|sections?|instructions?|list|chapters?)'
  - '(?:next|following|this|that|other) (?:steps?|sections?|instructions?|chapters?)'
  - 'sections?'
  - 'readme'
  - 'go back to'
  - 'repeat (?:the |these |this )?steps?'
  - '[\w./-]+\.md'
```

### Vale: style rule `STE/Vague.yml`

```yaml
extends: existence
message: "vague: '%s'"
level: error
scope: list
ignorecase: true
tokens:
  - 'appropriate(?:ly)?'
  - 'as (?:needed|necessary|required|applicable)'
  - 'if (?:needed|necessary|possible)'
  - 'where possible'
  - 'properly'
  - 'correctly'
  - 'suitable'
  - 'relevant'
  - 'various'
  - 'several'
  - 'some'
  - 'a few'
  - 'a while'
  - 'soon'
  - 'shortly'
  - 'quickly'
  - 'simply'
  - 'just'
  - 'easily'
  - 'etc'
  - 'and so on'
  - 'somewhere'
  - 'something'
  - 'stuff'
  - 'things?'
  - 'should'
  - 'might'
  - 'maybe'
  - 'perhaps'
  - 'probably'
  - 'usually'
  - 'normally'
  - 'typically'
  - 'likely'
  - 'try to'
```

### Vale: style rule `STE/Wait.yml`

```yaml
extends: existence
message: "wait: the step names a wait but not the state to wait for"
level: error
scope: list
ignorecase: true
raw:
  - '^(?![\s\S]*(?:wait until|wait for[^.]*\b(?:to|until)\b|do not [^.]*\buntil\b|until you see))[\s\S]*\b(?:wait|waiting|loading|takes|restarts?|restarting|reboots?|processing|syncing|in progress|spinner|progress bar)\b[\s\S]*$'
```

