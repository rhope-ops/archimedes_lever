#!/usr/bin/env python3
"""The content check of scripts/check.sh: blocks personal data, secrets and the Administrator's own blocked content before
they reach the remote or leave in a tool call. One scanner for emails, phone numbers, ID-number shapes, private keys,
names and terms from word lists kept outside the repo, and files the settings file blocks.

Usage (scripts/check.sh --content passes its arguments here):
    python3 scripts/check_content.py --all             # every tracked file (working tree)
    python3 scripts/check_content.py --range A..B      # commits in A..B: added lines, messages, author and committer
    python3 scripts/check_content.py --push            # pre-push hook mode: reads the hook's stdin lines
    python3 scripts/check_content.py FILE ...          # these files (a missing, unreadable or non-regular path fails)
    python3 scripts/check_content.py --stdin [--label NAME]  # text on stdin: a brief, PR text or message before it is sent
    python3 scripts/check_content.py --hook            # Claude Code PreToolUse hook: scans the tool call's input and the
                                                       # files it names; exit 2 blocks the call
    python3 scripts/check_content.py --status          # word-list sources, entry counts and fingerprints (never the words), profile
    --require-denylist                                 # fail when no name denylist is found (pre-push and the Action use it),
                                                       # or only warn when the settings file has the line `denylist: warn`
    python3 scripts/check_content.py --test            # self-test; prints CONTENT CHECK TEST PASS

Settings file: `.check` at the repo root (the old name `.pii-guard` is still read when `.check` is absent). The
pre-push hook, scripts/check.sh and the Action scan only in a repo that has it; the PreToolUse hook always scans.
One entry per line, `#` comments:
    <exact string>          allowed although it looks like a finding
    skip: <path or glob>    not scanned (for example a public reference text that quotes office contacts)
    block: <path or glob>   must not be committed or sent (a glob with no "/" matches the file name in any folder)
    denylist: warn          with no name denylist, --require-denylist warns instead of failing (starter projects)
    profile: dod            the DoD tier (below)
Only the Administrator adds an allowed string or a skip line; agents never add one to get past a block (AGENTS.md
"Secrets and personal data").

Two tiers (the Administrator, 2026-11-15):
    minimum    no profile line: the checks under "Checks".
    DoD        `profile: dod`: the minimum checks plus the checks under "DoD checks"; a missing denylist always
               blocks (`denylist: warn` is ignored). In the Action the settings are read from the pull-request base
               (--allow-from), so a pull request cannot lower its own tier or widen its own allow list.

Word lists (never committed): one name or word per line, `#` comments, matched whole-word, any case.
    names (personal data)   env PII_GUARD_DENYLIST (newline or comma separated; the Action reads the Actions secret
                            of the same name), else env PII_GUARD_DENYLIST_FILE, else ~/.config/pii-guard/denylist.txt
    terms (the Administrator's own blocked words: a client, a code name; optional)
                            env CHECK_TERMS (Actions secret CHECK_TERMS), else env CHECK_TERMS_FILE, else
                            ~/.config/check/terms.txt
With no name denylist, names are not checked and the result line says so (exit code unchanged).
Fingerprint: 8 hex characters of SHA-256 over a list (lower case, no duplicates, sorted). Every copy of the same
list prints the same fingerprint, whatever its order or separators: compare the places to find a copy that differs.

Checks:
    email      any address, except *@users.noreply.github.com, noreply@ / no-reply@ addresses, and the
               reserved example domains (example.com/.org/.net, *.example, *.invalid, *.test, *.localhost)
    phone      US numbers (NNN-NNN-NNNN, (NNN) NNN-NNNN, NNN.NNN.NNNN), +country numbers
    id         SSN shape (NNN-NN-NNNN), or 9 digits next to SSN / social security
    secret     private-key PEM headers (provider tokens are covered by gitleaks in security.yml / check.sh)
    name       words of the name denylist
    term       words of the terms list
    blocked    a tracked, pushed or named file that a `block:` line names
DoD checks (only with `profile: dod`):
    milhost    a host name in the US military top-level domain (also inside a URL), and the DoD cloud hosts in MILHOST
    marking    controlled-information and classification banner marks (the list: MARKING; a phrase mark also over two lines)
    dodid      10 digits next to a DoD ID keyword (the list: DODID; the keyword and number also over two lines)
    unscanned  a file the scanner cannot read: a SKIP_SUFFIX type, a binary file (Office files too) or one over
               MAX_BYTES (a `content-max-bytes: <number>` line in .check raises it; the tool-call hook keeps its
               own limit on the total of the files one call names, HOOK_MAX_BYTES here,
               which that line does not change). It blocks unless a `skip: <path or glob>` line names it.
Known limits of the DoD checks: the scanner reads one line at a time, so a keyword on one line and its number on
the next pass; a binary file that enters only through a merge resolution is found by --all, not by the commit scan;
a one-word classification alone on a line is a mark in upper case only (in title case it is an ordinary heading).
A tier line in any form other than `profile: dod`, and a settings file that is not UTF-8 text, fail the scan: a wrong
spelling or a wrong file encoding cannot lower the tier in silence. Limit: a line with both the key and the value
misspelt is not seen as a tier line; `--status` and the result line always print the tier in use.
Matches are printed masked (names, terms and secrets as a length only), so CI logs do not repeat them. Exit 1 when anything is found.
Standard library only. Needs git (except for FILE mode).
A project's own finders: a file scripts/check_content_local.py replaces or adds finders for a finding kind (the
interface: the header of check_content_scan.py). The result line and --status say when it is active; when it cannot
be loaded, every scan fails and the hook blocks. Limit: that file is the project's own trusted code, like any script
a hook runs; a file that ends the process itself while it loads (os._exit) ends the scan with its own exit code (0 lets a hooked call run).
The code is split into three modules next to this file: check_content.py (CLI and --hook), check_content_scan.py
(patterns, finders, settings, word lists and scans), and check_content_test.py (--test).
Prevents: a secret or personal datum (email, phone, ID number, key, listed name or term) reaches a commit, a push or an outgoing tool call
Network: none (it runs local git read commands).
Writes: none (findings go to stdout or stderr; the self-test uses temporary folders).
Credentials: none; it reads the name denylist and the terms list (environment variable or file) and never prints an entry.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys

if "--hook" in sys.argv[1:]:   # before the scanner (and a project's own module) loads: a load that hangs must block
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, lambda *_: os._exit(2))   # exit 2 blocks the tool call
        # Seconds: 8, or the one character "1" to "7" that a test sets. No number is parsed, so no value can raise.
        signal.alarm({"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7}.get(os.environ.get("CHECK_HOOK_LOAD_S"), 8))


def missing_part(err):
    """Stop with exit 2 when a part of the guard is missing: a copy without its parts must block, not pass (exit 2
    also blocks the PreToolUse hook)."""
    print("CONTENT CHECK FAIL: %s; copy check_content_scan.py and check_content_test.py next to check_content.py "
          "(scripts/sync_baseline.py does this)" % err, file=sys.stderr)
    sys.exit(2)


try:
    import check_content_scan as scan   # for the state of a project's own finders (LOCAL, LOCAL_ERROR)
    from check_content_scan import (BLOCKED, MISSING_HELP, UNKNOWN_PROFILE, WARN_OPTION, LocalError, blocked,
                                    denylist_source, fingerprint, git, is_option_line, load_allow, load_denylist,
                                    load_terms, profile_of, push_revs, scan_commits, scan_files, scan_text,
                                    skipped, terms_source)
    from check_content_scan import warn_mode  # noqa: F401 - re-exported for first_use_check.py
except ImportError as err:
    if __name__ != "__main__":
        raise   # an importer (first_use_check.py) handles it and keeps its other output
    missing_part(err)


# ---------------------------------------------------------------- Claude Code PreToolUse hook ------------------------

HOOK_FILE_KEYS = ("file_path", "file_paths", "files")
HOOK_RECIPIENT_KEYS = ("to", "cc", "bcc")  # Gmail, top level: an address here is no finding

# Tools that write a local file: the keys that hold the new text. Only these are scanned.
WRITE_KEYS = {"Write": ("content",), "Edit": ("new_string",), "NotebookEdit": ("new_source",)}
# A Bash command is scanned only when it sends something out of the workspace.
# Programs that send their arguments or input to another host. A path before the name still counts (/usr/bin/curl).
CLIENTS = re.compile(r"(?<![\w.-])(?:curl|wget|wget2|xh|gh|glab|scp|sftp|lftp|rsync|rclone|ssh|nc|ncat|netcat|socat|telnet|ftp|mail|mailx"
                     r"|mutt|msmtp|sendmail|http|https|openssl|aws|s3cmd|gsutil|gcloud|bq|az|kubectl|docker|podman|npm|npx"
                     r"|pnpm|yarn|cargo|gem|poetry|uv|twine|pip|pip3|psql|mysql|hg|svn|claude)(?![\w-])|https?://|/dev/(?:tcp|udp)/")
# git verbs that publish text
GIT_OUT = frozenset(("commit", "commit-tree", "merge", "tag", "notes", "push", "send-email", "imap-send"))

HOOK_MAX_BYTES = 8_000_000  # named files above this total block: the scan must end well inside the hook timeout
HOOK_BUDGET_S = 8  # seconds; the hook timeout in .claude/settings.json is 10


def outgoing(cmd):
    """True when a Bash command can send something out: it names a network client or a URL, one of its simple
    commands (split on newline ; | &) has the word git and a publishing verb, or a line ends in a backslash. One pass
    (no slow pattern).

    Args:
        cmd: the Bash command text.

    Returns:
        True when the command can send something out.
    """
    # A backslash at a line end can join two lines into one word ("cu\<newline>rl" runs curl), and where the shell
    # joins depends on comments and quotes. The hook does not copy those rules: such a command is always scanned.
    if "\\\n" in cmd or "\\\r" in cmd or CLIENTS.search(cmd):
        return True
    for part in re.split(r"[\n;|&]", cmd):
        words = set(re.findall(r"[A-Za-z-]+", part))
        if "git" in words and words & GIT_OUT:
            return True
    return False


def hook_parts(tool_input, tool_name=""):
    """(texts, recipient texts, file paths, strict paths) of a PreToolUse tool_input. Every string value is scanned;
    the values of the file keys are also read as files (an Artifact or SendUserFile call sends a file's content).
    Recipient texts: the top-level recipient keys of a Gmail call only; they are scanned, but an email address there
    is no finding. Strict paths (file_path, file_paths) must exist: a named file the hook cannot read blocks.

    Args:
        tool_input: the tool_input object of the hook input.
        tool_name: the tool name (a Gmail call has recipient keys).

    Returns:
        (texts, recipient texts, file paths, strict paths), each a list.
    """
    texts, recipients, paths, strict = [], [], [], []
    mail = tool_name.startswith("mcp__Gmail__")

    def walk(v, key="", out=texts):
        """Add each string in v to out; key is the nearest named key above it (file keys win).

        Args:
            v: a value of the tool input (string, list or object).
            key: the nearest named key above v.
            out: the list that gets the strings.
        """
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
    exception (deep nesting, a wrong type) must not end the script with exit 1.

    Args:
        stdin_text: the hook input as text; None = read it from stdin.

    Returns:
        The exit code: 0 lets the call run, 2 blocks it.
    """
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
        why = str(e) if isinstance(e, LocalError) else f"the scan failed ({e.__class__.__name__})"   # a broken local module is named
        print(f"check hook: blocked: {why}; fail closed.", file=sys.stderr)
        return 2
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)


