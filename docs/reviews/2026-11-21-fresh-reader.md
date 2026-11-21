# Fresh-reader test: kit README steps (2026-11-21)

- Files: README.md (the 5 procedures: way A, way B, "Set up a project by hand", "Keep personal data out", "Update an existing project"). docs/github/README.md passes the check and has no numbered steps that the check reads.
- Reader: the `reviewer` subagent, a fresh context each round, model tier opus. Input: only the steps, cut from README.md into one file. Brief: the one in `.claude/skills/instructions/SKILL.md` "Fresh-reader test", plus "mark a button, page or box that is not on that screen".
- `python3 scripts/check_instructions.py README.md docs/github/README.md`: 47 findings before, 0 after each round.

| Round | Steps | Marked | Main causes |
|---|---|---|---|
| 1 | 79 | 25 | Commit before the noreply address was set; update pushed to the default branch; Windows and Notepad gaps; a value to remember (the repository name) |
| 2 | 76 | 21 | No `user.name`; the `git diff` pager; no branch update before the sync branch; two ways in one step (way B) |
| 3 | 76 | 17 | `gh auth login` outside the steps; no step for a failed check; claude.ai screen names |

After round 3, every mark that the author can check was fixed. The marks left all name claude.ai screens, which the author cannot see from a cloud session (unverified):

| Procedure | Step | What is not verified |
|---|---|---|
| A (web) | 6, 7 | The name of the button that connects GitHub, and the GitHub page that gives access to one repository |
| A (web) | 8 | The name of the repository picker on claude.ai/code, and whether an environment must be chosen |
| B | 4 | What a first run of `claude` asks (sign-in, trust of the folder) |
| Keep personal data out | 11 | Where the environment menu and its **Edit** item are in a Claude Code web session |
| By hand | 21, 23 | The names of the Project instructions control and its save button on claude.ai |

Result: the owner checks these 7 steps on screen before the merge, or the merge goes with them marked unverified.
