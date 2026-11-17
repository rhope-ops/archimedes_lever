#!/usr/bin/env python3
"""Claude Code Stop hook: log each turn's token use to the branch claude/token-usage of the session's repo.

Kit only: projects do not get a copy. A cloud environment's setup script installs it from the kit's main branch
as a user-level Stop hook, so every repo session is logged (the owner, 2026-11-17).

At each Stop:
  1. Outside a git repo it does nothing (sessions with no repo are not logged).
  2. Reads the session log and its subagent logs (<session>/**/*.jsonl) and counts each API response once: the log
     repeats the same usage on every content block of one message id. Message ids already logged are skipped, so
     an interrupted turn goes into the next row, never twice and never lost.
  3. Appends one row per model and source (main, subagent) to a local CSV, the full record of the session.
  4. Starts a background push (the end of the turn does not wait): it fetches claude/token-usage, writes
     sessions/<session id>.csv into a new commit with a temporary index, and pushes it through the normal pre-push
     hook. The work tree, the index and the current branch never change. A failed push leaves the rows in the local
     CSV; the next push carries them.

Columns: timestamp (UTC, the end of the turn), session_id, turn (user prompts so far), prompt_at (UTC), repo, branch,
model, source, api_calls, input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens.

Settings (environment): TOKEN_LOG=off turns it off; TOKEN_LOG_HOME is the local folder (default ~/.claude/token-log,
which also holds push.log); TOKEN_LOG_BRANCH (default claude/token-usage); TOKEN_LOG_SYNC=1 pushes in the foreground.
Errors never fail the turn: the hook always exits 0.

Manual push:  python3 scripts/token_log.py --push REPO_DIR SESSION_ID
Self-test (temporary repos, no network):  python3 scripts/token_log.py --test
Standard library only.
"""
import csv
import fcntl
import glob
import io
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

FIELDS = ["timestamp", "session_id", "turn", "prompt_at", "repo", "branch", "model", "source", "api_calls",
          "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"]
USAGE_KEYS = FIELDS[-4:]


def home():
    return os.environ.get("TOKEN_LOG_HOME") or os.path.expanduser("~/.claude/token-log")


def branch_name():
    return os.environ.get("TOKEN_LOG_BRANCH") or "claude/token-usage"


def git(cwd, *args, env=None, check=True):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args[0]}: {r.stderr.strip()}")
    return r.stdout.strip() if r.returncode == 0 else ""


def is_prompt(d):
    """A user prompt (not a tool result, a meta line or a compact summary)."""
    if d.get("type") != "user" or d.get("isMeta") or d.get("isCompactSummary"):
        return False
    c = (d.get("message") or {}).get("content") if isinstance(d.get("message"), dict) else None
    if isinstance(c, str):
        return bool(c.strip())
    return isinstance(c, list) and not any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c)


def read_log(path, source):
    """Return ({message id: (model, usage, source)}, prompt count, last prompt time) for one log file."""
    msgs, prompts, prompt_at = {}, 0, ""
    try:
        f = open(path, encoding="utf-8")
    except OSError:
        return msgs, prompts, prompt_at
    with f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if is_prompt(d):
                prompts, prompt_at = prompts + 1, d.get("timestamp") or ""
            m = d.get("message")
            if d.get("type") != "assistant" or not isinstance(m, dict):
                continue
            mid, u = m.get("id"), m.get("usage")
            if mid and isinstance(u, dict):
                msgs[mid] = (m.get("model") or "unknown", u, "subagent" if d.get("isSidechain") else source)
    return msgs, prompts, prompt_at


def log_turn(hook):
    """Append this turn's rows to the local CSV. Returns (repo root, session id), or None when nothing to push."""
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or hook.get("cwd") or os.getcwd()
    root = git(cwd, "rev-parse", "--show-toplevel", check=False)
    sid, tpath = hook.get("session_id"), hook.get("transcript_path")
    if not root or not sid or not tpath:
        return None
    os.makedirs(home(), exist_ok=True)
    state_path = os.path.join(home(), sid + ".json")
    try:
        with open(state_path) as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {"logged": []}
    logged = set(state["logged"])

    msgs, prompts, prompt_at = read_log(tpath, "main")
    for p in sorted(glob.glob(os.path.join(os.path.splitext(tpath)[0], "**", "*.jsonl"), recursive=True)):
        msgs.update(read_log(p, "subagent")[0])
    totals = {}
    for mid, (model, u, src) in msgs.items():
        if mid in logged:
            continue
        t = totals.setdefault((model, src), {"api_calls": 0, **{k: 0 for k in USAGE_KEYS}})
        t["api_calls"] += 1
        for k in USAGE_KEYS:
            t[k] += int(u.get(k) or 0)
    if not totals:
        return None

    out = os.path.join(home(), sid + ".csv")
    new_file = not os.path.exists(out)
    base = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "session_id": sid, "turn": prompts, "prompt_at": prompt_at, "repo": os.path.basename(root),
            "branch": git(root, "branch", "--show-current", check=False)}
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for (model, src), t in sorted(totals.items()):
            w.writerow({**base, "model": model, "source": src, **t})
    state["logged"] = sorted(logged | set(msgs))
    tmp = state_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, state_path)
    return root, sid


