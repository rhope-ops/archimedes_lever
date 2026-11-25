# Fleet debt: instructions at "80%" (2026-11-25)

The change (plan: [2026-11-25-instructions-80-plan.md](2026-11-25-instructions-80-plan.md)): the hard rule "Instructions people follow" gets the approved text; `scripts/check_instructions.py` drops the `next` and `cue` findings, allows up to 3 actions in one step, and adds one stricter finding, `filler` (a sentence that is only "Go on." or "Continue.").

Only `filler` is stricter, and it reads only the files that a repo's `.check` names in `audit-instructions:` lines.

| Repo | `audit-instructions:` files | Fails today | Fix plan |
|---|---|---|---|
| archimedes_lever (kit) | README.md, docs/github/README.md, docs/MAINTAINER_RUNBOOK.md, docs/check-config-schema.md | 0 (fixed in this change: 90 "Go on." removed from README.md, SECURITY.md and docs/MAINTAINER_RUNBOOK.md) | done |
| 90-161.Z | go.md, README.md, scripts/paste_bundles.json | go.md 33, README.md 33 (a copy of go.md), paste_bundles.json 0 | Phase 2 of the plan rewrites go.md in the new style in the same pull request as the kit sync |
| RADE | none | 0 | none (its instruction texts get the new style in a later session) |
| 33-332.Z, SPAR, 65-601.Z, 36-3003.Z | none (public `.check` read 2026-11-25) | 0 | none |
| ICF-Source, SEC-Source, no-more-beyond, other private repos | not readable from this session | unknown | Phase 3: each kit-sync session runs `python3 scripts/check_instructions.py` on the synced branch and deletes each "Go on." sentence in the same pull request |

debt-check: 8fbc03e13926
