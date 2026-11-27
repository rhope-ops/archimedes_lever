#!/usr/bin/env python3
"""Self-test of scripts/token_log.py (run by `python3 scripts/token_log.py --test`; kept in its own file so each
case stays under the 60-line cap of docs/code-standard.md C3).

It builds a bare origin and clones in a temporary folder (no network) and runs the Stop hook on sample session logs:
one row per API call, turns, subagent rows, a second session, a blocking pre-push hook, a lost local folder, a shallow
clone, retries, coalescing, FETCH_HEAD, a push with no answer, a push that waits for the lock, bad input and
TOKEN_LOG=off, the private log repo (with its fallback to origin), the rows (agent, agent_id and skill_use columns,
bad agent input), the report and prices, the self-update, and the /cost and /usage records.
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
import types
import unittest
from datetime import datetime, timezone


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
        self.tl, self.rows, self.rep = tl, tl, tl
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
    with open(fetch_head) as f:
        fx.expect("the shared FETCH_HEAD is not written", f.read(), "marker\n")

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


def case_skill_use(fx):
    """The skill_use column: one Skill call, one Read of a SKILL.md, one sed slice of a SKILL.md and one Read of
    another file, on invented data; a shell command with a false folder name; a row from before the column.

    Args:
        fx: the shared test fixture (Fixture).
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(fx.rows.__file__)))
    try:
        import skill_use  # the kit's own copy of the SKILL.md path rule; an installed hook has none: no check
        fx.expect("SKILL.md path rule: one rule in token_log.py and skill_use.py",
                  fx.rows.SKILL_PATH.pattern, skill_use.SKILL_FILE.pattern)
    except ImportError:
        pass
    t6 = os.path.join(fx.root, "proj", "s6.jsonl")
    u = json.loads(msg("k1", "2026-01-04T00:00:01Z"))["message"]["usage"]

    def call(mid, ts, name, **tool_input):
        """One assistant log line with one tool_use block."""
        block = {"type": "tool_use", "id": "t" + mid, "name": name, "input": tool_input}
        return json.dumps({"type": "assistant", "timestamp": ts,
                           "message": {"id": mid, "model": "claude-test", "usage": u, "content": [block]}})

    append(t6, prompt("2026-01-04T00:00:00Z"),
           call("k1", "2026-01-04T00:00:01Z", "Skill", skill="alpha"),
           call("k2", "2026-01-04T00:00:02Z", "Read", file_path="/r/.claude/skills/alpha/SKILL.md"),
           call("k3", "2026-01-04T00:00:03Z", "Bash", command="sed -n 1,9p .claude/skills/beta/SKILL.md"),
           call("k4", "2026-01-04T00:00:04Z", "Read", file_path="/r/AGENTS.md"),
           call("k5", "2026-01-04T00:00:05Z", "Bash", command='for f in a b; do grep x "$f/SKILL.md"; done'),
           call("k6", "2026-01-04T00:00:06Z", "Bash", command="ls .claude/skills/beta/SKILL.md"),
           call("k7", "2026-01-04T00:00:07Z", "Bash", command="grep x README.md; ls skills/a/SKILL.md"),
           call("k8", "2026-01-04T00:00:08Z", "Bash", command="ls .claude/skills/cat/SKILL.md"),
           call("k9", "2026-01-04T00:00:09Z", "Read", file_path="/r/myskills/z/SKILL.md"),
           call("k10", "2026-01-04T00:00:10Z", "Bash", command="ls x && cat skills/p/SKILL.md | head -3"))
    fx.hook(fx.work, "s6", t6, fx.logs)
    got = {x["message_id"]: x["skill_use"] for x in fx.remote_rows("s6") or []}
    fx.expect("skill_use column: Skill call, Read, sed slice; other Read, false folder name, ls: nothing",
              got, {"k1": '{"alpha":{"skill_tool":1}}', "k2": '{"alpha":{"read":1}}', "k3": '{"beta":{"slice":1}}',
                    "k4": "", "k5": "", "k6": "", "k7": "", "k8": "", "k9": "",
                    "k10": '{"p":{"slice":1}}'})
    t7 = os.path.join(fx.root, "proj", "s7.jsonl")  # bad lines and blocks, then good calls
    skill = {"type": "tool_use", "name": "Skill", "input": {"skill": "alpha"}}
    good = {"type": "assistant", "timestamp": "2026-01-04T01:00:03Z",
            "message": {"id": "g1", "model": "claude-test", "usage": u,
                        "content": [{**skill, "id": "x1"}, {**skill, "id": [1]}, {**skill}, {**skill}, "text", [2]]}}
    append(t7, prompt("2026-01-04T01:00:00Z"), "[1]", '{"type":"assistant","message":"x"}',
           json.dumps({"type": "assistant", "message": {"id": "g0", "content": {"a": 1}}}),
           json.dumps({"type": "assistant", "message": {"id": "b1", "usage": u, "content": [{**skill, "id": [1]}]}}),
           json.dumps(good))
    fx.hook(fx.work, "s7", t7, fx.logs)
    got = {x["message_id"]: x["skill_use"] for x in fx.remote_rows("s7") or []}
    fx.expect("skill_use column: bad lines and blocks are skipped; blocks with no usable id count each",
              got, {"b1": '{"alpha":{"skill_tool":1}}', "g1": '{"alpha":{"skill_tool":4}}'})
    old = {"message_id": "m1", "timestamp": "2026-01-01T00:00:00Z"}  # a row from before the column
    merged = list(csv.DictReader(io.StringIO(fx.rows.to_csv({"m1": old}))))
    fx.expect("old row without skill_use: merged with an empty value", merged[0]["skill_use"], "")


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
    row = {"model": "claude-opus-5-5", "input_tokens": "1000000", "cache_creation_input_tokens": "1000000",
           "cache_read_input_tokens": "1000000", "output_tokens": "1000000"}
    fx.expect("row cost: opus-5-5 is 4 + 5 + 0.20 + 20", round(fx.rep.row_cost(row), 2), 29.2)
    fx.expect("row cost: unknown model is None", fx.rep.row_cost({**row, "model": "claude-test"}), None)
    fx.expect("week: Sunday 23:00 Chicago is the week of the Monday before",
              fx.rep.week_of("2026-11-23T05:00:00Z"), "2026-11-16")
    fx.expect("week: bad timestamp", fx.rep.week_of("not a time"), "unknown")
    rows = [{**row, "source": "main", "agent": "main", "timestamp": "2026-11-17T12:00:00Z"},
            {**row, "source": "subagent", "agent": "scout", "agent_id": "a1", "model": "claude-haiku-5-5",
             "timestamp": "2026-11-17T12:00:00Z"},
            {**row, "source": "subagent", "agent": "scout", "agent_id": "a1", "model": "claude-haiku-5-5",
             "timestamp": "2026-11-17T12:00:01Z"},
            {**row, "source": "main", "model": "claude-test", "timestamp": ""}]
    text = fx.rep.report(rows)
    fx.expect("report: week line with main and subagent cost",
              "2026-11-16                          3   29.20        7.35    36.55" in text, True)
    fx.expect("report: one scout task of 2 calls", any(ln.split()[:3] == ["scout", "1", "2.0"] for ln in text.splitlines()),
              True)
    fx.expect("report: unpriced model listed", text.splitlines()[-3],
              "no token price (tokens counted as 0, web searches counted): claude-test")
    fx.expect("report: footer counts the old rows; no newer rows: priced as 5-minute", text.splitlines()[-1],
              "Rows from before the cache_write_1h_tokens column (4): 1-hour share of their cache writes estimated "
              "from the newer rows of the same source: none: priced as 5-minute.")
    new = [{**r, "cache_write_1h_tokens": "0"} for r in rows]
    fx.expect("report: no old-row footer when every row has the column",
              "cache_write_1h_tokens" in fx.rep.report(new), False)
    fx.expect("report: footer for 1 old row among new rows",
              fx.rep.report(new + rows[:1]).splitlines()[-1].endswith("same source: main 0%, subagent 0%."), True)
    hour = {**rows[0], "cache_write_1h_tokens": "250000"}  # a newer main row: a quarter of its writes are 1-hour
    filled, share, n = fx.rep.fill_1h([hour, rows[0], rows[1]])
    fx.expect("1-hour estimate: share from the newer rows of the same source, old rows filled, count",
              (share, filled[1]["cache_write_1h_tokens"], filled[2]["cache_write_1h_tokens"], n),
              ({"main": 0.25}, "250000", "0", 2))
    fx.expect("1-hour estimate: an old main row costs as the newer one", round(fx.rep.row_cost(filled[1]), 2),
              round(fx.rep.row_cost(hour), 2))
    fx.expect("report: one repo line for two letter cases",
              [ln.split()[:2] for ln in fx.rep.report([{**new[0], "repo": "Kit"}, {**new[0], "repo": "kit"}]).splitlines()
               if ln.startswith("kit ")], [["kit", "2"]])
    searched = {**row, "model": "claude-test", "web_search_requests": "3", "source": "main",
                "timestamp": "2026-11-17T12:00:00Z", "cache_write_1h_tokens": "0"}
    fx.expect("row cost: unknown model with 3 web searches is the search fee only",
              round(fx.rep.row_cost(searched), 6), 0.03)
    text = fx.rep.report([searched])
    fx.expect("report: search fee of an unknown model in the week total",
              "2026-11-16                          1    0.03        0.00     0.03" in text, True)
    fx.expect("report: unknown model with searches still listed as no token price",
              text.splitlines()[-1].endswith(": claude-test"), True)
    old = {k: v for k, v in rows[0].items() if k not in ("agent", "agent_id")}  # a row from before the columns
    merged = list(csv.DictReader(io.StringIO(fx.rows.to_csv({"m1": {**old, "message_id": "m1"}}))))
    fx.expect("old row without agent and agent_id: merged with empty values",
              (merged[0]["agent"], merged[0]["agent_id"]), ("", ""))
    fx.expect("old row: in the report", "29.20" in fx.rep.report(merged), True)


