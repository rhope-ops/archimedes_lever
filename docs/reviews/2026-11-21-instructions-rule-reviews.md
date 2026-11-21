# Kit PR 104 reviews: "Instructions people follow" (2026-11-21)

Fresh reviews of the diff (the `reviewer` subagent, a fresh context, model tier opus, the author's tier). The rule conflict check has its own record: [2026-11-21-rule-conflict-instructions.md](2026-11-21-rule-conflict-instructions.md).

## Review 1: the whole diff (head 0d7e3dc)

| # | Severity | Finding | Done |
|---|---|---|---|
| 1 | MAJOR | The full lane fails: no conflict-check record | Fixed in ee60ece (the record) |
| 2 | MAJOR | The pointer check flags next-state text ("You see the table **Totals**.") | Fixed in 6d78dba: the pointer search skips "You see ..." sentences; all the old pointer patterns stay |
| 3 | MINOR | A lead-in step skips the long and actions checks for its own text; in HTML, a `<ul>` or an unclosed `<li>` makes a lead-in | Fixed in 1d00910 |
| 4 | MINOR | Tab-indented sub-items read as top-level steps | Fixed in 1d00910 |
| 5 | MINOR | "May" (the month) flags vague; "You see 5 minutes" flags a wait | Fixed in 1d00910 and 6d78dba ("for N minutes" is a wait word) |
| 6 | MINOR | One broken `.check` line blocks every Write through the hook | Fixed in 1d00910 (a ValueError lets the call run; check.sh fails on the line); 6d78dba: a `.check` that cannot be read still blocks |
| 7 | MINOR | With no transcript, the hook blocks only the first write | Kept: a host with no transcript gets a reminder, not a proof (the script header says so) |
| 8 | MINOR | A relative file name from a subfolder crashes | Fixed in 1d00910, test in 6d78dba |
| 9 | MINOR | The project module is not listed with the other extension files | Fixed in 1d00910 (README, kit-update skill, sync_baseline header) |
| 10 | MINOR | Session load: 90-161.Z passes the cap after a sync | To the owner (the trade) |
| 11 | NIT | "Owner" with a capital O; the sync rename does not change it | To the owner, with the conflict-check findings |

## Review 2: the fix commit (ee60ece..1d00910)

| # | Severity | Finding | Done |
|---|---|---|---|
| 1 | MAJOR | The pointer fix let real pointers pass ("See page 4.", "Read the section **Install**.") | Fixed in 6d78dba, with tests |
| 2 | MAJOR | Guard files changed without the owner's approval | No defect: the owner asked for this work by the brief, and the pull request is lane C (the owner approves the merge) |
| 3 | MINOR | The hook fails open on a read error of `.check` | Fixed in 6d78dba |
| 4 | MINOR | New false pointers ("You see the other steps in the panel.") | Fixed in 6d78dba |
| 5 | MINOR | A note in a `<ul>` inside a step joins the step's text | Kept: the person reads that note at that step |
| 6 | MINOR | "Let it run for 10 minutes." is no wait finding | Fixed in 6d78dba |

## Review 3: the second fix commit (1d00910..6d78dba)

| # | Severity | Finding | Done |
|---|---|---|---|
| 1 | MAJOR | Pointer words dropped in 1d00910 (next, following, this, that, other, chapter) still pass ("See the next step.", "Repeat that step.") | Fixed in the next commit, with tests |
| 2 | MAJOR | The "You see" filter drops a whole sentence, so "You see the form, and see step 3." passes | Fixed: the filter works clause by clause, with a test |
| 3 | MINOR | Bare "section" flags on-screen text ("Open the Sections tab.") | Kept: the skill says to write on-screen names in bold, and bold text is not read |
| 4 | MINOR | No test of the fail-closed hook path | Fixed: a test with a `.check` that cannot be read |
| 5 | MINOR | "for ten minutes" and "for 2 mins" are no wait | Fixed, with tests |
| 6 | NIT | "You see the timer count for 10 minutes." is a wait finding | Fixed: wait words are read outside "You see" clauses, with a test |

## Review 4: the third fix commit

Result: added when the review ends.
