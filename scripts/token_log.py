#!/usr/bin/env python3
"""Claude Code Stop hook: log the token use of each API call to the branch claude/token-usage of the session's repo.

Kit only: projects do not get a copy. A cloud environment's setup script installs it from the kit's main branch
as a user-level Stop hook, so every repo session is logged (the owner, 2026-11-17).

At each Stop it starts a background push (the end of the turn does not wait) and exits 0. Outside a git repo it
does nothing: sessions with no repo are not logged, and the repo is the folder the session started in
(CLAUDE_PROJECT_DIR, else the hook's cwd), so a session that starts outside a repo is not logged. The push:
  1. Reads the session log and its subagent logs (<session>/**/*.jsonl). The log repeats the same usage on every
     content block of one reply, so each message id gives one row.
  2. Fetches claude/token-usage into a private ref (refs/token-log/remote; --depth 1 only in a shallow clone).
  3. Merges, by message id, the rows already in sessions/<session id>.csv with the rows from the logs. The file is
     built from the logs alone, so no local state can be lost: a failed push, a race with another session, or a
     new container is caught up by the next push, and no row is counted twice.
  4. Commits with a temporary index and pushes through the normal pre-push hook. The work tree, the index and the
     current branch never change. That hook runs the check lanes on the current work tree, so a failing work tree
     holds back the log push until it passes; the rows wait in the session log. A failed push is tried again after
     1 and 5 minutes, so the last turn of a session is not lost to one failure (only while the container still runs);
     a race is tried again at once. Pushes are coalesced: at most one runs and one waits per session. A fetch or
     push with no answer in time (TOKEN_LOG_NET_TIMEOUT) is killed with its pre-push hook.

One row per API call. Columns: message_id, timestamp (UTC, of the reply), turn (prompts up to that time: user messages
and system wake-ups such as task notifications, not tool results or interrupt markers; total by turn for a chart),
session_id, repo, model, source (main, subagent), agent (main; the subagent type of the Agent call, else unknown; empty
for an old row whose log is gone), agent_id (the subagent's id, one per Agent call, so its calls group into one task;
empty for main), input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens, and the price columns
cache_write_1h_tokens (the 1-hour part of the cache writes), speed, web_search_requests, inference_geo (empty in an old row).

Settings (environment): TOKEN_LOG=off turns it off; TOKEN_LOG_BRANCH (default claude/token-usage); TOKEN_LOG_SYNC=1
pushes in the foreground; TOKEN_LOG_HOME (default ~/.claude/token-log) holds push.log and the lock files;
TOKEN_LOG_NET_TIMEOUT (seconds, default 600) limits each ls-remote, fetch and push; TOKEN_LOG_UPDATE=off turns the
self-update off; TOKEN_LOG_KIT_URL is the repo the self-update clones (default: "kit_url" of kit.config.json, see kit_url()).

Manual push:  python3 scripts/token_log.py --push REPO_DIR SESSION_ID TRANSCRIPT_PATH
Report:  python3 scripts/token_log.py --report [REF]  (in a repo: fetches the log branch, or reads REF; prints the
  estimated cost by week in America/Chicago, by source, agent and model, and per subagent task, from PRICES)
Self-update: after each background push, the installed copy (token_log.py in ~/.claude/hooks) checks the kit's main
  branch at most once a day and replaces its files (UPDATE_FILES) with newer copies whose self-test passes; an old
  one-file install fetches token_log_report.py the same way (the Stop path never needs it) (TOKEN_LOG_UPDATE=off
  turns it off). The setup script installs it only when a container is built, so a resumed container kept an old copy.
Self-test (temporary repos, no network):  python3 scripts/token_log.py --test.  Standard library only.
Network: the git remote "origin" of the repo (fetch and push of the branch claude/token-usage); the self-update: a
shallow clone of the kit (kit_url()) at most once a day; none in the self-test.
Writes: the branch claude/token-usage (one CSV file for each session), through a temporary index; push.log, lock
files and update.stamp in TOKEN_LOG_HOME; the installed hook file (self-update); never the work tree.
Credentials: none itself; the push uses the credentials git already has for origin.
"""
import csv
import fcntl
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

FIELDS = ["message_id", "timestamp", "turn", "session_id", "repo", "model", "source", "agent", "agent_id",
          "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens", "cache_write_1h_tokens",
          "speed", "web_search_requests", "inference_geo"]