def case_prices(fx):
    """Cost cases from the price list: 1-hour writes, Haiku 5.5 long prompts, fast mode, web search, US geo, old rows.

    Args:
        fx: the shared test fixture (Fixture).
    """
    M = 1_000_000

    def cost(model, **kw):
        """Cost of one row of this model with these fields (token counts default to 0)."""
        r = {"model": model, "input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
             "output_tokens": 0}
        return round(fx.rep.row_cost({**r, **kw}), 6)
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
              fx.rep.row_cost({k: v for k, v in got[0].items() if k not in fx.rows.FIELDS[13:]}) is not None, True)


def case_self_update(fx):
    """Self-update: the newest release tag's copy replaces the file (main without a tag never); once a day; a copy
    whose self-test fails is not used.

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
    fx.sh(kit, "git", "tag", "v1.9.0")
    os.environ["TOKEN_LOG_HOME"] = os.path.join(root, "update-home")
    fx.expect("self-update: newer copy replaces the file", tl.self_update(target, kit, now=1e9), "updated")
    with open(target) as f:
        fx.expect("self-update: file has the new text", f.read(), "import sys\nsys.exit(0)  # new\n")
    fx.expect("self-update: second check the same day is skipped", tl.self_update(target, kit, now=1e9 + 60), "skipped")
    fx.expect("self-update: next day, same copy", tl.self_update(target, kit, now=1e9 + 90000), "up to date")
    with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
        f.write("import sys\nsys.exit(1)  # compiles, fails its self-test\n")
    fx.sh(kit, "git", "commit", "-q", "-am", "fails")
    stamp = os.path.join(os.environ["TOKEN_LOG_HOME"], "update.stamp")
    os.remove(stamp)  # an extra check between the daily ones
    fx.expect("self-update: a newer main with no new release tag is not installed",
              tl.self_update(target, kit, now=1e9 + 150000), "up to date")
    os.remove(stamp)
    fx.sh(kit, "git", "tag", "v1.10.0")  # newer than v1.9.0 by number, older by text
    fx.expect("self-update: a copy whose self-test fails is not used",
              tl.self_update(target, kit, now=1e9 + 200000).startswith("not updated: self-test failed"), True)
    with open(target) as f:
        fx.expect("self-update: file kept", f.read(), "import sys\nsys.exit(0)  # new\n")
    with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
        f.write("import sys\nsys.exit(0)  # new 2\n")
    fx.sh(kit, "git", "add", ".")
    fx.sh(kit, "git", "commit", "-q", "-m", "v1.11.0")
    fx.sh(kit, "git", "tag", "v1.11.0")
    os.remove(stamp)
    fx.expect("self-update: newer release replaces the file", tl.self_update(target, kit, now=1e9 + 300000), "updated")
    fx.sh(kit, "git", "checkout", "-q", "-b", "v1.11.0")  # a branch named as the newest tag, with other code
    with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
        f.write("import sys\nsys.exit(0)  # a branch, not the release\n")
    fx.sh(kit, "git", "commit", "-q", "-am", "branch")
    fx.sh(kit, "git", "tag", "x/v9.9.9")  # not a release tag name: left out
    os.remove(stamp)
    status = tl.self_update(target, kit, now=1e9 + 450000)
    with open(target) as f:
        target_text = f.read()
    fx.expect("self-update: the tag's code, not a branch of the same name nor a tag x/v9.9.9",
              (status, target_text),
              ("up to date", "import sys\nsys.exit(0)  # new 2\n"))
    os.remove(stamp)
    fx.sh(kit, "git", "checkout", "-q", "main")
    case_kit_url(fx, kit, target)
    case_installed_hook_works(fx)


def case_kit_url(fx, kit, target):
    """Self-update installs kit.config.json; kit_url() reads TOKEN_LOG_KIT_URL and the installed file, never the session repo.

    Args:
        fx: the shared test fixture (Fixture).
        kit: the test kit repo of case_self_update.
        target: the installed token_log.py of case_self_update.
    """
    tl = fx.tl
    with open(os.path.join(kit, "kit.config.json"), "w") as f:  # kit 11.0.0: the kit address lives in kit.config.json
        f.write('{"kit_url": "https://example.invalid/sample-org/sample-kit"}')
    fx.sh(kit, "git", "add", ".")
    fx.sh(kit, "git", "commit", "-q", "-m", "config")
    fx.sh(kit, "git", "tag", "v1.12.0")
    tl.self_update(target, kit, now=1e9 + 500000)
    sibling = os.path.join(os.path.dirname(target), "kit.config.json")
    fx.expect("self-update: kit.config.json installs next to the file", os.path.isfile(sibling), True)
    saved = {k: os.environ.pop(k, None) for k in ("TOKEN_LOG_KIT_URL", "CLAUDE_PROJECT_DIR")}
    try:
        fx.expect("kit_url: read from the installed kit.config.json", tl.kit_url(target),
                  "https://example.invalid/sample-org/sample-kit")
        os.environ["TOKEN_LOG_KIT_URL"] = "https://example.invalid/other"
        fx.expect("kit_url: TOKEN_LOG_KIT_URL wins", tl.kit_url(target), "https://example.invalid/other")
        del os.environ["TOKEN_LOG_KIT_URL"]
        os.remove(sibling)
        os.environ["CLAUDE_PROJECT_DIR"] = kit  # a repo with its own kit.config.json must not steer the update
        fx.expect("kit_url: a session repo's kit.config.json is never read (security)", tl.kit_url(target), None)
        fx.expect("self-update: no kit address does nothing",
                  tl.self_update(target, now=1e9 + 600000).startswith("not updated: no kit address"), True)
        with open(os.path.join(kit, "kit.config.json"), "w") as f:  # a new address in a copy that fails its self-test
            f.write('{"kit_url": "https://example.invalid/hostile"}')
        with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
            f.write("import sys\nsys.exit(1)  # fails its self-test\n")
        fx.sh(kit, "git", "commit", "-q", "-am", "hostile")
        fx.sh(kit, "git", "tag", "v1.13.0")
        with open(sibling, "w") as f:
            f.write('{"kit_url": "https://example.invalid/sample-org/sample-kit"}')
        tl.self_update(target, kit, now=1e9 + 700000)
        fx.expect("self-update: a failed self-test installs no kit.config.json", tl.kit_url(target),
                  "https://example.invalid/sample-org/sample-kit")
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def case_installed_hook_works(fx):
    """A fresh install (the UPDATE_FILES of this kit in an empty hooks folder) gives a working hook: the Stop path
    outside a repo exits 0, and row/report helpers load directly from token_log.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    hooks = os.path.join(fx.root, "fresh-hooks")
    os.makedirs(hooks)
    for n in tl.UPDATE_FILES:
        shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(tl.__file__)), n), os.path.join(hooks, n))
    run = subprocess.run([sys.executable, "-E", "-s", os.path.join(hooks, "token_log.py")], input="{}", text=True,
                         capture_output=True, cwd=fx.root, timeout=60)
    fx.expect("installed hook: Stop outside a repo exits 0", (run.returncode, run.stderr), (0, ""))
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); import token_log as tl; "
             "print(callable(tl.log_rows), callable(tl.row_cost), bool(tl.PRICES))")
    run = subprocess.run([sys.executable, "-E", "-s", "-c", probe, hooks], text=True, capture_output=True, cwd=fx.root,
                         timeout=60)
    fx.expect("installed hook: the rows and report helpers load from token_log", run.stdout.strip(), "True True True")


