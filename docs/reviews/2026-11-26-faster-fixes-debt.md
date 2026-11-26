# Fleet debt: faster small fixes (2026-11-26)

The change: AGENTS.md "Fresh review" (a small change may use the fast-tier review; a later fix or a base merge with a conflict gets a review of its diff and the earlier findings) and "Checks" (a duplicate bracket removed), the approved texts T1-T11 of [the plan](2026-11-26-faster-fixes-plan.md). Record: docs/DECISIONS.md, row of 2026-11-26.

| Repo | Fails today | Fix plan |
|---|---|---|
| archimedes_lever (kit) | 0 (session load ~5,061 -> ~5,060 tokens, measured) | none |
| 90-161.Z | 0 (session load ~5,433 -> ~5,427 with an earlier T1 text, measured 2026-11-26 in a scratch copy; the final T1 text is 6 tokens longer, so about 5,433) | the next kit sync; add the `concurrency:` block (T10) to its own workflows `ps51.yml` and `codeql.yml` |
| Every other fleet repo | 0: the rules ask for less review, not more, and the AGENTS.md text does not grow; not measured per repo | the next kit sync; a repo with its own workflows (RADE: the Windows job) adds the T10 `concurrency:` block in its sync pull request |

The one-in-one-out step (T8) is for new rule lines only: no rule of today fails it.

debt-check: 210907f36b08
