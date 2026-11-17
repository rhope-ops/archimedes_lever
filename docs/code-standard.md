# Code standard

Decided by the owner, 2026-11-17 (docs/DECISIONS.md): all code is lean, modular, commented and human-editable, and stays so as work continues. Why: a person must be able to read any script and know what it does before they run it. [scripts/code_standard.py](../scripts/code_standard.py) enforces the rules marked **(check)**; the fresh reviewer of each pull request checks the rules marked **(review)**.

The kit owns this file and the check. A project gets both by sync; it sets its own caps, scope and stricter rules (for example full docs per function) in its own `.code-standard.json` and a section below, never in a copy of the check.

## Scope

- Every file git tracks with the extension `.py`, `.ps1`, `.psm1`, `.js`, `.mjs`, `.cjs` or `.sh`, and every file with no extension whose first line is a shell or Python shebang (for example scripts/git-hooks/pre-push).
- Generated files get rule C6 only (their source gets the other rules). The list is `config.generated` in [.code-standard.json](../.code-standard.json).

## Rules

| No. | Rule | How |
|---|---|---|
| C1 | Each source file starts with a header comment: what the file is for, its inputs, its outputs and how to run it. Python: the module docstring. | **(check)** at least 60 characters; **(review)** the content |
| C1 safety | Opt-in: a project sets `"c1_safety": true` in its `.code-standard.json` "config". Then each source file's header also has the three lines `Network:` (the hosts it reaches, or "none"), `Writes:` (the files, lists or sites it changes, or "none") and `Credentials:` (what it asks for and how, or "none"), so a reviewer finds them before a run. | **(check)** the three labels; **(review)** true |
| C2 | Each function has a comment that says what it does. One line is enough; full parameter docs are not required. Python: a docstring, or a `#` line directly above the `def` or before its first statement. Shell and JS: a comment line directly above. The file header and a divider line (`# ----`) do not count. | **(check)** present; **(review)** true and useful |
| C3 | A function is at most 60 lines long. A longer job is split into named steps, each its own function. | **(check)** |
| C4 | A file is at most 600 lines long. A larger program is split into modules, one concern each. | **(check)** |
| C5 | One function lives in one file. A copy that must also run alone is generated, between marker lines `# >>> <name>: generated from <source> ...` and `# <<< <name>`. | **(check)** same body twice fails |
| C6 | A generated file says `GENERATED` in its first 15 lines and names its source and the command that builds it. | **(check)** |
| C7 | Names say what a thing is or does: Python `snake_case`; PowerShell `Verb-Noun`; no one-letter names except loop counters and short lambdas. | **(review)** |
| C8 | A comment says why or what, in plain English, and is true. Remove a comment the code makes obsolete in the same change. | **(review)** |
| C9 | No magic values: a fixed number, path, address or limit is a named constant with a comment that says where it comes from. | **(review)** |
| C10 | Each Python and PowerShell file parses. | **(check)** |
| C2 full | Opt-in: a project sets `"c2": "full"` in its `.code-standard.json` "config". Then each function longer than 10 lines also documents each parameter and its return value, in the form its language's own help tools read. Python: a docstring with an `Args:` section that names each parameter (not `self` or `cls`) and a `Returns:` section when it returns a value (PEP 257). PowerShell: comment-based help (.SYNOPSIS or .DESCRIPTION) with one `.PARAMETER` per parameter, placed where `Get-Help` finds it (about_Comment_Based_Help). JavaScript: a `/** */` JSDoc block directly above, with one `@param` per parameter and `@returns` when it returns a value. Shell: the C2 comment only. | **(check)** [scripts/code_standard_docs.py](../scripts/code_standard_docs.py); **(review)** true and useful |
| C11 | Lean: no dead code, no unused option, no second way to do the same job; prefer the standard library over a new dependency. A change does not make a check run slower than its baseline (.claude/skills/efficiency/SKILL.md). | **(review)**; time: `scripts/check.sh` TIME line |

## The ratchet

- `.code-standard.json` `debt` lists the violations that existed when a repo adopted the standard (empty in the kit). A violation not in that list fails; a listed function or file that grows fails.
- A listed item that is fixed also fails until the same change lowers the baseline (`--update`, which refuses new debt). So the list can only shrink.
- A rule turned on later (for example `"c2": "full"`): `--adopt` lists its current debt once, in the same change as a docs/DECISIONS.md row that names `.code-standard.json`; a second `--adopt` is refused. It never touches the debt of a rule the ratchet already holds.
- Never add an item to the baseline by hand, raise a cap or add an `exclude` to pass (AGENTS.md "Checks"). The check compares the baseline with the one on the merge base with origin/main; a cap or scope change needs a docs/DECISIONS.md row that names `.code-standard.json`.

## Commands

- Check: `python3 scripts/code_standard.py` (scripts/check.sh runs it in both lanes). Pass = last line `CODE-STANDARD pass`.
- Every measurement: `--report`. Lower the baseline after a fix: `--update`. A project's first baseline: `--init`. A rule just turned on: `--adopt`. Prove the check: `--test`.
