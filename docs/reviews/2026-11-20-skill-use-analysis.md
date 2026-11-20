# Skill use analysis: all repos and a session sample

Date: 2026-11-20 (America/Chicago). Asked by the owner. Plan that acts on it: [2026-11-20-skill-use-plan.md](2026-11-20-skill-use-plan.md).

## Method and limits

Three read-only explorers, 2026-11-20 about 07:05 to 07:30:

1. Repo records: shallow clones of the kit and 10 project repos (rhope-ops/sec is empty; standard_project is archived and was not read). Text search of AGENTS.md, `.claude/`, DECISIONS, LOG, handoffs, reviews.
2. Session records: `list_events` (kinds user and assistant) on 12 cloud sessions of 2026-11-18 to 11-20 across 6 projects, 84 pages, at most 10 pages per session. Seven sessions were read to their start; five were not.
3. The session "Kit · Third-party skill cap · 2026-11-20 · #78", pull requests 78 to 80, and a web search for public skills.

Limits: 12 of 130+ sessions; the starts of 5 sessions are missing; the project logs of 5 repos are private; a skill read through the shell is counted apart from a Skill-tool call; message classes were judged by hand. Confidence: medium for counts, high for the direction.

## 1. Skill use

| Skill | Skill-tool calls (12 sessions) | Shell reads of the file | Evidence in repo records |
|---|---|---|---|
| rule-change | 0 | 7 in 3 sessions | about 35 conflict-review files in 8 repos |
| deliver | 0 | 6 in 5 sessions | named in every sync record |
| handoff | 0 (1 by a subagent) | 6 in 4 sessions | a handoff file in every repo |
| delegate | 0 | 4 | 4 repos |
| project-log | 0 | 3 | 5 repos |
| efficiency, personal-data | 0 | 2 each | 2 to 3 repos |
| kit-update, verify | 0 | 1 each | all repos (sync); 2 repos (measure.mjs) |
| audit | 0 | 0 | 10 reports, all 11-13 to 11-17; 0 rules removed |
| data-change | 0 | 0 | none |
| turn-summary, ship, where-to-save, pages-and-tools (account) | 0 | 0 | none (the summary format is followed from the preferences) |
| spec, deeper-version (account) | 1 each | 0 | 3 repos each |
| frontend-design, artifact-design, artifact-capabilities | 1 each | 0 | not checked |
| design:* and engineering:* plugin skills | 0 | 0 | none |

Other tools in the sample: reviewer agent 30 calls in 9 sessions; general-purpose 9 (1 session); Explore 3; worker 1; scout 1; question dialogs 20 in 7 sessions; plan exits 4 (1 refused); web searches 2; pull requests created 44, merged 54.

