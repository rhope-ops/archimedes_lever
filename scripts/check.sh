#!/usr/bin/env bash
# One check command for the repo (AGENTS.md "Commands": Test), in two lanes (.claude/skills/deliver/SKILL.md):
#   scripts/check.sh          full lane: everything. Before a merge, on a push to main (pre-push), in the pull-request Action.
#   scripts/check.sh --fast   fast lane: each push to another branch (pre-push). Self-tests only of the kit scripts that
#                             changed against origin/main, and scripts/check.local.sh gets --fast.
# The checks:
#   1. the self-test of each kit script present (--test; a starter project has fewer),
#   2. the rule caps and the paths AGENTS.md names (scripts/bloat_check.py --rules; full tier),
#   3. the project log check (full tier),
#   4. the personal-data scan of all tracked files (when .pii-guard exists; in GitHub Actions the pii-guard step does it;
#      with --no-pii the caller does it: the pre-push hook scans files and pushed commits in one run),
#   5. scripts/check.local.sh, when it exists: this project's own tests (SKIP when missing: AGENTS.md Delivery then gates main).
# The checks run in parallel: each one works on its own temporary files. CHECK_SERIAL=1 runs them one at a time.
# Prints one PASS/FAIL/SKIP line per check, the output of each failed check, a TIME line (wall time and the 3 slowest
# checks) and "CHECK PASS" or "CHECK FAIL" last. Exit 0 only when no check failed. Needs bash, git and python3.
# Stamp: a lane that passes on a clean tree writes "<lane> <commit>" to .git/check-pass. With --cached, a run on the
# same commit and a clean tree passes at once (the full stamp covers both lanes). Never write the stamp by hand.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

lane=full cached=0 pii=1
for a in "$@"; do
  case "$a" in
    --fast) lane=fast ;;
    --cached) cached=1 ;;
    --no-pii) pii=0 ;;
    *) echo "usage: scripts/check.sh [--fast] [--cached] [--no-pii]" >&2; exit 2 ;;
  esac
done

gitdir="$(git rev-parse --git-dir)"
stamp="$gitdir/check-pass"
head="$(git rev-parse HEAD 2>/dev/null || echo none)"
clean() { [ -z "$(git status --porcelain 2>/dev/null)" ]; }
if [ "$cached" = 1 ] && [ -f "$stamp" ] && clean; then
  read -r s_lane s_head <"$stamp" || true
  if [ "${s_head:-}" = "$head" ] && { [ "${s_lane:-}" = full ] || [ "$lane" = fast ]; }; then
    echo "CHECK PASS (cached: the $s_lane lane passed on ${head:0:7}, clean tree)"
    exit 0
  fi
fi

now() {  # microseconds; whole seconds where bash has no EPOCHREALTIME (bash 3)
  if [ -n "${EPOCHREALTIME:-}" ]; then printf '%s' "${EPOCHREALTIME/[.,]/}"; else printf '%s000000' "$(date +%s)"; fi
}
secs() { printf '%d.%d' $(($1 / 1000000)) $((($1 % 1000000) / 100000)); }

# Fast lane: the files that differ from the merge base with the default branch, uncommitted and untracked ones included.
changed="*all*"
if [ "$lane" = fast ]; then
  for r in origin/main origin/master; do
    if base="$(git merge-base HEAD "$r" 2>/dev/null)"; then
      changed="$( { git diff --name-only "$base"; git ls-files -o --exclude-standard; } 2>/dev/null | sort -u)"
      break
    fi
  done
