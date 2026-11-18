#!/usr/bin/env python3
"""The one reader of the code standard and audit settings in `.check`, and the one reader and writer of
`.check.state.json` (the owner, 2026-11-18: one config layout in every repo).

The three files at the top of a repo:
    .check             every setting a person edits: one entry per line, `#` comments. The content check reads its
                       own lines (scripts/check_content_scan.py); this module reads the `code-` and `audit-` lines.
    .check.lock        written by a sync (scripts/check_lock.py); not read here.
    .check.state.json  everything tools write: {"code_standard": {"debt": {...}}, "audit": {"last_audit": {...}},
                       "timings": {...}}, with sorted keys and indent 1, so the same state gives the same bytes.

The setting lines (a missing key means the default; a key marked * may appear on several lines):
    code-max-file-lines: 600        code-max-function-lines: 60
    code-include: <glob> *          code-exclude: <glob> *          code-generated: <glob> *
    code-c1-safety: on|off          code-c2: full|lean
    audit-every-days: 14            audit-every-commits: 300
    audit-ignore: <glob> *          audit-start-read: <path> *
    audit-budget-<name>: <number>   names: the keys of AUDIT_DEFAULTS["budgets"]; the three KIT_CAPS may only be lowered
An unknown `code-` or `audit-` key, a key in capitals, a single key on two lines, or a value that is not valid raises
ValueError: the check that reads it fails with that message (a typo must not relax a limit in silence).

Inputs:  `.check` and `.check.state.json` in the working tree or at a git ref (`git show <ref>:<file>`); for --migrate
         also the old files `.code-standard.json`, `.bloat-audit.json` and `.pii-guard`.
Outputs: settings as dicts for scripts/code_standard.py and scripts/bloat_check.py; `.check.state.json` on a write.
Usage:   python3 scripts/check_settings.py            print the settings and the state that the checks read (JSON)
         python3 scripts/check_settings.py --migrate  move the old files of this repo into the three files: append
                                                      the settings that are not defaults to `.check` (existing lines
                                                      stay as they are), write `.check.state.json`, delete the old
                                                      files; prints each step; a second run changes nothing
         python3 scripts/check_settings.py --test     self-test in temporary repos; prints SETTINGS TEST PASS
Needs:   Python 3.8+ and git. Standard library only.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

CHECK = ".check"
STATE = ".check.state.json"
OLD_CODE = ".code-standard.json"   # before 2026-11-18: the code standard's caps, scope and debt list
OLD_AUDIT = ".bloat-audit.json"    # before 2026-11-18: the audit's settings, last audit and time baselines
OLD_CHECK = ".pii-guard"           # before 2026-11-18: the name of .check
MIGRATE = "python3 scripts/check_settings.py --migrate"
CODE_DEFAULTS = {"caps": {"max_file_lines": 600, "max_function_lines": 60}, "include": ["*"], "exclude": [],
                 "generated": [], "c1_safety": False, "c2": "lean"}
AUDIT_DEFAULTS = {"every_days": 14, "every_commits": 300, "start_read": [], "ignore": [],
                  "budgets": {"session_load_tokens": 6000, "session_load_warn_tokens": 5000, "rules_file_lines": 200,
                              "handoff_lines": 40, "file_kb": 500, "duplicate_lines": 20, "rules": 35,
                              "project_rules": 15}}
# The owner's caps for every repo (2026-11-18): a project can lower one of these budgets, never raise it.
KIT_CAPS = ("session_load_tokens", "session_load_warn_tokens", "rules_file_lines")
CODE_LISTS = ("include", "exclude", "generated")
AUDIT_LISTS = ("ignore", "start_read")
SETTING_LINE = re.compile(r"(?i)^((?:code|audit)-[A-Za-z0-9_-]+)\s*:\s*(.*)$")
# A docs/DECISIONS.md row "names .check" with the file name itself, not .check.lock or .check.state.json.
NAMES_CHECK = re.compile(r"(?<![\w.])\.check(?!\.(?:lock|state)|\w)")
STATE_PARTS = ("code_standard", "audit", "timings")


def read(root, name, ref=None):
    """The bytes of a top-level file in the working tree, or at a git ref; None when it does not exist there."""
    if ref:
        r = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{name}"], capture_output=True)
        return r.stdout if r.returncode == 0 else None
    p = Path(root) / name
    return p.read_bytes() if p.is_file() else None


def pairs(data):
    """[(key, value)] of the `code-` and `audit-` lines in the bytes of a .check file (None: no file), in file
    order. Comments and invisible characters are dropped the way the content check drops them."""
    if data is None:
        return []
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError(f"{CHECK} is not UTF-8 text: save it as UTF-8") from None
    out = []
    for raw in text.splitlines():
        line = "".join(c for c in raw if unicodedata.category(c) != "Cf")
        m = SETTING_LINE.match(re.split(r"(?:^|\s)#", line, maxsplit=1)[0].strip())
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


def collect(found, prefix, single, multi):
    """{key: value, or [values] for a key in multi} of the pairs whose key starts with prefix. ValueError for an
    unknown key (also a known key in capitals), a key with no value, and a single key on two lines."""
    out = {}
    for key, value in found:
        if not key.lower().startswith(prefix):
            continue
        if key not in single and key not in multi:
            raise ValueError(f"{CHECK}: unknown setting `{key}:` (the keys: the header of scripts/check_settings.py)")
        if not value:
            raise ValueError(f"{CHECK}: `{key}:` has no value")
        if key in multi:
            out.setdefault(key, []).append(value)
        elif key in out:
            raise ValueError(f"{CHECK}: `{key}:` is on two lines; keep one")
        else:
            out[key] = value
    return out


def number(key, value, least):
    """The whole number of a setting line; ValueError when it is not one, or is under `least`."""
    if not re.fullmatch(r"[0-9]{1,9}", value) or int(value) < least:
        raise ValueError(f"{CHECK}: `{key}: {value}` is not valid: use a whole number of {least} or more")
    return int(value)


def choice(key, value, options):
    """The value of a setting line that takes one of a few words; ValueError for any other word."""
    if value not in options:
        raise ValueError(f"{CHECK}: `{key}: {value}` is not valid: use {' or '.join(options)}")
    return value


def dash(name):
    """The key form of a settings name: max_file_lines -> max-file-lines."""
    return name.replace("_", "-")


def not_migrated(root, name):
    """ValueError when the working tree still has an old settings file: its limits must not be dropped in silence."""
    if (Path(root) / name).is_file():
        raise ValueError(f"{name} is the old layout: run `{MIGRATE}` (it moves the settings into {CHECK} and the "
                         f"state into {STATE})")


def code_settings(found):
    """The code standard settings from setting pairs: {"caps": {...}, "include": [...], "exclude": [...],
    "generated": [...], "c1_safety": bool, "c2": "lean"|"full"}. Lists are sorted, so two equal settings compare
    equal. ValueError for a line that is not valid."""
    single = ["code-" + dash(c) for c in CODE_DEFAULTS["caps"]] + ["code-c1-safety", "code-c2"]
    got = collect(found, "code-", single, ["code-" + n for n in CODE_LISTS])
    cfg = json.loads(json.dumps(CODE_DEFAULTS))
    for cap in cfg["caps"]:
        if "code-" + dash(cap) in got:
            cfg["caps"][cap] = number("code-" + dash(cap), got["code-" + dash(cap)], 1)
    for name in CODE_LISTS:
        if "code-" + name in got:
            cfg[name] = sorted(set(got["code-" + name]))
    cfg["c1_safety"] = choice("code-c1-safety", got.get("code-c1-safety", "off"), ("on", "off")) == "on"
    cfg["c2"] = choice("code-c2", got.get("code-c2", "lean"), ("full", "lean"))
    return cfg


def code_config(root, ref=None):
    """The code standard settings of `.check` in the working tree, or at a git ref (shape: code_settings)."""
    if ref is None:
        not_migrated(root, OLD_CODE)
    return code_settings(pairs(read(root, CHECK, ref)))


def code_from_old(old):
    """The settings dict (the shape of code_config) of the "config" of an old .code-standard.json."""
    cfg = json.loads(json.dumps(CODE_DEFAULTS))
    cfg["caps"].update(old.get("caps", {}))
    for name in CODE_LISTS:
        if name in old:
            cfg[name] = sorted(set(old[name]))
    cfg["c1_safety"] = bool(old.get("c1_safety"))
    cfg["c2"] = "full" if old.get("c2") == "full" else "lean"
    return cfg


def code_base(root, ref):
    """(settings, debt) of the code standard at a git ref, or None when that commit has no baseline. Transition: a
    commit with no code standard part in `.check.state.json` but with the old .code-standard.json is read from that
    file, so the first change after a migration is still compared with what main had."""
    part = load_state(root, ref).get("code_standard")
    if part is not None:
        return code_config(root, ref), part.get("debt", {})
    old = read(root, OLD_CODE, ref)
    if old is None:
        return None
    data = json.loads(old)
    return code_from_old(data.get("config", {})), data.get("debt", {})


def audit_settings(found):
    """The audit settings from setting pairs: AUDIT_DEFAULTS with each `audit-` line applied. ValueError for a line
    that is not valid, and for a KIT_CAPS budget set above the kit's value."""
    budgets = AUDIT_DEFAULTS["budgets"]
    single = ["audit-every-days", "audit-every-commits"] + ["audit-budget-" + b for b in budgets]
    got = collect(found, "audit-", single, ["audit-" + dash(n) for n in AUDIT_LISTS])
    cfg = json.loads(json.dumps(AUDIT_DEFAULTS))
    for name in ("every_days", "every_commits"):
        if "audit-" + dash(name) in got:
            cfg[name] = number("audit-" + dash(name), got["audit-" + dash(name)], 1)
    for name in budgets:
        key = "audit-budget-" + name
        if key in got:
            cfg["budgets"][name] = number(key, got[key], 0)
            if name in KIT_CAPS and cfg["budgets"][name] > budgets[name]:
                raise ValueError(f"{CHECK}: `{key}: {got[key]}` is not valid: this is a kit cap, a project can lower "
                                 f"it, never raise it (at most {budgets[name]})")
    for name in AUDIT_LISTS:
        cfg[name] = got.get("audit-" + dash(name), [])
    return cfg


