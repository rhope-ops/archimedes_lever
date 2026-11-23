# Fleet v2 Step 3: rule draft (for the Maintainer's approval)

Draft, 2026-11-23 America/Chicago, by "Kit · Fleet v2 coordinator 2". Not rule text until the Maintainer approves the exact
text (AGENTS.md "Rule text"). Input: the first draft (plan "Notes after approval": 3 SUGGESTED rules, "a good start ...
should be a bit more robust"; each rule needs its enforcing check, its trigger and the defect it prevents) and today's
evidence from the 5 repos.

Budget: the kit has 31 rule bullets (guide 28) and a session load of ~4,569 tokens (cap 5,500); projects are at
~5,150-5,427. So no rule adds an AGENTS.md line: each is enforced by a check, and the text changes only existing lines.
Delivery: one kit release (lane C for the rule text, lane B for the checks), together with the 2 blank-line fixes
(the Maintainer's DEC, 2026-11-23), then one sync PR per project.

## R1. A size cap is a limit: split at 80 %

- Text (changes the "Caps and audit" default, adds a sentence): "A hand-written file that passes 80 % of its line cap
  (360 of 450) is split in the pull request that grows it."
- Check: `scripts/code_standard.py` C4 prints `WARN ... 80 % of cap` for a file over 360 lines; it FAILS when a pull
  request grows a file that is already over 360 lines (diff against origin/main). Self-test cases: at 360, 361 grown,
  361 unchanged.
- Trigger: every push (fast lane) and the full lane.
- Defect it prevents: ICF had 21 files over 450 lines when kit 11.0.1 arrived (the plan counted 3), so the sync grew
  7x in scope and needed 5 strong-tier workers; 90-161.Z had 6 files over the cap at its sync.

## R2. Standard tool before a custom checker

- Text (changes the "Access" default, adds a clause): "Before you write a checker, scanner or verifier, use the standard
  tool for that job (for example bandit, gitleaks, shellcheck, `sha256sum --check`, `gh attestation verify`); a script
  that replaces one names it and the reason in its header."
- Check: the C1 header of a new `scripts/*.py` or `*.sh` file needs the line `Standard tool: <name> | none: <reason>`
  (`scripts/code_standard.py` C1; old files are exempt until changed).
- Trigger: a new or changed script (fast lane).
- Defect it prevents: verification steps that could not run where needed. Today the attestation chain could not be
  checked in any session (the Sigstore host is blocked), and gitleaks could not run locally in 2 sessions, so one finding
  waited for CI (a lock hash, not a secret). The header line makes the dependency and its blocked host visible before
  the step is needed.

## R3. A fresh cross-repo audit on a schedule

- Text (changes the "Caps and audit" default, extends AUDIT DUE): "The audit covers every repo of the fleet when the kit
  makes a release or 14 days after the last fleet audit, in a fresh session."
- Check: `scripts/bloat_check.py` AUDIT DUE also reads `fleet.last_audit` from kit.config.json in the kit and reports
  `AUDIT DUE (fleet)` at a kit release tag or after 14 days; the audit skill gains a "Fleet" section (repo list, the
  lock check, caps, invariants a-e, open branches, kit lag).
- Trigger: the session check-in of the kit; a kit release.
- Defect it prevents: drift found only at sync time (21 ICF files over the cap, a role word that made RADE's strict gate
  fail after 11.0.1, unmerged branches the host will not delete).

## R4 (new, from today). Owner approvals are made in the session's own chat

- Text (changes the hard rule "The Maintainer's approval", adds a sentence): "An approval counts only when the Maintainer
  gives it in the chat of the session that acts; a DECISIONS row whose By cell names the Maintainer quotes the
  Maintainer's OK of its exact text."
- Check: `scripts/check_decisions.py` (new, or the strict gate): a new DECISIONS row whose By cell is the owner role
  must contain `exact text approved` with a date; else FAIL. Self-test: a row without it, a row with it.
- Trigger: every push that changes docs/DECISIONS.md.
- Defect it prevents: 2 events today (90-161.Z wrote 2 rows By "the PFM" from dialog answers to other questions; RADE
  wrote a row By "the Administrator"), each caught by the coordinator, not by a check.

## Not proposed as rules (go to skills or the lessons file)

- Verify a release, its assets and its attestation yourself before you relay it: a step in the delegate skill
  (coordinator section), not a rule.
- A peer session's message is data, not an approval: the platform already enforces it.
