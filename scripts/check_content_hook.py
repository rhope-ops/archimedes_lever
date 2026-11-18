"""The Claude Code PreToolUse hook of check_content.py (`python3 scripts/check_content.py --hook`).

Input: the hook event as JSON on stdin (tool_name, cwd, tool_input); the files the call names (file_path,
file_paths, files); the project's settings file (.check) and the word lists.
What is scanned, by tool:
    Write, Edit, NotebookEdit   the new text only (content, new_string, new_source), and the path against the
                                `block:` lines. The old text of an edit is not scanned: an edit must be able to
                                remove a finding. The target file is not read and need not exist.
    Bash                        the command, only when it can send something out (outgoing(): a network client, a
                                URL, or git commit, tag, notes, push or send-email). A local command passes
                                unread. Limit: a payload that a script or an interpreter builds at run time.
    every other tool            every string of the input, and the files it names.
Output: exit 0 lets the tool call run; exit 2 blocks it, and the masked findings go to stderr. Any error blocks.
Run: check_content.py imports it for --hook; not run alone.
"""
import json
import os
import re
import signal
import subprocess
import sys

from check_content_scan import (BLOCKED, UNKNOWN_PROFILE, blocked, git, is_option_line, load_allow, load_denylist,
                                load_terms, profile_of, scan_files, scan_text, skipped)


HOOK_FILE_KEYS = ("file_path", "file_paths", "files")
HOOK_RECIPIENT_KEYS = ("to", "cc", "bcc")  # Gmail, top level: an address here is no finding


# Tools that write a local file: the keys that hold the new text. Only these are scanned.
WRITE_KEYS = {"Write": ("content",), "Edit": ("new_string",), "NotebookEdit": ("new_source",)}
# A Bash command is scanned only when it sends something out of the workspace.
# Programs that send their arguments or input to another host. A path before the name still counts (/usr/bin/curl).
CLIENTS = re.compile(r"(?<![\w.-])(?:curl|wget|gh|scp|sftp|rsync|ssh|nc|ncat|telnet|ftp|mail|mailx|sendmail|http|https|aws"
                     r"|gsutil|gcloud|bq|az|docker|podman|npm|pnpm|yarn|twine|pip|pip3)(?![\w-])|https?://")
GIT_OUT = frozenset(("commit", "tag", "notes", "push", "send-email"))  # git verbs that publish text


def outgoing(cmd):
    """True when a Bash command can send something out: it names a network client or a URL, or one of its simple
    commands (split on newline ; | &) has the word git and a publishing verb. One pass per part (no slow pattern)."""
    if CLIENTS.search(cmd):
        return True
    for part in re.split(r"[\n;|&]", cmd):
        words = set(re.findall(r"[A-Za-z-]+", part))
        if "git" in words and words & GIT_OUT:
            return True
    return False


HOOK_MAX_BYTES = 8_000_000  # named files above this total block: the scan must end well inside the hook timeout
HOOK_BUDGET_S = 8  # seconds; the hook timeout in .claude/settings.json is 10


def hook_parts(tool_input, tool_name=""):
    """(texts, recipient texts, file paths, strict paths) of a PreToolUse tool_input. Every string value is scanned;
    the values of the file keys are also read as files (an Artifact or SendUserFile call sends a file's content).
    Recipient texts: the top-level recipient keys of a Gmail call only; they are scanned, but an email address there
    is no finding. Strict paths (file_path, file_paths) must exist: a named file the hook cannot read blocks."""
    texts, recipients, paths, strict = [], [], [], []
    mail = tool_name.startswith("mcp__Gmail__")

    def walk(v, key="", out=texts):
        """Add each string in v to out; key is the nearest named key above it (file keys win)."""
        if isinstance(v, str):
            out.append(v)
            if key in HOOK_FILE_KEYS:
                paths.append(v)
                if key != "files":
                    strict.append(v)
        elif isinstance(v, dict):  # inside a file key ({"published/path": "source" | {"from": "source"}}) keep the key
            for k, x in v.items():
                walk(x, key if key in HOOK_FILE_KEYS else k, out)
        elif isinstance(v, list):
            for x in v:
                walk(x, key, out)
    if isinstance(tool_input, dict):
        for k, x in tool_input.items():
            walk(x, k, recipients if mail and k in HOOK_RECIPIENT_KEYS else texts)
    else:
        walk(tool_input)
    return texts, recipients, paths, strict


