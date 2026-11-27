# Fleet debt: IMMUTABLE NIPR code safety & check entry points (2026-11-27)

The change:
- AGENTS.md "Hard rules": `IMMUTABLE NIPR code safety (cannot be changed)` (DEC-NIPR)
- Check entry points: `scripts/nipr_guard.py` and `scripts/check_sh_test.sh`

| Repo | Fails today | Fix plan |
|---|---|---|
| archimedes_lever (kit) | 0 (`python3 scripts/nipr_guard.py` passes 100%) | None |
| rade | 7 Add-Type / csc.exe hits, %TEMP% exec, Sofia Sans TTFs | Fixed in Stage 2 (Batches F3 & F4 per FLEET-MASTER-PLAN-v3.md) |
| ion | CI `-ExecutionPolicy Bypass`, 26 split modules | Fixed in Stage 3A (Batch F5 per FLEET-MASTER-PLAN-v3.md) |
| kanon | CI `-ExecutionPolicy Bypass`, 50+ script shards | Fixed in Stage 3B (Batch F6 per FLEET-MASTER-PLAN-v3.md) |

debt-check: d11d203dfbaa