def record(sid, read_at="2026-01-05T10:00:00Z", pct=(10, 20), subagents=2, usd=1.5, version=1):
    """One agents-pane record with invented figures: a 5-hour and a 7-day reading at read_at.

    Args:
        sid: the session id the record names.
        read_at: limits_read_at.
        pct: the percent used of the 5-hour and the 7-day window.
        subagents: the number of subagent entries.
        usd: session_usd.
        version: the version field (1 for a good record).
    Returns:
        The record as a dict.
    """
    sub = [{"agent_id": f"a{i}", "type": "scout", "model": "claude-haiku-5-5", "status": "completed", "usd": 0.25,
            "input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "started_at": "2026-01-05T09:00:00Z",
            "ended_at": None} for i in range(subagents)]
    return {"version": version, "session_id": sid, "written_at": "2026-01-05T10:00:05Z", "session_usd": usd,
            "main_usd": 1.0, "subagents_usd": 0.25 * subagents,
            "limits": [{"window": "five_hour", "percent_used": pct[0], "resets_at": "2026-01-05T12:00:00Z"},
                       {"window": "seven_day", "percent_used": pct[1], "resets_at": "2026-01-08T00:00:00Z"}],
            "limits_read_at": read_at, "main": {"turns": 3, "input": 10, "output": 20, "cache_read": 30, "cache_write": 40},
            "subagents": sub}


