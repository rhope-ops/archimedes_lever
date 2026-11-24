#!/usr/bin/env python3
"""The check side of scripts/sync_baseline.py: before a sync writes, stop when a kit file it would write holds a project change.
Kit only: projects do not get a copy.

Part of scripts/sync_baseline.py (split out to keep each file under the line cap of docs/code-standard.md C4).
Imports go one way: sync_baseline.py imports this file and passes it what it needs (owner, kit_files, copy_state);
this file imports nothing from sync_baseline.py. It reads the project, the kit lock and the kit history; it writes nothing.
Inputs:  the baseline folder, the project folder, the planned files (a dict of path to text) that sync_baseline.py builds, the owner word.
Outputs: nothing when no kit file holds a project change; else the files with their way forward, and exit 2.
Usage:   imported by scripts/sync_baseline.py; it has no command line of its own.
Prevents: a sync overwrites a project change to a kit file without a word, so the change is lost
Network: none.
Writes: nothing.
Credentials: none.
"""
import sys

import check_lock  # scripts/check_lock.py: the kit lock that a sync checks before it writes


def unlocked_kit_files(base, root, new, owner, kit_files, copy_state):
    """The kit files this sync writes that the lock does not list and that the project already has with a project change.

    A copy that has the kit's text (line ends as read_text gives them, as the lock hash does) or is an earlier kit
    version holds no project change, so it is not listed.

    Args:
        base: the baseline folder.
        root: the project folder.
        new: a dict of project path to the synced text.
        owner: the owner word of this sync (sync_baseline.project_owner).
        kit_files: the paths the kit lock covers (sync_baseline.COPY_FILES).
        copy_state: the function that tells an earlier kit copy from a project change (sync_baseline.copy_state).

    Returns:
        A dict of path to the reason; empty when the project has no lock.
    """
    data = check_lock.load(root)
    if data is None:
        return {}
    found = {}
    for rel in sorted(new):
        path = root / rel
        if rel not in kit_files or rel in data["files"] or not path.is_file():
            continue
        if path.read_text(encoding="utf-8", errors="replace") == new[rel]:
            continue
        state = copy_state(base, root, rel, owner)[0]
        if state == "older":
            continue
        found[rel] = "not in the kit lock, and differs from the kit's file"
        if state == "unknown":
            found[rel] += "; the baseline has no git history, so an earlier kit copy cannot be told from a project change: " \
                          "if it is an old kit copy, delete the file and sync again"
    return found


def stop_on_changed_kit_files(base, root, new, owner, kit_files, copy_state):
    """Stop (exit 2, nothing written) when a kit file that this sync writes differs from its hash in the kit lock
    .check.lock, is an override in it, or is not in it and holds a project change. A lock that cannot be read is
    said in one line and does not stop the sync.

    Args:
        base: the baseline folder.
        root: the project folder.
        new: a dict of project path to the synced text (the files this sync writes).
        owner: the owner word of this sync (sync_baseline.project_owner).
        kit_files: the paths the kit lock covers (sync_baseline.COPY_FILES).
        copy_state: the function that tells an earlier kit copy from a project change (sync_baseline.copy_state).
    """
    try:
        found = {rel: "differs from the kit lock or is an override in it" for rel in check_lock.changed(root, set(new))}
        found.update(unlocked_kit_files(base, root, new, owner, kit_files, copy_state))
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
