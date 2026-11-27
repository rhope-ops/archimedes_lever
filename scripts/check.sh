#!/usr/bin/env bash
# One check command for the repo (AGENTS.md "Commands": Test): the one front door of every check and guard.
# Prevents: a change that reaches main or a pull request with a check not run, or a check that fails and is not seen.
# Two lanes (.claude/skills/deliver/SKILL.md):
#   scripts/check.sh          full lane: everything. Before a merge, on a push to main (pre-push), in the pull-request Action (public repos).
#   scripts/check.sh --fast   fast lane: each push to another branch (pre-push). Self-tests only of the kit scripts that
#                             changed against origin/main, and scripts/check.local.sh gets --fast.
# The content check alone (scripts/check_content.py: personal data, secrets, the Administrator's terms, blocked files):
#   scripts/check.sh --content ARGS...   for example --all, --stdin, --range A..B or file names
#   scripts/check.sh --status            the word lists (counts and fingerprints, never the words) and the tier
#   scripts/check.sh --hook              the Claude Code PreToolUse hook (.claude/settings.json); any error blocks
# The checks:
#   1. the self-test of each kit script present (--test; a starter project has fewer), the self-test of a project's
#      own extension files when they have one (scripts/check_content_local.py and scripts/code_standard_gate.py: the
#      file names --test; the full lane always, the fast lane when the file or a file it extends changed), and the
#      code standard (scripts/code_standard.py, when .check.state.json holds its baseline; settings: the `code-` lines of .check),
#   1b. the Python parse, line length and file size: ruff and pylint (ruff.toml, .pylintrc; a SKIP line when a linter is missing),
#   1c. shellcheck on the shell files the code standard covers: findings are WARN lines and never fail (a SKIP line when it is missing),
#   1d. bandit on scripts/ and gitleaks on the tracked files (full lane; the scans of .github/workflows/security.yml;
#       a SKIP line when one is missing),
#   1e. the kit package (scripts/kit_package.py --verify), when .check.lock lists a script that git does not track
#       (scripts/check.sh --kit-install installs it at the lock commit),
#   2. the rule caps and the paths AGENTS.md names, the lint of changed rule lines (WARN lines), and in the full lane
#      the conflict-check record for changed rule lines (scripts/bloat_check.py --rules [--gate]; full tier),
#   3. the project log check (full tier),
#   4. the content check of all tracked files (when the settings file .check exists; in GitHub Actions the "checks"
#      workflow's content step does it; with --no-content the caller does it: the pre-push hook scans files and pushed
#      commits in one run),
#   5. the fleet format (scripts/fleet_harvest.py --check), when .check has the line `fleet: on`,
#   5b. the site's shared parts (scripts/build_site.py --check: index.html says what README.md's site sections say;
#      a project's own kinds in scripts/build_site_local.py), when README.md has a `<!-- site:` mark,
#   5c. the steps a person follows (scripts/check_instructions.py), both lanes, when .check has `audit-instructions:`
#      lines (else on README.md); a project's own module: scripts/check_instructions_local.py,
#   6. scripts/check.local.sh, when it exists: this project's own tests (SKIP when missing: the review gate in
#      .claude/skills/deliver/SKILL.md then guards main).
# The checks run in parallel: each one works on its own temporary files. CHECK_SERIAL=1 runs them one at a time.
# Prints one PASS/FAIL/SKIP line per check, the output of each failed check, a TIME line (wall time and the 3 slowest
# checks), a line that compares the times with the baselines in .check.state.json (scripts/bloat_check.py --compare:
# the full lane and each step; the fast lane only its steps, as its total depends on what changed; a slowdown is a
# WARN line, never a failure) and "CHECK PASS" or "CHECK FAIL" last.
# --record (full lane only): after a pass, store this run's times as the new baselines (commit the change).
# Exit 0 only when no check failed. Needs bash, git and python3.
# Network: none itself; a project's scripts/check.local.sh may use the network for its own tests.
# Writes: .git/check-pass and .git/check-last (the stamp and the last TIME line); with --record the time baselines in
#   .check.state.json; temporary folders.
# Credentials: none; the content check reads the word lists from an environment variable or a file (scripts/check_content.py).
# Stamp: a lane that passes on a clean tree writes "<lane> <commit>" to .git/check-pass. With --cached, a run on the
# same commit and a clean tree passes at once (the full stamp covers both lanes). Never write the stamp by hand.
# Self-test (temporary repos, no network): scripts/check.sh --test (runs scripts/check_sh_test.sh)
set -uo pipefail
self="$(cd "$(dirname "$0")" && pwd -P)/$(basename "$0")"
# The content check's own modes: before any "cd", so they work from any folder (the hook also runs outside a repo).
case "${1:-}" in
  --hook) python3 "$(dirname "$self")/check_content.py" --hook && exit 0; exit 2 ;;  # any failure blocks the tool call
  --status) exec python3 "$(dirname "$self")/check_content.py" --status ;;
  --content) shift; exec python3 "$(dirname "$self")/check_content.py" "$@" ;;
