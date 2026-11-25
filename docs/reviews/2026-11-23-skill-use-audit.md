# Skill use audit, 2026-11-23 (started; partial data)

Started 2026-11-23 ~17:20 America/Chicago at the Maintainer's request ("start auditing skill use"), by session
"Kit · Tool retirement · 2026-11-23 · #125", with `.claude/skills/audit/SKILL.md` category 19 loaded. Follows the first
audit, [2026-11-20-skill-use-analysis.md](archive-index.md#2026-11-20-skill-use-analysis-md) (12 sessions, 4 Skill-tool calls).
Counts only; no message text.

## Method and what blocked it

1. This session's own logs: `python3 scripts/skill_use.py $(find ~/.claude/projects -name "*.jsonl")`, 19 log files
   (this session and its workers and reviewers, from 2026-11-23 ~14:33).
2. 14 other cloud sessions (kit, RADE, 90-161.Z, 33-332.Z, ICF; 2026-11-21 to 11-23) with `list_events`:
   **blocked.** The results now come back inline (one page of 100 assistant events was ~25,000 tokens) and are not
   saved to files, so `skill_use.py` has no input; on 2026-11-20 the same tool saved 84 pages to files. A worker
   (Sonnet) fetched 3 pages inline and stopped before transcribing anything (correct: a hand copy is not raw data).
3. The token log (`scripts/token_log_rows.py`) records agent types (Agent/Task calls), not Skill calls or SKILL.md reads.
4. Asked the coordinator session to run step 1 on its own container and to ask other running sessions (pending).

## Result: this session (19 logs)

| Group | Count | Detail |
|---|---|---|
| Skill tool (full load) | 5 (now 6, with project-log after the count) | where-to-save 1, deliver 1, delegate 1, rule-change 1, audit 1 |
| Read of a SKILL.md (full read) | 0 | - |
| Shell slice of a SKILL.md (`grep`, `sed`) | 44 | delegate 10, deliver 9, audit 7, rule-change 6, handoff 4, personal-data 4, kit-update 2, project-log 1, "f" 1 (false hit) |
| Agent calls | 17 | worker 11, reviewer 5, general-purpose 1 |
| Tools | 1,298 | Bash 977, Write 203, Read 19, ... |

Kit skills by use in this session: loaded in full: audit, delegate, deliver, rule-change, project-log; slice only:
handoff, personal-data, kit-update; not used: data-change, instructions, verify. Account skills: where-to-save 1;
turn-summary 0, ship 0, pages-and-tools 0 (none of the work was a page).

## Result: 3 more running sessions (their own counts, sent as messages, 2026-11-23 ~17:22-17:25)

Each ran `python3 scripts/skill_use.py $(find ~/.claude/projects -name "*.jsonl")` on its own container (counts only).

| Session | Logs | Skill tool (full load) | Shell slices | Agents | Tools |
|---|---|---|---|---|---|
| This session (kit, tool retirement) | 19 | 5: where-to-save, deliver, delegate, rule-change, audit | 44 | worker 11, reviewer 5, general-purpose 1 | 1,298 |
| Kit, fleet v2 coordinator 2 | 3 | 4: deliver, rule-change, instructions, deeper-version (account) | 1: rule-change | reviewer 1 | 305 |
| 90-161.Z, fleet v2 Stage 3A | 9 | 7: delegate 2, instructions 2, verify 1, kit-update 1, round 1 (project skill) | 2: deliver, round | reviewer 5, worker 3 | 633 |
| ICF, fleet v2 handover (logs before its compaction may be missing) | 28 | 3: instructions 2, delegate 1 | 8: kit-update 3, efficiency 1, port 1, run-verify 1, ui-verify 1, deliver 1 | reviewer 20, worker 7 | 1,769+ (top 10 only) |
| 33-332.Z, fleet v2 Stage 3B (sent with the Maintainer's OK, ~17:29) | 10 | 3: deliver, instructions, kit-update | 0 | reviewer 9 | 459 |
| RADE, fleet v2 engine-v36 (sent with the Maintainer's OK, ~17:29) | 14 | 3: instructions, kit-update, rule-change (+1 full Read: instructions) | 3: instructions, deliver, delegate | reviewer 12, worker 1 | 631 |
| 33-332.Z, Ion DoD ID detection fix (new 2026-11-23; sent ~18:05) | 7 | 0 | 0 | reviewer 6 | 152 |
| **Total (7 sessions, 90 logs)** | 90 | **25** (+1 Read) | **58** | 87 | ~5,250+ |

Kit skills across the 6 sessions (full loads / slices): delegate 4/11, instructions 7 (+1 full Read)/1, deliver 3/12, rule-change 3/7,
audit 1/7, verify 1/0, kit-update 3/5, handoff **0/4**, personal-data 0/4, project-log 0/1 (1 load after the count),
data-change **0/0**. Account skills: where-to-save 1, deeper-version 1, turn-summary **0**, ship **0**.

Self-reports from the sessions (their own notes, not measured): 3 of 4 changed a handoff file without the handoff
skill (this session, coordinator 2, 90-161.Z); 33-332.Z loaded skills only with the Skill tool (0 slices) and names verify, handoff and personal-data as not loaded; coordinator 2 also named verify (before a "verified" Site deploy) and
personal-data (before Drive exports). ICF read a skill named `efficiency`, which kit 6.0.0 merged into `audit`
(2026-11-20): a stale reference (F5).

## Findings

| # | Finding | Evidence | Cost |
|---|---|---|---|
| F1 | No fleet-wide source of skill-use data in cloud sessions | method 2 and 3 above | the audit cannot cover more than the running containers |
| F2 | Workers cannot load a skill: the `worker` agent has no Skill tool (Read, Edit, Write, Bash, Grep, Glob), and they read skills by `grep`/`sed` slices, not a full Read | `.claude/agents/worker.md`; 44 slices, 0 Reads | AGENTS.md "Skills": "a slice read through the shell misses steps" |
| F3 | The main session skipped skills its rules name: handoff (KIT_HANDOFF.md edited without it), project-log (log rows written only after this audit), turn-summary (every work turn), instructions (paste steps), verify | this session's Skill calls vs its actions | the same pattern as 2026-11-20 (account skills 0 calls) |
| F4 | `skill_use.py` counts a false skill "f" from a shell command | the shell group above | inflates the shell count by 1 |
| F5 | ICF still reads a removed skill (`efficiency`, merged into `audit` in kit 6.0.0) | ICF counts above | an agent may follow an old procedure |
| F6 | `handoff` was loaded 0 times in 7 sessions, but 3 of them changed a handoff file; `data-change` 0/0; account `turn-summary` and `ship` 0 (as on 2026-11-20) | the table above | handoff steps (40-line cap, plan saving) followed from memory |

## Proposals (the Maintainer added all 4 to plan P2: "Add all 4 to P2", question dialog, 2026-11-23 17:23 America/Chicago)

| # | Proposal | Home | Cost | Benefit |
|---|---|---|---|---|
| P1 | The token log's Stop hook also counts, per session, Skill-tool calls and Reads and shell slices of SKILL.md files (it already reads the session log for Agent calls) | `scripts/token_log_rows.py` (extend; rule T1), plan P2 | ~2 h worker + strong review (lane C: a hook script) | every session records skill use on the token-log branch; the audit reads it fleet-wide |
| P2 | Worker briefs say: "read each skill you need in full with the Read tool, never by grep or sed" | delegate skill "Brief" (one bullet next to S4) | 0 session-load tokens | workers follow whole procedures |
| P3 | Fix the "f" false hit in `skill_use.py` (match a skill folder name only after `skills/`) | `scripts/skill_use.py`, plan P2 | ~15 min | correct shell counts |
| P4 | Re-run this audit fleet-wide after P1 has run for 14 days, and propose a merge, a better description or a removal for each skill with 0 loads | audit skill "Fleet audit" (S3) | ~1 h | data-based skill changes |

Status: 6 running sessions measured (kit 2, RADE, 90-161.Z, 33-332.Z, ICF); the Ion fix session sent 0 skill loads and 0 reads (it opened a PR with 6 reviews and worked from AGENTS.md alone: deliver, verify and instructions not loaded). The full measure comes from P1 (token log) after 14 days. The full measure comes from P1 (token log) after 14 days.
