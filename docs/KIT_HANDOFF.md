# Kit handoff: archimedes_lever

The kit's own handoff (AGENTS.md "Handoff"; first use deletes it, and a project uses docs/NEXT_PROMPT.md). At most 40 lines, inside the session-load cap (`.check` counts it); evidence and older items: docs/reviews/. Times: America/Chicago.

Updated: 2026-11-28 06:50: kit 16.0.1 (`FLEET-MASTER-PLAN-v4.md` Batch F4a). Older items: [archive file](reviews/2026-11-24-kit-handoff-archive.md).

## State

- Kit 16.0.1: compressed `IMMUTABLE NIPR code safety` rule in `AGENTS.md`, added `Unblock-File` / `Zone.Identifier` removal guard in `scripts/nipr_guard.py`, guarded `security.yml` `--kit-install`, and added `.github/workflows/release.yml`.
- Fleet syncs: `rade` (`Batch F4c`), `kanon` (`Batch F6`), `ion` (`Batch F7`), and secondary repos (`Batch F8`) sync `16.0.1`.

## Open

- Skill-use audit due 2026-12-08.
- Open items in the [close-out list](reviews/2026-11-25-closeout-and-trim-proposals.md).

## Needs the Administrator

- Add the Dependabot secret `PII_GUARD_DENYLIST` if still missing on older Dependabot PRs.

## Do not

- Do not merge a kit pull request before listing open pull requests.
- Do not put a command that holds a denied git pattern in a shell heredoc: use the file tool.
- Do not loop on MINOR conflict findings: record them; only a MAJOR finding changes rule text again.
- Do not add kit text without measuring the session load of every repo first (`scripts/bloat_check.py --brief`): `kanon` is near the 5,500 cap.
