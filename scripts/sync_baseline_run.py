#!/usr/bin/env python3
"""The write side of scripts/sync_baseline.py: stop on a template placeholder, list the files a sync leaves for you to
delete, write the changed files and write the kit lock. Kit only: projects do not get a copy.

Part of scripts/sync_baseline.py (split out to keep each file under the line cap of docs/code-standard.md C4).
Imports go one way: sync_baseline.py imports this file and passes it the lists it needs (kit_files, advanced, moved);
this file imports nothing from sync_baseline.py. The plan (planned_files, build_agents, new_log) and main stay there.
Inputs:  the project git repo, the baseline folder, and the planned files (a dict of path to text) that sync_baseline.py builds.
Outputs: with write_files, the files and the kit lock (the sync_baseline.py header); the notes of report_leftovers.
Usage:   imported by scripts/sync_baseline.py; it has no command line of its own.
Prevents: a sync writes the wrong kit files or lock into a project, or writes into a project with uncommitted changes
Network: none.
Writes: with write_files and write_lock, the kit files of the project and its kit lock .check.lock.
Credentials: none.
"""
import shutil

import check_blocks  # scripts/check_blocks.py: the placeholder pattern
import check_lock  # scripts/check_lock.py: the kit lock that a sync writes
from sync_baseline_repo import baseline_sha, git  # scripts/sync_baseline_repo.py: git and the baseline's commit
from sync_merge import die  # scripts/sync_merge.py: stop with a message


def check_placeholders(root):
    """Stop when AGENTS.md, README.md or docs/*.md still holds a {{PLACEHOLDER}} (bootstrap has not run)."""
    for f in [root / "AGENTS.md", root / "README.md", *sorted(root.glob("docs/*.md"))]:
        rel = f.relative_to(root)
        if f.is_file() and check_blocks.placeholders([f]):
            die(f"{rel} still has template placeholders; run scripts/bootstrap.sh first")


def report_leftovers(root, tier, advanced, moved):
    """List the advanced files a starter project keeps and old copies of moved files, for deletion by hand.

    Args:
        root: the project folder.
        tier: the kit tier.
        advanced: the paths of the advanced files (sync_baseline.ADVANCED_FILES).
        moved: the paths that moved or were renamed in the kit (sync_baseline.MOVED_FILES).
    """
    if tier == "starter":
        extra = [f for f in advanced if (root / f).exists()]
        if extra:
            print(f"Tier starter: these advanced files are not synced; delete them by hand if you want: {', '.join(extra)}")
    old = [f for f in moved if (root / f).exists()]
    if old:
        print(f"These files moved or were renamed in the kit; delete the old copies by hand: {', '.join(old)}")
    old = [f for f in (".pii-guard", ".code-standard.json", ".bloat-audit.json") if (root / f).exists()]
    if old:
        print(f"Old settings files ({', '.join(old)}): run 'python3 scripts/check_settings.py --migrate' (it moves "
              "them into .check and .check.state.json; the lines of .check stay as they are).")


def write_files(base, root, new, changed, kit_files):
    """Write the changed files (with the baseline's file mode for scripts); stop when the project is not committed.

    Args:
        base: the baseline folder.
        root: the project folder.
        new: a dict of project path to the synced text.
        changed: the paths to write.
        kit_files: the paths the kit lock covers (sync_baseline.COPY_FILES).
    """
    if git("status", "--porcelain", cwd=root):
        die("the project has uncommitted changes; commit them first")
    for rel in changed:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new[rel])
        if rel.endswith((".sh", ".py")) or rel.startswith("scripts/git-hooks/"):
            shutil.copymode(base / rel, path) if (base / rel).exists() else None
    version = write_lock(base, root, new, kit_files)
    print(f"Written, with the kit lock {check_lock.LOCK} (kit version {version}). Review with 'git diff', then commit and push.")


def write_lock(base, root, files, kit_files):
    """Write the kit lock of the project for the kit files among `files`; return the kit version.

    Args:
        base: the baseline folder.
        root: the project folder.
        files: the paths a sync wrote or planned.
        kit_files: the paths the kit lock covers (sync_baseline.COPY_FILES).

    Returns:
        The kit version that the lock records.
    """
    version = (base / "KIT_VERSION").read_text().strip() if (base / "KIT_VERSION").exists() else "unknown"
    check_lock.write(root, check_lock.build(root, [r for r in files if r in kit_files], version,
                                            baseline_sha(base).split()[0]))
    return version