def push(root, sid):
    """Commit the local CSV as sessions/<sid>.csv on the log branch and push it. Retries once on a race."""
    src = os.path.join(home(), sid + ".csv")
    if not os.path.exists(src):
        return "nothing to push"
    ref = branch_name()
    with open(os.path.join(home(), sid + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # one push at a time; a waiting one pushes the newest rows
        for attempt in (1, 2):
            heads = subprocess.run(["git", "-C", root, "ls-remote", "--heads", "origin", ref],
                                   capture_output=True, text=True)
            if heads.returncode != 0:
                raise RuntimeError("ls-remote: " + heads.stderr.strip())
            parent = []
            if heads.stdout.strip():
                git(root, "fetch", "-q", "--depth", "1", "origin", ref)
                parent = [git(root, "rev-parse", "FETCH_HEAD")]
            blob = git(root, "hash-object", "-w", src)
            with tempfile.TemporaryDirectory() as tmp:
                env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}
                git(root, "read-tree", *(parent or ["--empty"]), env=env)
                git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},sessions/{sid}.csv", env=env)
                tree = git(root, "write-tree", env=env)
            if parent and git(root, "rev-parse", parent[0] + "^{tree}") == tree:
                return "up to date"
            args = sum((["-p", p] for p in parent), [])
            commit = git(root, "commit-tree", tree, *args, "-m", f"token log: session {sid}")
            r = subprocess.run(["git", "-C", root, "push", "-q", "origin", f"{commit}:refs/heads/{ref}"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                git(root, "update-ref", "refs/heads/" + ref, commit)
                return "pushed " + commit[:7]
            if attempt == 2:
                raise RuntimeError("push: " + (r.stderr.strip() or r.stdout.strip())[-500:])
    return "not pushed"


def start_push(root, sid):
    if os.environ.get("TOKEN_LOG_SYNC") == "1":
        print(push(root, sid), file=sys.stderr)
        return
    logf = open(os.path.join(home(), "push.log"), "a")
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "--push", root, sid], stdin=subprocess.DEVNULL,
                     stdout=logf, stderr=logf, start_new_session=True)


