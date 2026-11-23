#!/usr/bin/env python3
"""Self-test of scripts/token_log.py (run by `python3 scripts/token_log.py --test`; kept in its own file so each
case stays under the 60-line cap of docs/code-standard.md C3).

It builds a bare origin and clones in a temporary folder (no network) and runs the Stop hook on sample session logs:
one row per API call, turns, subagent rows, a second session, a blocking pre-push hook, a lost local folder, a shallow
clone, retries, coalescing, FETCH_HEAD, a push with no answer, a push that waits for the lock, bad input,
TOKEN_LOG=off, the agent and agent_id columns, the report and the self-update.
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


def case_agent_type(fx):
    """A subagent row gets the type of its Agent call; a subagent with no matching call says "unknown".

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, logs = fx.root, fx.work, fx.logs
    t3 = os.path.join(root, "proj", "s3.jsonl")
    u = json.loads(msg("p1", "2026-01-02T01:00:00Z"))["message"]["usage"]
    call = {"type": "assistant", "timestamp": "2026-01-02T01:00:00Z",
            "message": {"id": "p1", "model": "claude-test", "usage": u,
                        "content": [{"type": "tool_use", "id": "tu1", "name": "Agent", "input": {"subagent_type": "scout"}}]}}
    done = {"type": "user", "timestamp": "2026-01-02T01:00:01Z", "toolUseResult": {"agentId": "ab1"},
            "message": {"content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "x"}]}}
    append(t3, prompt("2026-01-02T00:59:00Z"), json.dumps(call), json.dumps(done))
    os.makedirs(os.path.join(root, "proj", "s3", "subagents"))
    append(os.path.join(root, "proj", "s3", "subagents", "agent-ab1.jsonl"),
           msg("sa2", "2026-01-02T01:00:02Z", side=True))
    append(os.path.join(root, "proj", "s3", "subagents", "agent-zz9.jsonl"),
           msg("sa3", "2026-01-02T01:00:03Z", side=True))
    fx.hook(work, "s3", t3, logs)
    got = fx.remote_rows("s3") or []
    fx.expect("agent column: main row, matched subagent type, unmatched subagent",
              [(x["message_id"], x["agent"]) for x in got], [("p1", "main"), ("sa2", "scout"), ("sa3", "unknown")])
    fx.expect("agent_id column: empty for main, the subagent's id from its log file name",
              [x["agent_id"] for x in got], ["", "ab1", "zz9"])


def case_agent_type_bad_input(fx):
    """Each bad field alone: a non-text type, an unmapped id, a non-text id and a non-number count. Each row still
    pushes; the bad type and the unmapped id say "unknown".

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, logs = fx.root, fx.work, fx.logs
    t4 = os.path.join(root, "proj", "s4.jsonl")
    u = json.loads(msg("p", "2026-01-02T02:00:00Z"))["message"]["usage"]

    def asst(mid, ts, content=None, usage=u):
        """One assistant log line with this id, time, content and usage."""
        m = {"id": mid, "model": "claude-test", "usage": usage}
        if content is not None:
            m["content"] = content
        return json.dumps({"type": "assistant", "timestamp": ts, "message": m})

    def use(tid, name, sub):
        """One tool_use block: an Agent or Task call with a subagent type."""
        return {"type": "tool_use", "id": tid, "name": name, "input": {"subagent_type": sub}}

    def result(ts, agent, tool_use_id):
        """One tool_result line with the agent id and the tool_use id it answers."""
        return json.dumps({"type": "user", "timestamp": ts, "toolUseResult": {"agentId": agent},
                           "message": {"content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "x"}]}})

    append(t4, prompt("2026-01-02T01:59:00Z"),
           asst("pA", "2026-01-02T02:00:00Z", [use("tA", "Task", {"a": 1})]),  # a dict type
           result("2026-01-02T02:00:01Z", "abA", "tA"),
           asst("pB", "2026-01-02T02:00:02Z", [use("tB", "Agent", "scout")]),
           result("2026-01-02T02:00:03Z", "abB", {"a": 1}),  # a dict tool_use_id: abB stays unmapped
           asst("pC", "2026-01-02T02:00:04Z", [use("tC", "Agent", "scout")]),
           result("2026-01-02T02:00:05Z", ["q"], "tC"),  # a list agentId
           asst(["x"], "2026-01-02T02:00:06Z"),  # a list message id: no row
           asst("pD", "2026-01-02T02:00:07Z"),
           asst("pE", "2026-01-02T02:00:08Z", usage=dict(u, input_tokens="abc")),  # a non-number count
           asst("pF", "2026-01-02T02:00:09Z", usage=dict(u, input_tokens=float("inf"))))  # an infinite count
    d = os.path.join(root, "proj", "s4", "subagents")
    os.makedirs(d)
    append(os.path.join(d, "agent-abA.jsonl"), msg("saA", "2026-01-02T02:00:10Z", side=True))
    append(os.path.join(d, "agent-abB.jsonl"), msg("saB", "2026-01-02T02:00:11Z", side=True))
    fx.hook(work, "s4", t4, logs)
    got = fx.remote_rows("s4") or []
    fx.expect("bad fields: each row still pushes; a dict type and an unmapped id say unknown",
              [(x["message_id"], x["agent"]) for x in got],
              [("pA", "main"), ("pB", "main"), ("pC", "main"), ("pD", "main"), ("pE", "main"),
               ("pF", "main"), ("saA", "unknown"), ("saB", "unknown")])
    fx.expect("non-number and infinite counts: counted as 0",
              [x["input_tokens"] for x in got if x["message_id"] in ("pE", "pF")], ["0", "0"])


def case_report(fx):
    """Price weights (longest prefix, cache write 1.25 x input), weeks in America/Chicago, tasks, unpriced models.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    row = {"model": "claude-opus-5-5", "input_tokens": "1000000", "cache_creation_input_tokens": "1000000",
           "cache_read_input_tokens": "1000000", "output_tokens": "1000000"}
    fx.expect("row cost: opus-5-5 is 4 + 5 + 0.20 + 20", round(tl.row_cost(row), 2), 29.2)
    fx.expect("row cost: unknown model is None", tl.row_cost({**row, "model": "claude-test"}), None)
    fx.expect("week: Sunday 23:00 Chicago is the week of the Monday before",
              tl.week_of("2026-11-23T05:00:00Z"), "2026-11-16")
    fx.expect("week: bad timestamp", tl.week_of("not a time"), "unknown")
    rows = [{**row, "source": "main", "agent": "main", "timestamp": "2026-11-17T12:00:00Z"},
            {**row, "source": "subagent", "agent": "scout", "agent_id": "a1", "model": "claude-haiku-5-5",
             "timestamp": "2026-11-17T12:00:00Z"},
            {**row, "source": "subagent", "agent": "scout", "agent_id": "a1", "model": "claude-haiku-5-5",
             "timestamp": "2026-11-17T12:00:01Z"},
            {**row, "source": "main", "model": "claude-test", "timestamp": ""}]
    text = tl.report(rows)
    fx.expect("report: week line with main and subagent cost",
              "2026-11-16                          3   29.20        7.35    36.55" in text, True)
    fx.expect("report: one scout task of 2 calls", any(l.split()[:3] == ["scout", "1", "2.0"] for l in text.splitlines()),
              True)
    fx.expect("report: unpriced model listed", text.splitlines()[-3],
              "no token price (tokens counted as 0, web searches counted): claude-test")
    fx.expect("report: footer counts the old rows priced as 5-minute cache writes", text.splitlines()[-1],
              "Rows from before the cache_write_1h_tokens column (4): cache writes priced as 5-minute.")
    new = [{**r, "cache_write_1h_tokens": "0"} for r in rows]
    fx.expect("report: no old-row footer when every row has the column",
              "cache_write_1h_tokens" in tl.report(new), False)
    fx.expect("report: footer for 1 old row among new rows",
              tl.report(new + rows[:1]).splitlines()[-1].endswith("column (1): cache writes priced as 5-minute."), True)
    searched = {**row, "model": "claude-test", "web_search_requests": "3", "source": "main",
                "timestamp": "2026-11-17T12:00:00Z", "cache_write_1h_tokens": "0"}
    fx.expect("row cost: unknown model with 3 web searches is the search fee only",
              round(tl.row_cost(searched), 6), 0.03)
    text = tl.report([searched])
    fx.expect("report: search fee of an unknown model in the week total",
              "2026-11-16                          1    0.03        0.00     0.03" in text, True)
    fx.expect("report: unknown model with searches still listed as no token price",
              text.splitlines()[-1].endswith(": claude-test"), True)
    old = {k: v for k, v in rows[0].items() if k not in ("agent", "agent_id")}  # a row from before the columns
    merged = list(csv.DictReader(io.StringIO(tl.to_csv({"m1": {**old, "message_id": "m1"}}))))
    fx.expect("old row without agent and agent_id: merged with empty values",
              (merged[0]["agent"], merged[0]["agent_id"]), ("", ""))
    fx.expect("old row: in the report", "29.20" in tl.report(merged), True)


def case_prices(fx):
    """Cost cases from the price list: 1-hour writes, Haiku 5.5 long prompts, fast mode, web search, US geo, old rows.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    M = 1_000_000

    def cost(model, **kw):
        """Cost of one row of this model with these fields (token counts default to 0)."""
        r = {"model": model, "input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
             "output_tokens": 0}
        return round(tl.row_cost({**r, **kw}), 6)
    fx.expect("5-minute cache write: 1.25 x input", cost("claude-opus-5", cache_creation_input_tokens=M), 6.25)
    fx.expect("1-hour cache write: 2 x input",
              cost("claude-opus-5", cache_creation_input_tokens=M, cache_write_1h_tokens=M), 10.0)
    fx.expect("cache write split: half 1-hour, half 5-minute",
              cost("claude-opus-5", cache_creation_input_tokens=M, cache_write_1h_tokens=M // 2), 8.125)
    fx.expect("Haiku 5.5 prompt of 100,000 tokens: short price", cost("claude-haiku-5-5", input_tokens=100_000), 0.01)
    fx.expect("Haiku 5.5 prompt of 100,001 tokens: long price", cost("claude-haiku-5-5", input_tokens=100_001), 0.050001)
    fx.expect("Haiku 5.5 prompt length counts cache reads and writes",
              cost("claude-haiku-5-5", cache_read_input_tokens=60_000, cache_creation_input_tokens=40_001), round(60_000 * 0.05 / M + 40_001 * 0.625 / M, 6))
    fx.expect("fast mode Opus 5.5: input 8, output 40",
              cost("claude-opus-5-5", input_tokens=M, output_tokens=M, speed="fast"), 48.0)
    fx.expect("fast mode Opus 5.5: 1-hour cache write is 2 x fast input",
              cost("claude-opus-5-5", cache_creation_input_tokens=M, cache_write_1h_tokens=M, speed="fast"), 16.0)
    fx.expect("fast mode on a model with no fast price: normal price",
              cost("claude-sonnet-5", input_tokens=M, speed="fast"), 2.0)
    fx.expect("3 web searches add $0.03", cost("claude-opus-5", web_search_requests=3), 0.03)
    fx.expect("inference_geo us adds 10%", cost("claude-opus-5", output_tokens=M, inference_geo="us"), 27.5)
    fx.expect("inference_geo us: web search fee not raised",
              cost("claude-opus-5", web_search_requests=10, inference_geo="us"), 0.1)
    fx.expect("inference_geo us: not on Opus 4.5", cost("claude-opus-4-5", output_tokens=M, inference_geo="us"), 25.0)
    fx.expect("old row without the new columns: cache write as 5-minute",
              cost("claude-opus-5", cache_creation_input_tokens=M), 6.25)
    fx.expect("Opus 4.1 and Opus 4 (retired): 15 / 75", (cost("claude-opus-4-1-20250805", input_tokens=M),
              cost("claude-opus-4-20250514", output_tokens=M)), (15.0, 75.0))
    fx.expect("Opus 4.7: 5 / 25", (cost("claude-opus-4-7", input_tokens=M), cost("claude-opus-4-7", output_tokens=M)),
              (5.0, 25.0))
    t5 = os.path.join(fx.root, "proj", "s5.jsonl")
    u = {"input_tokens": 1, "cache_creation_input_tokens": 10, "cache_read_input_tokens": 0, "output_tokens": 1,
         "cache_creation": {"ephemeral_5m_input_tokens": 4, "ephemeral_1h_input_tokens": 6}, "speed": "fast",
         "server_tool_use": {"web_search_requests": 2}, "inference_geo": "us"}
    append(t5, prompt("2026-01-03T00:00:00Z"),
           json.dumps({"type": "assistant", "timestamp": "2026-01-03T00:00:01Z",
                       "message": {"id": "q1", "model": "claude-opus-5-5", "usage": u}}))
    fx.hook(fx.work, "s5", t5, fx.logs)
    got = fx.remote_rows("s5") or [{}]
    fx.expect("log to row: 1-hour part, speed, web searches, geo recorded",
              [got[0].get(k) for k in ("cache_write_1h_tokens", "speed", "web_search_requests", "inference_geo")],
              ["6", "fast", "2", "us"])
    fx.expect("a row from before the new columns still parses and prices",
              tl.row_cost({k: v for k, v in got[0].items() if k not in tl.FIELDS[13:]}) is not None, True)


def case_self_update(fx):
    """Self-update: a newer copy replaces the file; once a day; a copy that does not compile is not used.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl, root = fx.tl, fx.root
    kit, target = os.path.join(root, "kit"), os.path.join(root, "installed", "token_log.py")
    os.makedirs(os.path.join(kit, "scripts"))
    os.makedirs(os.path.dirname(target))
    append(target, "old = 1")
    append(os.path.join(kit, "scripts", "token_log.py"), "import sys", "sys.exit(0)  # new")
    fx.sh(root, "git", "init", "-q", "-b", "main", kit)
    fx.sh(kit, "git", "add", ".")
    fx.sh(kit, "git", "commit", "-q", "-m", "kit")
    os.environ["TOKEN_LOG_HOME"] = os.path.join(root, "update-home")
    fx.expect("self-update: newer copy replaces the file", tl.self_update(target, kit, now=1e9), "updated")
    fx.expect("self-update: file has the new text", open(target).read(), "import sys\nsys.exit(0)  # new\n")
    fx.expect("self-update: second check the same day is skipped", tl.self_update(target, kit, now=1e9 + 60), "skipped")
    fx.expect("self-update: next day, same copy", tl.self_update(target, kit, now=1e9 + 90000), "up to date")
    with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
        f.write("import sys\nsys.exit(1)  # compiles, fails its self-test\n")
    fx.sh(kit, "git", "commit", "-q", "-am", "fails")
    fx.expect("self-update: a copy whose self-test fails is not used",
              tl.self_update(target, kit, now=1e9 + 200000).startswith("not updated: self-test failed"), True)
    fx.expect("self-update: file kept", open(target).read(), "import sys\nsys.exit(0)  # new\n")


def run(tl):
    """Run every case in order on one fixture; print the total line and return the exit code.

    Args:
        tl: the token_log module.
    Returns:
        The exit code: 0 when every case passes, else 1.
    """
    fx = Fixture(tl)
    fx.real_push = tl.push
    saved = {k: os.environ.get(k) for k in ("TOKEN_LOG_HOME", "TOKEN_LOG_NET_TIMEOUT")}  # restored at the end
    try:
        for case in (case_first_turn, case_second_turn, case_blocked_and_shallow, case_retry, case_coalesce,
                     case_fetch_head_and_timeout, case_waiting_push, case_bad_input_and_off, case_agent_type,
                     case_agent_type_bad_input, case_report, case_prices, case_self_update):
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