def write_record(fx, sid, rec):
    """Write a record (a dict, or raw text) where the hook reads it: <TOKEN_LOG_HOME>/cost/<sid>.json."""
    os.makedirs(os.path.join(fx.logs, "cost"), exist_ok=True)
    with open(os.path.join(fx.logs, "cost", sid + ".json"), "w") as f:
        f.write(rec if isinstance(rec, str) else json.dumps(rec))


def remote(fx, path):
    """The rows of a CSV file on the origin's log branch, or None."""
    r = subprocess.run(["git", "--git-dir", fx.origin, "show", f"claude/token-usage:{path}"], capture_output=True,
                       text=True, env=fx.env)
    return list(csv.DictReader(io.StringIO(r.stdout))) if r.returncode == 0 else None


def case_cost_files(fx):
    """No record: rows only. A good record: costs and limits in the same commit as the rows; the snapshot replaces
    the older one; the limits rows grow and deduplicate by (read_at, window).

    Args:
        fx: the shared test fixture (Fixture).
    """
    t7, t8 = (os.path.join(fx.root, "proj", f"{s}.jsonl") for s in ("c7", "c8"))
    append(t7, prompt("2026-01-05T08:00:00Z"), msg("c1", "2026-01-05T08:00:01Z"))
    fx.hook(fx.work, "c7", t7, fx.logs)
    fx.expect("no record: rows pushed, no costs or limits file",
              (len(remote(fx, "sessions/c7.csv") or []), remote(fx, "costs/c7.csv"), remote(fx, "limits/c7.csv")),
              (1, None, None))
    append(t8, prompt("2026-01-05T09:00:00Z"), msg("c2", "2026-01-05T09:00:01Z"))
    write_record(fx, "c8", record("c8"))
    fx.hook(fx.work, "c8", t8, fx.logs)
    names = fx.sh(fx.root, "git", "--git-dir", fx.origin, "log", "-1", "--name-only", "--format=", "claude/token-usage")
    fx.expect("good record: rows, costs and limits in one commit", sorted(names.splitlines()),
              ["costs/c8.csv", "limits/c8.csv", "sessions/c8.csv"])
    got = remote(fx, "costs/c8.csv") or []
    fx.expect("costs: one main row, then one row per subagent",
              [(x["source"], x["agent_id"], x["usd"], x["input"], x["session_usd"]) for x in got],
              [("main", "", "1.0", "10", "1.5"), ("subagent", "a0", "0.25", "1", "1.5"),
               ("subagent", "a1", "0.25", "1", "1.5")])
    write_record(fx, "c8", record("c8", subagents=1, usd=2.0, pct=(11, 99)))  # same read_at: an old reading
    fx.hook(fx.work, "c8", t8, fx.logs)
    fx.expect("costs: a new record replaces the snapshot",
              [(x["source"], x["session_usd"]) for x in remote(fx, "costs/c8.csv") or []],
              [("main", "2.0"), ("subagent", "2.0")])
    fx.expect("limits: the same read_at adds no row and keeps the first values",
              [(x["window"], x["percent_used"]) for x in remote(fx, "limits/c8.csv") or []],
              [("five_hour", "10"), ("seven_day", "20")])
    write_record(fx, "c8", record("c8", read_at="2026-01-05T11:00:00Z", pct=(15, 25)))
    fx.hook(fx.work, "c8", t8, fx.logs)
    fx.expect("limits: a new read_at adds rows; the earlier rows stay",
              [(x["read_at"][11:16], x["window"], x["percent_used"]) for x in remote(fx, "limits/c8.csv") or []],
              [("10:00", "five_hour", "10"), ("10:00", "seven_day", "20"), ("11:00", "five_hour", "15"),
               ("11:00", "seven_day", "25")])