Reading (the analyst's interpretation): the process runs from the rule text in AGENTS.md and from habit. The skills are read in slices, or not at all. Fresh review is the one practice that runs through an agent in nearly every session.

### Used too little

- `pages-and-tools`, `verify`, `design:design-critique`, `design:accessibility-review`: pages or artifacts were built or changed in 5 of 12 sessions with none of them.
- `spec`: spec-size work in 1 session without it. `deep-research`: 9 research agents in 1 session without it.
- `handoff`: 2 sessions ran out of context or moved to a new chat with no handoff skill in the main thread.
- `worker` and `scout` agents: 1 call each; the main session does nearly all the work.
- `engineering:deploy-checklist`, `engineering:testing-strategy`: releases and "check too narrow" misses without them.

### Not used at all

`data-change` (no repo has a database), `ship` (every repo has `deliver`, which wins), `where-to-save`, `turn-summary` as a loaded skill, `audit` since 11-17, all 10 `engineering:*` and 7 `design:*` plugin skills, `internal-comms`, `theme-factory`, `canvas-design`, `algorithmic-art`, `learn`, `morning`.

### Overlap and defects in the skills

| Skill | Finding |
|---|---|
| deliver / ship | Same procedure in two places; `ship` already says `deliver` wins. |
| handoff / turn-summary / rule-change | The resume prompt (handoff step 6, turn-summary step 5) and Suggest (rule-change, turn-summary step 3) each have two homes. |
| efficiency / audit | Both record baselines; efficiency hands off to audit. |
| verify / pages-and-tools | The 24 px target and contrast checks are in both. |
| data-change | Written for SQL and BigQuery; the repos hold SharePoint lists and static files. |
| audit | 103 lines, 21 categories; its first step and table repeat `scripts/bloat_check.py` output. |
| kit-update, personal-data | Old names remain (run-verify, ui-verify, port, `.pii-guard`). |
| handoff | One 600-character line (fleet format). |
| deliver | Step 9 (fleet sync) is kit-only text that every project receives. |
| icf-source `audit/PROJECT.md` | Copies kit audit lines word for word. |
| Account skills | Only turn-summary had a source copy in `docs/account-skills/`. |

## 2. Decision patterns and way of working

- **Messages.** 37 typed messages in the sample; median about 9 words; most are option codes ("1a 2a 3a"). Classes: new request 11, decision 9, correction 7, approval 6, question 4.
- **Decisions.** The recommended option is taken in most dialogs. Scope is cut hard when a proposal is broad. Work runs in numbered rounds; one repo per session; review before merge is expected.
- **Corrections (7 of 37).** Too few open questions listed; questions written as prose and not in a dialog; a term the owner did not know; the assistant asked the owner for sources it could find; the assistant was too strict about sources; a tool rename in other repos was not known; a plan picked a direction that was the owner's to pick.
- **Decision records.** Rows: kit 84, icf 194, RADE 139, 90-161.Z 511 (about 46 a day), sec 26, SPAR 22, others 2 to 16. Process and rule decisions are about 40 to 50% of rows. Rows that replace an earlier row: kit 51 of 84, RADE 72 of 139, icf 65 of 194, sec 18 of 26. Examples: merge approval changed two times; the audit trigger went from 30 to 300 commits; the session-load cap went 12,000, 6,000, 4,500, 5,000 tokens.
- **Cadence.** 15 kit versions in about 3 days; each one can mean a lane C pull request in 9 repos.
- **Recurring misses.** A check too narrow to see the defect (5 rows in icf); two sessions on one repo (2); the review did not cover the merged head commit (2); placeholder denylist entries (2); CI assumed in a private repo (2); "live" reported when only a preview changed (2).
- **Friction.** 16 stop blocks for uncommitted or unpushed work; about 20 of 37 owner messages follow a turn that ended waiting on the owner; open owner steps repeated over several turns (tags, a preferences line); steps outside chat (tags, branch deletes, tokens, environment approvals).
- **Strengths.** Evidence is required before "done"; decisions are recorded; review before merge is constant; scope control is firm.
- **Costs.** Rule and process work takes a large share of decisions and sessions; session load sits at 4,850 to 4,994 of 5,000 tokens in 4 repos; owner-only steps queue up across sessions.

## 3. Third-party session (state at 07:40)

- Merged: PR 78 (kit 5.0.0: third-party skills and agents counted apart, cap 1,500 tokens), PR 79 (5.0.1), PR 80 (plan record).
- The per-repo installs of impeccable 4.10.0 and ui-ux-pro-max-cli 2.15.0 were dropped. Reason: a cloud session loads only skills uploaded at claude.ai and org-managed plugins, not plugins a repo enables. Result: one account skill `ui-design` with 4 packs, built as a zip; the upload is the owner's step.
- Open on its side: upload and a load test of `ui-design`; tags v5.0.0 and v5.0.1; one branch delete in sec-source; one network host question.

## 4. Public skills checked

| Name | Source | License | Use here | Decision (the owner, 2026-11-20) |
|---|---|---|---|---|
| webapp-testing | anthropics/skills | Apache-2.0 (per repo) | Playwright tests of a local web app; tester rounds | Add as an account skill |
| product-management | anthropics/knowledge-work-plugins | Apache-2.0 | roadmap and stakeholder update | Add; only those two skills, no connectors |
| superpowers | obra/superpowers | MIT | 15 workflow skills | Not chosen (overlaps delegate, verify, handoff; start hook) |
| mattpocock skills | mattpocock/skills | MIT | to-spec, handoff, retro | Not chosen (overlap) |
| playwright, pr-review-toolkit, claude-md-management, plugin-dev, project-artifact, superdesign | claude-plugins-official | not checked | browser tests, review, rule files, plugins, status page, UI canvas | Not chosen; plugins do not load in cloud sessions |

## 5. Gaps with no skill

1. Publish or republish an artifact and prove that the live copy equals main.
2. Sync all repos after a kit release, with a session-load measurement first.
3. Two sessions on one repo.
4. Fleet harvest and port (6 steps each in docs/fleet.md).
5. Content and blind-answer audits in icf (prompt documents today).
6. Release tags (owner clicks).

The plan covers 1 (in `deliver`) and gives the data for the others (`scripts/skill_use.py`); 2 to 6 are follow-ups.
