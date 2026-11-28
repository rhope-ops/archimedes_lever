#!/usr/bin/env bash
# The self-test of scripts/check.sh (moved out of check.sh in kit 16.0.0: plan 1.1). Each case runs check.sh in a
# small temporary repo: a fake kit script with a --test, and a check.local.sh that records its argument.
# Usage: bash scripts/check_sh_test.sh   (or: scripts/check.sh --test). Prints ok/FAIL lines and CHECK SELF-TEST PASS|FAIL.
# Prevents: a change to check.sh that breaks a lane, the stamp, the SKIP lines or the package mode without a failing test
# Network: none. Writes: temporary folders only. Credentials: none.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd -P)"
self="$here/check.sh"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_PREFIX GIT_COMMON_DIR GIT_IMPLICIT_WORK_TREE
# Each case runs this script in a small temporary repo: a fake kit script with a --test, and a check.local.sh that
# records its argument. CHECK_IN_TEST stops the inner runs from starting this self-test again.
# A failed mktemp must stop here: with an empty $t the cases below would write at the top of the file system.
t="$(mktemp -d)" && [ -d "$t" ] || { echo "CHECK SELF-TEST FAIL: no temporary folder"; exit 1; }
trap 'rm -rf "$t"' EXIT
export CHECK_IN_TEST=1
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1  # the host's git config (signing, templates) must not matter
unset GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT  # nor "git -c ..." on the command that started this run
# git in the test repo, with a fixed author and no signing
g() { git -C "$t/r" -c user.email=t@t -c user.name=t -c commit.gpgsign=false "$@"; }
git init -q -b main "$t/r"; mkdir -p "$t/r/scripts"
cp "$self" "$t/r/scripts/check.sh"; cp "$here/check_sh_test.sh" "$t/r/scripts/check_sh_test.sh"
# Like the real self-tests, the fake one makes a temporary repo and commits in it.
cat > "$t/r/scripts/stop_check.py" <<'PY'
import subprocess, tempfile
with tempfile.TemporaryDirectory() as d:
  subprocess.run(["git", "init", "-q", d], check=True)
  subprocess.run(["git", "-C", d, "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false",
                  "commit", "-q", "--allow-empty", "-m", "stray"], check=True)
print("fake self-test")
PY
printf '%s\n' 'print("fake self-test")' > "$t/r/scripts/log_check.py"
# A fake bloat_check.py: its --test and --rules pass; --compare writes its arguments down.
printf '%s\n' 'import subprocess, sys' 'if "--compare" in sys.argv:' \
  '    d = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True).stdout.strip()' \
  '    open(d + "/compare-args", "w").write("\n".join(sys.argv[2:]) + "\n"); print("TIME  baseline: fake")' \
  'if "--rules" in sys.argv:' '    print("WARN  fake lint" + (" gate" if "--gate" in sys.argv else ""))' > "$t/r/scripts/bloat_check.py"
