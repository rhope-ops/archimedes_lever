# Kit · Fleet cleanup 10.1.0 · plan (2026-11-21)

## Context
The fleet is on kit 10.0.0. A check of the kit, NMB and TA found 1 new bug: every project gets a false "template placeholders remain" warning. The check reads the literal `{{PURPOSE}}` in `scripts/bloat_check_rules.py:333` and `scripts/bloat_check_test.py:250`, and these 2 files are not in `PLACEHOLDER_TOOLS` (`scripts/check_blocks.py:44`). The PATCH backlog from 3.2.0 is still open, and the session load is close to the cap (33-332.Z ~5,352 of 5,500). The owner chose items 1–8 and answered item 9 (dialog, 2026-11-21).

Done = kit 10.1.0 merged on kit main, then synced to each fleet repo in this session's scope, with `scripts/check.sh` green on each head commit, a fresh review for each PR, and this plan's steps ticked in docs/KIT_HANDOFF.md.

## Owner decisions (dialog 2026-11-21; I record them in docs/DECISIONS.md, scope: the kit and each repo by sync)
- 9a + 9d: fix the token_log crash on a timestamp that is not text, and fix the `tokens()` docstring, in the same PR.
- 9b: apply the handoff REC to the Delegation line (exact text below; your approval of this plan approves that text).
- 9c: you asked how you could know. I checked the source. **The claim is true.** Reviewer subagent, 2026-11-21 16:09 UTC, session 01PyXpdSt…: "One MAJOR finding … Line 58 gives two orders for a small search." I read the transcript event myself. Action: add that record (time, reviewer, quote, the wording it was about) to `docs/reviews/2026-11-21-rule-conflict-scout.md`, and change the DECISIONS row to "recorded in" that file. Nothing is removed.
- Item 4: 90-161.Z stays with its own session (K2). After the merge I send K2 a message to take 10.1.0 in PR 216 or after it.

## Exact rule text (AGENTS.md "Delegation", kit; reaches each repo by sync)
Now:
> Delegate only substantial independent work (about 30 minutes or more, and the fresh review) with bounded files and measurable done criteria. Exception: the main session sends searches that span many files, and summaries of long test or log output, to `scout`; it does a lookup with a known target itself. Give parallel agents disjoint files, …

New (fixes 1, 3, 4, 5):
> Delegate only substantial independent work (about 30 minutes or more; the fresh review at any size) with bounded files and measurable done criteria. Exception to size, files and done criteria: the main session (the orchestrator) always sends searches that span many files, and summaries of long test or log output, to `scout`; it does a lookup with a known target itself. Give parallel agents disjoint files, …

Fix 2 (skill, not rule text): delete "Do other small tasks yourself." from `.claude/skills/delegate/SKILL.md:56`.
A new conflict check (fresh `reviewer`) runs on the new text. If it finds a MAJOR conflict, I stop and show it to you before the merge.

## Steps
1. Save this plan in docs/KIT_HANDOFF.md (with the approval date), push it. Lane A.
2. **Kit PR, 10.1.0** (one PR, MINOR because of the rule text change; branch `claude/magical-faraday-o9phhz`):
   a. Placeholder fix: add the 2 files to `PLACEHOLDER_TOOLS`; add a self-test case that runs `--placeholders` on a synced project fixture and expects no finding.
   b. Backlog 0(a) role swap skips `scripts/check_settings.py`, or `OLD_HEADER_LINES` matches any role; 0(b) `new_header` does not stop at a blank line; 0(c) the 2 NITs; 0(d) `fix_hooks` repoints the known old path `tools/git-hooks` and warns about other paths; 0(f) first use empties "Project rules". Each fix gets a test. 0(e) (90-161.Z, needs pwsh) stays open.
   c. token_log: a timestamp that is not text does not drop the rows (test for each bad field); `tokens()` docstring "text that is not an integer".
   d. Delegation text above, plus the skill sentence; conflict-check record; the 9c record.
   e. Session-load trim. First I measure what loads in each repo (`bloat_check.py --brief` on a dry-run sync). Then I cut non-rule text (skill descriptions, check-in output lines, duplicate pointers). Target: each repo at or below 5,000 tokens (the warning level), or at least −300. If I must cut AGENTS.md rule text, the PR shows each old/new line in full, and that part waits for your yes (lane C).
   f. Handoff cleanup: remove the old 6.0.0 load numbers and the done items; record the tag status.
   g. CHANGELOG row 10.1.0; `scripts/check.sh`; fresh `reviewer` on the diff (a fix after the review gets its own review). Merge: lane C (rule text) → I ask you with the review result.
3. **Fleet sync to 10.1.0.** I add the 7 other repos with `add_repo` (push): RADE, 33-332.Z, ICF-Source, SEC-Source, SPAR, 36-3003.Z, 65-601.Z, plus NMB and TA (already here). One sync PR per repo (`scripts/sync_baseline.py`), `scripts/check.sh` on each, then the session load is measured again. Your approval of this plan covers these 9 sync merges when each is green and its review has no MAJOR finding; a repo with a conflict or a MAJOR finding waits for you.
4. **TA audit** (item 7, the audit skill, about 1 h). Report only; each fix it proposes waits for your yes.
5. Tags (item 5, your clicks). Correction: 5 tags are missing, not 8 (v3.2.0 and v4.0.0 exist; v5.0.1 is a PATCH, so it gets no tag): v4.1.0, v5.0.0, v6.0.0, v8.1.0, v9.0.0, and v10.1.0 after step 2. I give one release link for each in the report.
6. Handoff: tick the steps; send the 10.1.0 message to K2; final report.

## Not in scope / done
- Item 6: you deleted the old branches. **Keep `claude/token-usage`**: it is a data branch. The Stop hook `scripts/token_log.py` writes one CSV file per session there (it has no common history with main by design). If you delete it, the token log history is lost.
- Item 4 (90-161.Z): K2.

## Resources (for your approval)
- Models: main session (this model); fresh reviews: `reviewer` (a tier no lower than the author's); the measurement and audit summaries: `scout` (Haiku).
- Agents: about 5 (1 kit review, 1 conflict check, 1 review of the fixes, 1 TA audit review, scout calls).
- Time: about 4–5 h of agent time. The usage limit can stop the work; the handoff has each step, so a new session can continue it.

## Verification
- Kit: `scripts/check.sh` green on the head commit; the new tests fail before the fix and pass after it; `session_checkin.sh` in NMB and TA (after sync) no longer shows the placeholder warning.
- Each repo: `scripts/check.sh` green; `bloat_check.py --brief` shows the load before/after; `git log origin/main` has the merge commit.

## Risks
- The trim can remove text that a session needs. Mitigation: cut duplicates and pointers first; the review checks each cut.
- 9 sync PRs in one session: a merge conflict with another session's open PR. Mitigation: list the open PRs of each repo before each merge (handoff "Do not").
