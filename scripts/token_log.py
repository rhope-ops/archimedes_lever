#!/usr/bin/env python3
"""Claude Code Stop hook: log the token use of each API call to the branch claude/token-usage of the private log repo
(else of the session's repo).

Kit only: projects do not get a copy. A cloud environment's setup script installs it from the kit's newest release
tag as a user-level Stop hook, so every repo session is logged (the owner, 2026-11-17). Three files, installed side by
side: this one (the hook: push, lock, retries, self-update), token_log_rows.py (the rows and the CSV columns) and
token_log_report.py (the prices and --report).

At each Stop it starts a background push (the end of the turn does not wait) and exits 0. Outside a git repo it
does nothing: sessions with no repo are not logged, and the repo is the folder the session started in
(CLAUDE_PROJECT_DIR, else the hook's cwd), so a session that starts outside a repo is not logged. The push:
  1. Reads the session log and its subagent logs (<session>/**/*.jsonl). The log repeats the same usage on every
     content block of one reply, so each message id gives one row.
  2. Fetches claude/token-usage into a private ref (refs/token-log/remote, or refs/token-log/remote-private for the
     private log repo; --depth 1 only in a shallow clone).
  3. Merges, by message id, the rows already in sessions/<session id>.csv with the rows from the logs. The file is
     built from the logs alone, so no local state can be lost: a failed push, a race with another session, or a
     new container is caught up by the next push, and no row is counted twice.
  4. Adds costs/<session id>.csv (a snapshot of Claude Code's /cost figures: one main row, one row per subagent) and
     limits/<session id>.csv (the /usage plan limits over time, one row per reading and window; earlier rows kept)
     from the agents-pane record <TOKEN_LOG_HOME>/cost/<session id>.json, read at push time. No record: no files; a
     bad record (no JSON, not version 1, another session) is skipped with a line in push.log.
  5. Commits with a temporary index and pushes through the normal pre-push hook. The work tree, the index and the
     current branch never change. A push of only this branch skips the check lanes there (log_only in the hook);
     a block by its content check holds the push back, and the rows wait in the session log. A failed push is
     tried again after 1 and 5 minutes, so the last turn of a session is not lost to one failure (only while the container still runs);
     a race is tried again at once. Pushes are coalesced: at most one runs and one waits per session. A fetch or
     push with no answer in time (TOKEN_LOG_NET_TIMEOUT) is killed with its pre-push hook.

One row per API call. Columns: message_id, timestamp (UTC, of the reply), turn (prompts up to that time: user messages
and system wake-ups such as task notifications, not tool results or interrupt markers; total by turn for a chart),
session_id, repo, model, source (main, subagent), agent (main; the subagent type of the Agent call, else unknown; empty
for an old row whose log is gone), agent_id (the subagent's id, one per Agent call, so its calls group into one task;
empty for main), input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens, and the price columns
cache_write_1h_tokens (the 1-hour part of the cache writes), speed, web_search_requests, inference_geo (empty in an
old row), and skill_use (JSON; empty when the reply made no skill call). skill_use counts, by the reply that made the
call, per skill: skill_tool (Skill-tool calls), read (Reads of its SKILL.md) and slice (shell commands with grep, sed,
head, tail, cat or awk on its SKILL.md); a count of 0 is left out, e.g. {"deliver":{"skill_tool":1,"slice":2}}. Add the
rows of a session for its counts. An old row has no skill_use: it reads as empty.

Where: the private log repo ("token_log_repo" of the kit.config.json next to the installed file, or TOKEN_LOG_REPO)
when one is set; only when it cannot be reached (a cloud session gets git credentials only for its attached repos)
the rows go to the repo's own origin, without costs/ and limits/, with a push.log line; any other error retries the
private repo. A session log with replies that gives 0 rows writes an ALARM line in push.log. --report reads both.
Settings (environment): TOKEN_LOG=off turns it off; TOKEN_LOG_BRANCH (default claude/token-usage); TOKEN_LOG_REPO; TOKEN_LOG_SYNC=1
pushes in the foreground; TOKEN_LOG_HOME (default ~/.claude/token-log) holds push.log, the lock files and cost/ (the agents-pane records);
TOKEN_LOG_NET_TIMEOUT (seconds, default 600) limits each ls-remote, fetch and push; TOKEN_LOG_UPDATE=off turns the
self-update off; TOKEN_LOG_KIT_URL is the repo the self-update clones (default: "kit_url" of kit.config.json, see kit_url()).

Manual push:  python3 scripts/token_log.py --push REPO_DIR SESSION_ID TRANSCRIPT_PATH
Report:  python3 scripts/token_log.py --report [REF]  (in a repo: fetches the log branch, or reads REF; prints the
  estimated cost by week in America/Chicago, by source, agent and model, and per subagent task, from PRICES; the
  highest percent of each 7-day plan limit, the limit used per session (an estimate: each rise split by estimated $
  among the sessions logged on the branch), and Claude Code's /cost by week next to the estimate)
Self-update: after each background push, the installed copy (token_log.py in ~/.claude/hooks) checks the kit's newest
  release tag (vN.N.N, never main) at most once a day and replaces its files (UPDATE_FILES) with newer copies whose self-test passes; an old
  one-file install fetches the other two files the same way (the Stop path never needs them) (TOKEN_LOG_UPDATE=off
  turns it off). The setup script installs it only when a container is built, so a resumed container kept an old copy.
Self-test (temporary repos, no network):  python3 scripts/token_log.py --test.  Standard library only.
Prevents: token use and cost per session that no one can see (no log, or a log lost with the container)
Network: the private log repo, else the git remote "origin" of the repo (fetch and push of the branch
claude/token-usage); the self-update: a
shallow clone of the kit (kit_url()) at most once a day; none in the self-test.
Writes: the branch claude/token-usage (sessions/, costs/ and limits/: one CSV file each for each session), through a temporary index; push.log, lock
files and update.stamp in TOKEN_LOG_HOME; the installed hook file (self-update); never the work tree.
Credentials: none itself; the push uses the credentials git already has for the private log repo or origin; no git
network call asks for credentials (GIT_TERMINAL_PROMPT=0).
"""
import csv
import fcntl
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

