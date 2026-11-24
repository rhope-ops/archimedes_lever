#!/usr/bin/env python3
"""Self-test of scripts/token_log.py (run by `python3 scripts/token_log.py --test`; kept in its own file so each
case stays under the 60-line cap of docs/code-standard.md C3).

It builds a bare origin and clones in a temporary folder (no network) and runs the Stop hook on sample session logs:
one row per API call, turns, subagent rows, a second session, a blocking pre-push hook, a lost local folder, a shallow
clone, retries, coalescing, FETCH_HEAD, a push with no answer, a push that waits for the lock, bad input and
TOKEN_LOG=off. The cases of the rows, the report and the self-update are in scripts/token_log_test_parts.py; this
file holds the fixture and the sample log lines that both files use.
Input: the token_log module. Output: one PASS or FAIL line per case and a "TOKEN LOG SELF-TEST" total line; returns
the exit code (0 pass, 1 fail). Needs git.
Network: none.
Writes: temporary repos only.
Credentials: none.
"""
import csv
import fcntl
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

def msg(mid, ts, model="claude-test", side=False, n=1):
    """One assistant log line with usage n, 10n, 100n, 1000n."""
    u = {"input_tokens": n, "cache_creation_input_tokens": 10 * n, "cache_read_input_tokens": 100 * n,
         "output_tokens": 1000 * n}
    return json.dumps({"type": "assistant", "timestamp": ts, "isSidechain": side,
                       "message": {"id": mid, "model": model, "usage": u}})


def prompt(ts, text="hi"):
    """One user prompt log line."""
    return json.dumps({"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}})


def tool_result(ts):
    """One tool-result log line (not a prompt)."""
    return json.dumps({"type": "user", "timestamp": ts, "message": {"content": [{"type": "tool_result", "content": "x"}]}})


def append(path, *lines):
    """Append lines to a file."""
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")


class Fixture:
    """The temporary repos, the clean environment and the pass/fail count shared by the cases."""

    def __init__(self, tl):
        """Make the temporary root and a git environment with no user or global config.

        Args:
            tl: the token_log module.
        """
        import token_log_report
        import token_log_rows
        self.tl, self.rows, self.rep = tl, token_log_rows, token_log_report
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and not k.startswith("TOKEN_LOG")}
        env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", TOKEN_LOG_SYNC="1")
        env.pop("CLAUDE_PROJECT_DIR", None)
        self.env = env
        self.root = tempfile.mkdtemp(prefix="token_log_test_")
        self.origin = os.path.join(self.root, "origin.git")
        self.work, self.other = os.path.join(self.root, "work"), os.path.join(self.root, "other")
        self.logs, self.t1 = os.path.join(self.root, "logs"), os.path.join(self.root, "proj", "s1.jsonl")
        self.hooks = os.path.join(self.root, "hooks")
        self.fails = 0

    def sh(self, cwd, *args):
        """Run a command in the test environment; return its stripped stdout."""
        return subprocess.run(args, cwd=cwd, env=self.env, capture_output=True, text=True, check=True).stdout.strip()

    def hook(self, cwd, sid, tpath, logdir, stdin=None, extra=None):
        """Run token_log.py as the Stop hook with this session's input."""
        data = stdin if stdin is not None else json.dumps({"session_id": sid, "transcript_path": tpath, "cwd": cwd})
        return subprocess.run([sys.executable, os.path.abspath(self.tl.__file__)], input=data, capture_output=True,
                              text=True, env={**self.env, "TOKEN_LOG_HOME": logdir, **(extra or {})})

    def expect(self, name, got, want):
        """Print PASS or FAIL for one case and count the failures."""
        ok = got == want
        self.fails += not ok
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f": got {got!r}, want {want!r}"))

    def remote_rows(self, sid):
        """The rows of sessions/<sid>.csv on the origin's log branch, or None."""
        r = subprocess.run(["git", "--git-dir", self.origin, "show", f"claude/token-usage:sessions/{sid}.csv"],
                           capture_output=True, text=True, env=self.env)
        return list(csv.DictReader(io.StringIO(r.stdout))) if r.returncode == 0 else None

    def state(self, repo):
        """Work tree status, HEAD, branch and shallow state of a clone."""
        return (self.sh(repo, "git", "status", "--porcelain"), self.sh(repo, "git", "rev-parse", "HEAD"),
                self.sh(repo, "git", "branch", "--show-current"),
                self.sh(repo, "git", "rev-parse", "--is-shallow-repository"))

    def set_pre_push(self, body):
        """Install a pre-push hook script in the shared hooks folder."""
        with open(os.path.join(self.hooks, "pre-push"), "w") as f:
            f.write(body)
        os.chmod(os.path.join(self.hooks, "pre-push"), 0o700)


