#!/usr/bin/env bash
# Fill the template placeholders in a new project made from rhope-ops/archimedes_lever.
# Usage: scripts/bootstrap.sh "Project Name" Owner/repo "One-line purpose" ["Owner name"] ["Time zone"] [starter|full]
# Owner name: what agents call the decider (default "the owner"). A private repo may use your name; a public repo uses a role,
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

export BS_NAME="$1" BS_REPO="$2" BS_PURPOSE="$3" BS_OWNER="${4:-the owner}" BS_TZ BS_DATE BS_TIME
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
    s/\{\{SHORT_NAME\}\}/(split " ", $ENV{BS_NAME})[0]/ge; s/\{\{DATE\}\}/$ENV{BS_DATE}/g; s/\{\{TIME\}\}/$ENV{BS_TIME}/g; s/\{\{TIMEZONE\}\}/$ENV{BS_TZ}/g; s/\{\{OWNER\}\}/the owner/g;
    $_ = "" if /^> Template: first use fills in/' "$f"
done

# Replace the role word "the owner" / "The owner".
if [ "$BS_OWNER" != "the owner" ]; then
  # The same files sync_baseline.py renames (those of its COPY_FILES that hold the owner word), so a sync right after bootstrap changes nothing.
  # Not renamed on purpose: docs/FIRST_USE.md and scripts/first_use_check.py, whose
  # "the owner" is an option, a role or a literal the script needs.
  owner_files=("${files[@]}" .claude/skills/delegate/SKILL.md .claude/skills/audit/SKILL.md .claude/skills/project-log/SKILL.md .claude/skills/deliver/SKILL.md .claude/skills/personal-data/SKILL.md .claude/skills/rule-change/SKILL.md .claude/skills/handoff/SKILL.md .claude/skills/kit-update/SKILL.md .claude/skills/data-change/SKILL.md .claude/skills/verify/SKILL.md .claude/skills/instructions/SKILL.md
    .claude/agents/reviewer.md .github/workflows/check.yml .claude/rule-tests.md scripts/bloat_check.py scripts/bloat_check_rules.py scripts/bloat_check_timing.py scripts/bloat_check_test_rules.py scripts/session_checkin.sh scripts/stop_check.py scripts/worker_guard.py scripts/check_lock.py
    scripts/log_check.py scripts/timeline.py scripts/check_content.py scripts/check_content_scan.py scripts/check_content_hook.py scripts/check_content_test.py scripts/check_content_test_blocks.py
    scripts/bloat_check_skills.py scripts/bloat_check_test.py scripts/check_settings.py scripts/check_settings_read.py scripts/code_standard.py scripts/code_standard_test.py scripts/code_standard_docs.py docs/code-standard.md scripts/check.sh scripts/git-hooks/pre-push)
  for f in "${owner_files[@]}"; do
    perl -pi -e 'my $c = ucfirst $ENV{BS_OWNER}; s/\b([Tt])he owner\b/$1 eq "T" ? $c : $ENV{BS_OWNER}/ge' "$f"
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

# The maintainer's preferences template (PREFERENCES.md) and the kit's file list (docs/FILES.md) live only in the template repo. The kit's license moves next to the docs: the copied scripts
# stay under it, and the root LICENSE is the project's own choice (docs/FIRST_USE.md, question 6).
rm -f -- PREFERENCES.md docs/FILES.md
# The kit's state (.check.state.json: its last audit and time baselines) is the kit's own. The project starts with a
# fresh file: the code standard adopted with no debt (the kit's code meets it), no audit yet and no time baselines.
printf '%s\n' '{' ' "code_standard": {' '  "debt": {}' ' }' '}' > .check.state.json
# The kit's own review reports describe the kit, not the project; docs/reviews/README.md stays.
find docs/reviews -maxdepth 1 -name '20*.md' -delete 2>/dev/null || true
# Projects do not stay in sync with the kit (the owner, 2026-11-13): the sync tools stay in the kit only.
# The token log hook is installed from the kit by the cloud setup scripts (the owner, 2026-11-17).
python3 scripts/sync_baseline.py --lock-here  # the kit lock (.check.lock) of the new project
rm -f -- scripts/sync_baseline.py scripts/sync_merge.py scripts/drift.py scripts/token_log.py scripts/token_log_test.py \
  KIT_VERSION docs/CHANGELOG.md docs/KIT_HANDOFF.md
if [ -f LICENSE ]; then mv -- LICENSE docs/archimedes_lever-LICENSE.txt; fi

rm -- "$0"
if [ "$BS_OWNER" != "the owner" ] && [ -f .check ]; then
  echo "Note: the content check is on (.check). If \"$BS_OWNER\" is a real name in your denylist, the check blocks it: remove .check in a private repo."
fi
echo "Done. Next: review with 'git diff', then commit and push."
echo "Then paste the Project text from docs/host-prompts.md into the claude.ai Project instructions."
