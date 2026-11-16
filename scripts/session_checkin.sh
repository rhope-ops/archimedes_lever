#!/usr/bin/env bash
# Session check-in: run at the start and the end of each session.
set -uo pipefail
t0=$(date +%s%N 2>/dev/null)  # nanoseconds where date has %N (GNU); the run's time is compared with its baseline below
top=$(git rev-parse --show-toplevel) && cd "$top" || exit 1  # paths below are repo-relative; a run from a subfolder must still find them

git fetch --quiet origin main 2>/dev/null || echo "warning: fetch of origin/main failed"

# Git hooks for every agent (scripts/git-hooks/pre-push blocks force-pushes). Set when no hooks path is set, when it is the
# old relative value, or when it names a scripts/git-hooks folder that is gone (a moved clone). The path is absolute, in
# the main clone (not a linked worktree that can be removed): git looks for a relative path in the folder a command runs
# in, so "git --git-dir=<repo>/.git push" from another folder would find no hook. Another hooks path is kept.
# core.hooksPath hides .git/hooks; our pre-push chains to an old .git/hooks/pre-push (Git LFS). Other old hooks: warned below.
hooks=$(git config --get core.hooksPath || true)
common=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
want="$(dirname "$common")/scripts/git-hooks"
[ "$(basename "$common")" = .git ] && [ -d "$want" ] || want="$top/scripts/git-hooks"
installed="" fix=0
case "$hooks" in
  ''|scripts/git-hooks) fix=1 ;;
  */scripts/git-hooks) [ -d "$hooks" ] || fix=1 ;;
esac
if [ "$fix" = 1 ] && [ -d "$want" ]; then
  git config core.hooksPath "$want" && hooks="$want" && installed=" (installed now)"
fi
echo "hooks:       ${hooks:-none}${installed:-}"
if [ "$hooks" = "$want" ]; then
  for h in "$(git rev-parse --git-common-dir)"/hooks/*; do
    case "$h" in *.sample|*/pre-push) continue ;; esac
    [ -x "$h" ] && echo "warning: $(basename "$h") in .git/hooks is not run while core.hooksPath is set; copy it to scripts/git-hooks or unset core.hooksPath"
  done
fi
echo "branch:      $(git rev-parse --abbrev-ref HEAD)"
echo "head:        $(git rev-parse --short HEAD)"
echo "origin/main: $(git rev-parse --short origin/main 2>/dev/null || echo unknown)"

if counts=$(git rev-list --left-right --count HEAD...origin/main 2>/dev/null); then
  read -r ahead behind <<<"$counts"
  echo "ahead:       $ahead"
  echo "behind:      $behind"
else
  echo "ahead/behind: unknown (shallow clone or no origin/main)"
fi

uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
echo "uncommitted: $uncommitted"
[ "$uncommitted" -gt 0 ] && git status --short

[ -f scripts/bloat_check.py ] && python3 scripts/bloat_check.py --brief
# The last check run in this clone: lane, wall time and the 3 slowest checks (scripts/check.sh writes it).
last="$(git rev-parse --git-dir)/check-last"
[ -f "$last" ] && echo "check:       $(sed 's/^TIME  //' "$last")"
# Personal-data guard: list source, entry count, fingerprint (compare it between places) and tier; never the names.
if [ -f .pii-guard ] && [ -f scripts/pii_guard.py ]; then python3 scripts/pii_guard.py --status || true; fi

# The kit itself keeps its placeholders on purpose (same origin rule as TEMPLATE_NAME in scripts/first_use_check.py).
origin=$(git remote get-url origin 2>/dev/null); origin=${origin%/}; origin=${origin%.git}; origin=${origin##*/}
if [ "$(printf '%s' "$origin" | tr '[:upper:]' '[:lower:]')" != "archimedes_lever" ] && grep -rIl '{{[A-Z_]*}}' --exclude-dir=.git --exclude=bootstrap.sh --exclude=session_checkin.sh --exclude=sync_baseline.py --exclude=first_use_check.py --exclude=drift.py --exclude=check.sh --exclude=README.md . >/dev/null 2>&1; then
  echo "warning: template placeholders remain; run scripts/bootstrap.sh"
fi
# This run's time against the "checkin" baseline in .bloat-audit.json (warn only; .claude/skills/efficiency/SKILL.md).
case "$t0" in *N|'') ;; *) [ -f scripts/bloat_check.py ] && python3 scripts/bloat_check.py \
  --compare "checkin=$(awk -v a="$t0" -v b="$(date +%s%N)" 'BEGIN {printf "%.1f", (b - a) / 1e9}')" 2>&1 | tail -n 1 ;; esac
exit 0