def case_first_turn(fx):
    """Set up origin and work clone; outside a repo, turn 1 rows, no-op push.

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, t1, logs = fx.root, fx.work, fx.t1, fx.logs
    fx.sh(root, "git", "init", "-q", "--bare", "-b", "main", fx.origin)
    fx.sh(root, "git", "clone", "-q", fx.origin, work)
    append(os.path.join(work, "a.txt"), "a")
    fx.sh(work, "git", "add", "a.txt")
    fx.sh(work, "git", "commit", "-q", "-m", "init")
    fx.sh(work, "git", "push", "-q", "origin", "HEAD:main")
    append(os.path.join(work, "a.txt"), "work in progress")  # an uncommitted change that must stay as it is
    fx.sh(work, "git", "add", "a.txt")
    fx.before = fx.state(work)
    os.makedirs(os.path.dirname(t1))
    append(t1, prompt("2026-01-01T00:00:00Z"), msg("m1", "2026-01-01T00:00:01Z"), msg("m1", "2026-01-01T00:00:02Z"),
           tool_result("2026-01-01T00:00:03Z"), msg("m2", "2026-01-01T00:00:04Z"), "not json")

    r = fx.hook(root, "s1", t1, logs)
    fx.expect("outside a repo: exit 0, nothing pushed", (r.returncode, fx.remote_rows("s1")), (0, None))

    fx.hook(work, "s1", t1, logs)
    got = fx.remote_rows("s1") or []
    fx.expect("turn 1: one row per API call (a reply repeated per block counts once)",
              [(x["message_id"], x["turn"], x["output_tokens"], x["timestamp"]) for x in got],
              [("m1", "1", "1000", "2026-01-01T00:00:01Z"), ("m2", "1", "1000", "2026-01-01T00:00:04Z")])
    fx.expect("turn 1: work tree, index, HEAD, branch and shallow state unchanged", fx.state(work), fx.before)

    tip = fx.sh(root, "git", "--git-dir", fx.origin, "rev-parse", "claude/token-usage")
    fx.hook(work, "s1", t1, logs)
    fx.expect("no new calls: no new commit",
              fx.sh(root, "git", "--git-dir", fx.origin, "rev-parse", "claude/token-usage"), tip)


def case_second_turn(fx):
    """Another session pushes first; turn 2 adds main and subagent calls.

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, t1, logs = fx.root, fx.work, fx.t1, fx.logs
    fx.sh(root, "git", "clone", "-q", fx.origin, fx.other)  # a second session in another clone pushes first
    t2 = os.path.join(root, "proj", "s2.jsonl")
    append(t2, prompt("2026-01-01T01:00:00Z"), msg("x1", "2026-01-01T01:00:01Z"))
    fx.hook(fx.other, "s2", t2, os.path.join(root, "logs2"))
    append(t1, prompt("2026-01-01T02:00:00Z", "[Request interrupted by user]"), prompt("2026-01-01T02:00:01Z"),
           msg("m3", "2026-01-01T02:00:02Z", n=2))
    os.makedirs(os.path.join(root, "proj", "s1", "subagents"))
    append(os.path.join(root, "proj", "s1", "subagents", "agent-a.jsonl"),
           msg("sa1", "2026-01-01T02:00:03Z", model="claude-small", side=True, n=3))
    fx.hook(work, "s1", t1, logs)
    got = fx.remote_rows("s1") or []
    fx.expect("turn 2: new main and subagent calls; an interrupt marker is not a turn",
              [(x["message_id"], x["turn"], x["model"], x["source"]) for x in got[2:]],
              [("m3", "2", "claude-test", "main"), ("sa1", "2", "claude-small", "subagent")])
    fx.expect("another session's file stays on the branch", len(fx.remote_rows("s2") or []), 1)
    fx.expect("turn 2: work tree, index, HEAD, branch and shallow state unchanged", fx.state(work), fx.before)


