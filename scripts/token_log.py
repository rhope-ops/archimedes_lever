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

One row per API call. Columns: message_id, timestamp (UTC, of the reply), turn (prompts up to that time: user messages and
system wake-ups such as task notifications, not tool results or interrupt markers; total by turn for a chart), session_id, repo, model, source (main, subagent), agent (main; the subagent type of the Agent call, else unknown; empty for an old row whose log is gone), input_tokens,
cache_creation_input_tokens, cache_read_input_tokens, output_tokens.

Settings (environment): TOKEN_LOG=off turns it off; TOKEN_LOG_BRANCH (default claude/token-usage); TOKEN_LOG_SYNC=1
pushes in the foreground; TOKEN_LOG_HOME (default ~/.claude/token-log) holds push.log and the lock files;
TOKEN_LOG_NET_TIMEOUT (seconds, default 600) limits each ls-remote, fetch and push.

Manual push:  python3 scripts/token_log.py --push REPO_DIR SESSION_ID TRANSCRIPT_PATH
Self-test (temporary repos, no network):  python3 scripts/token_log.py --test
Standard library only.
Network: the git remote "origin" of the repo (fetch and push of the branch claude/token-usage); none in the self-test.
Writes: the branch claude/token-usage (one CSV file for each session), through a temporary index; push.log and lock
files in TOKEN_LOG_HOME; never the work tree.
Credentials: none itself; the push uses the credentials git already has for origin.
"""
import bisect
import csv
import fcntl
import glob
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

FIELDS = ["message_id", "timestamp", "turn", "session_id", "repo", "model", "source", "agent", "input_tokens",
          "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"]
USAGE_KEYS = FIELDS[-4:]
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


def prompt_text(d):
    """The text of a user prompt, or None (tool results, meta lines, compact summaries, interrupt markers).

    Args:
        d: one parsed line (a dict) of a session log.
    Returns:
        The prompt text, or None when the line is not a user prompt.
    """
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
    """Return ({message id: (timestamp, model, usage, source)}, [prompt timestamps]) for one log file.

    Args:
        path: the log file.
        source: "main" or "subagent": where the rows come from (only "main" counts prompts).
    Returns:
        (msgs, prompts): a dict of message id to (timestamp, model, usage, source), and the list of prompt timestamps.
    """
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
            if isinstance(mid, str) and mid and isinstance(u, dict):
                src = "subagent" if d.get("isSidechain") else source
                ts = msgs[mid][0] if mid in msgs else d.get("timestamp") or ""  # the first block's time
                msgs[mid] = (ts, m.get("model") or "unknown", u, src)  # the last block's usage (final counts)
    return msgs, prompts


def agent_types(tpath):
    """The subagent type of each Agent call in the session log, by agent id. A call whose type or id is not found
    is left out (the row then says "unknown").

    Args:
        tpath: the path of the session's log file.
    Returns:
        A dict of agent id to subagent type (for example "scout").
    """
    calls, types = {}, {}
    try:
        f = open(tpath, encoding="utf-8")
    except OSError:
        return types
    with f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            c = d.get("message", {}).get("content") if isinstance(d, dict) and isinstance(d.get("message"), dict) else None
            for b in c if isinstance(c, list) else []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task") and isinstance(b.get("input"), dict):
                    t = b["input"].get("subagent_type")
                    if isinstance(b.get("id"), str):
                        calls[b["id"]] = t if isinstance(t, str) and t else "unknown"
                if b.get("type") == "tool_result" and isinstance(d.get("toolUseResult"), dict):
                    aid, tid = d["toolUseResult"].get("agentId"), b.get("tool_use_id")
                    if isinstance(aid, str) and aid and isinstance(tid, str) and tid in calls:
                        types[aid] = calls[tid]
    return types


def tokens(v):
    """A token count as int(v), or 0 when int() rejects v (non-numeric text, NaN or an infinite number); the row is kept.

    Args:
        v: the usage value from the log.
    Returns:
        int(v), or 0 when int() raises TypeError, ValueError or OverflowError.
    """
    try:
        return int(v or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def log_rows(sid, tpath, repo):
    """One row per API call in the session log and its subagent logs.

    Args:
        sid: the session id.
        tpath: the path of the session's log file.
        repo: the repo name.
    Returns:
        A dict of message id to the row (a dict with the FIELDS).
    """
    msgs, prompts = read_log(tpath, "main")
    types = agent_types(tpath)
    agent = {mid: "main" if src == "main" else "unknown" for mid, (_, _, _, src) in msgs.items()}
    for p in sorted(glob.glob(os.path.join(os.path.splitext(tpath)[0], "**", "*.jsonl"), recursive=True)):
        name = os.path.basename(p)
        aid = name[len("agent-"):-len(".jsonl")] if name.startswith("agent-") else ""
        for k, v in read_log(p, "subagent")[0].items():
            if k not in msgs:
                msgs[k] = v
                agent[k] = types.get(aid, "unknown")
    prompts.sort()
    rows = {}
    for mid, (ts, model, u, src) in msgs.items():
        rows[mid] = {"message_id": mid, "timestamp": ts, "turn": bisect.bisect_right(prompts, ts) if ts else len(prompts),
                     "session_id": sid, "repo": repo, "model": model, "source": src, "agent": agent[mid],
                     **{k: tokens(u.get(k)) for k in USAGE_KEYS}}
    return rows


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


def self_test():
    """Run the self-test in scripts/token_log_test.py on this module (temporary repos, no network)."""
    import token_log_test  # scripts/token_log_test.py: kept apart so each case stays short (rule C3)
    return token_log_test.run(sys.modules[__name__])


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