def _hook_root(project, cwd):
    """Resolve the repository root for hook settings (project dir first so a cwd outside cannot drop the tier).

    Args:
        project: the project directory path or None.
        cwd: the current working directory path or None.

    Returns:
        The resolved repository root directory path.
    """
    root = None
    for where in (project, cwd):
        if where and os.path.isdir(where):
            try:
                root = git("rev-parse", "--show-toplevel", root=where).strip()
                break
            except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
                pass
    return root or project or cwd


def _hook(stdin_text):
    """PreToolUse hook. Exit 0 lets the call run; exit 2 blocks it and shows stderr to Claude. Bad input blocks
    (fail closed). Names are checked only when a denylist exists; the hook never blocks for a missing list.
    Args:
        stdin_text: the hook input as text (JSON).
    Returns:
        The exit code: 0 lets the call run, 2 blocks it.
    """
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
    root = _hook_root(project, cwd)
    allow = load_allow(root)
    prof = profile_of(allow)
    if prof == "unknown":
        print("check hook: blocked: " + UNKNOWN_PROFILE, file=sys.stderr)
        return 2
    dod = prof == "dod"
    allow = {v for v in allow if not is_option_line(v)}
    deny, terms = load_denylist(), load_terms()
    name = str(event.get("tool_name", ""))

    def full(p):
        """Join relative hook path with cwd while leaving absolute/user paths intact."""
        return os.path.join(cwd, os.path.expanduser(p))
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
    """Findings for a Write, Edit or NotebookEdit call: the new text, and the target path against the block lines.

    Args:
        name: the tool name (a key of WRITE_KEYS).
        tool_input: the tool_input object of the hook input.
        full: a function that turns a path of the call into a full path.
        root: the repo root (a folder path).
        deny: the names of the denylist.
        allow: the lines of the settings file (load_allow).
        dod: True in the DoD tier: also run the DoD checks.
        terms: the Administrator's own blocked words.

    Returns:
        The findings, each (where, line number, kind, masked value).
    """
    new = [v for k in WRITE_KEYS[name] for v in [tool_input.get(k)] if isinstance(v, str)]
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    rel = None
    if isinstance(path, str) and path:  # real paths: a symlinked folder must not hide the file from a block line
        rel = os.path.relpath(os.path.realpath(full(path)), os.path.realpath(root)).replace(os.sep, "/")
        if blocked(rel, allow):
            return [(path, 0, "blocked", BLOCKED)]
    # New text is scanned also under a `skip:` line: the line could be new in this working tree, and the push scan of
    # the pull request reads the skip lines of the base. A skipped reference file is changed by the Administrator's request.
    return scan_text("\n".join(new), "new text", deny, allow, dod, terms)


