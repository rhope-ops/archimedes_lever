#!/usr/bin/env python3
"""The kit package (plan 2026-11-23, P3, the Administrator's design B): a project takes the kit scripts from the
installed `archimedes-kit` package instead of from its own commits.

A project in package mode keeps in git only the kit files that a hook calls (and what they import), the instruction
files and `.check.lock`. Every other script that the lock lists is not tracked: `--install` writes it from the
package into `scripts/` and lists it in `.git/info/exclude`, so check.sh, the lock check and the extension files
run as before. The package must be installed at the commit that `.check.lock` names (pip records it).

Usage:
    pip install "git+<kit_url from kit.config.json>@<the commit in .check.lock>"
    archimedes-kit --install    # write the untracked kit scripts from the package (or: python3 -m archimedes_kit.kit_package)
    archimedes-kit --verify     # check.sh runs this (or python3 -m archimedes_kit.kit_package --verify):
                                # the package is at the lock commit and each file equals its copy
    python3 scripts/kit_package.py --test
Input: the repo at the current folder (or --project DIR), its .check.lock, the installed package. Output: PASS and
FAIL lines on stdout; exit 1 on a FAIL.
Writes: --install only: the untracked kit scripts in scripts/ and one block in .git/info/exclude.
Prevents: a check that runs a kit script copy other than the one the lock names (an old or edited package, or a project copy left behind)
Network: none (pip does the download).
Credentials: none.
Standard library only.
"""
import argparse
import importlib.metadata
import json
import pathlib
import subprocess
import sys
import tempfile

PKG = pathlib.Path(__file__).resolve().parent  # the installed package folder: the kit's scripts/ folder as it was built
DIST = "archimedes-kit"
BEGIN, END = "# kit package: scripts/kit_package.py --install", "# end kit package"


def git(root, *args):
    """Output of a git command in the project."""
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


def package_files(root):
    """(lock commit, the lock's scripts/ files that git does not track): the files the package provides here."""
    lock = json.loads((root / ".check.lock").read_text(encoding="utf-8"))
    want = sorted(k for k in lock["files"] if k.startswith("scripts/"))
    tracked = set(git(root, "ls-files", "-z", "--", *want).split("\0")) if want else set()
    return str(lock.get("commit", "")), [k for k in want if k not in tracked]


def installed():
    """(commit, url) of the installed package as pip recorded it; (None, None) when it is not installed from git."""
    try:
        info = json.loads(importlib.metadata.distribution(DIST).read_text("direct_url.json") or "{}")
    except importlib.metadata.PackageNotFoundError:
        return None, None
    return info.get("vcs_info", {}).get("commit_id"), info.get("url")


def run(root, pkg, have, url, write):
    """Check (and with write: install) the package files of a project.

    Args:
        root: the project's top folder (a Path).
        pkg: the package folder that holds the kit scripts (a Path).
        have: the commit of the installed package, or None.
        url: the git URL the package was installed from, or None.
        write: True to write the files and the exclude block (--install), False to compare only (--verify).

    Returns:
        (lines to print, True when a check failed).
    """
    commit, files = package_files(root)
    if not files:
        return ["KIT PACKAGE: not used (each kit script in .check.lock is tracked)"], False
    if have != commit:
        lock_url = json.loads((root / ".check.lock").read_text(encoding="utf-8")).get("kit_url")
        if not lock_url and (root / "kit.config.json").is_file():
            lock_url = json.loads((root / "kit.config.json").read_text(encoding="utf-8")).get("kit_url")
        return [f"FAIL  the installed kit package is at {have or 'nothing'}; .check.lock names {commit}: "
                f"pip install --force-reinstall \"git+{url or lock_url or '<kit_url>'}@{commit}\""], True
    out = []
    for rel in files:
        src, dst = pkg / rel[len("scripts/"):], root / rel
        if not src.is_file():
            out.append(f"FAIL  not in the package: {rel}")
        elif write:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            dst.chmod(src.stat().st_mode & 0o777)
        elif not dst.is_file() or dst.read_bytes() != src.read_bytes():
            out.append(f"FAIL  {'missing' if not dst.is_file() else 'differs from the package'}: {rel} (run: archimedes-kit --install)")
    if write:
        exclude = root / git(root, "rev-parse", "--git-path", "info/exclude").strip()
        before, _, rest = (exclude.read_text(encoding="utf-8") if exclude.is_file() else "").partition(BEGIN)
        before = before.rstrip("\n") + "\n" if before.strip() else ""  # the lines of others stay; the old block goes
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text(before + "\n".join([BEGIN, *("/" + f for f in files), END]) + "\n"
                           + (rest.partition(END)[2].lstrip("\n") if END in rest  # no end line: keep every line that is not ours
                              else "".join(ln for ln in rest.splitlines(True) if ln.strip() not in {"/" + f for f in files}).lstrip("\n")), encoding="utf-8")
    bad = any(ln.startswith("FAIL") for ln in out)
    out.append(f"KIT PACKAGE {'FAIL' if bad else 'PASS'}: {len(files)} kit scripts from the package at {commit[:7]}"
               + (" (written)" if write and not bad else ""))
    return out, bad