PRIVATE_REF = "refs/token-log/remote"
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
        p = subprocess.Popen(["git", "-C", cwd, *args], stdout=out, stderr=err, start_new_session=True,
                             env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})  # no credentials: fail, never ask
        try:
            p.wait(timeout=net_timeout())
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            raise RuntimeError(f"git {args[0]}: no answer in {net_timeout()} s")
        out.seek(0)
        err.seek(0)
        return p.returncode, out.read().strip(), err.read().strip()


def write_tree(root, parent, files):
    """The tree of the parent commit (or an empty one) with these files added or replaced, through a temporary index:
    the repo's own index and work tree never change.

    Args:
        root: the repo folder.
        parent: [the parent commit] or [] for the first commit of the branch.
        files: {path in the branch: text}.
    Returns:
        The tree id.
    """
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}
        git(root, "read-tree", *(parent or ["--empty"]), env=env)
        for i, (path, text) in enumerate(sorted(files.items())):
            f = os.path.join(tmp, f"file{i}.csv")
            with open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            blob = git(root, "hash-object", "-w", f)
            git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        return git(root, "write-tree", env=env)


def cost_files(root, parent, sid):
    """The costs/<sid>.csv snapshot and the limits/<sid>.csv series from the agents-pane record
    <TOKEN_LOG_HOME>/cost/<sid>.json, read now (at push time, so a later retry picks up a later write). A missing
    record gives no file; a bad one gives no file and a line in push.log. The files already on the branch stay.

    Args:
        root: the repo folder.
        parent: [the parent commit] or [].
        sid: the session id.
    Returns:
        {path in the branch: CSV text}; {} when there is no usable record.
    """
    try:
        token_log_rows = sibling("token_log_rows")
        rec = token_log_rows.read_cost_record(os.path.join(home(), "cost", sid + ".json"), sid)
        if rec is None:
            return {}
        old = git(root, "show", f"{parent[0]}:limits/{sid}.csv", check=False) if parent else ""
        if not old and parent and git(root, "ls-tree", "--name-only", parent[0], f"limits/{sid}.csv", check=False):
            raise RuntimeError("the limits file on the branch cannot be read")  # never rewrite it without its rows
        limits = token_log_rows.limits_csv(rec, old)
        return {f"costs/{sid}.csv": token_log_rows.cost_csv(rec), **({f"limits/{sid}.csv": limits} if limits else {})}
    except Exception as e:  # a bad record never stops the rows push
        print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sid, "cost record skipped:", e, flush=True)
        return {}


def sibling(name, *needs):
    """Import one of the other two hook files (token_log_rows or token_log_report) from this file's folder. A copy
    from before the plain imports (it still has the `core` slot its old loader filled) raises ImportError, so the
    push takes the repair path: the self-update runs at once and installs the matching copy. So does a copy that lacks
    a name in needs (older than this file)."""
    import importlib
    mod = importlib.import_module(name)
    if hasattr(mod, "core") or not all(hasattr(mod, n) for n in needs):
        raise ImportError(f"{name}.py is an older copy than token_log.py")
    return mod