cp "$t/r/scripts/log_check.py" "$t/r/scripts/timeline.py"
printf '%s\n' 'echo "arg=${1:-none}" > "$(git rev-parse --git-dir)/local-arg"' '[ ! -f fail.flag ]' > "$t/r/scripts/check.local.sh"
g add -A; g commit -q -m a; g update-ref refs/remotes/origin/main HEAD
fails=0
# ok NAME GOT WANT: print ok or FAIL, and remember a failure
ok() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got: $2; want: $3)"; fails=1; fi; }
# run the copied check.sh in the test repo with these arguments; stderr joins stdout
c() { (cd "$t/r" && bash scripts/check.sh "$@" 2>&1); }
out="$(c)"; ok "full lane passes" "$?" 0
ok "full lane runs the self-test of an unchanged script" "$(printf '%s\n' "$out" | grep -c '^PASS  stop_check self-test')" 1
ok "full lane: check.local.sh gets no argument" "$(cat "$t/r/.git/local-arg")" "arg=none"
ok "a pass on a clean tree writes the full stamp" "$(cut -d' ' -f1 "$t/r/.git/check-pass")" full
ok "a TIME line names the lane" "$(printf '%s\n' "$out" | grep -c '^TIME  full lane ')" 1
ok "the full lane compares its wall time with the baseline" "$(grep -c '^check=' "$t/r/.git/compare-args")" 1
ok "the full lane compares each step" "$(grep -c '^check:stop_check self-test=' "$t/r/.git/compare-args")" 1
ok "the comparison line is printed" "$(printf '%s\n' "$out" | grep -c '^TIME  baseline: fake')" 1
ok "a passing check shows its WARN lines; the full lane gates" "$(printf '%s\n' "$out" | grep -c '^      WARN  fake lint gate$')" 1
ok "no --record unless asked" "$(grep -c -- '--record' "$t/r/.git/compare-args")" 0
c --record >/dev/null; ok "--record after a full pass" "$(grep -c -- '--record' "$t/r/.git/compare-args")" 1
c --fast --record >/dev/null 2>&1; ok "--record with --fast exits 2" "$?" 2
ok "--cached uses the full stamp" "$(c --cached | head -n 1 | cut -c1-18)" "CHECK PASS (cached"
ok "--cached --fast uses the full stamp" "$(c --cached --fast | head -n 1 | cut -c1-18)" "CHECK PASS (cached"
echo x > "$t/r/new.txt"
ok "a dirty tree is not cached" "$(c --cached | grep -c 'cached')" 0
ok "a run on a dirty tree writes no new stamp" "$( [ -f "$t/r/.git/check-pass" ] && cut -d' ' -f2 "$t/r/.git/check-pass")" "$(g rev-parse HEAD)"
g add -A; g commit -q -m b
ok "a new commit is not cached" "$(c --cached --fast | grep -c 'cached')" 0
ok "fast lane: check.local.sh gets --fast" "$(cat "$t/r/.git/local-arg")" "arg=--fast"
ok "fast lane skips the self-test of an unchanged script" "$(c --fast | grep -c 'stop_check self-test')" 0
ok "the fast lane does not gate" "$(c --fast | grep -c '^      WARN  fake lint$')" 1
ok "the fast lane compares no wall time (it depends on what changed)" "$(grep -c '^check=' "$t/r/.git/compare-args")" 0
ok "a fast stamp does not pass a full run" "$(c --cached | grep -c 'cached')" 0
echo "# changed" >> "$t/r/scripts/stop_check.py"
ok "fast lane runs the self-test of a changed script" "$(c --fast | grep -c '^PASS  stop_check self-test')" 1
ok "fast lane skips timeline while log_check is unchanged" "$(c --fast | grep -c 'timeline self-test')" 0
echo "# changed" >> "$t/r/scripts/log_check.py"
ok "a change to log_check also runs the timeline self-test (it imports log_check)" "$(c --fast | grep -c '^PASS  timeline self-test')" 1
g checkout -q scripts/log_check.py
g commit -q -am c; rm -f "$t/r/.git/check-pass"
c --fast --no-content >/dev/null
ok "--no-content writes no stamp" "$( [ -f "$t/r/.git/check-pass" ] && echo stamp || echo none)" none
c >/dev/null; touch "$t/r/fail.flag"
c >/dev/null; ok "a failing check fails the run" "$?" 1
ok "a failed run removes the stamp" "$( [ -f "$t/r/.git/check-pass" ] && echo stamp || echo none)" none
rm "$t/r/fail.flag"
g update-ref -d refs/remotes/origin/main
ok "no default branch ref: the fast lane runs every self-test" "$(c --fast | grep -c '^PASS  stop_check self-test')" 1
c --bogus >/dev/null 2>&1; ok "an unknown flag exits 2" "$?" 2
# The code standard: skipped while nothing holds a baseline; run when the default branch holds one, also a large
# one (over 64 KB), although the state file of the work tree is gone.
printf '%s\n' 'print("CODE-STANDARD fake")' > "$t/r/scripts/code_standard.py"
echo '{"timings": {"check": {"steps": {"code standard": 1}}}}' > "$t/r/.check.state.json"
g add -A; g commit -q -m "state without a baseline"; g update-ref refs/remotes/origin/main HEAD
ok "no baseline here or on the default branch: the code standard is skipped" "$(c | grep -c '^SKIP  code standard')" 1
python3 -c 'import json; print(json.dumps({"code_standard": {"debt": {"length": {"f%d.py::main" % i: 99 for i in range(4000)}}}}, indent=1))' > "$t/r/.check.state.json"
g add -A; g commit -q -m "a large baseline"; g update-ref refs/remotes/origin/main HEAD
rm "$t/r/.check.state.json"
ok "a large baseline on the default branch, state file deleted: the code standard runs" "$(c | grep -c '^PASS  code standard$')" 1
g checkout -q .check.state.json; g update-ref -d refs/remotes/origin/main
# The Python lint (ruff and pylint): no config files, no step; with them and a linter missing, a SKIP line that names the install, never a silent pass.
# The PATH of the case puts, in place of each folder that holds ruff, pylint, shellcheck, bandit or gitleaks, a folder of links to its
# other programs (a runner can have shellcheck in /usr/bin, next to bash and git).
nolint=""; i=0
while IFS= read -r d; do
  if [ -x "$d/ruff" ] || [ -x "$d/pylint" ] || [ -x "$d/shellcheck" ] || [ -x "$d/bandit" ] || [ -x "$d/gitleaks" ]; then
    i=$((i+1)); mkdir -p "$t/nolint/$i"
    for f in "$d"/*; do case "${f##*/}" in ruff|pylint|shellcheck|bandit|gitleaks) ;; *) [ -x "$f" ] && ln -s "$f" "$t/nolint/$i/";; esac; done
    d="$t/nolint/$i"
  fi
  nolint+="${nolint:+:}$d"
