# Fleet debt: context trim R1-R3 (2026-11-25)

The change: AGENTS.md "Caps and audit", "Start of session" and the "Project rules" comment get the shorter texts that the Maintainer approved on 2026-11-25 (R1-R3 of [the close-out report](2026-11-25-closeout-and-trim-proposals.md) B4; record: docs/DECISIONS.md, row of 2026-11-25). No check, cap or trigger changes: the caps stay in `scripts/bloat_check.py` (KIT_CAPS) and `.check`, and the check-in still prints the AUDIT DUE and cap lines.

| Repo | Fails today | Fix plan |
|---|---|---|
| archimedes_lever (kit) | 0 (session load falls from ~5,471 to ~5,355 tokens) | none |
| Every fleet repo | 0: the change is shorter kit text, not a stricter rule; each repo's session load falls by about 116 tokens at its next kit sync (33-332.Z needs this: its last record is 5,504 > 5,500) | the next kit sync |

debt-check: 124fc6a7a950