USAGE_KEYS = FIELDS[9:13]  # the four token counts that the report sums
PRIVATE_REF = "refs/token-log/remote"
NOT_PROMPTS = ("[Request interrupted",)
RETRY_DELAYS = (0, 60, 300)  # seconds before each push try: the last turn of a session gets more than one chance
def net_timeout():
    """Seconds for ls-remote, fetch or push: TOKEN_LOG_NET_TIMEOUT, else 600 (also for a value that is not a whole
    number of at least 1)."""
    try:
        v = int(os.environ.get("TOKEN_LOG_NET_TIMEOUT", ""))
    except ValueError:
        return 600
    return v if v >= 1 else 600


RACE = ("non-fast-forward", "fetch first", "stale info", "cannot lock ref")


def home():
    """The folder for push.log and the lock files: TOKEN_LOG_HOME, else ~/.claude/token-log."""
    return os.environ.get("TOKEN_LOG_HOME") or os.path.expanduser("~/.claude/token-log")


def branch_name():
    """The log branch: TOKEN_LOG_BRANCH, else claude/token-usage."""
    return os.environ.get("TOKEN_LOG_BRANCH") or "claude/token-usage"


def git(cwd, *args, env=None, check=True, timeout=None):
    """Run a local git command; return its stripped stdout ("" on failure when check is False)."""
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args[0]}: {r.stderr.strip()}")
    return r.stdout.strip() if r.returncode == 0 else ""


def git_net(cwd, *args):
    """A git call that uses the network, with a time limit. On timeout the whole process group is killed: git and
    the pre-push hook with the check lane it started. Returns (exit code, stdout, stderr).

    Args:
        cwd: the repo folder.
        args: the git arguments, after `git -C <cwd>`.
    Returns:
        (exit code, stdout, stderr), the output stripped.
    """
    # Output goes to files, not pipes: a hook child that escapes the kill (its own session) cannot keep this waiting.
    with tempfile.TemporaryFile("w+") as out, tempfile.TemporaryFile("w+") as err:
        p = subprocess.Popen(["git", "-C", cwd, *args], stdout=out, stderr=err, start_new_session=True)
        try:
            p.wait(timeout=net_timeout())
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            raise RuntimeError(f"git {args[0]}: no answer in {net_timeout()} s")
        out.seek(0)
        err.seek(0)
        return p.returncode, out.read().strip(), err.read().strip()


def to_csv(rows):
    """The CSV text of the rows, header first, sorted by timestamp and message id."""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in sorted(rows.values(), key=lambda r: (r["timestamp"], r["message_id"])):
        w.writerow({k: r.get(k, "") for k in FIELDS})
    return out.getvalue()


def push(root, sid, tpath):
    """Merge this session's rows into sessions/<sid>.csv on the log branch and push. Tries again at once only
    after a race with another push. The caller holds the session's push lock.

    Args:
        root: the repo folder.
        sid: the session id.
        tpath: the path of the session's log file.
    Returns:
        A short result text: "pushed ...", "up to date" or "nothing to log". Raises RuntimeError when git fails.
    """
    ref, path = branch_name(), f"sessions/{sid}.csv"
    for attempt in (1, 2):
        rc, heads, err = git_net(root, "ls-remote", "--heads", "origin", ref)
        if rc != 0:
            raise RuntimeError("ls-remote: " + err)
        parent, rows = [], {}
        if heads:
            shallow = git(root, "rev-parse", "--is-shallow-repository") == "true"
            rc, _, err = git_net(root, "fetch", "-q", "--no-write-fetch-head",
                                 *(["--depth", "1"] if shallow else []), "origin", f"+refs/heads/{ref}:{PRIVATE_REF}")
            if rc != 0:
                raise RuntimeError("fetch: " + err)
            parent = [git(root, "rev-parse", PRIVATE_REF)]
            old = git(root, "show", f"{parent[0]}:{path}", check=False)
            rows = {r["message_id"]: r for r in csv.DictReader(io.StringIO(old)) if r.get("message_id")}
        rows.update(_part("token_log_rows").log_rows(sid, tpath, os.path.basename(root)))
        if not rows:
            return "nothing to log"
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "rows.csv")
            with open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(to_csv(rows))
            blob = git(root, "hash-object", "-w", f)
            env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}
            git(root, "read-tree", *(parent or ["--empty"]), env=env)
            git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
            tree = git(root, "write-tree", env=env)
        if parent and git(root, "rev-parse", parent[0] + "^{tree}") == tree:
            return "up to date"
        args = sum((["-p", p] for p in parent), [])
        commit = git(root, "commit-tree", tree, *args, "-m", f"token log: session {sid}")
        rc, out, err = git_net(root, "push", "-q", "origin", f"{commit}:refs/heads/{ref}")
        if rc == 0:
            git(root, "update-ref", PRIVATE_REF, commit)
            return f"pushed {commit[:7]} ({len(rows)} rows)"
        err = err or out
        if attempt == 2 or not any(x in err for x in RACE):  # only a race with another push is tried at once
            raise RuntimeError("push: " + err[-500:])
    return "not pushed"


