#!/usr/bin/env bash
# Fill the template placeholders in a new project made from the kit (kit.config.json "kit_repo").
# Prevents: a new project keeps template placeholders, the wrong owner word or tier files, or the kit-only files, so it runs with unset values
# Usage: scripts/bootstrap.sh "Project Name" Owner/repo "One-line purpose" ["Owner name"] ["Time zone"] [starter|full]
# Owner name: what agents call the decider (default "the Maintainer"). A private repo may use your name; a public repo uses a role,
# for example "the maintainer".
# Time zone: an IANA name for project log times, for example Europe/Berlin or America/New_York (default UTC).
# Tier (default starter): starter keeps the core rules, hooks and checks, and the name denylist only warns when missing;
# full adds orchestration, the project log, the bloat audit and the rule tests (scripts/sync_baseline.py ADVANCED_FILES).
# The script deletes itself when it finishes. Review the result, then commit and push.
# Network: none.
# Writes: the files of this repo: it fills the placeholders, renames the owner word, applies the tier, writes README.md,
#   .check.state.json and .check.lock, and deletes the kit-only files and itself.
# Credentials: none.
set -euo pipefail

if [ $# -lt 3 ] || [ $# -gt 6 ]; then
  echo 'usage: scripts/bootstrap.sh "Project Name" Owner/repo "One-line purpose" ["Owner name"] ["Time zone"] [starter|full]' >&2
  exit 1
fi

owner_re='^[A-Za-z0-9 ._,()-]+$'
if [ $# -ge 4 ] && ! [[ "$4" =~ $owner_re ]]; then
  echo 'error: owner name: use letters, digits, space . _ , ( ) - only' >&2
  exit 1
fi

BS_TIER="${6:-starter}"
case "$BS_TIER" in starter|full) ;; *) echo "error: tier '$BS_TIER': use starter or full" >&2; exit 1 ;; esac

BS_TZ="${5:-UTC}"
if ! [[ "$BS_TZ" =~ ^[A-Za-z0-9_+/-]+$ ]] || { [ "$BS_TZ" != UTC ] && ! python3 -c 'import sys, zoneinfo; zoneinfo.ZoneInfo(sys.argv[1])' "$BS_TZ" 2>/dev/null; }; then
  echo "error: time zone '$BS_TZ' is not a known IANA name (for example UTC, Europe/Berlin, America/New_York)" >&2
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

# The dod-security line of .check, read before the first write: a typo must stop the run while the tree is unchanged.
if ! python3 -c 'import sys; sys.path.insert(0, "scripts"); from build_site_html import dod_security; dod_security(".")' 2>/dev/null; then
  echo "error: the dod-security line of .check is not 'on' or 'off'; correct it and run bootstrap again" >&2
  exit 1
fi

export BS_NAME="$1" BS_REPO="$2" BS_PURPOSE="$3" BS_OWNER="${4:-the Maintainer}" BS_TZ BS_DATE BS_TIME
# One clock read in the project time zone, so the date and time agree (project log times use it).
BS_STAMP="$(TZ="$BS_TZ" date '+%F %H:%M')"
BS_DATE="${BS_STAMP% *}"
BS_TIME="${BS_STAMP#* }"

# The kit's docs/DECISIONS.md and docs/LOG.md are the maintainer's own, public record (2026-11-13): a project starts from
# the blank copies in docs/templates/ instead.
for f in DECISIONS.md LOG.md; do
  if [ -f "docs/templates/$f" ]; then mv -f -- "docs/templates/$f" "docs/$f"; fi
done
rm -rf -- docs/templates

files=(AGENTS.md docs/NEXT_PROMPT.md docs/DECISIONS.md docs/host-prompts.md docs/LOG.md)
for f in "${files[@]}"; do
  perl -pi -e 's/\{\{PROJECT_NAME\}\}/$ENV{BS_NAME}/g; s/\{\{REPO\}\}/$ENV{BS_REPO}/g; s/\{\{PURPOSE\}\}/$ENV{BS_PURPOSE}/g;
    s/\{\{SHORT_NAME\}\}/(split " ", $ENV{BS_NAME})[0]/ge; s/\{\{DATE\}\}/$ENV{BS_DATE}/g; s/\{\{TIME\}\}/$ENV{BS_TIME}/g; s/\{\{TIMEZONE\}\}/$ENV{BS_TZ}/g; s/\{\{OWNER\}\}/the Maintainer/g;
    $_ = "" if /^> Template: first use fills in/' "$f"
done

# Replace the role word "the Maintainer" / "The Maintainer".
if [ "$BS_OWNER" != "the Maintainer" ]; then
  # The same files sync_baseline.py renames (those of its COPY_FILES that hold the owner word), so a sync right after bootstrap changes nothing.
  # Not renamed on purpose: docs/FIRST_USE.md and scripts/first_use_check.py, whose
  # "the owner" is an option, a role or a literal the script needs.
  # The list comes from the sync itself (COPY_FILES without NO_OWNER_RENAME), so it cannot fall behind it.
  mapfile -t kit_owner_files < <(python3 -c 'import os, sys; sys.path.insert(0, "scripts"); import sync_baseline as s; print("\n".join(f for f in s.COPY_FILES if f not in s.NO_OWNER_RENAME and os.path.isfile(f)))')
  owner_files=("${files[@]}" "${kit_owner_files[@]}" .check docs/MAINTAINER_RUNBOOK.md docs/check-config-schema.md)  # kit-only text a project keeps
  for f in "${owner_files[@]}"; do
    perl -pi -e 'my $c = ucfirst $ENV{BS_OWNER}; s/\b([Tt])he Maintainer\b/$1 eq "T" ? $c : $ENV{BS_OWNER}/ge' "$f"
  done
