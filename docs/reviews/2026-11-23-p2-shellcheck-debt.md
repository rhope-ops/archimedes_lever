# P2 (g): shellcheck debt, measured per fleet repo (rule T5)

The shellcheck step in scripts/check.sh is new. Rule T5 says a new check lists what it finds today in every fleet repo. This file is that list. Counts only: no file contents.

**How it was measured (2026-11-24)**

- Tool: shellcheck 0.9.0 from the PyPI package `shellcheck-py==0.9.0.6` (the version W-A used, [tr-wa-linters](2026-11-23-tr-wa-linters.md) pair 2). Command: `shellcheck -f json` on the file list, no `-x`, no `-S` filter, no `.shellcheckrc`.
- File list: `python3 scripts/code_standard.py --shell-files` of this branch, run on a copy of each shallow clone (the clones were read, never written). The list is the shell files that the repo's own `.check` includes and does not exclude or mark generated. Only tracked files count. The repo icf has no `.check`: the defaults apply, and it has no shell file.
- The step never fails a check: every finding prints as a WARN line.

| Repo | Shell files | Findings | Files with findings | By level | By SC code |
| --- | --- | --- | --- | --- | --- |
| kit (this repo, this branch) | 4 | 15 | 3 | info 9, warning 6 | SC2015 7, SC2046 5, SC2016 2, SC2034 1 |
| rade | 10 | 239 | 9 | info 200, warning 33, error 3, style 3 | SC2015 161, SC2086 19, SC2016 16, SC1010 13, SC2154 12, SC2046 5, SC2012 4, SC2148 2, SC2002 1, SC2126 1, SC2164 1, SC2144 1, SC2010 1, SC2116 1, SC2034 1 |
| 33-332.z | 4 | 17 | 4 | info 10, warning 7 | SC2015 8, SC2046 5, SC2016 2, SC2034 1, SC2164 1 |
| 90-161.z | 8 | 137 | 7 | info 99, warning 28, style 8, error 2 | SC2015 84, SC2154 13, SC2086 10, SC2181 6, SC2128 5, SC2046 5, SC2016 3, SC2148 2, SC2002 2, SC2012 2, SC2164 2, SC2178 1, SC2053 1, SC2034 1 |
| icf-source | 12 | 20 | 6 | info 12, warning 8 | SC2015 11, SC2046 5, SC2054 1, SC2034 1, SC2164 1, SC2016 1 |
| sec-source | 4 | 14 | 3 | info 8, warning 6 | SC2015 7, SC2046 5, SC2034 1, SC2016 1 |
| transcription_assistant | 7 | 16 | 4 | info 9, warning 7 | SC2015 8, SC2046 5, SC2034 2, SC2016 1 |
| no-more-beyond | 8 | 17 | 4 | info 11, warning 6 | SC2015 9, SC2046 5, SC2016 2, SC2034 1 |
| spar | 3 | 14 | 3 | info 8, warning 6 | SC2015 7, SC2046 5, SC2034 1, SC2016 1 |
| 36-3003.z | 3 | 14 | 3 | info 8, warning 6 | SC2015 7, SC2046 5, SC2034 1, SC2016 1 |
| 65-601.z | 3 | 14 | 3 | info 8, warning 6 | SC2015 7, SC2046 5, SC2034 1, SC2016 1 |
| icf | 0 | 0 | 0 | - | - |

**Reading the table**

- The 3 files that the kit ships (pre-push, session_checkin.sh and check.sh) give the same 14 to 15 findings in every repo that holds them. The repos that have more (rade 239, 90-161.z 137) have their own shell files.
- The W-A numbers (rade 242, 90-161.z 146, kit 14) differ a little from these: the clones are newer, and W-A counted every shell file, not the files the repo's `.check` covers.
- The only error-level findings are in rade (3: SC2148 x2, SC2144 x1) and 90-161.z (2: SC2148 x2, a missing shebang).
- The "fix per repo" work (decision 6) starts from this list. No repo has a fix yet.