def case_bad_records(fx):
    """A record that does not parse, is not version 1, names another session or has a part of the wrong type is
    skipped with a line in push.log; the rows still push and the files on the branch stay.

    Args:
        fx: the shared test fixture (Fixture).
    """
    t8 = os.path.join(fx.root, "proj", "c8.jsonl")
    before = (remote(fx, "costs/c8.csv"), remote(fx, "limits/c8.csv"))
    bad = {"no JSON (a half-written file)": '{"version": 1, "sess',
           "version \"1\" (a text)": record("c8", version="1"), "version true": record("c8", version=True),
           "another session's record": record("c9"),
           "limits as a text": {**record("c8"), "limits": "five_hour 10"}, "main as a list": {**record("c8"), "main": []}}
    for i, (name, rec) in enumerate(bad.items()):
        write_record(fx, "c8", rec)
        append(t8, msg(f"b{i}", f"2026-01-05T12:00:0{i}Z"))
        r = fx.hook(fx.work, "c8", t8, fx.logs)
        fx.expect(f"bad record, {name}: skipped with a log line; the rows push; costs and limits stay",
                  ("cost record skipped" in r.stdout, f"b{i}" in [x["message_id"] for x in remote(fx, "sessions/c8.csv")],
                   (remote(fx, "costs/c8.csv"), remote(fx, "limits/c8.csv")) == before), (True, True, True))
    os.remove(os.path.join(fx.logs, "cost", "c8.json"))
    append(t8, msg("b9", "2026-01-05T12:00:09Z"))
    fx.hook(fx.work, "c8", t8, fx.logs)
    fx.expect("record gone: the next push keeps the files on the branch",
              ("b9" in [x["message_id"] for x in remote(fx, "sessions/c8.csv")],
               (remote(fx, "costs/c8.csv"), remote(fx, "limits/c8.csv")) == before), (True, True))
    odd = {**record("c8"), "limits_read_at": "2026-01-05T13:00:00Z",
           "limits": [{"window": "five_hour", "percent_used": float("nan")}, {"window": "seven_day", "percent_used": 101},
                      {"window": "spend_limit", "percent_used": "abc"}, "five_hour", {"window": "seven_day",
                                                                                      "percent_used": 30}]}
    fx.expect("limits: NaN, over 100, a text and a non-object entry are skipped",
              [(x["read_at"][11:16], x["window"]) for x in csv.DictReader(io.StringIO(fx.rows.limits_csv(odd, "")))],
              [("13:00", "seven_day")])
    fx.expect("limits: a read_at with no time zone is skipped",
              fx.rows.limits_csv({**record("c8"), "limits_read_at": "2026-01-05T13:00:00"}, ""), "")


