# Plan: third-party skills (kit 5.0.0) and the design skill packs in 4 repos

Approved by the owner 2026-11-20 (America/Chicago), with its exact rule text. Session: "Kit · Third-party skill cap · 2026-11-20".

## Request

Install `npx impeccable install --providers=claude --project --yes` (impeccable 4.10.0, Apache-2.0, npm) and
`npx ui-ux-pro-max-cli init --ai claude` (ui-ux-pro-max-cli 2.15.0, MIT, npm) in sec-source, 90-161.Z, icf-source and RADE.

## Owner decisions (2026-11-20; scope: this install)

- Install everything the installers add (8 skills, 5 agents); drop the impeccable hooks (`.claude/settings.local.json`).
- Count third-party descriptions apart in the kit, with per-repo `.check` exemptions (not user-level, not a raised cap).
- Add a third-party notices file in each repo.
- Rule text ("Caps and audit"): `when the session load passes 5,000 tokens (third-party skills and agents in `.check`: own cap 1,500), or`.

## Steps

- [x] 1. Kit PR 78 (merged 2026-11-20, 24c2391); fix 5.0.1 PR 79 (59528df), found by the first sync.
- [-] (was 1) Kit PR: `audit-third-party:` list, kit cap `third_party_tokens` 1,500, tests, rule text, CHANGELOG (5.0.0: a changed kit rule text is MAJOR; the plan said 4.2.0). Fresh review and rule conflict check. Lane C.
- [ ] 2. Tags v5.0.0 and v5.0.1 (the owner; optional). Was: Tag v5.0.0 (the owner), or sync from the merge commit.
- [-] 3. Dropped by the owner 2026-11-20: the packs became one claude.ai skill (`ui-design`, uploaded by the owner), not files in each repo. Was: One PR per repo: kit sync, vendor files, `.check` lines (`audit-third-party:` x13, `code-exclude:` vendor skill folders, `skip:` google-fonts.csv, google-font-licenses.json, design-system/scripts/generate-slide.py), no settings.local.json, THIRD_PARTY_NOTICES.md. Fresh review. Lane C.

## Measured (2026-11-20, before)

Session load with all 13 descriptions: sec-source ~5,699, 90-161.Z ~5,814, icf-source ~5,927, RADE ~5,925; without: ~4,760, ~4,875, ~4,988, ~4,986 tokens.

## Change (the owner, 2026-11-20)

The owner asked for one skill usable on any repo. Cloud sessions do not install plugins that a repo or a user's machine enables (https://code.claude.com/docs/en/cloud-environments.md); they load skills enabled on claude.ai. So the wrapper `ui-design` and 4 packs (impeccable, ui-ux-pro-max, ui-styling, design-system; the owner dropped design, brand, banner-design and slides on 2026-11-20; each `SKILL.md` renamed `SKILL.vendor.md`, agents under `packs/impeccable/agents/`) are one claude.ai skill. No project repo holds them; kit 5.0.x stays for later third-party skills.
