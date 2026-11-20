# Plan: skill use analysis, skill refinement, kit 6.0.0

Approved by the owner 2026-11-20 07:36 (America/Chicago), with the exact texts A to D below. Session: "Kit · Skill use analysis · 2026-11-20". Repo: rhope-ops/archimedes_lever (the kit). Start commit: 0131554 (kit 5.0.1; PR 80 merged before step 0).

## Context

The owner asked: examine all repos; analyze skill use, decision patterns and way of working; say which skills are used too little, not at all, are available outside, or need refinement; make new instructions that use the changes; integrate the work of the session "Kit · Third-party skill cap · 2026-11-20 · #78".

Evidence (3 read-only explorers; as of 2026-11-20 about 07:30):

- **Skills are almost never loaded.** 12 sampled sessions (84 pages, 2026-11-18 to 11-20): 6 Skill-tool calls in 4 sessions. `turn-summary`, `ship`, `where-to-save`, `pages-and-tools`, `data-change`: 0. Kit skills are read in slices through the shell (deliver 6, rule-change 7, handoff 6). The process runs from rule text and habit.
- **Largest gap: UI work.** Pages or artifacts were built in 5 of 12 sessions with no `pages-and-tools`, `design:*` or `verify` call.
- **What works:** fresh review (30 reviewer calls in 9 sessions). `worker` and `scout`: 1 call each.
- **Overlap:** deliver/ship; handoff/turn-summary/rule-change (resume prompt, Suggest); efficiency/audit; verify UI checks/pages-and-tools. `data-change` is written for SQL; no repo has a database.
- **Owner pattern:** 37 typed messages, median 9 words, mostly option codes; takes the recommendation in most dialogs; cuts scope hard; works in rounds; 7 of 37 messages were corrections (too few questions listed, questions in prose not a dialog, the assistant too cautious, a direction picked for the owner). Decisions: 40 to 50% are process or rule decisions; 51 of 84 kit decision rows replace an earlier one; 15 kit versions in 3 days, each one a lane C pull request in up to 9 repos. Recurring misses: a check too narrow to see the defect; "live" reported when only a preview changed; two sessions on one repo.
- **Third-party session:** kit 5.0.0/5.0.1 merged (separate 1,500-token cap for third-party skills). Per-repo installs were dropped; the result is one account skill `ui-design` (zip built, not uploaded, not tested). PR 80 (docs) is open. The session waits on the owner (4 or 8 packs; remove one network host; keep 5.0.x).
- **Limits:** 12 of 130+ sessions; 5 lack their start; project logs of 5 repos are private. Confidence: medium for counts, high for the direction.

Owner decisions for this plan (2026-11-20, question dialog; scope: this plan):
merge efficiency into audit; rewrite data-change; ship becomes fallback only; one home for the resume prompt and Suggest; add outside skills webapp-testing and product-management; full test loop for the top 3 skills; usage measurement by a script on demand.

## Assumptions