def hook_main():
    if os.environ.get("TOKEN_LOG", "").lower() == "off":
        return
    hook = json.load(sys.stdin)
    if not isinstance(hook, dict):
        return
    found = log_turn(hook)
    if found:
        start_push(*found)


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

    def hook(cwd, sid, tpath, logdir, stdin=None):
        data = stdin if stdin is not None else json.dumps({"session_id": sid, "transcript_path": tpath, "cwd": cwd})
        return subprocess.run([sys.executable, os.path.abspath(__file__)], input=data, capture_output=True,
                              text=True, env={**env, "TOKEN_LOG_HOME": logdir})

    def expect(name, got, want):
        nonlocal fails
        ok = got == want
        fails += not ok
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f": got {got!r}, want {want!r}"))

    def msg(mid, model="claude-test", side=False, n=1):
        u = {"input_tokens": n, "cache_creation_input_tokens": 10 * n, "cache_read_input_tokens": 100 * n,
             "output_tokens": 1000 * n}
        return json.dumps({"type": "assistant", "isSidechain": side, "message": {"id": mid, "model": model, "usage": u}})

    def prompt(ts):
        return json.dumps({"type": "user", "timestamp": ts, "message": {"role": "user", "content": "hi"}})

    def tool_result():
        return json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]}})

    def remote_csv(sid):
        r = subprocess.run(["git", "--git-dir", origin, "show", f"claude/token-usage:sessions/{sid}.csv"],
                           capture_output=True, text=True, env=env)
        return r.stdout if r.returncode == 0 else None

    def rows(text):
        return list(csv.DictReader(io.StringIO(text or "")))

    try:
        origin = os.path.join(root, "origin.git")
        work, other = os.path.join(root, "work"), os.path.join(root, "other")
        sh(root, "git", "init", "-q", "--bare", "-b", "main", origin)
        sh(root, "git", "clone", "-q", origin, work)
        with open(os.path.join(work, "a.txt"), "w") as f:
            f.write("a\n")
        sh(work, "git", "add", "a.txt")
        sh(work, "git", "commit", "-q", "-m", "init")
        sh(work, "git", "push", "-q", "origin", "HEAD:main")
        with open(os.path.join(work, "a.txt"), "a") as f:
            f.write("work in progress\n")  # an uncommitted change that must stay as it is
        sh(work, "git", "add", "a.txt")
        before = (sh(work, "git", "status", "--porcelain"), sh(work, "git", "rev-parse", "HEAD"),
                  sh(work, "git", "branch", "--show-current"))
        logs, t1 = os.path.join(root, "logs"), os.path.join(root, "proj", "s1.jsonl")
        os.makedirs(os.path.dirname(t1))
        with open(t1, "w") as f:
            f.write("\n".join([prompt("2026-01-01T00:00:00Z"), msg("m1"), msg("m1"), tool_result(), msg("m2"),
                               "not json"]) + "\n")

        r = hook(root, "s1", t1, logs)
        expect("outside a repo: exit 0, nothing written", (r.returncode, os.path.exists(logs)), (0, False))

        r = hook(work, "s1", t1, logs)
        got = rows(remote_csv("s1"))
        expect("turn 1: one row pushed to claude/token-usage", len(got), 1)
        expect("turn 1: a message repeated per block counts once",
               [got[0][k] for k in ("api_calls", "output_tokens", "turn", "source")] if got else None,
               ["2", "2000", "1", "main"])
        expect("turn 1: work tree, index, HEAD and branch unchanged",
               (sh(work, "git", "status", "--porcelain"), sh(work, "git", "rev-parse", "HEAD"),
                sh(work, "git", "branch", "--show-current")), before)
        expect("turn 1: local CSV equals the pushed file", open(os.path.join(logs, "s1.csv")).read(), remote_csv("s1"))

        tip = sh(root, "git", "--git-dir", origin, "rev-parse", "claude/token-usage")
        hook(work, "s1", t1, logs)
        expect("no new messages: no new row and no new commit",
               (len(rows(remote_csv("s1"))), sh(root, "git", "--git-dir", origin, "rev-parse", "claude/token-usage")),
               (1, tip))

        sh(root, "git", "clone", "-q", origin, other)  # a second session in another clone pushes first
        t2 = os.path.join(root, "proj", "s2.jsonl")
        with open(t2, "w") as f:
            f.write("\n".join([prompt("2026-01-01T01:00:00Z"), msg("x1")]) + "\n")
        hook(other, "s2", t2, os.path.join(root, "logs2"))
        with open(t1, "a") as f:
            f.write("\n".join([prompt("2026-01-01T02:00:00Z"), msg("m3", n=2)]) + "\n")
        os.makedirs(os.path.join(root, "proj", "s1", "subagents"))
        with open(os.path.join(root, "proj", "s1", "subagents", "agent-a.jsonl"), "w") as f:
            f.write(msg("sa1", model="claude-small", side=True, n=3) + "\n")
        r = hook(work, "s1", t1, logs)
        got = rows(remote_csv("s1"))
        expect("turn 2: one row per model and source",
               [(x["turn"], x["model"], x["source"], x["output_tokens"]) for x in got[1:]],
               [("2", "claude-small", "subagent", "3000"), ("2", "claude-test", "main", "2000")])
        expect("another session's file stays on the branch", len(rows(remote_csv("s2"))), 1)
        expect("turn 2: work tree, index, HEAD and branch unchanged",
               (sh(work, "git", "status", "--porcelain"), sh(work, "git", "rev-parse", "HEAD"),
                sh(work, "git", "branch", "--show-current")), before)

        with open(t1, "a") as f:
            f.write(msg("m4") + "\n")
        os.rename(origin, origin + ".gone")  # the push fails: the row waits in the local CSV
        r = hook(work, "s1", t1, logs)
        os.rename(origin + ".gone", origin)
        expect("failed push: exit 0", r.returncode, 0)
        expect("failed push: row kept locally", len(rows(open(os.path.join(logs, "s1.csv")).read())), 4)
        subprocess.run([sys.executable, os.path.abspath(__file__), "--push", work, "s1"], env={**env,
                       "TOKEN_LOG_HOME": logs}, capture_output=True, text=True)
        expect("next push carries the waiting row", len(rows(remote_csv("s1"))), 4)

        expect("bad input: exit 0", hook(work, "s1", t1, logs, stdin="not json").returncode, 0)
        r = subprocess.run([sys.executable, os.path.abspath(__file__)], input=json.dumps(
            {"session_id": "s3", "transcript_path": t1, "cwd": work}), capture_output=True, text=True,
            env={**env, "TOKEN_LOG_HOME": logs, "TOKEN_LOG": "off"})
        expect("TOKEN_LOG=off: nothing written", os.path.exists(os.path.join(logs, "s3.csv")), False)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("TOKEN LOG SELF-TEST " + ("PASS" if not fails else f"FAIL ({fails})"))
    return 1 if fails else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--test"]:
        sys.exit(self_test())
    if sys.argv[1:2] == ["--push"] and len(sys.argv) == 4:
        try:
            print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sys.argv[3], push(sys.argv[2], sys.argv[3]))
        except Exception as e:
            print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sys.argv[3], "error:", e)
        sys.exit(0)
    try:
        hook_main()
    except Exception as e:  # never fail the turn
        print(f"token_log: {e}", file=sys.stderr)
    sys.exit(0)
