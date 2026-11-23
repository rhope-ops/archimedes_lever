#!/usr/bin/env python3
"""The reader of kit.config.json: the one home of the kit's own addresses (fleet v2 plan DEC 7, 2026-11-23).

Why: the kit's repo address and the fleet page address were written into several scripts and docs. A new maintainer
changes them in one file; no script holds a fallback copy of an address.
Keys:    kit_repo (owner/name), kit_url (the git URL that sync_baseline.py and the token_log self-update clone),
         fleet_page (the private fleet page that docs/fleet.md names).
Inputs:  kit.config.json in the repo root (the parent of this scripts/ folder), or in a folder the caller names.
Outputs: the value of a key, or None when the file or the key is missing (the caller stops with its own message).
Network: none.  Writes: none.  Credentials: none.
Run:     kit only (not synced; bootstrap deletes it); imported by scripts/sync_baseline.py and scripts/drift.py;
         `python3 scripts/kit_config.py --test` is the self-test (scripts/check.sh runs it).
"""

import json
import os
import sys
import tempfile

NAME = "kit.config.json"
KEYS = ("kit_repo", "kit_url", "fleet_page")


def find(folders=None):
    """The path of the first kit.config.json in the folders, in order.

    Args:
        folders: folders to look in (default: the repo root that holds this scripts/ folder).
    Returns:
        The path as a string, or None when no folder has the file.
    """
    if folders is None:
        folders = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    for folder in folders:
        if folder and os.path.isfile(os.path.join(folder, NAME)):
            return os.path.join(folder, NAME)
    return None


def value(key, folders=None):
    """The value of one key of kit.config.json.

    Args:
        key: one of KEYS.
        folders: as in find().
    Returns:
        The value (a non-empty string), or None when the file, the key or its value is missing.
    Raises:
        ValueError: the key is not one of KEYS, or the file is not a JSON object.
    """
    if key not in KEYS:
        raise ValueError(f"{NAME}: unknown key {key!r} (known: {', '.join(KEYS)})")
    path = find(folders)
    if path is None:
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: not a JSON object")
    got = data.get(key)
    return got if isinstance(got, str) and got.strip() else None


def self_test():
    """Check find() and value() on temporary folders and the kit's own kit.config.json; print one line per failure.

    Returns:
        The number of failed cases (0: all passed).
    """
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        a, b = os.path.join(tmp, "a"), os.path.join(tmp, "b")
        os.makedirs(a)
        os.makedirs(b)
        with open(os.path.join(b, NAME), "w", encoding="utf-8") as f:
            json.dump({"kit_url": "https://example.invalid/sample-org/sample-kit", "kit_repo": ""}, f)
        cases = [
            ("first folder with the file wins", find([a, b]) == os.path.join(b, NAME)),
            ("no file gives None", find([a]) is None and value("kit_url", [a]) is None),
            ("value read", value("kit_url", [a, b]) == "https://example.invalid/sample-org/sample-kit"),
            ("empty value gives None", value("kit_repo", [b]) is None),
            ("missing key gives None", value("fleet_page", [b]) is None),
        ]
        try:
            value("other", [b])
            cases.append(("unknown key raises", False))
        except ValueError:
            cases.append(("unknown key raises", True))
        with open(os.path.join(a, NAME), "w", encoding="utf-8") as f:
            f.write("[]")
        try:
            value("kit_url", [a])
            cases.append(("non-object raises", False))
        except ValueError:
            cases.append(("non-object raises", True))
        cases.append(("the kit's own file has every key", all(value(k) for k in KEYS)))
    for name, ok in cases:
        if not ok:
            fails += 1
            print(f"FAIL {name}")
    print(f"KIT CONFIG TEST {'PASS' if not fails else 'FAIL'}: {len(cases) - fails} of {len(cases)} cases")
    return fails


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        sys.exit(1 if self_test() else 0)
    for k in KEYS:
        print(f"{k}: {value(k)}")