def at(hhmm, day=1):
    """A UTC datetime on 2026-01-<day> at HH:MM."""
    return datetime(2026, 1, day, int(hhmm[:2]), int(hhmm[3:]), tzinfo=timezone.utc)


def case_limit_split(fx):
    """The split of each rise of a window among the sessions by estimated $; a fall is not split; a rise with no
    logged use is "not attributed"; a new period starts at 0 % at its window start; the report parts.

    Args:
        fx: the shared test fixture (Fixture).
    """
    rep = fx.rep
    r1, r2 = "2026-01-08T00:00Z", "2026-01-15T00:00Z"
    series = [(at("10:00"), 10.0, r1), (at("12:00"), 20.0, r1), (at("13:00"), 15.0, r1), (at("14:00"), 25.0, r1),
              (at("10:00", 8), 4.0, r2)]
    spend = [(at("09:00"), "A", 3.0), (at("09:30"), "B", 1.0), (at("11:00"), "A", 2.0), (at("09:00", 8), "B", 1.0)]
    got = {k: {s: round(p, 2) for s, p in v.items()} for k, v in rep.split_rises(series, 168, spend).items()}
    fx.expect("split: by $ share; a fall is not split; no use is not attributed; a new window starts at 0 %", got,
              {r1: {"A": 17.5, "B": 2.5, "(not attributed)": 10.0}, r2: {"B": 4.0}})
    one = [(at("10:00"), 10.0, r1), (at("11:00"), 20.0, ""), (at("12:00"), 30.0, r1)]
    fx.expect("split: a missing reset time stays in its period (no use counted twice)",
              {k: {s: round(p, 2) for s, p in v.items()} for k, v in rep.split_rises(one, 168, spend).items()},
              {r1: {"A": 17.5, "B": 2.5, "(not attributed)": 10.0}})  # 30 points in all
    moved = [(at("10:00"), 10.0, r1), (at("11:00"), 20.0, "2026-01-08T00:01Z"), (at("12:00"), 30.0, r1)]
    fx.expect("split: a reset time that moves by a minute stays in its period",
              round(sum(rep.split_rises(moved, 168, spend)[r1].values()), 2), 30.0)
    fx.expect("/cost total: no session_usd and no main usd: no total (not the subagents' sum)",
              rep.cost_per_session([{"session_id": "x", "source": "main", "usd": "", "session_usd": ""},
                                    {"session_id": "x", "source": "subagent", "usd": "0.5", "session_usd": ""}]),
              {"x": None})
    fx.expect("split: no window length (spend_limit): the first reading of a period is not split",
              rep.split_rises([(at("10:00"), 5.0, ""), (at("11:00"), 7.0, "")], None, spend), {"": {"A": 2.0}})
    rows = [{"session_id": "sessA", "timestamp": "2026-01-01T09:00:00Z", "model": "claude-opus-5-5",
             "output_tokens": "100000"}, {"session_id": "sessB", "timestamp": "2026-01-01T09:30:00Z",
                                         "model": "claude-opus-5-5", "output_tokens": "50000"}]
    limits = [{"session_id": "sessA", "read_at": "2026-01-01T10:00:00Z", "window": "seven_day", "percent_used": "12",
               "resets_at": "2026-01-08T00:00:00Z"},
              {"session_id": "sessB", "read_at": "2026-01-01T10:00:00Z", "window": "seven_day", "percent_used": "12",
               "resets_at": "2026-01-08T00:00:00Z"}]
    costs = [{"session_id": "sessA", "source": "main", "usd": "1.0", "session_usd": "2.5"},
             {"session_id": "sessA", "source": "subagent", "usd": "1.5", "session_usd": "2.5"}]
    text = rep.limits_report(rows, costs, limits).splitlines()
    fx.expect("report: highest 7-day percent, one reading (the same reading from 2 sessions counts once)",
              text[2].split()[2:3] + text[2].split()[-1:], ["12.0", "1"])
    fx.expect("report: the split lines by session", [ln.split()[-2:] for ln in text if ln.startswith("seven_day")],
              [["sessA", "8.00"], ["sessB", "4.00"]])
    fx.expect("report: /cost by week next to the estimate", [ln.split() for ln in text if ln.startswith("2025-12-29")],
              [["2025-12-29", "2", "1", "2.00", "2.50", "1.00"]])
    fx.expect("report: sessions with no /cost record", text[-1], "no /cost record (1): sessB")