fi

# Tier: AGENTS.md blocks, and in starter the advanced files go (one list: scripts/sync_baseline.py ADVANCED_FILES).
python3 scripts/sync_baseline.py --set-tier "$BS_TIER"
if [ "$BS_TIER" = starter ] && [ -f .check ] && ! grep -qx 'denylist: warn' .check; then
  printf '%s\n' '# Starter tier: a missing name denylist warns instead of blocking. Delete this line to block (full tier default).' 'denylist: warn' >> .check
fi

log_link=""
[ -f docs/LOG.md ] && log_link=" Log: [docs/LOG.md](docs/LOG.md)."
cat > README.md <<EOF
# $BS_NAME

$BS_PURPOSE

Agents: read [AGENTS.md](AGENTS.md) first. Status: [docs/NEXT_PROMPT.md](docs/NEXT_PROMPT.md). Decisions: [docs/DECISIONS.md](docs/DECISIONS.md).$log_link

New to working with AI agents? Read [docs/WORKING_WITH_AGENTS.md](docs/WORKING_WITH_AGENTS.md).
EOF

present=(); for f in "${files[@]}" README.md; do [ -f "$f" ] && present+=("$f"); done
if ! python3 scripts/check_blocks.py --placeholders "${present[@]}"; then
  echo "error: placeholders remain (listed above)" >&2
  exit 1
fi

# The maintainer's preferences template (PREFERENCES.md), the kit's file list (docs/FILES.md) and its tool list (docs/tools.md) live only in the template repo. The kit's license moves next to the docs: the copied scripts
# stay under it, and the root LICENSE is the project's own choice (docs/FIRST_USE.md, question 6).
rm -f -- PREFERENCES.md docs/FILES.md docs/tools.md
# The kit's state (.check.state.json: its last audit and time baselines) is the kit's own. The project starts with a
# fresh file: the code standard adopted with no debt (the kit's code meets it), no audit yet and no time baselines.
printf '%s\n' '{' ' "code_standard": {' '  "debt": {}' ' }' '}' > .check.state.json
# The kit's own review reports describe the kit, not the project; docs/reviews/README.md stays.
find docs/reviews -maxdepth 1 -name '20*.md' -delete 2>/dev/null || true
# Projects do not stay in sync with the kit (the owner, 2026-11-13): the sync tools stay in the kit only.
# The token log hook is installed from the kit by the cloud setup scripts (the owner, 2026-11-17).
python3 scripts/sync_baseline.py --lock-here  # the kit lock (.check.lock) of the new project
rm -f -- scripts/sync_baseline.py scripts/sync_merge.py scripts/drift.py scripts/token_log.py scripts/token_log_test.py \
  scripts/drift_test.py scripts/sync_baseline_repo.py scripts/sync_baseline_run.py scripts/sync_baseline_stop.py scripts/token_log_test_report.py scripts/token_log_rows.py scripts/token_log_report.py \
  scripts/bootstrap_cli_test.py scripts/check_lock_cli_test.py scripts/drift_cli_test.py scripts/sync_baseline_cli_test.py \
  scripts/sync_merge_cli_test.py scripts/kit_config.py kit.config.json KIT_VERSION docs/CHANGELOG.md docs/KIT_HANDOFF.md \
  scripts/kit_package.py pyproject.toml  # the kit package (P3): a project installs it, it does not build it
# The kit's threat model describes the kit. The DoD group (sync_baseline.DOD_FILES) stays only with `dod-security: on`
# in .check (fleet v2 DEC 4: opt-in); a project writes its own threat model.
rm -f -- docs/threat-model.md
dod=0
python3 -c 'import sys; sys.path.insert(0, "scripts"); from build_site_html import dod_security
try:
    sys.exit(0 if dod_security(".") else 1)
except ValueError as e:
    print(e, file=sys.stderr)
    sys.exit(2)' || dod=$?
case "$dod" in
  0) ;;
  1) rm -f -- SECURITY.md .github/dependabot.yml .github/workflows/security.yml ;;
  *) echo "error: the dod-security line of .check is not 'on' or 'off'; correct it and run bootstrap again" >&2; exit 1 ;;
esac
if [ -f LICENSE ]; then mv -- LICENSE docs/archimedes_lever-LICENSE.txt; fi

rm -- "$0"
if [ "$BS_OWNER" != "the Maintainer" ] && [ -f .check ]; then
  echo "Note: the content check is on (.check). If \"$BS_OWNER\" is a real name in your denylist, the check blocks it: remove .check in a private repo."
fi
echo "Done. Next: review with 'git diff', then commit and push."
echo "Then paste the Project text from docs/host-prompts.md into the claude.ai Project instructions."
