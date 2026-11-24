# P2 item (h): AUD-5 records for the bloat check and the audit skill

Plan P2 item (h) (approved plan [2026-11-23-tool-retirement-plan.md](2026-11-23-tool-retirement-plan.md), coverage row
AUD-5): `scripts/bloat_check*.py` and `.claude/skills/audit/SKILL.md` get the same retire / shrink / keep record as the
other tools (plan section 7). Measured on origin/main 7dd6f4d, 2026-11-23 23:00 America/Chicago. Each record is a
recommendation (REC); the Maintainer decides.

## Facts

| Part | Lines | What it does | Standard tool that does the same job |
|---|---|---|---|
| `scripts/bloat_check.py` | 439 | the session load (tokens of the instruction files), caps, duplicate lines, big files, the audit due date, the check-in line | markdownlint and a `wc` step cover line caps only; none known for the session load or the audit date (docs/tools.md) |
| `scripts/bloat_check_rules.py` | 447 | the rule census of AGENTS.md (`--rules`, `--lint`), the rule-conflict and debt records | none known for a rule census (docs/tools.md) |
| `scripts/bloat_check_files.py` | 341 | T1 tool rows, T2 script-lines ratchet, T5 debt triggers, T6 role word | none known: each check reads the kit's own records |
| `scripts/bloat_check_skills.py` | 191 | the skills check (`--skills`): frontmatter, names, rules stated in a skill | none known |
| `scripts/bloat_check_timing.py` | 111 | the timed commands and the slow-run WARN | a CI time limit catches a hang, not a slowdown against a baseline |
| `scripts/bloat_check_test.py`, `bloat_check_test_rules.py` | 352 + 418 | the self-tests | - |
| `.claude/skills/audit/SKILL.md` | 151 | the slow-run procedure, the full audit, the fleet audit (text S3) | none: a procedure, not a tool |

The family is 2,299 lines (12 % of the kit's 18,785 custom script lines). `bloat_check.py` is run by `check.sh`, the
hooks, the settings and 10 other scripts; 40 commits in 30 days (docs/tools.md). The audit skill is named by AGENTS.md
"Caps and audit", the check-in (AUDIT DUE) and 8 other kit files.

## Records

| Part | Record (REC) | Why |
|---|---|---|
| `bloat_check*.py` | **keep** | no standard tool does the session load, the rule census or T1/T2/T5/T6; the plan's own checks (P1) live here |
| `bloat_check_timing.py` | **keep** | the slow-run WARN found a real 3.5x slowdown on 2026-11-23 (the machine, not the kit); a CI time limit would not |
| `bloat_check_test*.py` | **shrink later** | 770 lines of tests for 1,529 lines of code; R4f row 13 found the same "fixtures mixed with cases" pattern in other test splits: a fixtures file would cut repeats (estimate, not measured) |
| audit skill | **keep** | a procedure the Maintainer starts; no tool replaces it; the fleet audit section (S3) is new in P1 |

No line changes in this item: it is a record only.