fi
touched() {  # true when the lane is full, the base is unknown, or one of the named files (or this script) changed
  [ "$changed" = "*all*" ] && return 0
  local p
  for p in scripts/check.sh "$@"; do printf '%s\n' "$changed" | grep -qxF -- "$p" && return 0; done
  return 1
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
n=0 pass=0 fail=0 skip=0 untested=0
names=()
t0="$(now)"

run() {  # run NAME COMMAND...: start the check in the background; results are collected below
  local name="$1" i; shift
  n=$((n + 1)); i=$n; names[i]="$name"
  (
    s="$(now)"
    "$@" >"$tmp/$i.out" 2>&1; rc=$?
    echo "$rc $(( $(now) - s ))" >"$tmp/$i.rc"
  ) &
  [ "${CHECK_SERIAL:-}" = 1 ] && wait
  return 0
}
skips=()
skip() { skips+=("SKIP  $1 ($2)"); skip=$((skip + 1)); }
selftest() {  # selftest NAME FILE [MORE FILES IT DEPENDS ON...] -- COMMAND...
  local name="$1" file="$2" deps=(); shift
  while [ "$1" != "--" ]; do deps+=("$1"); shift; done; shift
  [ -f "$file" ] || return 0  # absent: not in this tier
  if touched "${deps[@]}"; then run "$name self-test" "$@"; else untested=$((untested + 1)); fi
}

for s in stop_check worker_guard log_check timeline bloat_check; do
  selftest "$s" "scripts/$s.py" -- python3 "scripts/$s.py" --test
done
selftest pii_guard scripts/pii_guard.py -- python3 scripts/pii_guard.py --test
selftest first_use_check scripts/first_use_check.py scripts/pii_guard.py -- python3 scripts/first_use_check.py --test
# Kit only: projects have no sync tools. The drift self-test reads the kit's AGENTS.md and stop_check.py.
selftest drift scripts/drift.py scripts/sync_baseline.py AGENTS.md scripts/stop_check.py -- python3 scripts/drift.py --test
selftest pre-push scripts/git-hooks/pre-push -- scripts/git-hooks/pre-push --test
[ "$untested" -gt 0 ] && skip "$untested self-tests" "fast lane: those scripts did not change; the full lane runs them"

if [ -f scripts/bloat_check.py ]; then run "rule caps and pointers" python3 scripts/bloat_check.py --rules; fi

if [ ! -f scripts/log_check.py ]; then
  :  # starter tier: no project log
elif grep -q '{{PROJECT_NAME}}' AGENTS.md 2>/dev/null && grep -q '{{PROJECT_NAME}}' docs/LOG.md 2>/dev/null; then
  skip "project log" "template placeholders: run first use"
elif [ -f docs/LOG.md ]; then
  run "project log" python3 scripts/log_check.py docs/LOG.md
else
  skip "project log" "no docs/LOG.md: the log lives in the place AGENTS.md Project rules names"
fi

if [ ! -f .pii-guard ]; then
  skip "personal-data scan" "no .pii-guard: guard off"
elif [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  skip "personal-data scan" "GitHub Actions: the pii-guard step scans with the base allow list"
elif [ "$pii" = 0 ]; then
  skip "personal-data scan" "the pre-push hook scans the files and the pushed commits next"
else
  run "personal-data scan" python3 scripts/pii_guard.py --all
fi

if [ -f scripts/check.local.sh ]; then
  if [ "$lane" = fast ]; then
    run "project checks (check.local.sh --fast)" bash scripts/check.local.sh --fast
  else
    run "project checks (check.local.sh)" bash scripts/check.local.sh
  fi
else
  skip "project checks" "no scripts/check.local.sh: no project tests yet; AGENTS.md Delivery gates main"
fi

wait
times=""
for ((i = 1; i <= n; i++)); do
  rc=1 us=0
  [ -f "$tmp/$i.rc" ] && read -r rc us <"$tmp/$i.rc"
  if [ "$rc" = 0 ]; then
    echo "PASS  ${names[i]}"; pass=$((pass + 1))
  else
    echo "FAIL  ${names[i]}"; sed 's/^/      /' "$tmp/$i.out" 2>/dev/null | tail -n 25; fail=$((fail + 1))
  fi
  times+="$us ${names[i]}"$'\n'
done
[ "${#skips[@]}" -gt 0 ] && printf '%s\n' "${skips[@]}"

slow="$(printf '%s' "$times" | sort -rn | head -n 3 | while read -r us name; do printf '%s %s s, ' "$name" "$(secs "$us")"; done)"
timeline="TIME  $lane lane $(secs $(( $(now) - t0 ))) s wall; slowest: ${slow%, }"
echo "$timeline"
echo "$timeline ($(date '+%Y-%m-%d %H:%M'), ${head:0:7})" >"$gitdir/check-last" 2>/dev/null || true

total=$((pass + fail + skip))
if [ "$fail" -eq 0 ]; then
  # The stamp says "every check of this lane passed here": not written when the caller scans personal data itself.
  if [ "$pii" = 1 ] && [ "$head" = "$(git rev-parse HEAD 2>/dev/null)" ] && clean; then echo "$lane $head" >"$stamp"; fi
  echo "CHECK PASS: $pass passed, $skip skipped, of $total"
else
  rm -f "$stamp"
  echo "CHECK FAIL: $fail failed, $pass passed, $skip skipped, of $total"
  exit 1
fi