def audit_config(root):
    """What scripts/bloat_check.py works with: the audit settings of `.check`, plus "last_audit" and "timings" from
    `.check.state.json`. ValueError when a file cannot be read or a line is not valid."""
    not_migrated(root, OLD_AUDIT)
    cfg = audit_settings(pairs(read(root, CHECK)))
    state = load_state(root)
    cfg["last_audit"] = state.get("audit", {}).get("last_audit")
    cfg["timings"] = state.get("timings", {})
    return cfg


def audit_from_old(old):
    """The audit settings dict of an old .bloat-audit.json; a KIT_CAPS budget above the kit's value is cut to it, as
    the old reader did."""
    cfg = json.loads(json.dumps(AUDIT_DEFAULTS))
    for name in ("every_days", "every_commits") + AUDIT_LISTS:
        if name in old:
            cfg[name] = old[name]
    cfg["budgets"].update(old.get("budgets", {}))
    for name in KIT_CAPS:
        cfg["budgets"][name] = min(cfg["budgets"][name], AUDIT_DEFAULTS["budgets"][name])
    return cfg


def load_state(root, ref=None):
    """The dict in `.check.state.json` (working tree, or at a git ref); {} when the file does not exist.
    ValueError when it is not JSON, not an object, or one of its parts is not an object."""
    data = read(root, STATE, ref)
    if data is None:
        return {}
    try:
        state = json.loads(data.decode("utf-8"))
    except ValueError as e:
        raise ValueError(f"{STATE} is not JSON ({e})") from None
    if not isinstance(state, dict) or any(not isinstance(state.get(p, {}), dict) for p in STATE_PARTS):
        raise ValueError(f"{STATE}: the top level and each of its parts must be an object")
    return state