esac
# The self-test lives in scripts/check_sh_test.sh (kit 16.0.0).
[ "${1:-}" = "--test" ] && exec bash "$(dirname "$self")/check_sh_test.sh"
# Git gives a hook GIT_DIR and friends (in a linked worktree they point at the real repo). The self-tests make
# temporary repos with "git init" and "git commit": with those variables set they would write into that repo.
# Unset them first, so the top folder is found from the current folder (a hook starts at the top of its worktree).
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_PREFIX GIT_COMMON_DIR GIT_IMPLICIT_WORK_TREE
cd "$(git rev-parse --show-toplevel)" || exit 1
[ -f scripts/check.sh ] || { echo "CHECK FAIL: $(pwd) is not the top folder of a repo with scripts/check.sh" >&2; exit 1; }


lane=full cached=0 pii=1 record=0 kitinstall=0
for a in "$@"; do
  case "$a" in
    --fast) lane=fast ;;
    --cached) cached=1 ;;
    --no-content) pii=0 ;;
    --record) record=1 ;;
    --kit-install) kitinstall=1 ;;
    *) echo "usage: scripts/check.sh [--fast] [--cached] [--no-content] [--record] | --kit-install | --content ARGS... | --status | --hook" >&2; exit 2 ;;
  esac
done
[ "$record" = 1 ] && [ "$lane" = fast ] && { echo "usage: --record needs the full lane" >&2; exit 2; }

