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
     1 and 5 minutes, so the last turn of a session is not lost to one failure; a race is tried again at once.

One row per API call. Columns: message_id, timestamp (UTC, of the reply), turn (prompts up to that time: user messages and
system wake-ups such as task notifications, not tool results or interrupt markers; total by turn for a chart), session_id, repo, model, source (main, subagent), input_tokens,
cache_creation_input_tokens, cache_read_input_tokens, output_tokens.

Settings (environment): TOKEN_LOG=off turns it off; TOKEN_LOG_BRANCH (default claude/token-usage); TOKEN_LOG_SYNC=1
pushes in the foreground; TOKEN_LOG_HOME (default ~/.claude/token-log) holds push.log and the lock files.

Manual push:  python3 scripts/token_log.py --push REPO_DIR SESSION_ID TRANSCRIPT_PATH
Self-test (temporary repos, no network):  python3 scripts/token_log.py --test
Standard library only.
"""
import bisect
import csv
import fcntl
import glob
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

FIELDS = ["message_id", "timestamp", "turn", "session_id", "repo", "model", "source", "input_tokens",
          "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"]
USAGE_KEYS = FIELDS[-4:]
PRIVATE_REF = "refs/token-log/remote"
NOT_PROMPTS = ("[Request interrupted",)
RETRY_DELAYS = (0, 60, 300)  # seconds before each push try: the last turn of a session gets more than one chance
NET_TIMEOUT = 600  # seconds for a fetch or a push (the pre-push hook runs the check lane)
RACE = ("non-fast-forward", "fetch first", "stale info", "cannot lock ref")


def home():
    return os.environ.get("TOKEN_LOG_HOME") or os.path.expanduser("~/.claude/token-log")


def branch_name():
    return os.environ.get("TOKEN_LOG_BRANCH") or "claude/token-usage"


def git(cwd, *args, env=None, check=True, timeout=None):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args[0]}: {r.stderr.strip()}")
    return r.stdout.strip() if r.returncode == 0 else ""


def prompt_text(d):
    """The text of a user prompt, or None (tool results, meta lines, compact summaries, interrupt markers)."""
    if d.get("type") != "user" or d.get("isMeta") or d.get("isCompactSummary") or not isinstance(d.get("message"), dict):
        return None
    c = d["message"].get("content")
    if isinstance(c, list):
        if any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
            return None
        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    if not isinstance(c, str) or not c.strip() or c.lstrip().startswith(NOT_PROMPTS):
        return None
    return c


def read_log(path, source):
    """Return ({message id: (timestamp, model, usage, source)}, [prompt timestamps]) for one log file."""
    msgs, prompts = {}, []
    try:
        f = open(path, encoding="utf-8")
    except OSError:
        return msgs, prompts
    with f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if source == "main" and prompt_text(d) is not None:
                prompts.append(d.get("timestamp") or "")
            m = d.get("message")
            if d.get("type") != "assistant" or not isinstance(m, dict):
                continue
            mid, u = m.get("id"), m.get("usage")
            if mid and isinstance(u, dict):
                src = "subagent" if d.get("isSidechain") else source
                ts = msgs[mid][0] if mid in msgs else d.get("timestamp") or ""  # the first block's time
                msgs[mid] = (ts, m.get("model") or "unknown", u, src)  # the last block's usage (final counts)
    return msgs, prompts


def log_rows(sid, tpath, repo):
    """One row per API call in the session log and its subagent logs."""
    msgs, prompts = read_log(tpath, "main")
    for p in sorted(glob.glob(os.path.join(os.path.splitext(tpath)[0], "**", "*.jsonl"), recursive=True)):
        msgs.update({k: v for k, v in read_log(p, "subagent")[0].items() if k not in msgs})
    prompts.sort()
    rows = {}
    for mid, (ts, model, u, src) in msgs.items():
        rows[mid] = {"message_id": mid, "timestamp": ts, "turn": bisect.bisect_right(prompts, ts) if ts else len(prompts),
                     "session_id": sid, "repo": repo, "model": model, "source": src,
                     **{k: int(u.get(k) or 0) for k in USAGE_KEYS}}
    return rows


def to_csv(rows):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in sorted(rows.values(), key=lambda r: (r["timestamp"], r["message_id"])):
        w.writerow({k: r.get(k, "") for k in FIELDS})
    return out.getvalue()


def push(root, sid, tpath):
    """Merge this session's rows into sessions/<sid>.csv on the log branch and push. Retries once on a race."""
    ref, path = branch_name(), f"sessions/{sid}.csv"
    os.makedirs(home(), exist_ok=True)
    with open(os.path.join(home(), sid + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # one push per session at a time; a waiting one pushes the newest rows
        for attempt in (1, 2):
            heads = subprocess.run(["git", "-C", root, "ls-remote", "--heads", "origin", ref],
                                   capture_output=True, text=True, timeout=NET_TIMEOUT)
            if heads.returncode != 0:
                raise RuntimeError("ls-remote: " + heads.stderr.strip())
            parent, rows = [], {}
            if heads.stdout.strip():
                shallow = git(root, "rev-parse", "--is-shallow-repository") == "true"
                git(root, "fetch", "-q", "--no-write-fetch-head", *(["--depth", "1"] if shallow else []), "origin",
                    f"+refs/heads/{ref}:{PRIVATE_REF}", timeout=NET_TIMEOUT)
                parent = [git(root, "rev-parse", PRIVATE_REF)]
                old = git(root, "show", f"{parent[0]}:{path}", check=False)
                rows = {r["message_id"]: r for r in csv.DictReader(io.StringIO(old)) if r.get("message_id")}
            rows.update(log_rows(sid, tpath, os.path.basename(root)))
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
            r = subprocess.run(["git", "-C", root, "push", "-q", "origin", f"{commit}:refs/heads/{ref}"],
                               capture_output=True, text=True, timeout=NET_TIMEOUT)
            if r.returncode == 0:
                git(root, "update-ref", PRIVATE_REF, commit)
                return f"pushed {commit[:7]} ({len(rows)} rows)"
            err = (r.stderr.strip() or r.stdout.strip())[-500:]
            if attempt == 2 or not any(x in err for x in RACE):  # only a race with another push is tried at once
                raise RuntimeError("push: " + err)
    return "not pushed"


def push_main(args, delays=RETRY_DELAYS):
    """Push, and try again later when it fails (the lock is free while it waits)."""
    for i, delay in enumerate(delays):
        time.sleep(delay)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            print(stamp, args[1], push(*args), flush=True)
            return True
        except Exception as e:
            print(stamp, args[1], f"try {i + 1} of {len(delays)} error:", e, flush=True)
    return False


def hook_main():
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


def self_test():
    import shutil
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and not k.startswith("TOKEN_LOG")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", TOKEN_LOG_SYNC="1")
    env.pop("CLAUDE_PROJECT_DIR", None)
    root = tempfile.mkdtemp(prefix="token_log_test_")
    fails = 0

    def sh(cwd, *args):
        return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, check=True).stdout.strip()

    def hook(cwd, sid, tpath, logdir, stdin=None, extra=None):
        data = stdin if stdin is not None else json.dumps({"session_id": sid, "transcript_path": tpath, "cwd": cwd})
        return subprocess.run([sys.executable, os.path.abspath(__file__)], input=data, capture_output=True,
                              text=True, env={**env, "TOKEN_LOG_HOME": logdir, **(extra or {})})

    def expect(name, got, want):
        nonlocal fails
        ok = got == want
        fails += not ok
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f": got {got!r}, want {want!r}"))

    def msg(mid, ts, model="claude-test", side=False, n=1):
        u = {"input_tokens": n, "cache_creation_input_tokens": 10 * n, "cache_read_input_tokens": 100 * n,
             "output_tokens": 1000 * n}
        return json.dumps({"type": "assistant", "timestamp": ts, "isSidechain": side,
                           "message": {"id": mid, "model": model, "usage": u}})

    def prompt(ts, text="hi"):
        return json.dumps({"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}})

    def tool_result(ts):
        return json.dumps({"type": "user", "timestamp": ts, "message": {"content": [{"type": "tool_result", "content": "x"}]}})

    def remote_rows(sid):
        r = subprocess.run(["git", "--git-dir", origin, "show", f"claude/token-usage:sessions/{sid}.csv"],
                           capture_output=True, text=True, env=env)
        return list(csv.DictReader(io.StringIO(r.stdout))) if r.returncode == 0 else None

    def append(path, *lines):
        with open(path, "a") as f:
            f.write("\n".join(lines) + "\n")

    def state(repo):
        return (sh(repo, "git", "status", "--porcelain"), sh(repo, "git", "rev-parse", "HEAD"),
                sh(repo, "git", "branch", "--show-current"), sh(repo, "git", "rev-parse", "--is-shallow-repository"))

    try:
        origin = os.path.join(root, "origin.git")
        work, other = os.path.join(root, "work"), os.path.join(root, "other")
        sh(root, "git", "init", "-q", "--bare", "-b", "main", origin)
        sh(root, "git", "clone", "-q", origin, work)
        append(os.path.join(work, "a.txt"), "a")
        sh(work, "git", "add", "a.txt")
        sh(work, "git", "commit", "-q", "-m", "init")
        sh(work, "git", "push", "-q", "origin", "HEAD:main")
        append(os.path.join(work, "a.txt"), "work in progress")  # an uncommitted change that must stay as it is
        sh(work, "git", "add", "a.txt")
        before = state(work)
        logs, t1 = os.path.join(root, "logs"), os.path.join(root, "proj", "s1.jsonl")
        os.makedirs(os.path.dirname(t1))
        append(t1, prompt("2026-01-01T00:00:00Z"), msg("m1", "2026-01-01T00:00:01Z"), msg("m1", "2026-01-01T00:00:02Z"),
               tool_result("2026-01-01T00:00:03Z"), msg("m2", "2026-01-01T00:00:04Z"), "not json")

        r = hook(root, "s1", t1, logs)
        expect("outside a repo: exit 0, nothing pushed", (r.returncode, remote_rows("s1")), (0, None))

        hook(work, "s1", t1, logs)
        got = remote_rows("s1") or []
        expect("turn 1: one row per API call (a reply repeated per block counts once)",
               [(x["message_id"], x["turn"], x["output_tokens"], x["timestamp"]) for x in got],
               [("m1", "1", "1000", "2026-01-01T00:00:01Z"), ("m2", "1", "1000", "2026-01-01T00:00:04Z")])
        expect("turn 1: work tree, index, HEAD, branch and shallow state unchanged", state(work), before)

        tip = sh(root, "git", "--git-dir", origin, "rev-parse", "claude/token-usage")
        hook(work, "s1", t1, logs)
        expect("no new calls: no new commit", sh(root, "git", "--git-dir", origin, "rev-parse", "claude/token-usage"), tip)

        sh(root, "git", "clone", "-q", origin, other)  # a second session in another clone pushes first
        t2 = os.path.join(root, "proj", "s2.jsonl")
        append(t2, prompt("2026-01-01T01:00:00Z"), msg("x1", "2026-01-01T01:00:01Z"))
        hook(other, "s2", t2, os.path.join(root, "logs2"))
        append(t1, prompt("2026-01-01T02:00:00Z", "[Request interrupted by user]"), prompt("2026-01-01T02:00:01Z"),
               msg("m3", "2026-01-01T02:00:02Z", n=2))
        os.makedirs(os.path.join(root, "proj", "s1", "subagents"))
        append(os.path.join(root, "proj", "s1", "subagents", "agent-a.jsonl"),
               msg("sa1", "2026-01-01T02:00:03Z", model="claude-small", side=True, n=3))
        hook(work, "s1", t1, logs)
        got = remote_rows("s1") or []
        expect("turn 2: new main and subagent calls; an interrupt marker is not a turn",
               [(x["message_id"], x["turn"], x["model"], x["source"]) for x in got[2:]],
               [("m3", "2", "claude-test", "main"), ("sa1", "2", "claude-small", "subagent")])
        expect("another session's file stays on the branch", len(remote_rows("s2") or []), 1)
        expect("turn 2: work tree, index, HEAD, branch and shallow state unchanged", state(work), before)

        hooks = os.path.join(root, "hooks")
        os.makedirs(hooks)
        with open(os.path.join(hooks, "pre-push"), "w") as f:
            f.write("#!/bin/sh\necho blocked >&2\nexit 1\n")
        os.chmod(os.path.join(hooks, "pre-push"), 0o755)
        sh(work, "git", "config", "core.hooksPath", hooks)
        append(t1, msg("m4", "2026-01-01T02:00:05Z"))
        r = hook(work, "s1", t1, logs)
        expect("pre-push hook blocks: exit 0, nothing pushed", (r.returncode, len(remote_rows("s1") or [])), (0, 4))
        os.remove(os.path.join(hooks, "pre-push"))
        shutil.rmtree(logs)  # a new container: the local folder is gone
        hook(work, "s1", t1, logs)
        got = remote_rows("s1") or []
        expect("next push (local folder lost): carries the waiting call, no row twice",
               sorted(x["message_id"] for x in got), ["m1", "m2", "m3", "m4", "sa1"])

        sh(root, "git", "clone", "-q", "--depth", "1", "file://" + origin, os.path.join(root, "shallow"))
        sh(os.path.join(root, "shallow"), "git", "config", "core.hooksPath", hooks)
        append(t1, msg("m5", "2026-01-01T02:00:06Z"))
        hook(os.path.join(root, "shallow"), "s1", t1, logs)
        expect("shallow clone: pushes", len(remote_rows("s1") or []), 6)

        calls, real_push = [], globals()["push"]
        def flaky(*a):
            calls.append(a)
            if len(calls) == 1:
                raise RuntimeError("blocked")
            return "pushed"
        globals()["push"] = flaky
        try:
            ok = push_main(["r", "s", "t"], delays=(0, 0, 0))
        finally:
            globals()["push"] = real_push
        expect("a failed push is tried again, then stops", (ok, len(calls)), (True, 2))

        expect("bad input: exit 0", hook(work, "s1", t1, logs, stdin="not json").returncode, 0)
        expect("session id with a slash: ignored", hook(work, "../x", t1, logs).returncode, 0)
        append(t1, msg("m6", "2026-01-01T02:00:07Z"))
        hook(work, "s1", t1, logs, extra={"TOKEN_LOG": "off"})
        expect("TOKEN_LOG=off: nothing pushed", len(remote_rows("s1") or []), 6)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("TOKEN LOG SELF-TEST " + ("PASS" if not fails else f"FAIL ({fails})"))
    return 1 if fails else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--test"]:
        sys.exit(self_test())
    if sys.argv[1:2] == ["--push"] and len(sys.argv) == 5:
        push_main(sys.argv[2:])
        sys.exit(0)
    try:
        hook_main()
    except Exception as e:  # never fail the turn
        print(f"token_log: {e}", file=sys.stderr)
    sys.exit(0)