def state_text(state):
    """The file text of a state dict: sorted keys and indent 1, so the same state gives the same bytes."""
    return json.dumps(state, indent=1, sort_keys=True) + "\n"


def save_part(root, part, value):
    """Write one part ("code_standard", "audit" or "timings") into `.check.state.json`; the file is read again
    first, so the parts of the other tools stay as they are."""
    state = load_state(root)
    state[part] = value
    (Path(root) / STATE).write_text(state_text(state), encoding="utf-8")


# ---------------------------------------------------------------- migration ------------------------------------------

def code_lines(cfg):
    """The `.check` lines for the code standard settings that differ from the defaults."""
    out = [f"code-{dash(c)}: {v}" for c, v in cfg["caps"].items() if v != CODE_DEFAULTS["caps"].get(c)]
    for name in CODE_LISTS:
        if cfg[name] != CODE_DEFAULTS[name]:
            out += [f"code-{name}: {g}" for g in cfg[name]]
    return out + (["code-c1-safety: on"] if cfg["c1_safety"] else []) + (["code-c2: full"] if cfg["c2"] == "full" else [])


def audit_lines(cfg):
    """The `.check` lines for the audit settings that differ from the defaults."""
    out = [f"audit-{dash(n)}: {cfg[n]}" for n in ("every_days", "every_commits") if cfg[n] != AUDIT_DEFAULTS[n]]
    out += [f"audit-budget-{b}: {v}" for b, v in cfg["budgets"].items() if v != AUDIT_DEFAULTS["budgets"].get(b)]
    for name in AUDIT_LISTS:
        out += [f"audit-{dash(name)}: {g}" for g in cfg[name]]
    return out