done < <(tr ':' '\n' <<<"$PATH")
ok "no ruff.toml and .pylintrc: no Python lint step" "$(c | grep -c 'python lint')" 0
touch "$t/r/ruff.toml" "$t/r/.pylintrc"
ok "a missing linter is a SKIP line that names the install" \
  "$(cd "$t/r" && PATH="$nolint" bash scripts/check.sh 2>&1 | grep -c '^SKIP  python lint (ruff or pylint is missing: pip install ruff==0.17.6 pylint==4.1.4)$')" 1
rm "$t/r/ruff.toml" "$t/r/.pylintrc"
# The shell lint: a missing tool is a SKIP line that names the install; findings are WARN lines and the step passes.
ok "a missing shellcheck is a SKIP line that names the install" \
  "$(cd "$t/r" && PATH="$nolint" bash scripts/check.sh 2>&1 | grep -c '^SKIP  shellcheck (shellcheck is missing: pip install shellcheck-py==0.9.0.6)$')" 1
# bandit: full lane only; a missing bandit is a SKIP line that names the install.
ok "a missing bandit is a SKIP line that names the install (full lane)" \
  "$(cd "$t/r" && PATH="$nolint" bash scripts/check.sh 2>&1 | grep -c '^SKIP  bandit (bandit is missing: pip install bandit==1.9.4)$')" 1
ok "the fast lane runs no bandit" "$(cd "$t/r" && PATH="$nolint" bash scripts/check.sh --fast 2>&1 | grep -c 'bandit')" 0
ok "a missing gitleaks is a SKIP line that names the install (full lane)" \
  "$(cd "$t/r" && PATH="$nolint" bash scripts/check.sh 2>&1 | grep -c '^SKIP  gitleaks (gitleaks is missing: go install github.com/zricethezav/gitleaks/v8@v8.30.1)$')" 1
ok "the fast lane runs no gitleaks" "$(cd "$t/r" && PATH="$nolint" bash scripts/check.sh --fast 2>&1 | grep -c 'gitleaks')" 0
if command -v shellcheck >/dev/null; then
  printf '%s\n' '#!/bin/bash' 'echo $1' > "$t/r/bad.sh"; printf '%s\n' 'import sys' 'sys.stdout.write("bad.sh\0" if "--shell-files" in sys.argv else "")' > "$t/r/scripts/code_standard.py"
  out="$(c)"; ok "a shellcheck finding is a WARN line" "$(printf '%s\n' "$out" | grep -c '^      WARN  bad.sh:2:.*SC2086')" 1
  ok "a finding does not fail the step" "$(printf '%s\n' "$out" | grep -c '^PASS  shellcheck$')" 1
  ok "the run with a finding exits 0" "$(cd "$t/r" && bash scripts/check.sh >/dev/null 2>&1; echo $?)" 0
  rm "$t/r/bad.sh"