- The owner uploads account skills; an agent cannot (source: third-party session, docs check; confidence high).
- All 9 project repos are on kit 4.0.0 and take 6.0.0 in one sync (source: `.check.lock` in each clone; high).
- The top 3 skills for the test loop are `pages-and-tools`, `deliver`, `handoff` (source: the owner's dialog answer; high).
- github.com raw files for anthropics/skills and anthropics/knowledge-work-plugins are reachable from this environment (not tested; low: if blocked, step 5 reports it and asks).

## GAPS

- **Skill-load telemetry:** none today. Cost: 1 script. Benefit: the next analysis takes minutes, not a 12-session sample. In this plan (step 4).
- **Skill tests (evals):** no kit skill has test cases. Cost: about 18 agent runs now. Benefit: a skill change has proof from outside. In this plan for 3 skills (step 3).
- **Release batching:** 15 kit versions in 3 days times 9 repos. Cost: none. Benefit: fewer lane C approvals. This plan ships all kit changes as one release (6.0.0). A standing rule is under SUGGESTED, not in this plan.
- **Account skills have no source copy:** only turn-summary is in `docs/account-skills/`. Cost: 5 files. Benefit: review, diff and one home. In this plan (step 2).
- **One session per repo:** two sessions changed the kit today. Risk is real (2 logged misses). Handled here by step 1; no new rule proposed.

## Steps

- [x] 0. **Start.** Title this session "Kit · Skill use analysis · 2026-11-20", tag `project:kit`. Run `scripts/session_checkin.sh`. Save this plan as `docs/reviews/2026-11-20-skill-use-plan.md` with the approval date, add it to `docs/KIT_HANDOFF.md`, push (branch `claude/amazing-wozniak-rki9fa`, merged up from origin/main first).
- [x] 1. (message sent 07:42; reply open) **Coordinate with the third-party session** (`send_message` to session_01PyXpdRuGj6eMuDwZhjdVd2): give it this plan's file list; ask it to merge PR 80 first and to change no kit skill, AGENTS.md or bloat-check file after that; ask for the final `ui-design` contents (pack list after the owner's answer) and its trigger description. This session then owns kit files; that session owns `ui-design`. Its 3 open questions stay the owner's.
- [x] 2. **Analysis record (lane A).** `docs/reviews/2026-11-20-skill-use-analysis.md`: the three explorer reports, condensed, with methods and limits. Copy the 5 missing account skills into `docs/account-skills/` (read from the session's synced skill folder under `/root/.claude/skills/synced/`), so each has a source copy.
- [x] 3. (results: [2026-11-20-skill-tests/README.md](2026-11-20-skill-tests/README.md); description tuning with run_loop not run for kit skills: the session-load cap fixes their length) **Refine and test the top 3** with the skill-creator loop (snapshot old version; 3 test prompts per skill from real session cases; new against old; graders; `eval-viewer/generate_review.py --static` review page for the owner; then description tuning with `scripts.run_loop`, 20 queries per skill).
   - `pages-and-tools` (account): description covers artifacts, previews, comparison pages and fleet-page updates; body points to `verify` for measurement (24 px targets and contrast stay in one home, `verify`) and to `ui-design` and `design:*` for design work.
   - `deliver` (kit): absorbs the uncommitted/unpushed block case (16 blocks in the sample) and a "live copy equals main" check after a publish; kit-only step 9 (fleet sync) moves to a kit-only PROJECT.md.
   - `handoff` (kit): the only home of the resume prompt; split the 600-character fleet line.
   - Agents: about 18 runs plus graders, model Sonnet; about 1 to 2 hours; the usage limit can interrupt it (results are kept per run on disk).
- [x] 4. (in the kit 6.0.0 pull request; drift: Suggest stays in rule-change, the kit-release step went to kit-update, no block counts in skill_use.py, 5 more descriptions and 3 agent descriptions shortened for the cap) **Other kit skill changes (one pull request with step 3's kit files, lane C).**
   - `efficiency` merged into `audit` (a "Slow run" section); delete `.claude/skills/efficiency/`; `audit` step 1 and its before/after table move to `scripts/bloat_check.py` output where the script already prints them.
   - `data-change` rewritten for the data the repos have (SharePoint lists, static data files, artifact databases), same name, same dry-run and row-count steps.
   - `rule-change`: its Suggest section becomes a pointer to `turn-summary` (the "caps" text is not touched: the owner rejected that edit today).
   - `kit-update` and `personal-data`: remove the old names (run-verify, ui-verify, port, `.pii-guard`) except in the first-sync note.
   - New `scripts/skill_use.py` + test: reads saved session event files, prints skill, agent, question and block counts; `audit` gets one step that fetches events for N sessions and runs it. Reuse: the explorer's regex method; `scripts/bloat_check_skills.py` for the skill list.
   - Account skill text (owner uploads): `ship` cut to a short fallback ("a repo's deliver skill wins; use this only where none exists"); `turn-summary` keeps Suggest, points to `handoff` for the resume prompt.
- [x] 5. (3 `.skill` files sent; `webapp-testing` then dropped by the owner) **Outside skills (account).** Fetch `webapp-testing` (anthropics/skills) and `roadmap` + `stakeholder-update` from `product-management` (anthropics/knowledge-work-plugins, Apache-2.0, no connectors file); read every file; run the content check; package each as a `.skill` file with a notices file; send to the owner. Not added to any repo. Report package, version (commit) and source.
- [x] 6. (PR 82; the "Skills" first sentence was changed by the owner's second dialog: docs/DECISIONS.md) **Rule text (lane C; MAJOR, kit 6.0.0).** Exact texts below. Before the pull request: measure the session load of all 9 repos with the new files (`scripts/bloat_check.py`); if a repo passes 5,000 tokens, cut skill description words first and report; never raise a cap. Run the rule conflict check (`rule-change` skill). Fresh review by the `reviewer` agent on the head commit. Then ask the owner to merge.
- [ ] 7. **Sync 9 repos to 6.0.0** (after the owner merges step 6): one kit-update pull request per repo (lane C each), by `worker` agents with disjoint repos (9 agents, Sonnet, about 1 hour), each reviewed fresh. Also in those pull requests: delete `icf-source/.claude/skills/audit/PROJECT.md` (copies the kit word for word) and fix the stale kit version in icf `docs/NEXT_PROMPT.md`. NMB skill merges (review-merge, write-brief into delegate) are out of scope: listed as a follow-up.
- [ ] 8. **Close.** Update `docs/KIT_HANDOFF.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md` (the dialog decisions, scope: this plan), one `docs/LOG.md` row; turn summary with what waits on the owner; subscribe to each pull request.

## Exact rule and instruction texts (for approval with this plan)

**A. AGENTS.md "Caps and audit", last two sentences.** Old: `The full audit runs when the owner asks for it: `.claude/skills/audit/SKILL.md`. A run slower than its baseline: `.claude/skills/efficiency/SKILL.md`.` New:

`The full audit runs when the owner asks for it, and a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`.`

**B. AGENTS.md "Defaults", new line after "Verification".**

`- **Skills.** When a skill's description matches the step, load the whole skill with the Skill tool before the step (a slice read through the shell misses steps). For a page, a tool, an artifact or a UI change, load `.claude/skills/verify/SKILL.md` and, where the owner's account has them, the `pages-and-tools` and `ui-design` skills.`

**C. Owner's account preferences, "Reporting", third bullet** (the owner pastes it; PREFERENCES.md in the kit gets the same text). Old: `Save deliverables with my `where-to-save` skill; ship repo work with my `ship` skill.` New:

`Save deliverables with my `where-to-save` skill. Deliver repo work with the repo's `deliver` skill; where a repo has none, with my `ship` skill.`

**D. Owner's account preferences, "How to work", new bullet.**

`Before you build or change a page, tool or artifact, load my `pages-and-tools` skill; for UI or visual design, also my `ui-design` skill.`

Skill file texts (steps 3 and 4) are not rules; the owner sees them in the review page and the pull request diff.

## Critical files

- Kit: `AGENTS.md`, `PREFERENCES.md`, `.claude/skills/{audit,efficiency,data-change,deliver,handoff,rule-change,kit-update,personal-data}/SKILL.md`, `docs/account-skills/*`, `scripts/skill_use.py` (new) and its test, `scripts/bloat_check*.py` (read; change only if the audit table moves), `.check.lock` (relock changed kit files), `KIT_VERSION`, `docs/CHANGELOG.md`, `docs/KIT_HANDOFF.md`, `docs/DECISIONS.md`, `docs/LOG.md`, `docs/reviews/2026-11-20-skill-use-{plan,analysis}.md`.
- Workspaces (not in the repo): `<skill>-workspace/iteration-N/` under the scratchpad.
- 9 project repos: kit-sync files only, plus the two icf fixes.

## Verification

- `scripts/check.sh` passes one time on each head commit (kit and each repo); public repos: the pull-request Action is green.
- `scripts/bloat_check.py` in each of the 9 repos: session load at or under 5,000 tokens; numbers reported before and after.
- Skill tests: `benchmark.json` per skill shows new against old (pass rate, tokens, time); description tuning reports the held-out trigger score before and after.
- `scripts/skill_use.py` run on the 12 sampled sessions' saved event files reproduces the explorer's counts (6 Skill-tool calls).
- Fresh review (`reviewer` agent) on every lane B and C head commit; rule conflict check file in `docs/reviews/`.
- Content check (personal data and secrets) on every push and on each packaged `.skill` file; result reported.
- Proof of effect (later, owner's call): run `skill_use.py` on sessions one week after the sync and compare with today's baseline.

## Waits on the owner

- Approval of this plan and texts A to D.
- Third-party session: its 3 questions; upload of `ui-design`; tags v5.0.0 and v5.0.1; delete of one sec-source branch.
- After the work: upload of the changed account skills (`pages-and-tools`, `ship`, `turn-summary`) and the new ones (step 5); paste of texts C and D; merge approval for the kit pull request and the 9 sync pull requests; tag v6.0.0.

## SUGGESTED (not part of this plan; needs its own approval)

- Kit releases: at most one release per day that needs repo syncs, unless a fix blocks work.
