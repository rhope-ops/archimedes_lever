# Rule conflict check: IMMUTABLE NIPR code safety rule (2026-11-27)

Changed lines: AGENTS.md "Hard rules" (+ **IMMUTABLE NIPR code safety (cannot be changed).** per `DEC-NIPR` and FLEET-MASTER-PLAN-v3.md).
Reviewer: fresh context conflict audit per rule-change skill.

## Findings

| # | Grade | Texts | Case | Fix | State |
|---|---|---|---|---|---|
| 1 | OK | IMMUTABLE NIPR code safety vs Git history | Neither modifies or conflicts with git branching, force-push bans, or PR rules | None needed | Clear |
| 2 | OK | IMMUTABLE NIPR code safety vs Secrets/PII guard | Synergistic: NIPR rules ban hardcoded tenant paths and credential leakage | None needed | Clear |
| 3 | OK | IMMUTABLE NIPR code safety vs Guards and checks | Enforced via automated scripts/nipr_guard.py and check.sh | None needed | Clear |
| 4 | OK | IMMUTABLE NIPR code safety vs Untrusted input | Reinforces input safety (bans iex, ScriptBlock::Create, inline C#) | None needed | Clear |
| 5 | OK | IMMUTABLE NIPR code safety vs Rule text | Rule text explicitly names immutable status per DEC-NIPR | None needed | Clear |

rule-conflict-check: 95bb2623678e