else echo "SKIP the shellcheck WARN cases: shellcheck is not installed here"; fi
printf '%s\n' 'print("CODE-STANDARD fake")' > "$t/r/scripts/code_standard.py"
# A git error is not a clean tree: with a broken index, a stamp for this commit must not be used.
c >/dev/null; ok "a stamp exists before the index breaks" "$(cut -d' ' -f2 "$t/r/.git/check-pass")" "$(g rev-parse HEAD)"
cp "$t/r/.git/index" "$t/index.bak"; echo broken > "$t/r/.git/index"
ok "a git error is not treated as a clean tree" "$(c --cached 2>&1 | grep -c 'cached')" 0
cp "$t/index.bak" "$t/r/.git/index"
# Inside a hook git sets GIT_DIR (in a linked worktree it points at the real repo): the self-tests' "git init"
# and "git commit" must not write into that repo.
o="$t/other"; git init -q -b main "$o"
git -C "$o" -c user.email=t@t -c user.name=t -c commit.gpgsign=false commit -q --allow-empty -m base
want="$(git -C "$o" rev-parse HEAD) $(git -C "$o" rev-list --count HEAD) $(git -C "$o" config --get core.bare)"
(cd "$t/r" && GIT_DIR="$o/.git" bash scripts/check.sh >/dev/null 2>&1)
ok "a run with GIT_DIR set leaves that repo unchanged" "$(git -C "$o" rev-parse HEAD) $(git -C "$o" rev-list --count HEAD) $(git -C "$o" config --get core.bare)" "$want"
mkdir -p "$t/r/sub"
ok "a run from a subfolder with GIT_DIR set still runs the checks" "$(cd "$t/r/sub" && GIT_DIR="$t/r/.git" bash ../scripts/check.sh 2>&1 | grep -c '^PASS  stop_check self-test')" 1
# The check-in self-test must not delete the folder it runs in when it cannot make a temporary folder.
if [ -f "$here/session_checkin.sh" ]; then
  mkdir -p "$t/keep"; cp "$here/session_checkin.sh" "$t/keep/"; touch "$t/keep/marker"
  (cd "$t/keep" && TMPDIR="$t/no-such-dir" bash session_checkin.sh --test >/dev/null 2>&1)
  ok "check-in self-test with no temporary folder: fails, deletes nothing" "$?:$( [ -f "$t/keep/marker" ] && echo kept)" "1:kept"
