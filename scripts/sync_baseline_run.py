#!/usr/bin/env python3
"""The steps of one run of scripts/sync_baseline.py: read the command line, find the project and the baseline, show
the diff (dry run) or write it (--apply), or apply --set-tier or --lock-here in place. Kit only: projects do not get
a copy.

Part of scripts/sync_baseline.py (split out to keep each file under the line cap of docs/code-standard.md C4).
sync_baseline.main() calls run() with the sync_baseline module itself as `sb`, so the lists, the notes and the
helpers in force are the ones of that module.
Inputs:  the command line (sync_baseline.parse_args), the project git repo, and the baseline folder or URL.
Outputs: the kit baseline line, the diff, notes and the result line; with --apply, the files (sync_baseline.py header).
Usage:   imported by scripts/sync_baseline.py; it has no command line of its own.
Prevents: a sync writes the wrong kit files or lock into a project, or writes with no dry-run diff the Maintainer can see
Network: the baseline repo, only when --baseline is a URL (one git clone).
Writes: with --apply, the kit files of the project and its kit lock .check.lock; without it, nothing.
Credentials: none itself; a clone uses the credentials git already has.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import check_blocks  # scripts/check_blocks.py: the placeholder pattern
import check_lock  # scripts/check_lock.py: the kit lock that a sync checks before it writes
from sync_merge import changed_matchers, die  # scripts/sync_merge.py: the hook matchers a sync replaces; stop with a message


def check_placeholders(root):
    """Stop when AGENTS.md, README.md or docs/*.md still holds a {{PLACEHOLDER}} (bootstrap has not run)."""
    for f in [root / "AGENTS.md", root / "README.md", *sorted(root.glob("docs/*.md"))]:
        rel = f.relative_to(root)
        if f.is_file() and check_blocks.placeholders([f]):
            die(f"{rel} still has template placeholders; run scripts/bootstrap.sh first")


def stop_on_changed_kit_files(root):
    """Stop (exit 2, nothing written) when a kit file in the project differs from its hash in the kit lock .check.lock.

    Args:
        root: the project folder.
    """
    changed = check_lock.changed(root)
    if changed:
        print(f"Sync stopped, nothing written: {len(changed)} kit file(s) in this project differ from the kit lock "
              f"{check_lock.LOCK}:\n  " + "\n  ".join(changed) + "\nA sync would overwrite them. Move this project's change into a "
              "PROJECT.md beside the kit skill (or into AGENTS.md \"Project rules\" or .check), or make the change in the kit "
              "and sync from there. Then run the sync again.")
        sys.exit(2)


def run(sb):
    """Sync the project: show the diff (dry run) or write it (--apply); or apply --set-tier in place.

    Args:
        sb: the sync_baseline module (its parse_args, lists, notes and write steps).
    """
    args = sb.parse_args()
    try:
        root = Path(sb.git("rev-parse", "--show-toplevel"))
    except subprocess.CalledProcessError:
        die("run this inside the project git repo")
    if args.set_tier:
        sb.set_tier(root, args.set_tier)
        return
    if args.lock_here:  # bootstrap: this clone of the kit becomes a project; lock its kit files as they are now
        sb.write_lock(root, root, sb.COPY_FILES)
        return

    with tempfile.TemporaryDirectory() as tmp:
        base = sb.get_baseline(args.baseline, tmp)
        if base.resolve() == root.resolve():
            die("this is the baseline repo itself; run the script in a project repo")
        print(f"Kit baseline: {sb.baseline_sha(base)}. A sync writes the kit lock {sb.check_lock.LOCK} (the kit version and a "
              "hash of each kit file); the project does not keep the sync tools.")
        check_placeholders(root)
        stop_on_changed_kit_files(root)
        new, tier = sb.planned_files(base, root, args)
        changed = sb.show_diff(root, new)
        sb.report_leftovers(root, tier)
        for note in sb.COPY_NOTES:
            print(note)
        for matcher in changed_matchers(sb.REPLACED_HOOKS, base / ".claude/settings.json"):
            print("An older kit hook entry is replaced by the kit's. If you had added tool names to its matcher, add a "
                  f"hook entry of your own for them. The old matcher: {matcher}")
        if not changed:
            print("No changes: the project already matches the baseline.")
            if args.apply:
                sb.write_lock(base, root, new)
            return
        print(f"\n{len(changed)} file(s) to change: {', '.join(changed)}")
        if not args.apply:
            print("Dry run: nothing written. Run again with --apply to write.")
            return
        sb.write_files(base, root, new, changed)
