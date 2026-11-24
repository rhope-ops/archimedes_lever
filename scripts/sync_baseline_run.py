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


def unlocked_kit_files(sb, base, root, new, args):
    """The kit files this sync writes that the lock does not list and that the project already has with a project change.

    A copy that has the kit's text (line ends as read_text gives them, as the lock hash does) or is an earlier kit
    version holds no project change, so it is not listed.

    Args:
        sb: the sync_baseline module (COPY_FILES, copy_state, project_owner).
        base: the baseline folder.
        root: the project folder.
        new: a dict of project path to the synced text.
        args: the parsed command line.

    Returns:
        A dict of path to the reason; empty when the project has no lock.
    """
    data = check_lock.load(root)
    if data is None:
        return {}
    found = {}
    for rel in sorted(new):
        path = root / rel
        if rel not in sb.COPY_FILES or rel in data["files"] or not path.is_file():
            continue
        if path.read_text(encoding="utf-8", errors="replace") == new[rel]:
            continue
        state = sb.copy_state(base, root, rel, sb.project_owner(root, args))[0]
        if state == "older":
            continue
        found[rel] = "not in the kit lock, and differs from the kit's file"
        if state == "unknown":
            found[rel] += "; the baseline has no git history, so an earlier kit copy cannot be told from a project change: " \
                          "if it is an old kit copy, delete the file and sync again"
    return found


def stop_on_changed_kit_files(sb, base, root, new, args):
    """Stop (exit 2, nothing written) when a kit file that this sync writes differs from its hash in the kit lock
    .check.lock, is an override in it, or is not in it and holds a project change. A lock that cannot be read is
    said in one line and does not stop the sync.

    Args:
        sb: the sync_baseline module.
        base: the baseline folder.
        root: the project folder.
        new: a dict of project path to the synced text (the files this sync writes).
        args: the parsed command line.
    """
    try:
        found = {rel: "differs from the kit lock or is an override in it" for rel in check_lock.changed(root, set(new))}
        found.update(unlocked_kit_files(sb, base, root, new, args))
    except ValueError:
        print(f"{check_lock.LOCK} could not be read: local edits to kit files were not checked.")
        return
    if found:
        rules_way = "put the project's own rules in AGENTS.md \"Project rules\", or change the text in the kit"
        skill_way = "move the project's change into a PROJECT.md beside the kit skill, or change the file in the kit"
        script_way = "move the project's change into scripts/check.local.sh or .check, or change the file in the kit"
        print(f"Sync stopped, nothing written: {len(found)} kit file(s) in this project would be overwritten:")
        for rel, why in sorted(found.items()):
            if rel == check_lock.KIT_PART:
                way = rules_way
            elif rel.startswith(".claude/skills/"):
                way = skill_way
            else:
                way = script_way
            print(f"  {rel} ({why}): {way}.")
        print("Then run the sync again.")
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
        new, tier = sb.planned_files(base, root, args)
        stop_on_changed_kit_files(sb, base, root, new, args)
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