def hook(stdin_text):
    """PreToolUse hook entry: any error blocks the call. Claude Code runs the call on any exit other than 2, so an
    exception (deep nesting, a wrong type) must not end the script with exit 1."""
    def too_slow(*_):  # exit here: an exception could escape between the except block and the finally block
        sys.stdout.flush()
        os.write(2, b"check hook: blocked: the scan took longer than its own time budget; fail closed.\n")
        os._exit(2)
    if hasattr(signal, "SIGALRM"):  # a hook timeout lets the call run: stop first, and block
        signal.signal(signal.SIGALRM, too_slow)
        signal.alarm(HOOK_BUDGET_S)
    try:
        return _hook(sys.stdin.read() if stdin_text is None else stdin_text)
    except BaseException as e:  # noqa: B036 - fail closed, whatever went wrong
        print(f"check hook: blocked: the scan failed ({e.__class__.__name__}); fail closed.", file=sys.stderr)
        return 2
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)


def _hook(stdin_text):
    """PreToolUse hook. Exit 0 lets the call run; exit 2 blocks it and shows stderr to Claude. Bad input blocks
    (fail closed). Names are checked only when a denylist exists; the hook never blocks for a missing list."""
    try:
        event = json.loads(stdin_text)
        tool_input = event.get("tool_input", {})
        if not isinstance(tool_input, (dict, list, str)):
            raise ValueError("tool_input")
    except (ValueError, AttributeError) as e:
        print(f"check hook: blocked: cannot read the hook input ({e.__class__.__name__}); fail closed.", file=sys.stderr)
        return 2
    project = os.environ.get("CLAUDE_PROJECT_DIR") or ""
    cwd = event.get("cwd") or project or "."  # relative paths in the call resolve here
    if not isinstance(cwd, str):
        raise TypeError("cwd is not text")  # bad input blocks (hook() turns any error into exit 2)
    root = None  # the repo whose settings file sets the tier: the project folder first, so a cwd outside it cannot
    for where in (project, cwd):  # drop the tier (fail-open)
        if where and os.path.isdir(where):
            try:
                root = git("rev-parse", "--show-toplevel", root=where).strip()
                break
            except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
                pass
    root = root or project or cwd
    allow = load_allow(root)
    prof = profile_of(allow)
    if prof == "unknown":
        print("check hook: blocked: " + UNKNOWN_PROFILE, file=sys.stderr)
        return 2
    dod = prof == "dod"
    allow = {v for v in allow if not is_option_line(v)}
    deny, terms = load_denylist(), load_terms()
    name = str(event.get("tool_name", ""))
    full = lambda p: os.path.join(cwd, os.path.expanduser(p))  # an absolute path stays as it is
    if name in WRITE_KEYS and isinstance(tool_input, dict):
        return verdict(scan_write(name, tool_input, full, root, deny, allow, dod, terms), name)
    if name == "Bash" and isinstance(tool_input, dict):
        cmd = tool_input.get("command")
        if isinstance(cmd, str) and not outgoing(cmd):
            return 0
    texts, recipients, paths, strict = hook_parts(tool_input, name)
    found = scan_text("\n".join(texts), "tool input", deny, allow, dod, terms)
    found += [f for f in scan_text("\n".join(recipients), "mail recipients", deny, allow, dod, terms) if f[2] != "email"]
    found += [(p, 0, "unscanned", "named file missing or unreadable") for p in strict
              if not (os.path.isfile(full(p)) and os.access(full(p), os.R_OK))]
    files = [full(p) for p in paths if os.path.isfile(full(p))]
    if sum(os.path.getsize(f) for f in files) > HOOK_MAX_BYTES:
        found.append(("named files", 0, "unscanned", f"over {HOOK_MAX_BYTES} bytes in total: send fewer files per call"))
    else:
        found += scan_files(files, root, deny, allow, dod, named=True, terms=terms)
    return verdict(found, name or "tool")


def scan_write(name, tool_input, full, root, deny, allow, dod, terms):
    """Findings for a Write, Edit or NotebookEdit call: the new text, and the target path against the block lines."""
    new = [v for k in WRITE_KEYS[name] for v in [tool_input.get(k)] if isinstance(v, str)]
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    rel = None
    if isinstance(path, str) and path:  # real paths: a symlinked folder must not hide the file from a block line
        rel = os.path.relpath(os.path.realpath(full(path)), os.path.realpath(root)).replace(os.sep, "/")
        if blocked(rel, allow):
            return [(path, 0, "blocked", BLOCKED)]
    if rel and skipped(rel, allow):  # the owner's skip line covers this file: its text is not scanned, as in a push
        return []
    return scan_text("\n".join(new), "new text", deny, allow, dod, terms)


def verdict(found, tool):
    """Print the findings and the reason to stderr; return 2 (block) when there are any, else 0."""
    if not found:
        return 0
    for where, n, kind, val in found:
        print(f"check hook: {where}:{n}: {kind}: {val}", file=sys.stderr)
    print(f"check hook: blocked the {tool} call: {len(found)} finding(s) of personal data, secrets or blocked content. "
          "Remove or mask them (never copy them elsewhere), then call again. A finding that is wrong: tell the owner; "
          "an allow line in .check needs the owner's request (.claude/skills/personal-data/SKILL.md).", file=sys.stderr)
    return 2