def self_test():
    """The self-test, in temporary project and package folders; no network, no pip.

    Returns:
        The exit code: 0 when every case passes, else 1.
    """
    fails = []

    def ok(label, good):  # print one case and remember a failure
        print(("ok    " if good else "FAIL  ") + label)
        if not good:
            fails.append(label)

    with tempfile.TemporaryDirectory() as d:
        root, pkg = pathlib.Path(d, "p"), pathlib.Path(d, "pkg")
        (root / "scripts").mkdir(parents=True)
        pkg.mkdir()
        (pkg / "a.py").write_text("print('package a')\n")
        (pkg / "hook.sh").write_text("echo package hook\n")
        (pkg / "hook.sh").chmod(0o755)
        (root / "scripts/hook.sh").write_text("echo project hook\n")
        lock = {"commit": "c0ffee", "files": {"scripts/a.py": "x", "scripts/hook.sh": "y", "AGENTS.md (kit sections)": "z"}}
        (root / ".check.lock").write_text(json.dumps(lock))
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        git(root, "add", "scripts/hook.sh", ".check.lock")
        lines, bad = run(root, pkg, "c0ffee", None, write=False)
        ok("a missing untracked file fails and names the install", bad and "missing: scripts/a.py (run: archimedes-kit --install)" in lines[0])
        lines, bad = run(root, pkg, "beef", "https://example.invalid/kit", write=True)
        ok("a package at another commit fails and writes nothing", bad and not (root / "scripts/a.py").exists()
           and "git+https://example.invalid/kit@c0ffee" in lines[0])
        ok("no package installed fails", run(root, pkg, None, None, write=False)[1])
        lines, bad = run(root, pkg, "c0ffee", None, write=True)
        ok("install writes the untracked file", not bad and (root / "scripts/a.py").read_text() == "print('package a')\n")
        ok("install leaves a tracked kit file alone", (root / "scripts/hook.sh").read_text() == "echo project hook\n")
        ok("install hides the written file from git",
           git(root, "status", "--porcelain", "--untracked-files=all").split() == ["A", ".check.lock", "A", "scripts/hook.sh"])
        run(root, pkg, "c0ffee", None, write=True)
        ok("a second install keeps one exclude block", (root / ".git/info/exclude").read_text().count(BEGIN) == 1)
        ex = root / ".git/info/exclude"
        ex.write_text(ex.read_text().replace(END + "\n", "") + "/scripts/my_own.py\n")
        run(root, pkg, "c0ffee", None, write=True)
        ok("a block with no end line keeps the user's lines", ex.read_text().endswith(END + "\n/scripts/my_own.py\n"))
        ok("verify passes after install",
           run(root, pkg, "c0ffee", None, write=False) == (["KIT PACKAGE PASS: 1 kit scripts from the package at c0ffee"], False))
        (root / "scripts/a.py").write_text("print('edited')\n")
        lines, bad = run(root, pkg, "c0ffee", None, write=False)
        ok("an edited copy fails", bad and "differs from the package: scripts/a.py" in lines[0])
        git(root, "add", "-f", "scripts/a.py")
        ok("with every kit script tracked the package is not used", run(root, pkg, None, None, write=False)[1] is False)
    print("KIT PACKAGE TEST " + ("FAIL: " + "; ".join(fails) if fails else "PASS"))
    return 1 if fails else 0


def main():
    """The command line: --install, --verify or --test.

    Returns:
        The exit code: 0 on a pass, else 1.
    """
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    for m in ("--install", "--verify", "--test"):
        mode.add_argument(m, action="store_true")
    ap.add_argument("--project", default=".", help="the project folder (default: the current folder)")
    a = ap.parse_args()
    if a.test:
        return self_test()
    root = pathlib.Path(git(pathlib.Path(a.project), "rev-parse", "--show-toplevel").strip())
    lines, bad = run(root, PKG, *installed(), write=a.install)
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
