#!/usr/bin/env python3
"""Self-test of scripts/token_log.py (run by `python3 scripts/token_log.py --test`; kept in its own file so each
case stays under the 60-line cap of docs/code-standard.md C3).

It builds a bare origin and clones in a temporary folder (no network) and runs the Stop hook on sample session logs:
one row per API call, turns, subagent rows, a second session, a blocking pre-push hook, a lost local folder, a shallow
clone, retries, coalescing, FETCH_HEAD, a push with no answer, bad input and TOKEN_LOG=off.
Input: the token_log module. Output: one PASS or FAIL line per case and a "TOKEN LOG SELF-TEST" total line; returns
the exit code (0 pass, 1 fail). Needs git.
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
        """Make the temporary root and a git environment with no user or global config."""
        self.tl = tl
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
        os.chmod(os.path.join(self.hooks, "pre-push"), 0o755)


def case_first_turn(fx):
    """Set up origin and work clone; outside a repo, turn 1 rows, no-op push."""
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
    """Another session pushes first; turn 2 adds main and subagent calls."""
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
    """A blocking pre-push hook, a lost local folder, and a shallow clone."""
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


def case_retry_and_coalesce(fx):
    """In process: retries after a failed push, giving up, and a coalesced third push."""
    tl = fx.tl
    old_home = os.environ.get("TOKEN_LOG_HOME")
    os.environ["TOKEN_LOG_HOME"] = os.path.join(fx.root, "locks")  # the in-process tests never touch the real home
    os.makedirs(tl.home())
    calls, real_push = [], tl.push

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
        tl.push = real_push
    fx.expect("a failed push is tried again; a success stops the retries", (ok, len(calls)), (True, 2))

    def broken(*a):
        """A push that always fails."""
        raise RuntimeError("blocked")
    tl.push = broken
    try:
        ok = tl.push_main(["r", "s", "t"], delays=(0, 0, 0))
    finally:
        tl.push = real_push
    fx.expect("3 failed tries: gives up", ok, False)

    try:
        with open(os.path.join(tl.home(), "s.wait"), "w") as held:  # another push is waiting
            fcntl.flock(held, fcntl.LOCK_EX)
            fx.expect("a push is waiting: a third one exits at once", tl.locked_push("r", "s", "t"), "coalesced")
    finally:
        os.environ.pop("TOKEN_LOG_HOME") if old_home is None else os.environ.update(TOKEN_LOG_HOME=old_home)


def case_fetch_head_and_timeout(fx):
    """FETCH_HEAD is not written; a push with no answer is killed; a bad timeout setting falls back."""
    root, work, t1, logs = fx.root, fx.work, fx.t1, fx.logs
    fetch_head = os.path.join(work, ".git", "FETCH_HEAD")
    with open(fetch_head, "w") as f:
        f.write("marker\n")
    append(t1, msg("m7", "2026-01-01T02:00:08Z"))
    fx.hook(work, "s1", t1, logs)
    fx.expect("the shared FETCH_HEAD is not written", open(fetch_head).read(), "marker\n")

    marker = os.path.join(root, "hook-child-ran")
    fx.set_pre_push(f"#!/bin/sh\n(sleep 2; touch '{marker}') &\nsetsid sleep 30 &\nsleep 30\n")
    append(t1, msg("m8", "2026-01-01T02:00:09Z"))
    start = time.time()
    r = fx.hook(work, "s1", t1, logs, extra={"TOKEN_LOG_NET_TIMEOUT": "1"})
    took = time.time() - start
    time.sleep(2.5)
    fx.expect("a push with no answer: killed with its hook, not held by an escaped child, exit 0",
              (r.returncode, os.path.exists(marker), took < 10), (0, False, True))
    os.environ["TOKEN_LOG_NET_TIMEOUT"] = "x"
    try:
        fx.expect("a bad TOKEN_LOG_NET_TIMEOUT: the default", fx.tl.net_timeout(), 600)
    finally:
        os.environ.pop("TOKEN_LOG_NET_TIMEOUT")
    os.remove(os.path.join(fx.hooks, "pre-push"))


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
    """Run every case in order on one fixture; print the total line and return the exit code."""
    fx = Fixture(tl)
    try:
        for case in (case_first_turn, case_second_turn, case_blocked_and_shallow, case_retry_and_coalesce,
                     case_fetch_head_and_timeout, case_bad_input_and_off):
            case(fx)
    finally:
        shutil.rmtree(fx.root, ignore_errors=True)
    print("TOKEN LOG SELF-TEST " + ("PASS" if not fx.fails else f"FAIL ({fx.fails})"))
    return 1 if fx.fails else 0