def verdict(found, tool):
    """Print the findings and the reason to stderr; return 2 (block) when there are any, else 0."""
    if not found:
        return 0
    for where, n, kind, val in found:
        print(f"check hook: {where}:{n}: {kind}: {val}", file=sys.stderr)
    print(f"check hook: blocked the {tool} call: {len(found)} finding(s) of personal data, secrets or blocked content. "
          "Remove or mask them (never copy them elsewhere), then call again. A finding that is wrong: tell the Administrator; "
          "an allow line in .check needs the Administrator's request (.claude/skills/personal-data/SKILL.md).", file=sys.stderr)
    return 2


# ---------------------------------------------------------------- CLI -----------------------------------------------

def report(found, what, deny, dod=False, terms=()):
    """Print each finding and the PASS or FAIL line; return the exit code.

    Args:
        found: the findings, each (where, line number, kind, masked value).
        what: what was scanned, for the result line.
        deny: the names of the denylist.
        dod: True in the DoD tier.
        terms: the Administrator's own blocked words.

    Returns:
        The exit code: 0 pass, 1 fail.
    """
    for where, n, kind, val in found:
        print(f"check: {where}:{n}: {kind}: {val}")
    names = (f"names checked ({len(deny)} denylist entries, fingerprint {fingerprint(deny)})" if deny
             else "names NOT checked (no denylist)")
    if terms:
        names += f"; {len(terms)} terms checked (fingerprint {fingerprint(terms)})"
    print(f"CONTENT CHECK {'FAIL' if found else 'PASS'}: {len(found)} finding(s) in {what}; {names}; "
          f"profile {'dod' if dod else 'minimum'}" + (f"; {scan.LOCAL}" if scan.LOCAL else ""))
    return 1 if found else 0


