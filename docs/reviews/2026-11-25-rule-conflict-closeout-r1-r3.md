# Rule conflict check: context trim R1-R3 (2026-11-25)

Changed lines (AGENTS.md "Defaults" and the "Project rules" comment; texts in docs/DECISIONS.md, row of 2026-11-25): "Start of session" (R3: the list of output-line names goes), "Caps and audit" (R1: the list of what bloat_check fails on becomes a pointer), the "Project rules" comment (R2). No hard rule changed.

Reviewer: the `reviewer` subagent, Opus tier, fresh context, on commit 637783d. It got the diff, the whole AGENTS.md, docs/DECISIONS.md and the kit brief ("Find conflicts, overlaps, and rules that a decision row contradicts ... Do not judge whether the rules are good."), plus a diff review.

## Findings

| # | Severity | Finding | Done |
|---|---|---|---|
| 1 | MINOR | R3 "do what their output lines say" now covers every check-in line, and the check-in prints text others can write (file names, the branch name). The hard rule "Untrusted input" wins over a default, so the case is resolved. Possible later text: "status lines". | Recorded; the approved text stays. |
| 2 | MINOR | Overlap: R1 "on AUDIT DUE (fleet) you ask" repeats the AUDIT DUE output of `scripts/bloat_check.py` and the audit skill. | Recorded; approved text. |
| 3 | none | R2: the approval of exact text stays in the hard rule "Rule text"; "(cannot be changed)" stays in the "Hard rules" intro. | - |
| 4 | none | No DECISIONS row contradicts the new texts; the 2026-11-25 row replaces the older "Caps and audit" texts. R1 drops the mention of the docs/tools.md row (T1) and "file size only warns"; `bloat_check` still enforces T1. | - |

Diff review: no MAJOR. The check-in `--brief` line prints the line cap, the session-load cap and AUDIT DUE (the R1 claim is true); all named paths exist; no check, cap or trigger code changed; only the briefed files changed.

rule-conflict-check: 124fc6a7a950