def push(root, sid, tpath):
    """Push the log to the private log repo (log_repo()) when one is set, else to origin. Only when the private repo
    cannot be reached (its ls-remote fails: no access or not found; a timeout is not this) do the rows go to origin,
    with a push.log line, and then without costs/ and limits/: the account-wide figures stay off a repo that may be
    public. Any other error is raised, so the retries try the private repo again. The caller holds the push lock.

    Args:
        root: the repo folder.
        sid: the session id.
        tpath: the path of the session's log file.
    Returns:
        The result text of push_to(). Raises RuntimeError when git fails.
    """
    url = log_repo(os.path.abspath(__file__))
    if url:
        try:
            return push_to(root, sid, tpath, url, PRIVATE_REF + "-private")
        except RuntimeError as e:
            if not str(e).startswith("ls-remote: "):
                raise
            print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sid, "private log repo not reachable, "
                  "pushing the rows (no costs/ or limits/) to origin:", str(e)[-300:], flush=True)
    return push_to(root, sid, tpath, "origin", PRIVATE_REF, costs=not url)


def has_replies(tpath):
    """True when the session log holds at least one assistant reply with token use (a log of 0 rows then means its
    format changed)."""
    try:
        with open(tpath, encoding="utf-8", errors="replace") as f:
            return any('"assistant"' in ln and '"usage"' in ln for ln in f)
    except OSError:
        return False


def push_to(root, sid, tpath, remote, private_ref, costs=True):
    """Merge this session's rows into sessions/<sid>.csv on the log branch of one remote, add the /cost and /usage
    files of cost_files(), and push them in one commit. Tries again at once only
    after a race with another push.

    Args:
        root: the repo folder.
        sid: the session id.
        tpath: the path of the session's log file.
        remote: "origin" or the private log repo's URL.
        private_ref: the local ref that holds that remote's log branch.
        costs: False to leave out costs/ and limits/ (a fallback push to origin).
    Returns:
        A short result text: "pushed ...", "up to date" or "nothing to log". Raises RuntimeError when git fails.
    """
    token_log_rows = sibling("token_log_rows", "read_cost_record")  # only the background push needs it
    ref, path = branch_name(), f"sessions/{sid}.csv"
    for attempt in (1, 2):
        rc, heads, err = git_net(root, "ls-remote", "--heads", remote, ref)
        if rc != 0:
            raise RuntimeError("ls-remote: " + err)
        heads = [ln for ln in heads.splitlines() if ln.endswith("\trefs/heads/" + ref)]  # exact: not x/<ref>
        parent, rows = [], {}
        if heads:
            shallow = git(root, "rev-parse", "--is-shallow-repository") == "true"
            rc, _, err = git_net(root, "fetch", "-q", "--no-write-fetch-head",
                                 *(["--depth", "1"] if shallow else []), remote, f"+refs/heads/{ref}:{private_ref}")
            if rc != 0:
                raise RuntimeError("fetch: " + err)
            parent = [git(root, "rev-parse", private_ref)]
            old = git(root, "show", f"{parent[0]}:{path}", check=False)
            rows = {r["message_id"]: r for r in csv.DictReader(io.StringIO(old)) if r.get("message_id")}
        got = token_log_rows.log_rows(sid, tpath, os.path.basename(root))
        if not got and has_replies(tpath):
            print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sid, "ALARM: the session log has replies "
                  "but gave 0 rows (did its format change?)", flush=True)
        rows.update(got)
        if not rows:
            return "nothing to log"
        extra = cost_files(root, parent, sid) if costs else {}
        tree = write_tree(root, parent, {path: token_log_rows.to_csv(rows), **extra})
        if parent and git(root, "rev-parse", parent[0] + "^{tree}") == tree:
            return "up to date"
        args = sum((["-p", p] for p in parent), [])
        commit = git(root, "commit-tree", tree, *args, "-m", f"token log: session {sid}")
        rc, out, err = git_net(root, "push", "-q", remote, f"{commit}:refs/heads/{ref}")
        if rc == 0:
            git(root, "update-ref", private_ref, commit)
            return f"pushed {commit[:7]} ({len(rows)} rows)" + ("" if remote == "origin" else " to the private log repo")
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
        except ImportError:  # a missing or older rows file: the caller repairs the install (no retries, no lost wait)
            raise
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


def config_value(path, key, env):
    """A setting of the installed hook: the environment variable env, else key in the kit.config.json next to the
    installed file (the setup script and each self-update install it). Never a repo's own kit.config.json: any repo
    opened in a session could then point the hook at its own address (security review, 2026-11-23). Residual risk:
    a repo's .claude/settings.json "env" block can set the variable for its sessions; such a repo can already run its
    own hooks, so this adds little (threat model, kit 11.0.0).

    Args:
        path: the installed token_log.py.
        key: the kit.config.json key ("kit_url" or "token_log_repo").
        env: the environment variable that wins over the file (TOKEN_LOG_KIT_URL or TOKEN_LOG_REPO).
    Returns:
        The value, or None when no source names one.
    """
    if os.environ.get(env):
        return None if os.environ[env].startswith("-") else os.environ[env]
    try:
        with open(os.path.join(os.path.dirname(path), KIT_CONFIG), encoding="utf-8") as f:
            got = json.load(f).get(key)
    except (OSError, ValueError, AttributeError):
        return None
    return got if isinstance(got, str) and got.strip() and not got.startswith("-") else None  # "-": a git option


