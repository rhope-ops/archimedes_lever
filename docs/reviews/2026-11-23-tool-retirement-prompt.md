# Custom tool retirement program: start prompt (approved 2026-11-23)

The Maintainer approved this prompt on 2026-11-23 in "Kit · Fleet v2 coordinator 2" (deeper-version rewrite, with both
"left out" parts included). Decisions with it: the program starts after fleet v2 closes, in a new session titled
"Kit · Tool retirement · <date>"; the rule texts are approved through the program plan. Evidence: the Step 3 draft
(2026-11-23-fleet-v2-step3-rules.md) and the 5 causes in the fleet v2 lessons file.
Origin: this program is Part 2 of FLEET-MASTER-PLAN-v2.md (the Maintainer's Drive, folder Rhope), backlog items
"Installable archimedes-kit CLI package" (est. 30-60 % smaller downstream repos) and "Standard linters and secret
scanners" (ruff, shellcheck, PSScriptAnalyzer, gitleaks, trufflehog). Fleet v2 ran Part 1 only, which split the custom
scripts to the 450-line cap instead of retiring them.

Paste into the new session:

```
Plan a "custom tool retirement" program for the archimedes_lever kit (rhope-ops/archimedes_lever) and its project repos (RADE, 90-161.Z, 33-332.Z, ICF-Source, sec-source). Keep the deliverable: one approved plan, with exact rule texts, models, agent count and hours. Do not build yet.

Start from raw material, not summaries:
1. Inventory every kit script (today: 65 scripts, 17,096 lines; 69 locked files per project). For each one: its job in one line, lines, callers (check.sh, hooks, CI), self-test and mutant counts, changes in the last 30 days (git log --numstat), and the sync PRs it caused. Put it in docs/tools.md, the one tool inventory.
2. For each candidate overlap, run a side-by-side trial on the same commits of all 5 repos and diff the findings: code_standard.py vs ruff + pylint (too-many-lines) + radon; check_content* vs gitleaks custom rules and detect-secrets; sync_baseline/sync_merge/drift/check_settings vs copier and cruft; token_log vs Claude Code's OpenTelemetry usage metrics; check_instructions vs Vale with a custom style. Read each tool's own docs. Record per pair: retire, shrink (keep only the part no tool covers) or keep, with the evidence.
3. Also inventory and trial the project-specific tools of each repo (for example the RADE engine lock and release tooling, ICF publish_pages.py vs actions/deploy-pages, the 90-161.Z task-script generator), with the same retire / shrink / keep record. A project's own retirement is that project's decision: show it to the Maintainer per repo.
4. Design distribution by version: shared checks as a pre-commit hook repo or a reusable GitHub workflow at a tag. Choose one project as the pilot, with a rollback.
5. Cut the kit's AGENTS.md rule bullets back to the guide of 28 (today 31): for each line cut or merged, show the old and new text, and run the rule-conflict check (.claude/skills/rule-change/SKILL.md).

The plan must include, as exact text for the Maintainer's approval (each with its enforcing check, trigger and the defect it prevents):
- T1 search-first: no new script without a docs/tools.md entry that names at least 3 candidates and why each fails (CI fails without it).
- T2 ratchet: the total custom script lines only go down from the measured baseline; an increase needs the Maintainer's approval of the number.
- T5 no stricter cap or new rule without a measured fleet-wide debt list and a fix plan.
- T6 one role word, "the Maintainer"; an approval counts only in the acting session's own chat; a DECISIONS row By the Maintainer quotes the OK of its exact text (a check enforces it).
- R1 split a hand-written file at 80 % of its cap (360 of 450), in the PR that grows it.
- R3 a fresh cross-repo audit at each kit release or every 14 days.
Add no new AGENTS.md lines: extend existing lines and enforce with checks.

Proof required for every retirement: the standard tool finds at least the same defects on the same commits, the mutant kill count is equal or higher, CI is green, and the custom-line count falls (wc -l in CI). Proof for distribution: after the pilot, a kit change reaches the pilot in one version bump, measured as the files changed per kit change, and the token cost per kit change before and after (from the token log).

Plan format: phases with lanes (A/B/C), the model per agent (lowest tier that gives the same result), the agent count, estimated hours, the order across repos, a rollback per phase, and the GAPS lines.
```

Added scope (the Maintainer's choice): step 3 (project-specific tools, about 1-2 days) and step 5 (rule bullets back
to 28, about half a day plus a conflict check per line).