def old_json(root, name):
    """The object in an old JSON settings file, or None when the file does not exist."""
    data = read(root, name)
    if data is None:
        return None
    obj = json.loads(data.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{name}: top level is not an object")
    return obj


def migrate_plan(root):
    """Work out the migration and change nothing: returns (new bytes of .check or None, new state or None, old files
    to delete, lines to print). ValueError when the new `.check` would not give the same settings as the old files
    (for example a key that is already there with another value), so nothing is lost in silence."""
    root = Path(root)
    code, audit = old_json(root, OLD_CODE), old_json(root, OLD_AUDIT)
    data, renamed = read(root, CHECK), False
    if data is None and (root / OLD_CHECK).is_file():
        data, renamed = read(root, OLD_CHECK), True
    notes = []
    if not renamed and (root / OLD_CHECK).is_file():
        notes.append(f"NOTE  both {CHECK} and {OLD_CHECK} exist: move the lines of {OLD_CHECK} into {CHECK} by hand, "
                     "then delete it")
    if code is None and audit is None and not renamed:
        return None, None, [], notes + ["nothing to migrate: no old settings file here"]
    want = [(OLD_CODE, code_from_old(code.get("config", {})), code_lines, code_settings)] if code is not None else []
    want += [(OLD_AUDIT, audit_from_old(audit), audit_lines, audit_settings)] if audit is not None else []
    have = {l.strip() for l in (data or b"").decode("utf-8", "replace").splitlines()}
    add = [l for _, cfg, lines, _ in want for l in lines(cfg) if l not in have]
    text = data or b""
    if add:
        text += b"" if not text or text.endswith(b"\n") else b"\n"
        text += ("# Code standard and audit settings (the keys: the header of scripts/check_settings.py).\n"
                 + "\n".join(add) + "\n").encode()
    for name, cfg, _, parse in want:
        if parse(pairs(text)) != cfg:
            raise ValueError(f"the settings of {name} cannot be written into {CHECK} as they are (a value with no "
                             "line form, or a line that is already there with another value)")
    state = load_state(root)
    if code is not None:
        state["code_standard"] = {"debt": code.get("debt", {})}
    if audit is not None and audit.get("last_audit"):
        state["audit"] = {"last_audit": audit["last_audit"]}
    if audit is not None and audit.get("timings"):
        state["timings"] = audit["timings"]
    known = {OLD_CODE: ("config", "debt"), OLD_AUDIT: tuple(AUDIT_DEFAULTS) + ("last_audit", "timings")}
    for name, obj in ((OLD_CODE, code), (OLD_AUDIT, audit)):
        extra = sorted(set(obj or {}) - set(known[name]))
        notes += [f"NOTE  {name}: unknown key(s) not moved: {', '.join(extra)}"] if extra else []
    notes += [f"{CHECK}: started from the lines of {OLD_CHECK}"] if renamed else []
    notes += [f"{CHECK}: added `{l}`" for l in add] or (
        [f"{CHECK}: no setting line to add (the old settings are the defaults, or the lines are there)"] if want else [])
    gone = [n for n, there in ((OLD_CODE, code is not None), (OLD_AUDIT, audit is not None), (OLD_CHECK, renamed)) if there]
    return (text if add or renamed else None), (state if want else None), gone, notes


def migrate(root):
    """--migrate: move the old settings files of this repo into `.check` and `.check.state.json`, delete them, and
    print each step. Returns 0, or 1 with nothing changed when the old settings cannot be moved as they are."""
    root = Path(root)
    try:
        text, state, gone, notes = migrate_plan(root)
    except ValueError as e:
        print(f"SETTINGS MIGRATE FAIL: {e}. Nothing changed.")
        return 1
    if text is not None:
        new = not (root / CHECK).is_file()
        (root / CHECK).write_bytes(text)
        if new and OLD_CHECK not in gone:
            notes.append(f"NOTE  {CHECK} is new here: the content check of tracked files is now on "
                         "(.claude/skills/personal-data/SKILL.md)")
    if state is not None:
        (root / STATE).write_text(state_text(state), encoding="utf-8")
        notes.append(f"{STATE}: written ({', '.join(p for p in STATE_PARTS if p in state)})")
    for name in gone:
        (root / name).unlink()
        notes.append(f"{name}: deleted")
    print("\n".join(notes))
    if gone:
        print(f"SETTINGS MIGRATED: review with git diff, then commit {CHECK}, {STATE} and the deleted files")
    return 0


# ---------------------------------------------------------------- self-test ------------------------------------------

def fails(call, *args):
    """The message of the ValueError that call(*args) raises, or "" when it raises none."""
    try:
        call(*args)
    except ValueError as e:
        return str(e)
    return ""


def test_settings(root, git):
    """Self-test of the readers: defaults, each key, the lines that must fail, a git ref, and the state file."""
    assert code_config(root) == CODE_DEFAULTS and audit_settings([]) == AUDIT_DEFAULTS, "no .check: the defaults"
    assert code_lines(CODE_DEFAULTS) == audit_lines(AUDIT_DEFAULTS) == [], "the defaults need no line"
    (root / CHECK).write_text("# c\nAllowed Name\nskip: a/*\nprofile: dod\ncode-max-file-lines: 300  # lower\n"
                              "code-exclude: vendor/*\ncode-exclude: a.py\ncode-c1-safety: on\ncode-c2: full\n"
                              "audit-every-days: 7\naudit-ignore: ref/**\naudit-start-read: docs/A.md\n"
                              "audit-budget-file_kb: 100\naudit-budget-rules_file_lines: 150\n")
    cfg = code_config(root)
    assert cfg["caps"] == {"max_file_lines": 300, "max_function_lines": 60} and cfg["exclude"] == ["a.py", "vendor/*"] \
        and cfg["include"] == ["*"] and cfg["c1_safety"] and cfg["c2"] == "full", "the code- lines are read: %s" % cfg
    aud = audit_config(root)
    assert aud["every_days"] == 7 and aud["every_commits"] == 300 and aud["ignore"] == ["ref/**"] \
        and aud["start_read"] == ["docs/A.md"] and aud["budgets"]["file_kb"] == 100 \
        and aud["budgets"]["rules_file_lines"] == 150 and aud["timings"] == {}, "the audit- lines are read: %s" % aud
    for line, why in (("code-max-file-line: 900", "unknown setting"), ("Code-max-file-lines: 900", "unknown setting"),
                      ("code-max-file-lines: many", "whole number"), ("code-max-file-lines: 0", "whole number"),
                      ("code-max-file-lines:", "no value"), ("code-c2: ful", "use full or lean"),
                      ("code-c1-safety: yes", "use on or off"), ("code-c2: full\ncode-c2: lean", "two lines")):
        (root / CHECK).write_text(line + "\n")
        assert why in fails(code_config, root), "a code- line that is not valid fails: " + line
    for line, why in (("audit-every-day: 1", "unknown setting"), ("audit-budget-nope: 1", "unknown setting"),
                      ("audit-every-days: 1.5", "whole number"), ("audit-budget-session_load_tokens: 6001", "never raise")):
        (root / CHECK).write_text(line + "\n")
        assert why in fails(audit_config, root), "an audit- line that is not valid fails: " + line
    assert code_config(root) == CODE_DEFAULTS, "a bad audit- line does not fail the code standard"
    (root / CHECK).write_bytes(b"\xff\xfec\x00o\x00")
    assert "UTF-8" in fails(code_config, root), "a .check that is not UTF-8 fails"
    (root / CHECK).write_text("code-max-function-lines: 40\n")
    save_part(root, "code_standard", {"debt": {"length": {"a.py::f": 70}}})
    git("add", "-A"); git("commit", "-q", "-m", "base")
    (root / CHECK).write_text("code-max-function-lines: 50\n")
    save_part(root, "timings", {"check": {"seconds": 2.0}})
    save_part(root, "audit", {"last_audit": {"date": "2026-01-01"}})
    assert code_config(root, "HEAD")["caps"]["max_function_lines"] == 40 and "timings" not in load_state(root, "HEAD"), \
        "a git ref gives the files of that commit"
    assert code_base(root, "HEAD") == (code_config(root, "HEAD"), {"length": {"a.py::f": 70}}), "the baseline at a ref"
    state = load_state(root)
    assert set(state) == set(STATE_PARTS) and state["code_standard"]["debt"], "a write keeps the other parts"
    before = (root / STATE).read_bytes()
    save_part(root, "timings", {"check": {"seconds": 2.0}})
    assert (root / STATE).read_bytes() == before == state_text(state).encode(), "the same state gives the same bytes"
    for bad in ("{bad", "[]", '{"timings": 1}'):
        (root / STATE).write_text(bad)
        assert fails(load_state, root), "a state file that is not valid fails: " + bad
    assert NAMES_CHECK.search("| x | `.check` |") and NAMES_CHECK.search("see .check.") \
        and not NAMES_CHECK.search(".check.lock and .check.state.json and x.check"), "a row names .check itself"


def test_migrate(root, git):
    """Self-test of --migrate: the old files become lines and state, existing lines stay, a second run changes
    nothing, the old base is still read, and a clash changes nothing."""
    import contextlib
    import io
    old_code = {"config": {"caps": {"max_file_lines": 600, "max_function_lines": 80}, "include": ["*"],
                           "exclude": ["gen/*"], "generated": [], "c2": "full"}, "debt": {"length": {"a.py::f": 90}}}
    old_audit = {"every_days": 7, "budgets": {"file_kb": 100, "session_load_tokens": 99999}, "ignore": ["ref/**"],
                 "last_audit": {"date": "2026-01-01"}, "timings": {"check": {"seconds": 4.2}}, "odd": 1}
    (root / OLD_CHECK).write_bytes(b"# old\nprofile: dod\nskip: data/*")
    (root / OLD_CODE).write_text(json.dumps(old_code))
    (root / OLD_AUDIT).write_text(json.dumps(old_audit))
    assert MIGRATE in fails(code_config, root) and MIGRATE in fails(audit_config, root), "an old file fails the readers"
    git("add", "-A"); git("commit", "-q", "-m", "old layout")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert migrate(root) == 0, "the migration runs"
    text = (root / CHECK).read_text()
    assert text.startswith("# old\nprofile: dod\nskip: data/*\n# Code standard"), "the old lines stay first: " + text
    assert text.splitlines()[4:] == ["code-max-function-lines: 80", "code-exclude: gen/*", "code-c2: full",
                                     "audit-every-days: 7", "audit-budget-file_kb: 100", "audit-ignore: ref/**"], text
    assert load_state(root) == {"code_standard": {"debt": old_code["debt"]}, "audit": {"last_audit": old_audit["last_audit"]},
                                "timings": old_audit["timings"]}, "the state is moved"
    assert not any((root / n).exists() for n in (OLD_CHECK, OLD_CODE, OLD_AUDIT)), "the old files are deleted"
    assert "unknown key(s) not moved: odd" in out.getvalue() and "SETTINGS MIGRATED" in out.getvalue(), out.getvalue()
    assert code_config(root) == code_from_old(old_code["config"]) == code_base(root, "HEAD")[0], \
        "the new settings equal the old ones, and the old file at the base is still read"
    assert audit_config(root)["budgets"]["session_load_tokens"] == 6000, "a raised kit cap is not moved"
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    with contextlib.redirect_stdout(out):
        assert migrate(root) == 0, "a second run passes"
    assert before == {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}, "a second run changes nothing"
    (root / OLD_CODE).write_text(json.dumps({"config": {"caps": {"max_function_lines": 90}}, "debt": {}}))
    with contextlib.redirect_stdout(out):
        assert migrate(root) == 1 and (root / OLD_CODE).exists(), "a clash with a line that is there changes nothing"
    assert before == {p.name: p.read_bytes() for p in root.iterdir() if p.is_file() and p.name != OLD_CODE}, "no write"
    for name in (CHECK, STATE, OLD_CODE):
        (root / name).unlink()
    (root / OLD_CODE).write_text(json.dumps({"config": CODE_DEFAULTS, "debt": {}}))
    with contextlib.redirect_stdout(out):
        assert migrate(root) == 0 and not (root / CHECK).exists(), "defaults only: no .check is made"
    assert (root / STATE).read_text() == '{\n "code_standard": {\n  "debt": {}\n }\n}\n', "the state of a clean repo"


def self_test():
    """Run the cases in temporary repos; print SETTINGS TEST PASS (an assert stops on a failure)."""
    import tempfile
    for case in (test_settings, test_migrate):
        with tempfile.TemporaryDirectory() as d:
            def git(*args):
                """Run one git command in the test repo as a throwaway user; fail the test on an error."""
                subprocess.run(["git", "-C", d, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
                                "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)
            git("init", "-q")
            case(Path(d), git)
    print("SETTINGS TEST PASS")
    return 0


def main():
    """Parse the options and run the chosen mode; return its exit code."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    ap.add_argument("--migrate", action="store_true", help="move the old settings files into .check and .check.state.json")
    ap.add_argument("--test", action="store_true", help="self-test in temporary repos")
    args = ap.parse_args()
    if args.test:
        return self_test()
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    root = Path(top.stdout.strip() if top.returncode == 0 else ".")
    if args.migrate:
        return migrate(root)
    try:
        print(json.dumps({"code": code_config(root), "audit": audit_config(root)}, indent=1, sort_keys=True))
    except ValueError as e:
        print(f"SETTINGS FAIL: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