def locked_push(root, sid, tpath):
    """Coalesce pushes: at most one runs and one waits per session. The waiting one reads the newest rows when it
    starts, so a third has nothing to add and exits at once ("coalesced").

    Args:
        root: the repo folder.
        sid: the session id.
        tpath: the path of the session's log file.
    Returns:
        "coalesced" when a push already waits, else the result text of push().
    """
    os.makedirs(home(), exist_ok=True)
    with open(os.path.join(home(), sid + ".wait"), "w") as wait, open(os.path.join(home(), sid + ".lock"), "w") as run:
        try:
            fcntl.flock(wait, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "coalesced"
        fcntl.flock(run, fcntl.LOCK_EX)
        fcntl.flock(wait, fcntl.LOCK_UN)  # the next turn's push may wait now
        return push(root, sid, tpath)


def push_main(args, delays=RETRY_DELAYS):
    """Push, and try again later when it fails (no lock is held while it waits). Stops when a newer push waits.

    Args:
        args: [root, sid, tpath] for locked_push().
        delays: seconds to wait before each try (default RETRY_DELAYS).
    Returns:
        True when a try worked, else False.
    """
    for i, delay in enumerate(delays):
        time.sleep(delay)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            print(stamp, args[1], locked_push(*args), flush=True)
            return True
        except Exception as e:
            print(stamp, args[1], f"try {i + 1} of {len(delays)} error:", e, flush=True)
    return False


def hook_main():
    """The Stop hook: read the hook input and start the push in the background (or the foreground with TOKEN_LOG_SYNC=1)."""
    if os.environ.get("TOKEN_LOG", "").lower() == "off":
        return
    hook = json.load(sys.stdin)
    if not isinstance(hook, dict):
        return
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or hook.get("cwd") or os.getcwd()
    root = git(cwd, "rev-parse", "--show-toplevel", check=False)
    sid, tpath = hook.get("session_id"), hook.get("transcript_path")
    if not root or not isinstance(sid, str) or not isinstance(tpath, str) or not sid or "/" in sid:
        return  # not a repo (not logged), or no usable session
    args = [root, sid, tpath]
    if os.environ.get("TOKEN_LOG_SYNC") == "1":
        push_main(args, delays=(0,))
        return
    os.makedirs(home(), exist_ok=True)
    logf = open(os.path.join(home(), "push.log"), "a")
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "--push", *args], stdin=subprocess.DEVNULL,
                     stdout=logf, stderr=logf, start_new_session=True)


KIT_CONFIG = "kit.config.json"  # the one home of the kit address (scripts/kit_config.py reads it in the kit)


def kit_url(path):
    """The kit repo the self-update clones: TOKEN_LOG_KIT_URL, else "kit_url" of the kit.config.json next to the
    installed file (self-update installs it), else of the one in the session's repo (a synced project has it).

    Args:
        path: the installed token_log.py.
    Returns:
        The URL, or None when no source names one (the self-update then does nothing).
    """
    if os.environ.get("TOKEN_LOG_KIT_URL"):
        return os.environ["TOKEN_LOG_KIT_URL"]
    for folder in (os.path.dirname(path), os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()):
        try:
            with open(os.path.join(folder, KIT_CONFIG), encoding="utf-8") as f:
                got = json.load(f).get("kit_url")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(got, str) and got.strip():
            return got
    return None
UPDATE_EVERY = 24 * 3600  # seconds between self-update checks
UPDATE_FILES = ("token_log_rows.py", "token_log_report.py", "token_log.py")  # the installed files: the parts first, the entry file last


def same_file(a, b):
    """True when file b exists and has the same bytes as file a."""
    if not os.path.isfile(b):
        return False
    with open(a, "rb") as f, open(b, "rb") as g:
        return f.read() == g.read()