def case_blocked_and_shallow(fx):
    """A blocking pre-push hook, a lost local folder, and a shallow clone.

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, t1, logs, hooks = fx.root, fx.work, fx.t1, fx.logs, fx.hooks
    os.makedirs(hooks)
    fx.set_pre_push("#!/bin/sh\necho blocked >&2\nexit 1\n")
    fx.sh(work, "git", "config", "core.hooksPath", hooks)
    append(t1, msg("m4", "2026-01-01T02:00:05Z"))
    r = fx.hook(work, "s1", t1, logs)
    fx.expect("pre-push hook blocks: exit 0, nothing pushed", (r.returncode, len(fx.remote_rows("s1") or [])), (0, 4))
    os.remove(os.path.join(hooks, "pre-push"))
    shutil.rmtree(logs)  # a new container: the local folder is gone
    fx.hook(work, "s1", t1, logs)
    got = fx.remote_rows("s1") or []
    fx.expect("next push (local folder lost): carries the waiting call, no row twice",
              sorted(x["message_id"] for x in got), ["m1", "m2", "m3", "m4", "sa1"])

    shallow = os.path.join(root, "shallow")
    fx.sh(root, "git", "clone", "-q", "--depth", "1", "file://" + fx.origin, shallow)
    fx.sh(shallow, "git", "config", "core.hooksPath", hooks)
    append(t1, msg("m5", "2026-01-01T02:00:06Z"))
    fx.hook(shallow, "s1", t1, logs)
    fx.expect("shallow clone: pushes", len(fx.remote_rows("s1") or []), 6)


def case_retry(fx):
    """In process: retries after a failed push, and giving up after 3 tries.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    os.environ["TOKEN_LOG_HOME"] = os.path.join(fx.root, "locks")  # the in-process tests never touch the real home
    os.makedirs(tl.home())
    calls = []

    def flaky(*a):
        """A push that fails once, then succeeds."""
        calls.append(a)
        if len(calls) == 1:
            raise RuntimeError("blocked")
        return "pushed"
    tl.push = flaky
    try:
        ok = tl.push_main(["r", "s", "t"], delays=(0, 0, 0))
    finally:
        tl.push = fx.real_push
    fx.expect("a failed push is tried again; a success stops the retries", (ok, len(calls)), (True, 2))

    def broken(*a):
        """A push that always fails."""
        raise RuntimeError("blocked")
    tl.push = broken
    try:
        ok = tl.push_main(["r", "s", "t"], delays=(0, 0, 0))
    finally:
        tl.push = fx.real_push
    fx.expect("3 failed tries: gives up", ok, False)


def case_coalesce(fx):
    """In process: a third push exits while one waits; a retry loop stops when a newer push starts waiting.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    with open(os.path.join(tl.home(), "s.wait"), "w") as held:  # another push is waiting
        fcntl.flock(held, fcntl.LOCK_EX)
        fx.expect("a push is waiting: a third one exits at once", tl.locked_push("r", "s", "t"), "coalesced")
    newer, tries = [], []

    def fails_while_newer_starts(*a):
        """The first try fails; meanwhile a newer push starts waiting."""
        tries.append(a)
        if not newer:
            w = open(os.path.join(tl.home(), "s.wait"), "w")
            fcntl.flock(w, fcntl.LOCK_EX | fcntl.LOCK_NB)
            newer.append(w)
        raise RuntimeError("blocked")
    tl.push = fails_while_newer_starts
    try:
        ok = tl.push_main(["r", "s", "t"], delays=(0, 0, 0))
    finally:
        tl.push = fx.real_push
        for w in newer:
            w.close()
    fx.expect("a failed try, then a newer push waits: the retry loop stops (1 push call)", (ok, len(tries)), (True, 1))


def case_fetch_head_and_timeout(fx):
    """FETCH_HEAD is not written; a push with no answer is killed; a bad timeout setting falls back.

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, t1, logs = fx.root, fx.work, fx.t1, fx.logs
    fetch_head = os.path.join(work, ".git", "FETCH_HEAD")
    with open(fetch_head, "w") as f:
        f.write("marker\n")
    append(t1, msg("m7", "2026-01-01T02:00:08Z"))
    fx.hook(work, "s1", t1, logs)
    fx.expect("the shared FETCH_HEAD is not written", open(fetch_head).read(), "marker\n")

    marker, started = os.path.join(root, "hook-child-ran"), os.path.join(root, "hook-started")
    fx.set_pre_push(f"#!/bin/sh\ntouch '{started}'\n(sleep 2; touch '{marker}') &\nsetsid sleep 30 &\nsleep 30\n")
    append(t1, msg("m8", "2026-01-01T02:00:09Z"))
    start = time.time()
    r = fx.hook(work, "s1", t1, logs, extra={"TOKEN_LOG_NET_TIMEOUT": "1"})
    took = time.time() - start
    time.sleep(2.5)
    fx.expect("a push with no answer: the hook started, then was killed; not held by an escaped child; exit 0",
              (r.returncode, os.path.exists(started), os.path.exists(marker), took < 10), (0, True, False, True))
    for bad in ("x", "0", "-5", "\u00b2"):
        os.environ["TOKEN_LOG_NET_TIMEOUT"] = bad
        fx.expect(f"TOKEN_LOG_NET_TIMEOUT={bad!r}: the default", fx.tl.net_timeout(), 600)
    os.environ.pop("TOKEN_LOG_NET_TIMEOUT")
    os.remove(os.path.join(fx.hooks, "pre-push"))