fi
# With no temporary folder, check.sh stops at once (a real run and this self-test). A fake mktemp names a folder
# that does not exist inside $t: if the stop ever breaks, the writes fail there, never outside this test's folder.
mkdir -p "$t/fakebin"; printf '#!/bin/sh\necho "%s"\n' "$t/missing" > "$t/fakebin/mktemp"; chmod +x "$t/fakebin/mktemp"
# nt ARGS...: run the copied check.sh with the fake mktemp; print its last line and its exit code
nt() { { cd "$t/r" && PATH="$t/fakebin:$PATH" bash scripts/check.sh "$@" 2>&1; echo "rc=$?"; } | tail -n 2; }
ok "a real run with no temporary folder fails at once" "$(nt)" "CHECK FAIL: no temporary folder (mktemp failed)
rc=1"
ok "the self-test with no temporary folder fails at once" "$(nt --test)" "CHECK SELF-TEST FAIL: no temporary folder
rc=1"
# A project's own extension files: the self-test of each runs when the file names --test (full lane: always; fast
# lane: when the file, or a kit file it extends, changed); a file with no self-test is a SKIP line.
g update-ref refs/remotes/origin/main HEAD
printf '%s\n' 'import sys' 'if "--test" in sys.argv:' '    print("local self-test")' > "$t/r/scripts/check_content_local.py"
printf '%s\n' '# --test is named only in this comment' 'print("a gate with no self-test")' > "$t/r/scripts/code_standard_gate.py"
out="$(c)"
ok "full lane: the self-test of a project's own finders runs" "$(printf '%s\n' "$out" | grep -c '^PASS  check_content_local self-test')" 1
ok "an extension file with no self-test is a SKIP line" "$(printf '%s\n' "$out" | grep -c '^SKIP  code_standard_gate self-test')" 1
ok "fast lane: a new extension file runs its self-test" "$(c --fast | grep -c '^PASS  check_content_local self-test')" 1
g add -A; g commit -q -m "extension files"; g update-ref refs/remotes/origin/main HEAD
ok "fast lane: an unchanged extension file is not tested again" "$(c --fast | grep -c 'check_content_local self-test')" 0
echo "# changed" >> "$t/r/scripts/check_content_scan.py"
ok "fast lane: a change to the kit file it extends runs it" "$(c --fast | grep -c '^PASS  check_content_local self-test')" 1
printf '%s\n' 'import sys' 'if "--test" in sys.argv:' '    raise SystemExit(1)' > "$t/r/scripts/check_content_local.py"
c >/dev/null; ok "a failing self-test of an extension file fails the run" "$?" 1
# Package mode (scripts/kit_package.py): a lock-listed script that git does not track needs the installed package.
printf '%s\n' '{"commit": "c0ffee", "kit_url": "https://example.invalid/kit", "files": {"scripts/gone.py": "x"}}' > "$t/r/.check.lock"
nopkg="$t/nopkg:$(dirname "$(command -v python3)"):$(dirname "$(command -v git)"):/usr/bin:/bin"  # a PATH with no archimedes-kit
out="$(cd "$t/r" && PATH="$nopkg" bash scripts/check.sh 2>&1)"
ok "package mode with no package fails and names the install" "$(printf '%s\n' "$out" | grep -c -e '^FAIL  kit package' -e 'install: scripts/check.sh --kit-install')" 2
printf '%s\n' '{"commit": "c0ffee"}' > "$t/r/.check.lock"
ok "a lock with no file list fails the package step, never skips it" "$(cd "$t/r" && PATH="$nopkg" bash scripts/check.sh 2>&1 | grep -c '^FAIL  kit package')" 1
printf '%s\n' '{"commit": "c0ffee", "kit_url": "https://example.invalid/kit", "files": {"scripts/gone.py": "x"}}' > "$t/r/.check.lock"
mkdir -p "$t/pkgbin"; printf '#!/bin/sh\necho "KIT PACKAGE PASS: $*"\n' > "$t/pkgbin/archimedes-kit"; chmod +x "$t/pkgbin/archimedes-kit"
ok "package mode runs the package's verify" "$(cd "$t/r" && PATH="$t/pkgbin:$PATH" bash scripts/check.sh 2>&1 | grep -c '^PASS  kit package')" 1
# --kit-install under PEP 668: a fake python3 whose pip refuses the system Python (or fails with $PIPERR).
mkdir -p "$t/pep668"
cat >"$t/pep668/python3" <<EOF
#!/bin/sh
case "\$*" in
*"-m pip install"*) echo "\$*" >>"$t/pip.log"; case "\$*" in *--user*) exit 0;; esac
  echo "error: \${PIPERR:-externally-managed-environment}" >&2; exit 1;;
*"-m archimedes_kit.kit_package"*) shift 2; echo "KIT PACKAGE PASS: module \$*"; exit 0;;
esac
exec $(command -v python3) "\$@"
EOF
chmod +x "$t/pep668/python3"; nokit="$t/pep668:$(dirname "$(command -v git)"):/usr/bin:/bin"  # no archimedes-kit command
out="$(cd "$t/r" && PATH="$nokit" bash scripts/check.sh --kit-install 2>&1)"
ok "--kit-install: pip refused by PEP 668 makes a user install" "$(grep -c -- '--user --break-system-packages' "$t/pip.log")" 1
ok "--kit-install: with no archimedes-kit command the package module writes the scripts" \
  "$(printf '%s\n' "$out" | grep -c '^KIT PACKAGE PASS: module --install$')" 1
ok "the package step finds the package module with no archimedes-kit command" \
  "$(cd "$t/r" && PATH="$nokit" bash scripts/check.sh 2>&1 | grep -c '^PASS  kit package')" 1
rm "$t/pip.log"; out="$(cd "$t/r" && PIPERR="no network" PATH="$nokit" bash scripts/check.sh --kit-install 2>&1; echo "rc=$?")"
ok "--kit-install: another pip error fails, shows it and makes no user install" "$(printf '%s\n' "$out" | grep -c -e '^error: no network$' -e '^rc=1$')$(grep -c -- '--user' "$t/pip.log")" 20
g add -f .check.lock; printf 'x\n' > "$t/r/scripts/gone.py"; g add -f scripts/gone.py
ok "with each locked script tracked there is no package step" "$(c | grep -c 'kit package')" 0
ok "with each locked script tracked --kit-install does nothing" "$(c --kit-install; echo "rc=$?")" "KIT PACKAGE: not used (each kit script in .check.lock is tracked)
rc=0"
[ "$fails" = 0 ] && echo "CHECK SELF-TEST PASS" || { echo "CHECK SELF-TEST FAIL"; exit 1; }
exit 0