def parse_args():
    """Read the command line; stop with a usage error when no mode or target is given.

    Returns:
        The parsed arguments (argparse namespace).
    """
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true", help="scan every tracked file")
    ap.add_argument("--range", help="scan commits in this range (A..B)")
    ap.add_argument("--push", action="store_true", help="pre-push mode: read the hook's stdin")
    ap.add_argument("--allow-from", metavar="REF", help="read the settings file from this git ref (CI: the PR base), not the tree")
    ap.add_argument("--require-denylist", action="store_true", help="fail when no name denylist is found")
    ap.add_argument("--status", action="store_true", help="print the denylist source and entry count, never the names")
    ap.add_argument("--stdin", action="store_true", help="scan the text on stdin")
    ap.add_argument("--label", default="stdin", help="name for --stdin text in the findings")
    ap.add_argument("--hook", action="store_true", help="Claude Code PreToolUse hook mode (JSON on stdin)")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if not (a.test or a.hook or a.status or a.files or a.all or a.range or a.push or a.stdin):
        ap.error("give --all, --range, --push, --stdin, --hook, --status or files")
    return a


def repo_root():
    """The top folder of the git repo here, or "." outside a repo or without git."""
    try:
        return git("rev-parse", "--show-toplevel").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "."


def show_status():
    """--status: print the denylist source, entry count and fingerprint (never the names), and the tier.

    Returns:
        The exit code: 0 when a denylist exists and the tier line is valid, else 1.
    """
    _, src = denylist_source()
    deny = load_denylist()
    n = len(deny)
    top = repo_root()
    print(f"denylist: {n} entries from {src}; fingerprint {fingerprint(deny)}" if src and n
          else "denylist: none (" + MISSING_HELP + ")")
    terms, tsrc = load_terms(), terms_source()[1]
    if terms:
        print(f"terms: {len(terms)} entries from {tsrc}; fingerprint {fingerprint(terms)}")
    prof = profile_of(load_allow(top))
    print("profile: " + (prof if prof != "unknown" else "UNKNOWN (" + UNKNOWN_PROFILE + ")"))
    if scan.LOCAL or scan.LOCAL_ERROR:
        print("finders: " + (scan.LOCAL or "FAIL (" + scan.LOCAL_ERROR + ")"))
    return 0 if n and prof != "unknown" and not scan.LOCAL_ERROR else 1


