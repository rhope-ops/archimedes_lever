# Role Scrub & Kit v16.0.0 Fleet Debt

- Date: 2026-11-27
- Change: Standardize role title on `Administrator` (`DEC-ROLE`) and add `scripts/check_sh_test.sh`, `scripts/nipr_guard.py`.

## Fleet debt

| Repo | Debt | Fix plan |
|---|---|---|
| `rade` | Legacy role titles (`the Maintainer`, `the owner`), 43 script shards, NIPR invariants, Fulcrum Dark v2.1.0 | Resolved in Stage 2 (Batches F3 & F4) |
| `ion` | Legacy role titles, `-ExecutionPolicy Bypass` in `ps51.yml`, 26 `src/` shards | Resolved in Stage 3A (Batch F5) |
| `kanon` | Legacy role titles, `-ExecutionPolicy Bypass` in `ps51.yml`, `T20`/`T22` shards | Resolved in Stage 3B (Batch F6) |

debt-check: edc4f582d068
