# RADE: project-file changes for the re-port

Scratch result (results/rade-new-full.txt): `LOCK PASS: 44 kit files`, 0 overrides (18 before);
`CHECK FAIL: 1 failed, 22 passed, 1 skipped, of 24` (before: 1 failed, 20 passed, 1 skipped, of 22). The one failure
is the same as before: the conflict-check record for the changed rule lines (hash 59fa42518535). Project tests,
same lines as before: `MANIFEST files=1 fail=0`, `NETRULES pass`, `APPS apps=1 fail=0`, `ENGINE pass=114 fail=0`,
`LAYOUT pass=10 fail=0`, `TEXT51 pass=10 fail=0`, `LINT findings=0`. Code standard: `CODE-STANDARD pass (files=78,
debt: comment 72, length 2, safety 41, docs 103, line 31, gate code_standard_gate.py active)`; before: files=71,
safety 54, docs 186, line 39. No debt item added; no kit file left in the debt list. Session load 5,920 tokens
(before 5,917; cap 6,000).

| File | What moves where |
|---|---|
| scripts/check_content_local.py (new; in scripts/ here) | The two lines RADE had in the kit's check_content_scan.py (import of check_content_milhosts; `MILHOST, milhosts = ...`; `milhosts(line)` in scan_text) become `REPLACE = {"milhost": [find_milhost]}`. Its `--test` runs scripts/check_content_test_milhosts.py (the call RADE had at the end of the kit's check_content_test.py). 34 ok lines: RADE's 33 cases, none dropped, and 1 line that the scanner uses the finder. |
| scripts/check_content_milhosts.py, scripts/check_content_test_milhosts.py | Code unchanged. Their header text still says the kit's scanner and test import them: change the wording to "scripts/check_content_local.py" (not done in the scratch copy). |
| scripts/code_standard_gate.py (changed; in scripts/ here) | Header rewritten. Added the five entry points: `RULES` (kind `line`; RADE's label for `safety`), `OPT_IN` (kind `line` only), `decided(root, ref)` (the `owner_row` call that RADE had in the kit's `against_main`), `new_debt_refusal` (the "new files meet the rules" test from `against_main`), and a `--test` entry. Removed: `safety_level`, `level`, `main_config`, the old `OPT_IN` (the kit now holds the levels: off 0, on 1, strict 2, and the --adopt logic). `file_rules`, `safety_ok`, `owner_row`, `row_refusal`, `owner_role*`, `exists_at` unchanged. It now imports check_settings. |
| scripts/code_standard_gate_test.py (new; in scripts/ here) | RADE's cases from its copy of the kit's code_standard_test.py: `owner_row` (helper), `self_test_strict`, `self_test_safety`, `self_test_rows`, `self_test_row_tricks`, `self_test_lines`, `self_test_strict_main`. Changes: `cs.gate` is `cs.GATE`; `cs.header_block` is `cs.parse.header_block`; the numeric safety levels (2, '2', -1) became `strict` (2 asserts rewritten, 1 dropped: `gate.level('safety', {'c1_safety': '9' * 5000})`); the helpers `write`, `config_of`, `commit` are imported from the kit's code_standard_test.py. |
| docs/code-standard-rade.md (new; in docs/ here) | The section "RADE extras" (X1 to X7), the strict C1 safety text, the row "C4 line", "The owner row" and "New files meet the rules" from RADE's copy of docs/code-standard.md, which is the kit's file again. To do in the port: point the X-rule citations at the new file (tests/bundle_layout_test.py line 11, docs/standards-mapping.md "Rule X7", README.md, docs/NEXT_PROMPT.md); the "Project rules" line "Code standard" names docs/code-standard.md "(the kit core plus the RADE extras ...)": a new text needs the Administrator's approval; rhope-ops/90-161.Z links to "RADE extras". |
| docs/code-standard.md, scripts/check.sh, scripts/check_settings.py, scripts/code_standard.py, scripts/code_standard_test.py, scripts/check_content_scan.py, scripts/check_content_test.py, the 8 "comments only" scripts, .github/workflows/check.yml | The kit's files, by sync. RADE's parts are in the kit (docs, safety lines, line wraps, the `scan_commits` split, the key `code-max-line-chars`, the pinned checkout and `persist-credentials: false`) or in the project files above. |
| .claude/skills/deliver/SKILL.md | The kit's file: it now has RADE's 2 lines on unattended work. |
| .claude/skills/port/SKILL.md | The kit's file. RADE's "RADE never syncs" text goes; so must the "Project rules" line "No kit sync" (owner's approval of the removal). |
| .claude/agents/reviewer.md | Replaced by the sync (it was an earlier kit version, never changed in RADE). |
| .check | `--migrate` replaces the first comment line. The setting lines stay: `code-max-line-chars: 200`, `code-c1-safety: on`, `code-c2: full`. RADE's gate applies the strict label form at `on`, as before; the value `strict` exists if the Administrator wants the setting to say so (a setting change: owner row). |
| .check.state.json | `code_standard.py --update` after the sync: safety 54 to 41, docs 186 to 103, line 39 to 31. Time baselines: 2 new steps have none. |
| scripts/check.local.sh | Unchanged. |
