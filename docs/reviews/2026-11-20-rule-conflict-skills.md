# Rule conflict check: "Skills" and "Caps and audit" (kit 6.0.0), 2026-11-20

Changed lines (AGENTS.md "Defaults"), both approved by the owner 2026-11-20 07:36 with the plan [2026-11-20-skill-use-plan.md](2026-11-20-skill-use-plan.md), texts A and B:

- New: "**Skills.** When a skill's description matches the step, load the whole skill with the Skill tool before the step (a slice read through the shell misses steps). For a page, a tool, an artifact or a UI change, load `.claude/skills/verify/SKILL.md` and, where the owner's account has them, the `pages-and-tools` and `ui-design` skills."
- "Caps and audit", last sentences. Old: "The full audit runs when the owner asks for it: `.claude/skills/audit/SKILL.md`. A run slower than its baseline: `.claude/skills/efficiency/SKILL.md`." New: "The full audit runs when the owner asks for it, and a run slower than its baseline uses the same skill: `.claude/skills/audit/SKILL.md`."

Reviewer: the `reviewer` subagent, fresh context, the author's model tier. Input: the changed lines as `--rules` lists them, the whole AGENTS.md, docs/DECISIONS.md, and the skill's brief. Head: 5828db4.

## Findings

- MAJOR: none.
- MINOR 1: the new line could put icf-source and RADE over the 5,000-token session load (the reviewer's estimate: about 5,027). Checked by a dry-run sync in scratch copies after the description cuts of this change: RADE ~4,986 before, ~4,984 after; icf-source ~4,977 to ~4,975; 90-161.Z ~4,875 to ~4,873; sec-source ~4,760 to ~4,758. No change needed.
- MINOR 2: "Skills" says "load the whole skill with the Skill tool"; "Kit files" says a project's PROJECT.md is read with the skill and wins. The Skill tool loads only SKILL.md. Recorded; a text change ("and its PROJECT.md") is the owner's.
- MINOR 3: "Skills" names no fallback for a host with no Skill tool (a claude.ai chat, a subagent). Recorded; a text change ("else read the whole file") is the owner's.
- MINOR 4: "Caps and audit" could be read as "a slow run runs the full audit". The audit skill's first paragraph says to read only "A slow run" for that case. Recorded.
- NIT 5: "Skills" and "Verification" both name `.claude/skills/verify/SKILL.md`.
- NIT 6: 29 kit rule bullets against the guide of 28 (a warning, not a cap).
- NIT 7: the 2026-11-16 decision rows on `efficiency` are replaced in part; the new row's "Replaces" cell names the pointer only.

rule-conflict-check: f50d99df5d12

## Second check (the owner's new "Skills" first sentence), 2026-11-20

The owner answered MINOR 2 and 3 in a dialog with this exact text for the first sentence of "Skills": "When a skill's description matches the step, load the whole skill before the step: with the Skill tool, else read the whole file; read its PROJECT.md too (a slice read through the shell misses steps)." The second sentence and the "Caps and audit" line are as above.

Reviewer: the `reviewer` subagent, fresh context, the author's model tier; same input and brief.

- MAJOR: none.
- MINOR 1: "Skills" ("read its PROJECT.md too") and "Kit files" ("read it with the skill; it wins over the skill") give the same order in two lines. Recorded; a cut in "Kit files" is the owner's.
- MINOR 2: the session load (the reviewer's estimate: icf-source about 5,050). Measured by a dry-run sync in scratch copies with the final files: RADE ~4,986, icf-source ~4,977, 90-161.Z ~4,875, sec-source ~4,760, each equal to its number before the sync (5 descriptions were shortened for the longer line).
- MINOR 3: "uses the same skill" in "Caps and audit" can be read as "run the full audit" (as MINOR 4 above). Recorded.
- NIT 4: "Skills" and "Verification" both name the verify skill. NIT 5: the "Replaces" cell: fixed (it now names the `efficiency` skill rows).

rule-conflict-check: d1c1909217ed
