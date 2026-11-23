# Fleet remediation v2: approved plan

Approved by the owner 2026-11-23 (America/Chicago), in session "Kit · Fleet v2 remediation · 2026-11-23". Source plan: FLEET-MASTER-PLAN-v2.md (the owner's Drive). This file adds the verified corrections and decisions; where the two differ, this file wins.

Source: Google Drive "FLEET-MASTER-PLAN-v2.md" (compiled 2026-11-22). Checked 2026-11-23 against shallow clones:
archimedes_lever 160c81e, rade 8026ebd, 90-161.z 3fc3c69, 33-332.z 406653a, icf-source 4a2fd6b, icf e08c341.
Method: 3 read-only verification agents + my own spot checks + programmatic contrast (WCAG relative luminance).
No repo file changed. Gate baselines ran on scratchpad copies.

## Context
5-repo remediation; only ICF-Source/icf is handed over. Step 1 = verify the plan, report Agreed / Changes / Decisions, stop.

## Baseline of existing exit gates (before any change)
Run 2026-11-23 on scratchpad copies (script: a scratchpad script; output kept in this file).
| Repo | Command | Exit | Count |
|---|---|---|---|
| kit | bash scripts/check.sh | 0 | 28 passed |
| kit | python3 -m unittest discover -s scripts -p '*_test.py' | **5** | Ran 0 tests (plan says exit 0: wrong) |
| kit | python3 scripts/fulcrum_tokens.py --test | 0 | FULCRUM TEST PASS |
| rade | bash scripts/check.sh | 0 | 29 passed |
| rade | bash tests/engine_test.sh | 0 | 162 pass / 0 fail |
| rade | python3 tests/check_apps_test.py | 0 | canary rules ok |
| 90-161.z | bash scripts/check.sh | 0 | 30 passed |
| 90-161.z | tests/check_palette.py / check_go_page.js / sha256sum -c | 0/0/0 | 31 pairs / PASS / 5 OK |
| 33-332.z | bash scripts/check.sh | 0 | 29 passed |
| 33-332.z | build_paste.py --check / pwsh tests/Run-Tests.ps1 | 0/0 | PASS / 535 passed, 0 failed |
| icf-source | bash scripts/check.sh | 0 | 27 passed, 1 skipped |
| icf-source | node --test site/tests/*.test.mjs | 0 | 352 pass / 0 fail |
| icf-source | python3 -m pytest scripts/ | **1** | 462 passed, 1 failed, 11 errors |
pytest red cause: 11 errors = kit *_test.py helper functions named test_* collected by pytest (fixed by Stage 1.4 unittest
conversion); 1 fail = sandbox lacks `pymupdf` (scripts/check_environment.py:146). ICF-Source runs no pytest in its own checks.
REC gate: `python3 -m pytest scripts/test_*.py` with pymupdf installed (named dependency), plus kit *_test.py via unittest.
90-161.z tests/check_palette.py already asserts contrast pairs: extend it for Option A (no new contrast tool there).
Slow-run WARN lines (check.sh 18 s vs 4.2 s baseline etc.) are sandbox timing, not failures.

## A. Agreed (verified as written)
- Kit: bloat_check.py:241 shell=True (only one in scripts/); 6 hygiene files missing; rhope-ops hardcodes at sync_baseline.py L2/L9/L81,
  token_log.py:384, drift.py:548, bootstrap.sh:2, timeline.py:314,319, docs/fleet.md:3; 8 line counts exact (580-599);
  unittest discover = "Ran 0 tests"; no CSP/skip-link/theme-color/reduced-motion in build_site.py or timeline.py.
- rade: build_readme.py:42 urlopen; index.html:197 card.innerHTML=o.html; <main>+aria-live at L124; no CSP/theme-color/skip-link;
  6 line counts exact; window.json maxPx 900; apps.json:3 RHOPE-OPS; TLS -bor 3072 at 03-files.ps1:100.
- 90-161.z: task-common.ps1:59, New-Publication.ps1:92, bump_lock.py:320, .check:45 scratchpad skip, rade.lock.json:4 engine-v32,
  check_t22_r14.py L36/L85 unguarded pwsh, 6 line counts exact, list-mockup.css #1D5FA8, ref/SHA256SUMS 5 OK, --ctl #8a97a8.
- 33-332.z: 7 hygiene files missing; check.local.sh:15 Install-Module; paste .ps1/.txt identical 364,630 B; 6 line counts exact;
  index.html 119,119 B, no CSP/aria-live/skip-link/theme-color; ExecutionPolicy only in ps51.yml (CI).
- ICF: pagecount.mjs L10-13 (host, path, beacon URL, token); stale analytics.mjs:14 and styles.css:204; styles.css @layer L12,
  --control L18/L22, 4 a11y !important (L50 x2, L447, L449), L280 width:auto!important, --t1 comment L9 vs L20, --warn:var(--bad) L19;
  setup-ui.mjs 192L / 0 aria / 0 role / 6 innerHTML; 30 modulepreload; migrations.json 1.22 MB; _headers no-store.
- Contrast: 24 of 30 claimed ratios match within 0.03 (6 real mismatches, B17); all current-state failure ratios reproduce (page-line 1.25, track 1.23,
  turn 1.42, hover 2.01, ICF quiet lines 2.05-2.12, marks 3.89-4.38).

## B. Proposed changes (each with proof and REC)
1. Engine number. Tags engine-v33, v34, v35 exist; rade_build.py:569 ENGINE_RELEASE = 35. "Cut engine-v33" collides.
   REC: cut engine-v36; 90-161.z lock bump v32 -> v36 pulls v33-v35 too (13 engine files, +296/-48, R42 items E1-E5).
2. Role words: one mechanism exists. sync_baseline.py:105 BASELINE_OWNER="the owner"; apply_owner() L194-200 swaps it for each
   repo's AGENTS.md "- Owner:" (rade the Administrator, 90-161.z the PFM, 33-332.z the PAM, icf-source the owner).
   Hand-scrubbing 900-1,900 hits breaks .check.lock hashes. Counts: 921/1,093 are match counts of the narrow regex; 90-161.z is
   1,689 (narrow) not 1,983; 33-332.z 749 is the broad regex. Conflicts: KIT_HANDOFF.md:5 (PR 107 closed, "the owner" kept);
   AGENTS.md header defines "Owner" (Hard rule "Rule text": exact-text approval).
   REC: change BASELINE_OWNER + each "- Owner:" line; leave history (DECISIONS, LOG, reviews) unchanged; no docs/archive/ move.
3. 450-line cap scope. Kit has 14 files > 450 (not 8: + code_standard_test 571, check_instructions 566, bloat_check_test 534,
   token_log_test 518, fleet_harvest 472, bloat_check 467). Downstream copies are kit-locked: split only in the kit.
   90-161.z T24 holds generated blocks L73-256; T22/T24 are user-pasted scripts (a split = 2 pastes). -> see C.
4. code_standard_gate.py is not in the kit; it is in rade, 90-161.z, 33-332.z scripts/. Fold = kit change + delete 3 project copies.
5. .kit-manifest.json duplicates .check.lock + check_lock.py (--verify/--status/--relock). REC: drop; extend check_lock.py (One home).
6. fulcrum_tokens.py has no --check flag (check is the default; flags --write/--test) and already computes contrast (L67-76, L140).
   REC: gate = `python3 scripts/fulcrum_tokens.py && python3 scripts/fulcrum_tokens.py --test`; extend, do not add.
   fulcrum.json:4 is a date line, not a source string; version is L3 "1.0.0". DECISIONS.md:18 pins Fulcrum to the Rho standard:
   new focus #B83B14 needs that pin updated. rade index.html:76 maps its tokens onto --fm-*: remove when rade moves to Option A.
7. shell=True severity: cmd comes from committed .check.state.json "timings" (check_settings.py:327), same trust as check.sh.
   REC: still fix (shlex + allowlist), label CWE-78 "defense in depth", not "untrusted input".
8. rade 2.1: 0 .pyc files are tracked (.gitignore has __pycache__/). REC: remove that item.
9. rade Bypass list: real uses 04-steps.ps1:14, 05-installed.ps1:310 (desktop shortcut), 07-checks.ps1:165 (conditional) and its
   probe L420-428, window/07-run.ps1:80; plus tests/engine_test.sh:13, tests/window_real.py:303, tests/text_mode_51.py:31.
   07-checks.ps1:112 is a second TLS -bor line (fix both TLS lines). Replacement policy -> see C.
10. TLS 1.3: [Net.SecurityProtocolType]::Tls13 throws on PS 5.1 hosts without .NET 4.8 + Win11/Server 2022.
    REC: assign Tls12, add Tls13 only when the enum value exists.
11. 90-161.z Bypass: 51 lines in 30 files. 21 of 44 T* scripts carry the generated task-common block (build_task_scripts.py);
    R41 paste bundle is generated by the RADE engine (4 engine runner lines) -> fix in rade first, then rebuild.
    Keep: ps51.yml:31 (CI), Test-Environment.ps1 (read-only Get-ExecutionPolicy). Fix also tests/ps/Invoke-Ps51.ps1, Test-T22Layout.ps1:381.
12. OneDrive path: 89 lines, not 58 (76 in scripts/gov, of which ~63 = 3 lines x 21 generated copies). Fix src/task-common.ps1 + rebuild.
13. Retained-repo config: rade already has apps.json; 90-161.z rhope-ops = 298 lines / 78 files (157 in docs).
    Hidden coupling: 90-161.z rade.lock.json:2 and bump_lock.py:30,91 name rhope-ops/RADE; rade release.yml attests in its own repo.
    REC: scope "0 hardcodes" to code + HTML; keep docs/history; keep lock "repo" (attestation subject). Config home -> see C.
14. 33-332.z: Ion-script.txt is a published link (README.md:31, index.html:155) and a recorded decision (DECISIONS.md:36-37).
    DEC 8: keep .txt only. index.html is mostly hand-written; build_site_local.py only adds 2 section types -> edit index.html CSS, not the builder.
    SVG = ~106 KB of 119 KB; "< 35 KB" needs SVGs moved to files.
15. ICF facts: deploy repo icf = byte copy of site/dist + .nojekyll, published by hand (scripts/publish_pages.py --push), no CI.
    _headers and index.html (#release-files, import map, ?v=) are rewritten by build_site_assets.py (L40, L54): edit the script.
    #release-files holds 12-char sha256 prefixes, checked by site/tests/offline.test.mjs:372-378. modulepreload is L27-56.
    migrations.json: app fetches it lazily already (app.mjs:271) but sw.js fill() L123-127 precaches every release file
    -> fix = exclude from SW precache list. No --font-* tokens (only --f L21). Dark theme = data-theme, not prefers-color-scheme.
    CSS breakpoint 640 vs JS 760 (nav.mjs:25, exam-ui.mjs:104): reconcile. Test command `node --test site/tests/` fails
    (directory); use `node --test site/tests/*.test.mjs` (352 pass). renderWithFocus does not exist (new).
16. Option A on ICF: ICF paper is #EDF1F5 (not #F4F6F9); blue is #0B3D91 (not #00539F). Plan dark --control #5C6F8A = 3.69/3.34
    is WORSE than ICF's current #64758E = 4.03/3.65. Light #6C7B8E on #EDF1F5 = 3.81 (ok). -> see C.
17. Contrast table errors (pass/fail unchanged): #0E1A2B/#FFF 17.48 (15.4); #4A586B/#FFF 7.24 AAA (6.4 AA); #FFD520/#0B2545
    10.84 (11.78); #D96B64/#2A1B1F 4.89 (4.75); #5FD08E/#15171D 9.30 (9.45); #F0C24B/#15171D 10.68 (10.85).
18. Kit sync into ICF-Source carries scripts/bloat_check*.py, check.sh, .github/workflows/check.yml (.check.lock, 55 files).
    New DoD files must NOT enter the sync list. -> see C.
19. Tools: bandit and gitleaks are not installed (pwsh, pytest, node, ruff are). Gates that name them need installs (named in summary).
20. Access/host limits: push access only to archimedes_lever and icf-source now; rade, 90-161.z, 33-332.z, icf need add_repo push.
    rade engine release = manual release.yml run from main (tags are the Maintainer's). Guard-file changes (AGENTS.md, .claude/,
    workflows, .check) = lane C: each such PR waits for your merge OK. Stage 4.3 drill and owner.json rotation need the incoming
    maintainer (a person) -> owner steps, not agent steps.
21. Other kit fleet repos (SEC-Source, SPAR, 36-3003.Z, 65-601.Z, no-more-beyond, transcription_assistant) stay on 10.0.0 -> drift
    warnings after v11. REC: list in handoff; no sync in this program.
22. Sequencing: rade Bypass fix must land and release before 90-161.z R41 rebuild (stage order already right). ICF 4.1 "CSS from
    source partials" adds a build step to a hashed file. DEC 11: keep in Stage 4 (concat step in refresh_site.sh).

## C. Decisions (DEC, the owner, 2026-11-23; scope: this fleet program)
1. Engine: cut engine-v36; 90-161.z lock v32 -> v36.
2. Roles: kit BASELINE_OWNER "the owner" -> "the Maintainer"; each repo's "- Owner:" -> "the Maintainer"; history files not rewritten.
   Supersedes the PR 107 choice (KIT_HANDOFF.md:5). Exact rule text for approval (with this plan):
   - AGENTS.md L3 sentence `"Owner" is the name agents use for the person who decides; a public repo uses a role (for example
     "the maintainer") instead of a real name.` -> `"The Maintainer" is the role that decides; the Content Approver approves content
     changes and the Release Manager makes tags and releases. One person can hold all three roles.`
   - Every "the owner"/"The owner" in kit-synced text -> "the Maintainer"/"The Maintainer" by apply_owner() (mechanical; no other
     wording change). Headings "The owner's approval" / "Owner changes" become "The Maintainer's approval" / "Maintainer changes".
3. Bypass: remove the flag everywhere except CI ps51.yml; no replacement flag; GPO MachinePolicy governs. 07-checks.ps1:165 probe
   reports the policy when a child launch is blocked; docs say so. Owner proof step: paste `Get-ExecutionPolicy -List` once on a work PC.
4. ICF vs DoD: new DoD files (SECURITY.md, threat-model, security.yml, dependabot, bandit/gitleaks gate) are opt-in by a .check key,
   not in the sync list; off in ICF-Source. bloat_check.py shell=True fix syncs as a normal kit bug fix.
5. ICF tokens: one shared Option A token set; where a current value has higher contrast it wins (dark --control #64758E);
   blue unifies on #00539F.
6. Line cap 450 for hand-written code only; kit files split in the kit; generated outputs and user-paste scripts keep the 600 cap.
7. Config homes as the plan says: kit.config.json, rade apps.json, site.config.json (90-161.z, 33-332.z); 0 hardcodes in code/HTML;
   docs/history and rade.lock.json "repo" unchanged.
8. 33-332.z: keep paste/Ion-script.txt only; delete the .ps1; update build_paste.py, README.md, index.html, DECISIONS.md together.
9. Stage 3 = 3 cloud sub-sessions (one per repo), titled "<Project> · <task> · 2026-11-23", tag project:<name>.
10. Merges pre-approved: merge any PR whose checks are green and whose fresh review has no MAJOR; stop on MAJOR or red.
    (Rule-text changes still only as shown in DEC 2.)
11. ICF Stage 4.1 CSS source partials: keep in Stage 4 (concat step inside refresh_site.sh, before build_site_assets.py).

## Execution (after approval)
Stage order as in the plan (1 kit -> 2 rade -> 3A/3B/3C parallel sub-sessions -> 4 ICF). Each stage: branch, PR, gates with
exit code + test count > 0, fresh reviewer subagent, checkpoint report (plan adherence, proof, invariants a-e). Kit branch:
claude/keen-cori-eiotd2. Step 3 rule text drafted after Stage 4, shown for approval before any instruction file changes.

First action after approval: save this plan with its approval date to archimedes_lever docs/reviews/2026-11-23-fleet-v2-plan.md and
link it from docs/KIT_HANDOFF.md, then push (handoff rule), then Stage 1.

GAPS (practice missing / cost / benefit):
- Baseline-first gates: low cost / every gate compared to today's run (done above; repeat per stage).
- Owner-side policy proof (Get-ExecutionPolicy -List): 1 paste / confirms DEC 3 is safe; RISK if skipped on a non-GPO PC.
- Rollback note per stage (revert PR + re-pin lock): small / safe undo of engine-v36 in 90-161.z.
- Live-link check after deploy (Pages URLs, Ion-script.txt link, icf site): small / proves "0 broken live links".

## Verification
Gates per stage as corrected above; contrast via a script (as in this intake); invariant greps: rhope-ops values in each config file,
DoD file list absent in ICF-Source, pagecount.mjs beacon present, 4 a11y !important present, `grep -rn "ExecutionPolicy Bypass"`
= only ps51.yml in each repo after rebuild.