gitdir="$(git rev-parse --git-dir)"
stamp="$gitdir/check-pass"
head="$(git rev-parse HEAD 2>/dev/null || echo none)"
# true when the work tree has no changes; a git error is not "clean"
clean() { local s; s="$(git status --porcelain 2>/dev/null)" || return 1; [ -z "$s" ]; }
# Package mode (scripts/kit_package.py): .check.lock lists a script that git does not track. A lock that does not parse
# counts as package mode, so the package step runs and fails. git status cannot see the untracked kit scripts, so no cached pass.
pkg_mode() {
  [ -f .check.lock ] && python3 -c 'import json, subprocess, sys
try: f = [k for k in json.load(open(".check.lock"))["files"] if k.startswith("scripts/")]
except Exception: sys.exit(0)
sys.exit(0 if set(f) - set(subprocess.run(["git", "ls-files", "-z", "--"] + f, capture_output=True, text=True).stdout.split("\0")) else 1)'
}
# The kit package's command: archimedes-kit, else its module (a user install can put the command off PATH).
kit() { if command -v archimedes-kit >/dev/null; then archimedes-kit "$@"; else python3 -m archimedes_kit.kit_package "$@"; fi; }
# --kit-install: in package mode, install the kit package at the lock commit and write the kit scripts (the CI step, the
# SessionStart hook at startup, kit-update and a setup script that calls it use it: one home for the install command); else nothing.
if [ "$kitinstall" = 1 ]; then
  pkg_mode || { echo "KIT PACKAGE: not used (each kit script in .check.lock is tracked)"; exit 0; }
  read -r c kit_url < <(python3 -c 'import json, os
lock = json.load(open(".check.lock"))
url = lock.get("kit_url") or (json.load(open("kit.config.json")).get("kit_url") if os.path.isfile("kit.config.json") else None)
if not url: raise SystemExit("missing kit_url in .check.lock or kit.config.json")
print(lock["commit"], url)') || exit 1
  u="git+${kit_url}@$c"
  if ! o="$(python3 -m pip install -q --force-reinstall "$u" 2>&1)"; then
    # PEP 668: a system Python that refuses pip outside a venv gets a user install (many such systems have no venv module).
    grep -q 'externally-managed-environment' <<<"$o" || { printf '%s\n' "$o"; exit 1; }
    echo "KIT PACKAGE: pip refuses the system Python (PEP 668); it makes a user install"
    python3 -m pip install -q --user --break-system-packages --force-reinstall "$u" || exit 1
  fi
  kit --install
  exit $?
fi
if [ "$cached" = 1 ] && [ -f "$stamp" ] && clean && ! pkg_mode; then
  read -r s_lane s_head <"$stamp" || true
  if [ "${s_head:-}" = "$head" ] && { [ "${s_lane:-}" = full ] || [ "$lane" = fast ]; }; then
    echo "CHECK PASS (cached: the $s_lane lane passed on ${head:0:7}, clean tree)"
    exit 0
  fi
fi

# microseconds; whole seconds where bash has no EPOCHREALTIME (bash 3)
now() {
  if [ -n "${EPOCHREALTIME:-}" ]; then printf '%s' "${EPOCHREALTIME/[.,]/}"; else printf '%s000000' "$(date +%s)"; fi
}
# secs MICROSECONDS: print them as seconds with one decimal
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
# true when the lane is full, the base is unknown, or one of the named files (or this script) changed
touched() {
  [ "$changed" = "*all*" ] && return 0
  local p
  for p in scripts/check.sh "$@"; do printf '%s\n' "$changed" | grep -qxF -- "$p" && return 0; done
  return 1
}

tmp="$(mktemp -d)" && [ -d "$tmp" ] || { echo "CHECK FAIL: no temporary folder (mktemp failed)"; exit 1; }
trap 'rm -rf "$tmp"' EXIT
n=0 pass=0 fail=0 skip=0 untested=0
names=()
t0="$(now)"

# run NAME COMMAND...: start the check in the background; results are collected below
run() {
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
# skip NAME REASON: record a SKIP line for the summary
skip() { skips+=("SKIP  $1 ($2)"); skip=$((skip + 1)); }
# selftest NAME FILE [MORE FILES IT DEPENDS ON...] -- COMMAND...: run a script's self-test when the lane needs it
selftest() {
  local name="$1" file="$2" deps=(); shift
  while [ "$1" != "--" ]; do deps+=("$1"); shift; done; shift
  [ -f "$file" ] || return 0  # absent: not in this tier
  if touched "${deps[@]}"; then run "$name self-test" "$@"; else untested=$((untested + 1)); fi
}

for s in stop_check worker_guard; do   # worker_guard --test also runs the scan self-test (its samples: worker_guard_scan_samples.json)
  selftest "$s" "scripts/$s.py" scripts/worker_guard_scan_samples.json scripts/check_content_scan.py -- python3 "scripts/$s.py" --test
done
selftest log_check scripts/log_check.py -- python3 scripts/log_check.py --test
# A script whose cases or parts live in sibling modules lists them, so the fast lane reruns its self-test when they change.
selftest check_settings scripts/check_settings.py scripts/check_settings_test.py scripts/build_site.py scripts/check_content_scan.py \
  -- python3 scripts/check_settings.py --test
selftest bloat_check scripts/bloat_check.py scripts/bloat_check_test.py scripts/log_check.py scripts/check_lock.py \
  scripts/check_settings.py scripts/build_site.py scripts/check_content_scan.py -- python3 scripts/bloat_check.py --test
selftest token_log scripts/token_log.py scripts/token_log_test.py scripts/skill_use.py -- python3 scripts/token_log.py --test
selftest code_standard scripts/code_standard.py scripts/code_standard_test.py scripts/check_settings.py scripts/build_site.py \
  scripts/check_content_scan.py -- python3 scripts/code_standard.py --test
selftest timeline scripts/timeline.py scripts/log_check.py scripts/build_site.py -- python3 scripts/timeline.py --test  # it imports log_check
selftest check_content scripts/check_content.py scripts/check_content_scan.py scripts/check_content_test.py \
  -- python3 scripts/check_content.py --test
# The IMMUTABLE NIPR guard (AGENTS.md "IMMUTABLE NIPR code safety"; DEC-NIPR): its self-test always; its scan where .check has
# `nipr-safe: on` or `dod-security: on` (below).
selftest nipr_guard scripts/nipr_guard.py -- python3 scripts/nipr_guard.py --test
# A project's own extension files (the kit has none): each proves itself when it has a self-test. The deps are the
# file, its sibling files (for example its test cases: scripts/check_content_local_test.py) and the kit files it extends.
# extension NAME FILE [KIT FILES IT EXTENDS...]: run "python3 FILE --test" when its code names "--test" (not only a comment); else a SKIP line
extension() {
  local name="$1" file="$2"; shift 2
  [ -f "$file" ] || return 0
  if grep -Eq -- "^[^#]*[\"']--test[\"']" "$file"; then selftest "$name" "$file" "${file%.py}"*.py "$@" -- python3 "$file" --test
  else skip "$name self-test" "$file has no self-test (a file that names --test is run with it)"; fi
}
extension check_content_local scripts/check_content_local.py scripts/check_content_scan.py
extension code_standard_gate scripts/code_standard_gate.py scripts/code_standard.py scripts/check_settings.py
selftest check_instructions scripts/check_instructions.py scripts/check_instructions_test.py scripts/check_settings.py \
  scripts/build_site.py scripts/check_content_scan.py -- python3 scripts/check_instructions.py --test
extension check_instructions_local scripts/check_instructions_local.py scripts/check_instructions.py
selftest skill_use scripts/skill_use.py -- python3 scripts/skill_use.py --test
selftest fleet_harvest scripts/fleet_harvest.py scripts/fleet_harvest_test.py scripts/fleet_harvest_parse.py -- python3 scripts/fleet_harvest.py --test
selftest check_blocks scripts/check_blocks.py .claude/settings.json -- python3 scripts/check_blocks.py --test
selftest check_lock scripts/check_lock.py -- python3 scripts/check_lock.py --test
selftest fulcrum_palette scripts/fulcrum_palette.py docs/brand/fulcrum.json docs/brand/fulcrum.css -- python3 scripts/fulcrum_palette.py --test
selftest build_site scripts/build_site.py -- python3 scripts/build_site.py --test
extension build_site_local scripts/build_site_local.py scripts/build_site.py
selftest first_use_check scripts/first_use_check.py scripts/check_blocks.py scripts/check_content.py scripts/check_content_scan.py \
  -- python3 scripts/first_use_check.py --test
# Kit only: projects have no sync tools. The drift self-test reads the kit's AGENTS.md and stop_check.py.
selftest drift scripts/drift.py scripts/sync_baseline.py scripts/sync_merge.py AGENTS.md scripts/stop_check.py \
  scripts/drift_test.py -- python3 scripts/drift.py --test
selftest pre-push scripts/git-hooks/pre-push -- scripts/git-hooks/pre-push --test
selftest session_checkin scripts/session_checkin.sh -- bash scripts/session_checkin.sh --test
[ -f kit.config.json ] && selftest kit_config scripts/kit_config.py kit.config.json -- python3 scripts/kit_config.py --test  # kit only
# Kit only: the command-line tests of the sync, drift, lock and bootstrap scripts (bootstrap deletes them in a project).
cli_tests() { (cd scripts && python3 -m unittest -q sync_test bootstrap_cli_test check_lock_cli_test drift_cli_test); }
[ -f scripts/sync_test.py ] && selftest cli_tests scripts/sync_test.py scripts/*_cli_test.py scripts/sync_baseline.py \
  scripts/sync_merge.py scripts/drift.py scripts/check_lock.py scripts/bootstrap.sh scripts/check_blocks.py scripts/kit_config.py \
  scripts/build_site.py -- cli_tests
# This script's own self-test (not inside that self-test: it runs this script in temporary repos): scripts/check_sh_test.sh.
[ -z "${CHECK_IN_TEST:-}" ] && [ -f scripts/check_sh_test.sh ] && selftest check.sh scripts/check.sh scripts/check_sh_test.sh -- bash scripts/check_sh_test.sh
[ "$untested" -gt 0 ] && skip "$untested self-tests" "fast lane: those scripts did not change; the full lane runs them"

# The code standard (docs/code-standard.md), both lanes: it takes about 0.1 s. A repo that has not adopted it skips.
# Adopted: .check.state.json holds the "code_standard" baseline. A repo that still has the old .code-standard.json
# runs the check too: it fails there and names the migration, so the old limits are not dropped in silence.
# Also adopted: the default branch holds a baseline (a deleted state file must fail the check, not skip it).
# (The state file alone is no baseline: the time baselines and the audit write it too.)
on_main() {  # on_main FILE [TEXT]: the default branch has FILE (and FILE holds TEXT)
  local r t; for r in origin/main origin/master; do  # no pipe: with pipefail, grep -q closes a large file early
    t=$(git show "$r:$1" 2>/dev/null) && grep -q -- "${2:-}" <<<"$t" && return 0
  done; return 1
}
if [ -f scripts/code_standard.py ] && { grep -qs '"code_standard"' .check.state.json || [ -f .code-standard.json ] \
     || on_main .check.state.json '"code_standard"' || on_main .code-standard.json '"debt"'; }; then
  run "code standard" python3 scripts/code_standard.py
elif [ -f scripts/code_standard.py ]; then
  skip "code standard" "no code standard baseline in .check.state.json: adopt it with python3 scripts/code_standard.py --init (docs/code-standard.md)"
fi

# Python parse, line length and file size (docs/code-standard.md C4, C10): ruff and pylint, the configs ruff.toml and .pylintrc,
# the caps from .check. The parse and the line cap fail; the file size only warns. Never a silent pass: a missing linter is a SKIP line.
python_lint() {
  local caps cap max files=() long=() f rc=0
  caps=$(python3 -c 'import sys; sys.path.insert(0, "scripts"); import check_settings as s; c = s.code_config(".")["caps"]; print(c.get("max_line_chars") or 0, c["max_file_lines"])') || return 1
  read -r cap max <<<"$caps"
  # The files are the ones the code standard covers (include, exclude, generated). A file with a generated block is out of the line list.
  python3 scripts/code_standard.py --python-files all >"$tmp/lint.all" && python3 scripts/code_standard.py --python-files line >"$tmp/lint.line" || return 1
  while IFS= read -r -d '' f; do files+=("$f"); done <"$tmp/lint.all"
  while IFS= read -r -d '' f; do long+=("$f"); done <"$tmp/lint.line"
  [ "${#files[@]}" -gt 0 ] || return 0
  # An empty line list must not become "every file": ruff and pylint with no file name lint the whole folder.
  if [ "$cap" != 0 ] && [ "${#long[@]}" -gt 0 ]; then
    ruff check -q --config ruff.toml --select E501 --line-length "$cap" "${long[@]}" || rc=1
    pylint -sn -j 0 --rcfile .pylintrc --disable=all --enable=line-too-long --max-line-length "$cap" "${long[@]}" || rc=1
  fi
  ruff check -q --config ruff.toml "${files[@]}" || rc=1
  pylint -sn -j 0 --rcfile .pylintrc --disable=too-many-lines,line-too-long "${files[@]}" || rc=1
  if [ -n "$max" ] && [ "$max" != "None" ]; then
    pylint -sn -j 0 --rcfile .pylintrc --disable=syntax-error,line-too-long --max-module-lines "$max" \
      --msg-template='WARN  {path}: {msg}; a warning only (docs/code-standard.md C4)' "${files[@]}" | grep '^WARN ' || true
  fi
  return $rc
}
if [ -f ruff.toml ] && [ -f .pylintrc ]; then
  if command -v ruff >/dev/null && command -v pylint >/dev/null; then run "python lint" python_lint
  else skip "python lint" "ruff or pylint is missing: pip install ruff==0.17.6 pylint==4.1.4"; fi
fi

# The shell lint on the files the code standard covers (the plan's decision 6: WARN first, so a finding never fails the step;
# a tool that fails to run is a WARN line too). Never a silent pass: a missing shellcheck is a SKIP line.
shell_lint() {
  local files=() f out rc
  python3 scripts/code_standard.py --shell-files >"$tmp/shell.all" || return 1
  while IFS= read -r -d '' f; do files+=("$f"); done <"$tmp/shell.all"
  [ "${#files[@]}" -gt 0 ] || return 0
  out="$(shellcheck -f gcc -- "${files[@]}" 2>&1)"; rc=$?
  [ "$rc" -le 1 ] || echo "WARN  shellcheck stopped with exit code $rc; a warning only"
  [ -z "$out" ] || printf '%s\n' "$out" | sed 's/^/WARN  /; s/$/; a warning only (shellcheck, docs\/code-standard.md)/'
  return 0
}
if [ -f scripts/code_standard.py ]; then
  if command -v shellcheck >/dev/null; then run "shellcheck" shell_lint
  else skip "shellcheck" "shellcheck is missing: pip install shellcheck-py==0.9.0.6"; fi
fi
# bandit (medium severity and higher) on scripts/ and gitleaks on the working tree, full lane only: the scans of
# .github/workflows/security.yml, which skips pull requests in a private repo. Never a silent pass: a missing tool is a
# SKIP line that names the install.
# gitleaks reads a copy of the tracked files (uncommitted edits included): the files of the CI checkout, as gitleaks
# does not skip ignored files (a self-test's __pycache__ is a false finding; the Administrator, 2026-11-25).
gitleaks_tracked() {
  mkdir "$tmp/gitleaks" && git ls-files -z | tar --null --ignore-failed-read -T - -cf - 2>/dev/null | tar -xf - -C "$tmp/gitleaks" &&
    gitleaks detect --no-git --source "$tmp/gitleaks" --redact
}
if [ "$lane" = full ] && [ -d scripts ]; then
  if command -v bandit >/dev/null; then run "bandit" bandit -q -r scripts/ -ll
  else skip "bandit" "bandit is missing: pip install bandit==1.9.4"; fi
  if command -v gitleaks >/dev/null; then run "gitleaks" gitleaks_tracked
  else skip "gitleaks" "gitleaks is missing: go install github.com/zricethezav/gitleaks/v8@v8.30.1"; fi
fi

# Rule caps, paths, the lint of changed rule lines, and (full lane) the conflict-check record for changed rule lines.
if [ -f scripts/bloat_check.py ]; then
  if [ "$lane" = full ]; then run "rule caps and pointers" python3 scripts/bloat_check.py --rules --gate
  else run "rule caps and pointers" python3 scripts/bloat_check.py --rules; fi
  run "skills well-formed" python3 scripts/bloat_check.py --skills
fi
# The git-safety and key-file deny rules (scripts/check_blocks.py) are all in .claude/settings.json.
[ -f scripts/check_blocks.py ] && [ -f .claude/settings.json ] && run "deny rules" python3 scripts/check_blocks.py --settings
# The kit files of a project are as the last sync wrote them (scripts/check_lock.py; the kit itself has no lock).
[ -f scripts/check_lock.py ] && [ -f .check.lock ] && run "kit lock" python3 scripts/check_lock.py --verify
# Package mode (scripts/kit_package.py, plan 2026-11-23 P3): .check.lock lists a script that git does not track, so the
# installed kit package must be at the lock commit and each such file must equal its copy (pkg_mode, above: from the lock
# alone, because with the package missing the untracked scripts are missing too, and their steps above skip).
kit_package() {
  kit --verify && return 0
  echo "install: scripts/check.sh --kit-install (pip installs the kit package at the commit in .check.lock)"
  return 1
}
pkg_mode && run "kit package" kit_package
# The site page says what the README says (scripts/build_site.py), when README.md has site sections.
[ -f scripts/build_site.py ] && grep -qs -- '<!-- site:' README.md && run "site from README" python3 scripts/build_site.py --check

if [ ! -f scripts/log_check.py ]; then
  :  # starter tier: no project log
elif [ -f scripts/check_blocks.py ] && ! python3 scripts/check_blocks.py --placeholders AGENTS.md >/dev/null && ! python3 scripts/check_blocks.py --placeholders docs/LOG.md >/dev/null; then
  skip "project log" "template placeholders: run first use"
elif [ -f docs/LOG.md ]; then
  run "project log" python3 scripts/log_check.py docs/LOG.md
else
  skip "project log" "no docs/LOG.md: the log lives in the place AGENTS.md Project rules names"
fi
# T6 (plan 2026-11-23): a DECISIONS row By the Administrator quotes the approval. The kit (no .check.lock) always runs it: with no
# approval-quote-exempt-from marker every row is checked. A project runs it where docs/DECISIONS.md has the marker (its sync adds
# it) and prints a SKIP line otherwise. T7: each plan coverage list is complete.
if [ -f scripts/log_check_plan.py ]; then
  if [ ! -f .check.lock ] || grep -qs 'approval-quote-exempt-from' docs/DECISIONS.md; then
    run "decisions approval quote" python3 scripts/log_check.py --decisions
  else
    skip "decisions approval quote" "docs/DECISIONS.md has no approval-quote-exempt-from marker (a sync adds it)"
  fi
  for f in docs/reviews/*-coverage.md; do
    [ -f "$f" ] && run "plan coverage ${f##*/}" python3 scripts/log_check.py --coverage "$f"
  done
fi

# The IMMUTABLE NIPR guard scan (DEC-NIPR), both lanes, where .check has `nipr-safe: on` or `dod-security: on`.
if [ -f scripts/nipr_guard.py ] && grep -Eq '^[[:space:]]*(nipr-safe|dod-security):[[:space:]]*on[[:space:]]*$' .check 2>/dev/null; then
  run "nipr guard" python3 scripts/nipr_guard.py
fi

if [ ! -f .check ] && [ ! -f .pii-guard ]; then
  skip "content check" "no .check file: the scan of tracked files is off"
elif [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  skip "content check" "GitHub Actions: the checks workflow's content step scans with the base settings"
elif [ "$pii" = 0 ]; then
  skip "content check" "the pre-push hook scans the files and the pushed commits next"
else
  run "content check" python3 scripts/check_content.py --all
fi

# The fleet format (docs/reviews/2026-11-19-fleet-contract.md): both lanes, only where .check has the line `fleet: on`.
if [ -f scripts/fleet_harvest.py ] && grep -Eq '^[[:space:]]*fleet: on[[:space:]]*$' .check 2>/dev/null; then
  run "fleet format" python3 scripts/fleet_harvest.py --check
fi

# The steps a person follows (AGENTS.md "Instructions people follow"): both lanes, on the files .check names.
if [ -f scripts/check_instructions.py ]; then
  if grep -Eq '^[[:space:]]*audit-instructions[[:space:]]*:' .check 2>/dev/null; then
    run "instructions" python3 scripts/check_instructions.py
  else
    run "instructions (README.md; no audit-instructions: lines in .check)" python3 scripts/check_instructions.py README.md
  fi
fi

if [ -f scripts/check.local.sh ]; then
  if [ "$lane" = fast ]; then
    run "project checks (check.local.sh --fast)" bash scripts/check.local.sh --fast
  else
    run "project checks (check.local.sh)" bash scripts/check.local.sh
  fi
else
  skip "project checks" "no scripts/check.local.sh: no project tests yet; the review gate guards main (.claude/skills/deliver/SKILL.md)"
fi

wait
times="" items=()
for ((i = 1; i <= n; i++)); do
  rc=1 us=0
  [ -f "$tmp/$i.rc" ] && read -r rc us <"$tmp/$i.rc"
  if [ "$rc" = 0 ]; then
    echo "PASS  ${names[i]}"; pass=$((pass + 1))
    grep '^WARN ' "$tmp/$i.out" 2>/dev/null | sed 's/^/      /'  # a passing check can still warn (rule lint, conflict check)
  else
    echo "FAIL  ${names[i]}"; sed 's/^/      /' "$tmp/$i.out" 2>/dev/null | tail -n 25; fail=$((fail + 1))
  fi
  times+="$us ${names[i]}"$'\n'
  items+=("check:${names[i]}=$(secs "$us")")
done
[ "${#skips[@]}" -gt 0 ] && printf '%s\n' "${skips[@]}"

slow="$(printf '%s' "$times" | sort -rn | head -n 3 | while read -r us name; do printf '%s %s s, ' "$name" "$(secs "$us")"; done)"
wall=$(( $(now) - t0 ))
timeline="TIME  $lane lane $(secs "$wall") s wall; slowest: ${slow%, }"
echo "$timeline"
[ "$lane" = full ] && items=("check=$(secs "$wall")" ${items[@]+"${items[@]}"})
if [ -f scripts/bloat_check.py ] && [ "${#items[@]}" -gt 0 ]; then  # warn only: .claude/skills/audit/SKILL.md "A slow run"
  rec=""; [ "$record" = 1 ] && [ "$fail" -eq 0 ] && rec=--record
  python3 scripts/bloat_check.py --compare "${items[@]}" $rec 2>&1 | tail -n 1
fi
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