def kit_url(path):
    """The kit repo the self-update clones (TOKEN_LOG_KIT_URL, else "kit_url"), or None: the update does nothing."""
    return config_value(path, "kit_url", "TOKEN_LOG_KIT_URL")


def log_repo(path):
    """The private log repo (TOKEN_LOG_REPO, else "token_log_repo"), or None: the log goes to the repo's origin."""
    return config_value(path, "token_log_repo", "TOKEN_LOG_REPO")


UPDATE_EVERY = 24 * 3600  # seconds between self-update checks
UPDATE_FILES = ("token_log_rows.py", "token_log_report.py", "token_log.py")  # the installed files: the hook file last


def same_file(a, b):
    """True when file b exists and has the same bytes as file a."""
    if not os.path.isfile(b):
        return False
    with open(a, "rb") as f, open(b, "rb") as g:
        return f.read() == g.read()


def release_tag(url):
    """The kit's newest release tag (vMAJOR.MINOR.PATCH, highest by number), or None (none, or no answer)."""
    try:
        r = subprocess.run(["git", "ls-remote", "--tags", "--refs", url, "v*"], capture_output=True, text=True,
                           timeout=net_timeout(), env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except subprocess.TimeoutExpired:
        return None
    tags = [m.group(0) for m in (re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", ln.rsplit("refs/tags/", 1)[-1])
                                 for ln in r.stdout.splitlines() if r.returncode == 0) if m]
    return max(tags, key=lambda t: tuple(int(x) for x in t[1:].split(".")), default=None)


def self_update(path, url=None, now=None):
    """Replace the installed hook file with the copy of the kit's newest release tag (release_tag()) when it differs
    and its self-test passes; at most once a day. Never main: only a release the Release Manager tagged reaches every
    session (token log audit, 2026-11-25).

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
    tag = release_tag(url)
    if not tag:
        return "not updated: no release tag (vN.N.N) at the kit"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", tag, url,
                            os.path.join(tmp, "k")], capture_output=True, text=True, timeout=net_timeout(),
                           env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        src = os.path.join(tmp, "k", "scripts")
        names = [n for n in UPDATE_FILES if os.path.isfile(os.path.join(src, n))]
        if r.returncode != 0 or "token_log.py" not in names:
            return "not updated: " + (r.stderr.strip()[-200:] or "no scripts/token_log.py")
        config = os.path.join(tmp, "k", KIT_CONFIG)  # installed with the code, only after the code's self-test passed
        here = os.path.join(os.path.dirname(path), KIT_CONFIG)
        if all(same_file(os.path.join(src, n), os.path.join(os.path.dirname(path), n)) for n in names) and \
                (not os.path.isfile(config) or same_file(config, here)):
            return "up to date"
        # The new copy must pass its own self-test (temporary repos, no network): a copy that fails when run would
        # break every later Stop, and then no later update could repair it.
        new = os.path.join(src, "token_log.py")
        t = subprocess.run([sys.executable, "-E", "-s", new, "--test"], cwd=src, capture_output=True,
                           text=True, timeout=600, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        if t.returncode != 0:
            return "not updated: self-test failed " + (t.stdout + t.stderr).strip()[-200:]
        for n in names:  # the other two files first, token_log.py last: a hook that starts in between finds them
            dest = os.path.join(os.path.dirname(path), n)
            shutil.copyfile(os.path.join(src, n), dest + ".new")
            os.replace(dest + ".new", dest)
        if os.path.isfile(config):
            shutil.copyfile(config, here + ".new")
            os.replace(here + ".new", here)
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


def self_test():
    """Run the self-test in scripts/token_log_test.py on this module (temporary repos, no network)."""
    import token_log_test  # scripts/token_log_test.py: kept apart so each case stays short (rule C3)
    return token_log_test.run(sys.modules[__name__])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--test"]:
        sys.exit(self_test())
    if sys.argv[1:2] == ["--report"] and len(sys.argv) <= 3:
        try:
            report_file = sibling("token_log_report")
        except ImportError as e:
            sys.exit(f"token_log --report: {e}")
        sys.exit(report_file.report_main(sys.argv[2:]))
    if sys.argv[1:2] == ["--push"] and len(sys.argv) == 5:
        try:
            push_main(sys.argv[2:])
        except ImportError as e:  # an old install: a hook file is missing or older; the update installs it now
            print("token_log: hook file missing or old:", e, flush=True)
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