def self_update(path, url=None, now=None):
    """Replace the installed hook file with the kit's main copy when it differs and its self-test passes; at most
    once a day.

    Args:
        path: the installed token_log.py to replace.
        url: the kit repo to clone (default kit_url(path)).
        now: the current time in seconds (default time.time()), for the self-test.
    Returns:
        A short result text: "skipped", "up to date", "updated" or "not updated: <reason>".
    """
    stamp, now = os.path.join(home(), "update.stamp"), time.time() if now is None else now
    if os.path.exists(stamp) and now - os.path.getmtime(stamp) < UPDATE_EVERY:
        return "skipped"
    os.makedirs(home(), exist_ok=True)
    with open(stamp, "w"):
        pass
    os.utime(stamp, (now, now))  # a failed check also waits a day
    url = url or kit_url(path)
    if not url:
        return "not updated: no kit address (TOKEN_LOG_KIT_URL or kit.config.json)"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", "main", url,
                            os.path.join(tmp, "k")], capture_output=True, text=True, timeout=net_timeout())
        src = os.path.join(tmp, "k", "scripts")
        names = [n for n in UPDATE_FILES if os.path.isfile(os.path.join(src, n))]
        if r.returncode != 0 or "token_log.py" not in names:
            return "not updated: " + (r.stderr.strip()[-200:] or "no scripts/token_log.py")
        config = os.path.join(tmp, "k", KIT_CONFIG)  # data, not code: installed next to the file with no self-test
        if os.path.isfile(config) and not same_file(config, os.path.join(os.path.dirname(path), KIT_CONFIG)):
            shutil.copyfile(config, os.path.join(os.path.dirname(path), KIT_CONFIG))
        if all(same_file(os.path.join(src, n), os.path.join(os.path.dirname(path), n)) for n in names):
            return "up to date"
        # The new copy must pass its own self-test (temporary repos, no network): a copy that fails when run would
        # break every later Stop, and then no later update could repair it.
        new = os.path.join(src, "token_log.py")
        t = subprocess.run([sys.executable, "-E", "-s", new, "--test"], cwd=src, capture_output=True,
                           text=True, timeout=600, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        if t.returncode != 0:
            return "not updated: self-test failed " + (t.stdout + t.stderr).strip()[-200:]
        for n in names:  # the parts first, token_log.py last: a hook that starts in between finds its parts
            dest = os.path.join(os.path.dirname(path), n)
            shutil.copyfile(os.path.join(src, n), dest + ".new")
            os.replace(dest + ".new", dest)
    return "updated"


def update_main():
    """Self-update the installed copy after a background push (never a copy in a repo); errors go to push.log."""
    here = os.path.abspath(__file__)
    if os.environ.get("TOKEN_LOG_UPDATE", "").lower() == "off" or \
            os.path.dirname(here) != os.path.expanduser("~/.claude/hooks"):
        return
    try:
        print(datetime.now(timezone.utc).isoformat(timespec="seconds"), "self-update:", self_update(here), flush=True)
    except Exception as e:
        print("self-update error:", e, flush=True)


PARTS = ("token_log_rows", "token_log_report")  # the sibling part files; UPDATE_FILES installs them


def _part(name):
    """A part file (token_log_rows or token_log_report), loaded on first use and bound to this module."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    mod = __import__(name)
    mod.core = sys.modules[__name__]
    return mod


def __getattr__(name):
    """Names of the part files (log_rows, row_cost, report, PRICES, ...), so callers use token_log.<name> as before."""
    if not name.startswith("__"):
        for part in PARTS:
            if hasattr(_part(part), name):
                return getattr(_part(part), name)
    raise AttributeError(name)


def self_test():
    """Run the self-test in scripts/token_log_test.py on this module (temporary repos, no network)."""
    import token_log_test  # scripts/token_log_test.py: kept apart so each case stays short (rule C3)
    return token_log_test.run(sys.modules[__name__])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--test"]:
        sys.exit(self_test())
    if sys.argv[1:2] == ["--report"] and len(sys.argv) <= 3:
        sys.exit(_part("token_log_report").report_main(sys.argv[2:]))
    if sys.argv[1:2] == ["--push"] and len(sys.argv) == 5:
        try:
            push_main(sys.argv[2:])
        except ImportError as e:  # an old one-file install: a part is missing; the update installs it now
            print("token_log: part missing:", e, flush=True)
            stamp = os.path.join(home(), "update.stamp")
            if os.path.exists(stamp):
                os.utime(stamp, (0, 0))  # so the self-update below runs now, not after a day
        update_main()
        sys.exit(0)
    try:
        hook_main()
    except Exception as e:  # never fail the turn
        print(f"token_log: {e}", file=sys.stderr)
    sys.exit(0)