def wait_locked(pid, path):
    """True when process pid holds the lock on path (a blocked waiter), read from the kernel's lock table. Probing
    the lock instead could make the waiter exit as "coalesced". With no lock table (macOS): a short wait, then True.

    Args:
        pid: the process id of the waiter.
        path: the lock file it waits for.
    Returns:
        True when the process holds the lock.
    """
    if not os.path.exists("/proc/locks"):
        time.sleep(0.5)
        return True
    for _ in range(200):   # up to 10 s
        time.sleep(0.05)
        if not os.path.exists(path):
            continue
        inode = os.stat(path).st_ino
        with open("/proc/locks") as f:
            if any(f" {pid} " in line and line.split()[-3].endswith(f":{inode}") and "->" not in line for line in f):
                return True
    return False


def case_waiting_push(fx):
    """A push that waits for the lock reads the log only when it gets the lock, so it carries rows added meanwhile.

    Args:
        fx: the shared test fixture (Fixture).
    """
    work, t1, logs = fx.work, fx.t1, fx.logs
    os.makedirs(logs, exist_ok=True)
    with open(os.path.join(logs, "s1.lock"), "w") as running:  # a push is running
        fcntl.flock(running, fcntl.LOCK_EX)
        waiter = subprocess.Popen([sys.executable, os.path.abspath(fx.tl.__file__), "--push", work, "s1", t1],
                                  env={**fx.env, "TOKEN_LOG_HOME": logs}, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        fx.expect("the second push waits for the running one", wait_locked(waiter.pid, os.path.join(logs, "s1.wait")),
                  True)
        append(t1, msg("m10", "2026-01-01T02:00:11Z"))
    try:
        waiter.wait(timeout=30)
    except subprocess.TimeoutExpired:
        waiter.kill()
        waiter.wait()
    fx.expect("a waiting push carries a row added while it waited",
              "m10" in [x["message_id"] for x in fx.remote_rows("s1") or []], True)


def case_bad_input_and_off(fx):
    """Bad hook input, a session id with a slash, and TOKEN_LOG=off."""
    work, t1, logs = fx.work, fx.t1, fx.logs
    fx.expect("bad input: exit 0", fx.hook(work, "s1", t1, logs, stdin="not json").returncode, 0)
    fx.expect("session id with a slash: ignored", fx.hook(work, "../x", t1, logs).returncode, 0)
    count = len(fx.remote_rows("s1") or [])
    append(t1, msg("m9", "2026-01-01T02:00:10Z"))
    fx.hook(work, "s1", t1, logs, extra={"TOKEN_LOG": "off"})
    fx.expect("TOKEN_LOG=off: nothing pushed", len(fx.remote_rows("s1") or []), count)


def run(tl):
    """Run every case in order on one fixture; print the total line and return the exit code.

    Args:
        tl: the token_log module.
    Returns:
        The exit code: 0 when every case passes, else 1.
    """
    import token_log_test_parts as parts  # the cases of the rows, report and self-update (imports this file's samples)
    fx = Fixture(tl)
    fx.real_push = tl.push
    saved = {k: os.environ.get(k) for k in ("TOKEN_LOG_HOME", "TOKEN_LOG_NET_TIMEOUT")}  # restored at the end
    try:
        for case in (case_first_turn, case_second_turn, case_blocked_and_shallow, case_retry, case_coalesce,
                     case_fetch_head_and_timeout, case_waiting_push, case_bad_input_and_off, parts.case_agent_type,
                     parts.case_skill_use, parts.case_agent_type_bad_input, parts.case_report, parts.case_prices,
                     parts.case_self_update):
            case(fx)
    finally:
        tl.push = fx.real_push
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(fx.root, ignore_errors=True)
    print("TOKEN LOG SELF-TEST " + ("PASS" if not fx.fails else f"FAIL ({fx.fails})"))
    return 1 if fx.fails else 0


class TokenLogTest(unittest.TestCase):
    """The cases of `python3 scripts/token_log.py --test`, for `python3 -m unittest` and pytest. They run in order in
    one test: they share one fixture (the bare origin and its clones)."""

    def test_self_test(self):
        """Every case passes on the token_log module."""
        import token_log  # scripts/token_log.py: imported here, so a plain import of this file loads nothing
        self.assertEqual(run(token_log), 0)
