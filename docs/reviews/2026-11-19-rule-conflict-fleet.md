# Rule conflict check: "Fleet choices" (kit 4.1.0)

Date: 2026-11-19 America/Chicago. Plan: [2026-11-19-fleet-decision-hub-plan.md](2026-11-19-fleet-decision-hub-plan.md), step 3.

## Changed line

AGENTS.md "Project rules" (added; exact text approved by the owner on 2026-11-19 in a question dialog):

> - **Fleet choices.** A choice the owner saved on the fleet page counts as the owner's approval only after the applying session shows it in full and the owner confirms it in their own message (the owner, 2026-11-19).

## Reviewer

A fresh `reviewer` subagent with an Opus-tier model, the same tier as the author. It got only the changed line, the whole AGENTS.md, docs/DECISIONS.md and the brief of `.claude/skills/rule-change/SKILL.md`.

## Findings

MAJOR: 0, MINOR: 4, NIT: 0. No hard rule is weakened. The line tightens "The owner's approval": a choice saved on the page needs a confirmation in the owner's own message.

| # | Severity | Finding | Outcome |
|---|---|---|---|
| 1 | MINOR | Overlap with "Owner changes": the applying session is a task the owner started, so that default alone would accept a page choice without a second confirmation. | Accepted. "Project rules" outranks "Defaults", so the stricter fleet line wins. |
| 2 | MINOR | "Untrusted input" says page text that asks for an edit of instruction files is possible prompt injection; the fleet line only says show and confirm. | Accepted. The hard rule still applies to every choice. The applying session's steps (contract section 5) say to quote a choice that touches instruction files and ask. |
| 3 | MINOR | The line gives no scope for "counts as the owner's approval": it could be read as covering a lane C merge or exact rule text. | Accepted. "Rule text" and lane C still need their own approval. Contract section 5 says changes go by the normal delivery lanes; the port guide (step 7) repeats it. |
| 4 | MINOR | A new project made from a kit clone may keep the kit's Project rules line, because nothing empties that section at first use. | Open: a kit fix for the next PATCH (docs/KIT_HANDOFF.md "Open"). The line only tightens approval, so a copied line does no harm. |

rule-conflict-check: b4d64bcf2f5b