def case_best_and_sources(fx):
    """The best estimate (/cost where recorded, else the hook's $ x the median /cost ratio) and the --report sources.

    Args:
        fx: the shared test fixture (Fixture).
    """
    rep = fx.rep
    rows = [{"session_id": "sessA", "timestamp": "2026-01-01T09:00:00Z", "model": "claude-opus-5-5",
             "output_tokens": "100000"}, {"session_id": "sessB", "timestamp": "2026-01-01T09:30:00Z",
                                         "model": "claude-opus-5-5", "output_tokens": "50000"}]
    rows.append({**rows[1], "session_id": "sessD", "output_tokens": "40000"})  # $0.80, no /cost record
    costs = [{"session_id": s, "source": "main", "usd": "", "session_usd": u} for s, u in
             (("sessA", "2.5"), ("sessB", "1.5"), ("sessC", "0.5"))]  # ratios 1.25 and 1.5; sessC has no rows
    text = rep.limits_report(rows, costs, []).splitlines()
    fx.expect("report: best estimate: /cost where recorded (also with no rows), else $ x the median of an even count",
              [ln for ln in text if ln.startswith("best estimate")],
              ["best estimate, all weeks: 5.60 $ (/cost where recorded, else the hook's $ x 1.38, the median /cost "
               "ratio of 2 sessions)"])
    with tempfile.TemporaryDirectory() as d:
        core = types.SimpleNamespace(  # a stand-in for the token_log module
            __file__=os.path.join(d, "hooks", "token_log.py"), KIT_CONFIG="kit.config.json")
        with open(os.path.join(d, "kit.config.json"), "w", encoding="utf-8") as f:
            json.dump({"token_log_sources": ["https://h/a", "-x", 3, "https://h/b"]}, f)
        old_env = os.environ.pop("TOKEN_LOG_SOURCES", None)
        os.environ["TOKEN_LOG_SOURCES"] = "https://h/p https://h/a"
        try:
            fx.expect("sources: the variable first, then the repo's config; no repeats, no option, no non-text",
                      rep.sources(core, d), ["https://h/p", "https://h/a", "https://h/b"])
        finally:
            os.environ.pop("TOKEN_LOG_SOURCES")
            if old_env is not None:
                os.environ["TOKEN_LOG_SOURCES"] = old_env


