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
self-update off; TOKEN_LOG_KIT_URL (default KIT_URL) is the repo the self-update clones.

Manual push:  python3 scripts/token_log.py --push REPO_DIR SESSION_ID TRANSCRIPT_PATH
Report:  python3 scripts/token_log.py --report [REF]  (in a repo: fetches the log branch, or reads REF; prints the
  estimated cost by week in America/Chicago, by source, agent and model, and per subagent task, from PRICES)
Self-update: after each background push, the installed copy (only a token_log.py in ~/.claude/hooks) checks the
  kit's main branch at most once a day and replaces itself with a newer copy whose self-test passes (TOKEN_LOG_UPDATE=off
  turns it off). The setup script installs it only when a container is built, so a resumed container kept an old copy.
Self-test (temporary repos, no network):  python3 scripts/token_log.py --test.  Standard library only.
Network: the git remote "origin" of the repo (fetch and push of the branch claude/token-usage); the self-update: a
shallow clone of KIT_URL at most once a day; none in the self-test.
Writes: the branch claude/token-usage (one CSV file for each session), through a temporary index; push.log, lock
files and update.stamp in TOKEN_LOG_HOME; the installed hook file (self-update); never the work tree.
Credentials: none itself; the push uses the credentials git already has for origin.
"""
import bisect
import csv
import fcntl
import glob
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timezone

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


def price_facts(u):
    """The price columns (cache_write_1h_tokens, speed, web_search_requests, inference_geo) of one usage dict."""
    cc, st = [u.get(k) if isinstance(u.get(k), dict) else {} for k in ("cache_creation", "server_tool_use")]
    return {"cache_write_1h_tokens": tokens(cc.get("ephemeral_1h_input_tokens")), "speed": str(u.get("speed") or ""),
            "web_search_requests": tokens(st.get("web_search_requests")), "inference_geo": str(u.get("inference_geo") or "")}


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
    agent_id = {}
    for p in sorted(glob.glob(os.path.join(os.path.splitext(tpath)[0], "**", "*.jsonl"), recursive=True)):
        name = os.path.basename(p)
        aid = name[len("agent-"):-len(".jsonl")] if name.startswith("agent-") else ""
        for k, v in read_log(p, "subagent")[0].items():
            if k not in msgs:
                msgs[k] = v
                agent[k], agent_id[k] = types.get(aid, "unknown"), aid
    prompts.sort()
    rows = {}
    for mid, (ts, model, u, src) in msgs.items():
        rows[mid] = {"message_id": mid, "timestamp": ts, "turn": bisect.bisect_right(prompts, ts) if ts else len(prompts),
                     "session_id": sid, "repo": repo, "model": model, "source": src, "agent": agent[mid],
                     "agent_id": agent_id.get(mid, ""),
                     **{k: tokens(u.get(k)) for k in USAGE_KEYS}, **price_facts(u)}
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


KIT_URL = "https://github.com/rhope-ops/archimedes_lever"
UPDATE_EVERY = 24 * 3600  # seconds between self-update checks
# Prices in USD per million tokens: (input, output, cache read, inference_geo "us" applies). A cache write costs 1.25 x
# input (5-minute) or 2 x input (1-hour). Source: https://platform.claude.com/docs/en/about-claude/pricing (fetched
# 2026-11-23). Longest matching model id prefix wins. The weekly usage limit is assumed to weigh tokens like these prices.
# Assumptions (no price listed): a fast-mode cache read costs read x fast input / base input; US 1.1x not on web search.
PRICES_AS_OF = "2026-11-23"
PRICES = {
    "claude-fable-5-2": (8, 40, 0.20, 1), "claude-fable-5-1": (10, 50, 0.25, 1), "claude-fable-5": (10, 50, 1, 1),
    "claude-opus-5-5": (4, 20, 0.20, 1), "claude-opus-5": (5, 25, 0.50, 1), "claude-opus-4-8": (5, 25, 0.50, 1),
    "claude-opus-4-7": (5, 25, 0.50, 1), "claude-opus-4-6": (5, 25, 0.50, 1), "claude-opus-4-5": (5, 25, 0.50, 0),
    "claude-opus-4-1": (15, 75, 1.50, 0), "claude-opus-4": (15, 75, 1.50, 0),  # Opus 4 and 4.1 (retired)
    "claude-sonnet-5-5": (2, 10, 0.10, 1), "claude-sonnet-5": (2, 10, 0.20, 1), "claude-sonnet-4-6": (3, 15, 0.30, 1),
    "claude-sonnet-4-5": (3, 15, 0.30, 0), "claude-sonnet-4": (3, 15, 0.30, 0), "claude-haiku-4-5": (1, 5, 0.10, 0),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 1),
}
FAST_PRICES = {"claude-fable-5-2": (16, 80), "claude-opus-5-5": (8, 40), "claude-opus-5": (10, 50), "claude-opus-4-8": (10, 50)}  # speed fast
LONG_PROMPT, LONG_PRICES = 100_000, {"claude-haiku-5-5": (0.50, 2.50, 0.05)}  # prompt over 100,000: (input, output, read)
WEB_SEARCH_USD, GEO_US_FACTOR = 10.0 / 1000, 1.1  # per search; US factor: token categories only


def self_update(path, url=None, now=None):
    """Replace the installed hook file with the kit's main copy when it differs and its self-test passes; at most
    once a day.

    Args:
        path: the installed token_log.py to replace.
        url: the kit repo to clone (default TOKEN_LOG_KIT_URL, else KIT_URL).
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
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", "main", url or os.environ.get("TOKEN_LOG_KIT_URL") or KIT_URL,
                            os.path.join(tmp, "k")], capture_output=True, text=True, timeout=net_timeout())
        new = os.path.join(tmp, "k", "scripts", "token_log.py")
        if r.returncode != 0 or not os.path.isfile(new):
            return "not updated: " + (r.stderr.strip()[-200:] or "no scripts/token_log.py")
        with open(new, "rb") as f, open(path, "rb") as g:
            if f.read() == g.read():
                return "up to date"
        # The new copy must pass its own self-test (temporary repos, no network): a copy that fails when run would
        # break every later Stop, and then no later update could repair it.
        t = subprocess.run([sys.executable, "-E", "-s", new, "--test"], cwd=os.path.dirname(new), capture_output=True,
                           text=True, timeout=600, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        if t.returncode != 0:
            return "not updated: self-test failed " + (t.stdout + t.stderr).strip()[-200:]
        shutil.copyfile(new, path + ".new")
        os.replace(path + ".new", path)
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


def row_cost(r):
    """The estimated cost of one row in USD, or None for a model with no price and no web search.

    Args:
        r: a row (a dict with the FIELDS; token counts as text or int).
    Returns:
        The cost as a float (only the web search fee for a model with no token price), or None.
    """
    key = max((k for k in PRICES if (r.get("model") or "").startswith(k)), key=len, default=None)
    search = tokens(r.get("web_search_requests")) * WEB_SEARCH_USD
    if key is None:
        return search or None
    inp, out, read, geo = PRICES[key]
    n, write = [tokens(r.get(k)) for k in USAGE_KEYS], tokens(r.get("cache_creation_input_tokens"))
    if key in LONG_PRICES and sum(n[:3]) > LONG_PROMPT:
        inp, out, read = LONG_PRICES[key]
    if r.get("speed") == "fast" and key in FAST_PRICES:
        read, (inp, out) = read * FAST_PRICES[key][0] / inp, FAST_PRICES[key]
    w1h = min(max(tokens(r.get("cache_write_1h_tokens")), 0), write)  # an old row has none: all writes are 5-minute
    cost = (n[0] * inp + (write - w1h) * inp * 1.25 + w1h * inp * 2 + n[2] * read + n[3] * out) / 1e6
    return cost * (GEO_US_FACTOR if geo and r.get("inference_geo") == "us" else 1) + search


def week_of(ts, tz="America/Chicago"):
    """The Monday (YYYY-MM-DD) of the week of a UTC timestamp in the time zone, or "unknown"."""
    from zoneinfo import ZoneInfo
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(ZoneInfo(tz))
    except (ValueError, TypeError):
        return "unknown"
    return date.fromordinal(d.toordinal() - d.weekday()).isoformat()


def report(rows):
    """The report text: estimated cost by week, by source, agent and model, and per subagent task.

    Args:
        rows: a list of rows (dicts with the FIELDS).
    Returns:
        The report as text, one table per part.
    """
    week, group, task, unpriced, old = {}, {}, {}, set(), 0
    for r in rows:
        if row_cost({**r, "web_search_requests": 0}) is None:  # no token price; its web searches still count
            unpriced.add(r.get("model") or "unknown")
        old += r.get("cache_write_1h_tokens") in (None, "")  # a row from before the column
        c = row_cost(r) or 0.0
        w = week.setdefault(week_of(r.get("timestamp")), [0, 0.0, 0.0])
        w[0] += 1
        w[1 if r.get("source") == "main" else 2] += c
        g = group.setdefault((r.get("source") or "", r.get("agent") or "", r.get("model") or ""), [0, 0, 0, 0, 0, 0.0])
        for i, x in enumerate([1, *(tokens(r.get(k)) for k in USAGE_KEYS), c]):  # calls, the 4 token counts, cost
            g[i] += x
        if r.get("agent_id"):
            t = task.setdefault(r.get("agent") or "unknown", {}).setdefault(r["agent_id"], [0, 0.0])
            t[0], t[1] = t[0] + 1, t[1] + c
    out = [f"Estimated cost in USD (prices as of {PRICES_AS_OF}; a proxy for the weekly usage limit)", "",
           "week (America/Chicago, Monday)  calls  main $  subagent $  total $"]
    out += [f"{k:<31} {v[0]:>5} {v[1]:>7.2f} {v[2]:>11.2f} {v[1] + v[2]:>8.2f}" for k, v in sorted(week.items())]
    out += ["", "source    agent              model                  calls       input  cache write   cache read"
                "      output   cost $"]
    out += [f"{s:<9} {a:<18} {m:<22} {v[0]:>5} {v[1]:>11} {v[2]:>12} {v[3]:>12} {v[4]:>11} {v[5]:>8.2f}"
            for (s, a, m), v in sorted(group.items(), key=lambda kv: -kv[1][5])]
    out += ["", "subagent tasks: agent  tasks  calls/task  $/task  total $"]
    for a, ts in sorted(task.items()):
        n, calls, cost = len(ts), sum(t[0] for t in ts.values()), sum(t[1] for t in ts.values())
        out.append(f"{a:<22} {n:>6} {calls / n:>11.1f} {cost / n:>7.3f} {cost:>8.2f}")
    if unpriced:
        out += ["", "no token price (tokens counted as 0, web searches counted): " + ", ".join(sorted(unpriced))]
    out += ["", f"Rows from before the cache_write_1h_tokens column ({old}): cache writes priced as 5-minute."] if old else []
    return "\n".join(out)


def report_rows(root, ref):
    """Every row in sessions/*.csv at a git ref.

    Args:
        root: the repo folder.
        ref: the git ref that holds the log branch's files.
    Returns:
        A list of rows (dicts).
    """
    rows = []
    for f in git(root, "ls-tree", "-r", "--name-only", ref, "sessions/").splitlines():
        if f.endswith(".csv"):
            rows += list(csv.DictReader(io.StringIO(git(root, "show", f"{ref}:{f}"))))
    return rows


def report_main(args):
    """Print the report for the repo in the current folder: fetch the log branch, or read the ref in args.

    Args:
        args: the arguments after --report: [] or [REF].
    Returns:
        The exit code: 0, or 1 when the repo or the branch cannot be read.
    """
    root = git(os.getcwd(), "rev-parse", "--show-toplevel", check=False)
    if not root:
        print("token_log --report: not in a git repo", file=sys.stderr)
        return 1
    ref = args[0] if args else "refs/token-log/report"
    if not args:
        rc, _, err = git_net(root, "fetch", "-q", "--no-write-fetch-head", "origin",
                             f"+refs/heads/{branch_name()}:{ref}")
        if rc != 0:
            print("token_log --report: fetch: " + err, file=sys.stderr)
            return 1
    try:
        print(report(report_rows(root, ref)))
    except RuntimeError as e:
        print(f"token_log --report: {e}", file=sys.stderr)
        return 1
    return 0


def self_test():
    """Run the self-test in scripts/token_log_test.py on this module (temporary repos, no network)."""
    import token_log_test  # scripts/token_log_test.py: kept apart so each case stays short (rule C3)
    return token_log_test.run(sys.modules[__name__])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--test"]:
        sys.exit(self_test())
    if sys.argv[1:2] == ["--report"] and len(sys.argv) <= 3:
        sys.exit(report_main(sys.argv[2:]))
    if sys.argv[1:2] == ["--push"] and len(sys.argv) == 5:
        push_main(sys.argv[2:])
        update_main()
        sys.exit(0)
    try:
        hook_main()
    except Exception as e:  # never fail the turn
        print(f"token_log: {e}", file=sys.stderr)
    sys.exit(0)
