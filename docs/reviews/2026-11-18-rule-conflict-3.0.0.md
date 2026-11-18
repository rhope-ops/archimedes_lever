# Rule conflict check: kit 3.0.0

Date: 2026-11-18 (America/Chicago). Method: `.claude/skills/rule-change/SKILL.md`, fresh-context `reviewer` agents on the session tier.

Changed rule lines (exact texts approved by the owner): "Checks" (in a public repo the pull-request Action must finish green; a private repo skips it), "Secrets and personal data" and "Guards and checks" (the pull-request scan runs in public repos).

| Round | Hash | Result | Action |
|---|---|---|---|
| 1 | af6098efe43a | 1 MAJOR: the 2026-11-17 private-repo row was still in force; 2 MINOR | New row names it in Replaces; dead private branch removed from check.yml |
| 2 | af6098efe43a | 1 MAJOR: "Secrets and personal data" said every pull request is scanned | The owner approved the two enforcement texts |
| 3 | 5202e5f05232 | No MAJOR finding; 4 MINOR (wording that does not say "public repos") | deliver table fixed; the rest recorded |

Open MINOR: `.claude/skills/personal-data/SKILL.md` line 13, docs/FILES.md `.check` row, README "every pull-request check fails" do not say the pull-request scan is public-repo only.

rule-conflict-check: 5202e5f05232