def case_private_repo(fx):
    """The private log repo: rows go there when it can be reached; only when it cannot, to origin without costs/ and
    limits/ (with a push.log line); a refused push does not fall back; --report reads both places.

    Args:
        fx: the shared test fixture (Fixture).
    """
    private = os.path.join(fx.root, "private.git")
    fx.sh(fx.root, "git", "init", "-q", "--bare", "-b", "main", private)
    on = {"TOKEN_LOG_REPO": "file://" + private}
    t1, t2 = (os.path.join(fx.root, "proj", f"{s}.jsonl") for s in ("pv1", "pv2"))
    append(t1, prompt("2026-01-06T00:00:00Z"), msg("v1", "2026-01-06T00:00:01Z"))
    fx.hook(fx.work, "pv1", t1, fx.logs, extra=on)
    shown = subprocess.run(["git", "--git-dir", private, "show", "claude/token-usage:sessions/pv1.csv"],
                           capture_output=True, text=True, env=fx.env).stdout
    fx.expect("private log repo reachable: the rows go there, not to origin",
              ("v1" in shown, fx.remote_rows("pv1")), (True, None))
    append(t2, prompt("2026-01-06T01:00:00Z"), msg("v2", "2026-01-06T01:00:01Z"))
    write_record(fx, "pv2", record("pv2"))
    r = fx.hook(fx.work, "pv2", t2, fx.logs, extra={"TOKEN_LOG_REPO": "file://" + os.path.join(fx.root, "none.git")})
    fx.expect("private log repo not reachable: the rows go to origin, with a log line, without costs/ and limits/",
              ("private log repo not reachable" in r.stdout, len(fx.remote_rows("pv2") or []),
               remote(fx, "costs/pv2.csv"), remote(fx, "limits/pv2.csv")), (True, 1, None, None))
    ro = os.path.join(fx.root, "readonly.git")  # can be read, refuses every push (as with read-only access)
    fx.sh(fx.root, "git", "init", "-q", "--bare", "-b", "main", ro)
    with open(os.path.join(ro, "hooks", "pre-receive"), "w") as f:
        f.write("#!/bin/sh\necho read only >&2\nexit 1\n")
    os.chmod(os.path.join(ro, "hooks", "pre-receive"), 0o700)
    t3 = os.path.join(fx.root, "proj", "pv3.jsonl")
    append(t3, prompt("2026-01-06T02:00:00Z"), msg("v3", "2026-01-06T02:00:01Z"))
    r = fx.hook(fx.work, "pv3", t3, fx.logs, extra={"TOKEN_LOG_REPO": "file://" + ro})
    fx.expect("private log repo refuses the push: no fallback to origin (only not reachable falls back)",
              ("read only" in r.stdout, fx.remote_rows("pv3")), (True, None))
    odd = os.path.join(fx.root, "odd.git")  # only x/claude/token-usage there: an exact match finds no log branch
    fx.sh(fx.root, "git", "init", "-q", "--bare", "-b", "main", odd)
    empty = subprocess.run(["git", "--git-dir", odd, "mktree"], input="", capture_output=True, text=True).stdout.strip()
    tip = fx.sh(fx.root, "git", "--git-dir", odd, "-c", "user.name=t", "-c", "user.email=t@t", "commit-tree", empty,
                "-m", "x")
    fx.sh(fx.root, "git", "--git-dir", odd, "update-ref", "refs/heads/x/claude/token-usage", tip)
    t4 = os.path.join(fx.root, "proj", "pv4.jsonl")
    append(t4, prompt("2026-01-06T03:00:00Z"), msg("v4", "2026-01-06T03:00:01Z"))
    fx.hook(fx.work, "pv4", t4, fx.logs, extra={"TOKEN_LOG_REPO": "file://" + odd})
    fx.expect("a branch that only ends with the log branch name is not taken for it: the push makes the branch",
              "v4" in subprocess.run(["git", "--git-dir", odd, "show", "claude/token-usage:sessions/pv4.csv"],
                                     capture_output=True, text=True).stdout, True)
    t5 = os.path.join(fx.root, "proj", "pv5.jsonl")
    append(t5, '{"type": "assistant", "message": {"usage": {"input_tokens": 1}}}')  # a reply in an unknown form
    r = fx.hook(fx.work, "pv5", t5, fx.logs)
    fx.expect("a session log with replies that gives 0 rows: an ALARM line", "ALARM" in r.stdout, True)
    os.environ["TOKEN_LOG_REPO"] = "--upload-pack=touch x"
    fx.expect("an address that starts with '-' (a git option) is not used", fx.tl.log_repo(fx.tl.__file__), None)
    os.environ.pop("TOKEN_LOG_REPO")
    rep = subprocess.run([sys.executable, os.path.abspath(fx.tl.__file__), "--report"], cwd=fx.work, text=True,
                         capture_output=True, env={**fx.env, **on}, timeout=120)
    missing = [ln for ln in rep.stdout.splitlines() if ln.startswith("no /cost record")]
    fx.expect("--report: reads origin and the private log repo",
              (rep.returncode, bool(missing) and all(x in missing[0] for x in ("pv1", "pv2"))), (0, True))


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
                     case_skill_use, case_agent_type_bad_input, case_report, case_prices,
                     case_self_update, case_cost_files, case_bad_records, case_limit_split,
                     case_best_and_sources, case_private_repo):
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
