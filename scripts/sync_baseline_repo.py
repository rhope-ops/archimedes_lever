#!/usr/bin/env python3
"""The reads of the baseline repo for scripts/sync_baseline.py: git, the baseline folder or clone, the earlier
versions of a kit file, the baseline commit, the log template, a time stamp, the "- Owner:" line, and the diff of
the planned files. Kit only: projects do not get a copy.

Part of scripts/sync_baseline.py (split out to keep each file under the line cap of docs/code-standard.md C4);
sync_baseline.py imports every name here and re-exports it, so `sync_baseline.<name>` keeps working.
Inputs:  the baseline folder or URL, the project folder, and the planned file texts.
Outputs: paths, texts and lists; show_diff prints a unified diff.
Usage:   imported by scripts/sync_baseline.py; it has no command line.
Network: the baseline repo, only in get_baseline when it is a URL (one git clone).
Writes: a clone in the temporary folder that get_baseline is given; nothing else.
Credentials: none itself; a clone uses the credentials git already has.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

from sync_merge import die  # scripts/sync_merge.py: stop with a message


def git(*args, cwd=None):
    """Run git and return its stripped stdout; raise on failure."""
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def get_baseline(src, tmp):
    """The baseline folder: `src` itself when it is a folder, else a clone of it in `tmp` (with its history: an older
    kit copy of a file is known by it, copy_state).

    Args:
        src: a baseline folder or a git URL.
        tmp: a temporary folder to clone into.
    Returns:
        The path of the baseline folder.
    """
    path = Path(src)
    if path.is_dir():
        return path.resolve()
    dest = Path(tmp) / "baseline"
    try:
        git("clone", "--quiet", src, str(dest))
    except subprocess.CalledProcessError as e:
        die(f"cannot clone baseline {src}: {e.stderr.strip()}")
    return dest


def kit_history(base, rel):
    """The earlier versions of a baseline file, from the baseline's git history.

    Args:
        base: the baseline folder.
        rel: the file's path in it.

    Returns:
        A list of the file's bytes at each commit that changed it, newest first; None when the baseline folder is
        not the top of a git repo (no history to read).
    """
    try:
        if Path(git("rev-parse", "--show-toplevel", cwd=base)).resolve() != Path(base).resolve():
            return None
        shas = git("log", "--format=%H", "--", rel, cwd=base).split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    shown = [subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=base, capture_output=True) for sha in shas]
    return [r.stdout for r in shown if r.returncode == 0]   # a commit that deleted the file has no version


def baseline_sha(base):
    """The baseline commit, marked when its folder has uncommitted changes or is not a git repo.

    Args:
        base: the baseline folder (a Path).
    Returns:
        The commit hash, with a note when the folder has uncommitted changes, or an "unknown" text.
    """
    try:
        if Path(git("rev-parse", "--show-toplevel", cwd=base)).resolve() != base.resolve():
            raise subprocess.CalledProcessError(1, "git")
        sha = git("rev-parse", "HEAD", cwd=base)
        if git("status", "--porcelain", cwd=base):
            sha += " (with uncommitted baseline changes)"
        return sha
    except subprocess.CalledProcessError:
        return "unknown (baseline folder is not a git repo)"


def log_template(base):
    """The blank project log: docs/templates/LOG.md (the kit's docs/LOG.md is its own log); older baselines: docs/LOG.md."""
    t = base / "docs/templates/LOG.md"
    return t if t.exists() else base / "docs/LOG.md"


def log_stamp(zone):
    """'YYYY-MM-DD HH:MM' now, in the project time zone (UTC when the zone database is missing)."""
    import datetime
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(zone)
    except Exception:
        tz = datetime.timezone.utc
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")


def header_owner(text):
    """The project's "- Owner:" value, or None."""
    owner = re.search(r"^- Owner: (.+?)\s*$", text or "", re.M)
    return owner and owner.group(1)


def show_diff(root, new):
    """Print a unified diff for each file that would change; return their paths.

    Args:
        root: the project folder.
        new: a dict of project path to the synced text.
    Returns:
        The list of paths whose text would change.
    """
    changed = []
    for rel, text in new.items():
        path = root / rel
        old = path.read_text() if path.exists() else ""
        if old == text:
            continue
        changed.append(rel)
        sys.stdout.writelines(difflib.unified_diff(
            old.splitlines(True), text.splitlines(True), f"a/{rel}", f"b/{rel}"))
        if not text.endswith("\n"):
            print()
    return changed
