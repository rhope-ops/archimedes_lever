# Fleet v2: lessons learned and preventive measures

Written 2026-11-23 (America/Chicago) by "Kit · Fleet v2 coordinator 2", at the Maintainer's request (plan step added
2026-11-23). Facts come from the session reports, the repos and the token log; each number names its source.
A copy is in the Maintainer's Drive, folder Rhope.

## 1. What fleet v2 delivered

| Stage | Repo | Result (merge commits) |
|---|---|---|
| 1 | archimedes_lever | Kit 11.0.0 (PR 114, dedc3b3), 11.0.1 (PR 118, 9e3f6fa) |
| 2 | RADE | engine-v36 released and verified (#167, 6efe5c7); kit sync #169; guard files #168; role word #171 |
| 3A | 90-161.Z | #217-#222; engine-v36 lock and kit 11.0.1 in #221 (130cbf0) |
| 3B | 33-332.Z | #51, #53-#56; index.html 119,119 B -> 15,078 B |
| 3C, 4 | ICF-Source | #241-#250; Site 2.12.2 live on /icf/ (rhope-ops/icf aadd154, 61 of 61 files equal) |

Invariants a-e held at the end of every stage. No MAJOR review finding stayed open at a merge.

Cost (token log, branch claude/token-usage of the 5 repos, read 2026-11-23 ~11:13): 7.52 B tokens measured since
tracking began on 2026-11-17, ~$2,665 at list prices; fleet v2 day so far ~0.84 B tokens, ~$257.

## 2. The 5 causes of the state the repos were in

1. **New tools instead of existing ones.** The kit holds 65 custom scripts (17,096 lines). Several do what a standard
   tool does (code_standard vs ruff/pylint/radon; check_content vs gitleaks/detect-secrets; sync scripts vs
   copier/cruft; token_log vs Claude Code OpenTelemetry metrics; check_instructions vs Vale). Each needs tests, splits
   and syncs.
2. **The kit is copied, not referenced.** 69 locked files sit in every project. A one-byte kit fix needs a release and
   a sync PR per project.
3. **Rules and caps grow faster than their enforcement.** The 450-line cap met 21 ICF files over it (the plan said 3)
   and 6 in 90-161.Z. The kit has 31 rule bullets (guide 28); project session loads are at 5,150-5,427 of 5,500.
4. **Unclear role words and approval paths.** Five words named one person. An approval given in one chat was relayed
   to another session; twice an agent wrote a DECISIONS row that claimed an approval of text the owner had not seen.
5. **Throughput outran consolidation.** ~2,961 Claude commits in 7 days across 6 repos (search API counts). Each fix was
   correct, but nobody stepped back until a sync forced it; verification steps (Sigstore chain, local gitleaks) were
   not runnable where they were needed.

## 3. Misses during fleet v2

| Miss | Effect | Caught by |
|---|---|---|
| The master plan's Part 2 (standard tools, kit package) was left out of the approved plan without a question to the Maintainer | A day of work split custom scripts instead of retiring them | The Maintainer, at the end |
| Coordinator 2 told RADE to sync with `--owner "the Administrator"`; the approved text said "the Maintainer" | None: RADE followed the approved text | RADE |
| 2 DECISIONS rows By "the PFM" and 1 By "the Administrator" written from dialog answers to other questions | Would have made the strict gate read them as owner approvals | The coordinator; the owner then approved the texts |
| ICF scope grew from 3 to 21 file splits | 7x work; 5 strong-tier workers | ICF (drift report, DEC 12 stop) |
| The site repo was renamed to "ICF", so /icf/ gave 404 and the beacon did not count | Lost visit counts until the rename back | ICF |
| Attestation chain never verified in any session (Sigstore host blocked) | Release trust rests on the cert identity and the signature only | Open |
| 2 kit files end with a blank line (code_standard_test.py, check_content_hook.py) | `git diff --check` fails on unstaged copies | ICF; deferred to the next kit release |

## 4. What worked

- DEC 12 (report and continue; stop only on MAJOR, red gate, drift or invariant failure) kept 4 sessions moving with
  few questions, and the drift stop on the ICF split worked as meant.
- Fresh reviews found real defects: 7 MAJORs inside the ICF build-number guard, the focus-return MAJOR in #242.
- Independent checks of relayed facts: the coordinator verified the engine-v36 release, its 42 files and its
  attestation before relaying it, and verified the live Site file by file.
- "Act only on the Maintainer's own message in the session's chat" held: sessions refused relayed approvals and
  refused to work around denied access.

## 5. Preventive measures (the Part 2 program, session "Kit · Tool retirement · 2026-11-23")

Approved by the Maintainer as a program; each rule text is approved through its plan. Prompt:
[2026-11-23-tool-retirement-prompt.md](archive-index.md#2026-11-23-tool-retirement-prompt-md).

| Measure | Cause | Enforcement |
|---|---|---|
| T1 search first: a new script needs a docs/tools.md entry with 3 candidates and why each fails | 1 | CI fails without the entry |
| T2 custom script lines only go down from the measured baseline | 1, 3 | Ratchet in check.sh |
| T3 retire or shrink custom tools after side-by-side trials (same defects found, same or better mutant kills) | 1 | One PR per retirement |
| T4 shared checks by version (pre-commit hook repo or reusable workflow), one pilot first | 2 | Files changed per kit change |
| T5 no stricter cap or new rule without a measured fleet-wide debt list | 3, 5 | Audit output before merge |
| T6 one role word; approvals only in the acting session's chat; DECISIONS rows quote the exact-text OK | 4 | DECISIONS check |
| T7 a plan made from a source plan marks every source item in / out / later, approved by the Maintainer | the Part 2 miss | Item-count check |
| R1 split a file at 80 % of its cap in the PR that grows it | 3 | code_standard C4 |
| R3 fresh cross-repo audit at each kit release or every 14 days | 5 | AUDIT DUE (fleet) |

Also in the program: the Part 2 standard replacements (CodeQL + SBOM + hash-pinned Python; pac solution; WPF layout;
build-time static HTML; ICF term markup), the paste-truncation sentinel, the 6 other kit repos on kit 10.0.0, the ICF
pre-transfer scans, and the rule bullets back to 28.

## 6. Open after fleet v2

- Tags v11.0.0 (dedc3b3) and v11.0.1 (9e3f6fa): the Maintainer's step.
- Kit next release: the 2 blank-line files; bootstrap.sh (one dod-security check, do not hide Python errors);
  check_settings.py --validate-config does not read `fleet:`; rule-conflict MINOR 2-7.
- Remote branches the host would not delete (HTTP 403): the Maintainer deletes them, or a later session with rights.
- Sessions ready for the Maintainer to review and archive: RADE, 90-161.Z, 33-332.Z, ICF (fleet v2), and this one.
- ICF: forced-colours ring design, #247 NITs, a pre-existing screen-walk flake, AUDIT DUE (docs/reviews/2026-11-23-fleet-v2-icf.md).
- R41 r2 (90-161.Z) built but not run on a device.