def scan_targets(a, root, deny, allow, dod, revsets, terms=()):
    """Scan what the command line names (tracked files, files, stdin, commits); return (findings, what parts).

    Args:
        a: the parsed arguments (parse_args).
        root: the repo root (a folder path).
        deny: the names of the denylist.
        allow: the lines of the settings file (load_allow).
        dod: True in the DoD tier: also run the DoD checks.
        revsets: the git rev-list argument lists of the commits to scan.
        terms: the Administrator's own blocked words.

    Returns:
        (findings, the list of what was scanned).
    """
    found, what = [], []
    if a.all:
        files = git("ls-files", "-z", root=root).split("\0")
        found += scan_files([f for f in files if f], root, deny, allow, dod, terms=terms)
        what.append(f"{len([f for f in files if f])} tracked files")
    if a.files:
        rel = [os.path.relpath(os.path.abspath(f), root) for f in a.files]
        # A named path that cannot be read is a finding: a wrong path must never print PASS.
        found += [(f, 0, "unscanned", "missing, unreadable or not a regular file") for f, r in zip(a.files, rel, strict=False)
                  if not skipped(r, allow) and not (os.path.isfile(f) and os.access(f, os.R_OK))]
        found += scan_files(rel, root, deny, allow, dod, named=True, terms=terms)
        what.append(f"{len(a.files)} file(s)")
    if a.stdin:
        found += scan_text(sys.stdin.read(), a.label, deny, allow, dod, terms)
        what.append(a.label)
    n = 0
    for revs in revsets:
        f, k = scan_commits(revs, root, deny, allow, dod, terms)
        found += f
        n += k
    if revsets:
        what.append(f"{n} commit(s)")
    return found, what


def main():
    """Run the mode the command line asks for and return its exit code.

    Returns:
        The exit code: 0 pass, 1 fail; in hook mode 0 lets the call run and 2 blocks it.
    """
    a = parse_args()
    if a.test:
        import check_content_test  # scripts/check_content_test.py: kept apart (docs/code-standard.md C4)
        return check_content_test.run()
    if a.hook:
        return hook(None)
    if a.status:
        return show_status()
    if scan.LOCAL_ERROR:   # a project's own finders cannot be used: no scan runs, and none passes
        print("CONTENT CHECK FAIL: " + scan.LOCAL_ERROR)
        return 1
    root = repo_root()
    deny, terms, allow = load_denylist(), load_terms(), load_allow(root, a.allow_from)
    prof = profile_of(allow)
    if prof == "unknown":
        print("CONTENT CHECK FAIL: " + UNKNOWN_PROFILE)
        return 1
    dod = prof == "dod"
    warn_only = WARN_OPTION in allow and not dod
    allow = {v for v in allow if not is_option_line(v)}
    revsets = [[a.range]] if a.range else []
    if a.push:
        revsets += push_revs(sys.stdin.read(), root)
    deletes_only = a.push and not revsets and not (a.all or a.files or a.range)
    if a.require_denylist and not deny and not deletes_only:
        if not warn_only:
            print("CONTENT CHECK FAIL: " + MISSING_HELP)
            return 1
        print("CONTENT CHECK WARNING: names are not checked (the settings file has 'denylist: warn'); every other check runs. "
              + MISSING_HELP)
    found, what = scan_targets(a, root, deny, allow, dod, revsets, terms)
    skips = sorted(v[5:].strip() for v in allow if v.startswith("skip:"))
    if skips:
        what.append(f"{len(skips)} skip rule(s): {', '.join(skips)}")
    return report(found, ", ".join(what) or "nothing", deny, dod, terms)


if __name__ == "__main__":
    sys.exit(main())
