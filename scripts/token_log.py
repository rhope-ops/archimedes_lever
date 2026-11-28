#!/usr/bin/env python3
"""Claude Code Stop hook: log the token use of each API call to the branch claude/token-usage of the private log repo
(else of the session's repo).

Kit only: projects do not get a copy. A cloud environment's setup script installs it from the kit's newest release
tag as a user-level Stop hook, so every repo session is logged (the Administrator, 2026-11-17).

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
     current branch never change. In a full clone a push of only this branch skips the check lanes (log_only); a
     block by its content check holds the push back, and the rows wait in the session log. A failed push is tried
     again after 1 and 5 minutes, so the last turn of a session is not lost to one failure (only while the
     container still runs); a race is tried again at once. Pushes are coalesced: at most one runs and one waits
     per session. A fetch or push with no answer in time (TOKEN_LOG_NET_TIMEOUT) is killed with its pre-push hook.

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
  release tag (vN.N.N, never main) at most once a day and replaces its files (UPDATE_FILES) with newer copies whose self-test passes
  (TOKEN_LOG_UPDATE=off turns it off). The setup script installs it only when a container is built, so a resumed container kept an old copy.
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
import bisect
import csv
import fcntl
import glob
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
from datetime import date, datetime, timedelta, timezone

PRIVATE_REF = "refs/token-log/remote"
RETRY_DELAYS = (0, 60, 300)  # seconds before each push try: the last turn of a session gets more than one chance
RACE = ("non-fast-forward", "fetch first", "stale info", "cannot lock ref")

# ---------------------------------------------------------------- rows and CSV ---------------------------------------

FIELDS = ["message_id", "timestamp", "turn", "session_id", "repo", "model", "source", "agent", "agent_id",
          "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens", "cache_write_1h_tokens",
          "speed", "web_search_requests", "inference_geo", "skill_use"]
USAGE_KEYS = FIELDS[9:13]  # the four token counts that the report sums
NOT_PROMPTS = ("[Request interrupted",)

# A skill's name is the folder after skills/; skills/ must start a path part (not "myskills/").
SKILL_PATH = re.compile(r"(?:^|(?<=[/\s\"']))skills/([A-Za-z0-9_.-]+)/SKILL\.md")
SLICE_COMMANDS = ("grep", "sed", "head", "tail", "cat", "awk")  # shell commands that read part of a file
SIMPLE_COMMANDS = re.compile(r";|&&|\|\||\||\n")  # the split between simple commands (no \s* around it: linear on long runs of spaces)
ENV_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")  # NAME=value before the command word
SHELL_WORDS = ("do", "then", "else", "if", "while", "!", "(", "{", "time", "sudo")  # words before the command word

# The /cost and /usage record of the agents-pane mod: <TOKEN_LOG_HOME>/cost/<session id>.json, version 1.
COST_FIELDS = ["session_id", "written_at", "source", "agent_id", "type", "model", "status", "usd", "input", "output",
               "cache_read", "cache_write", "started_at", "ended_at", "session_usd"]
LIMIT_FIELDS = ["session_id", "read_at", "window", "percent_used", "resets_at"]
COST_TOKENS = ("input", "output", "cache_read", "cache_write")


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


def sliced_skills(command):
    """The skills whose SKILL.md a shell command reads with grep, sed, head, tail, cat or awk. The command word and
    the path must be in the same simple command (split on ; && || | and new lines).

    Args:
        command: the shell command text.
    Returns:
        A sorted list of skill names, each one time.
    """
    names = set()
    for part in SIMPLE_COMMANDS.split(command):
        words = part.split()
        while words and (words[0] in SHELL_WORDS or ENV_ASSIGNMENT.match(words[0])):
            words.pop(0)
        if words and os.path.basename(words[0]) in SLICE_COMMANDS:
            names.update(SKILL_PATH.findall(part))
    return sorted(names)


def _block_skills(block, seen):
    """Return [(skill name, kind)] for one tool_use block, deduping by block id in seen.

    Args:
        block: one parsed content block dict from a transcript message.
        seen: set of already counted tool_use block ids, mutated in place.

    Returns:
        List of (skill_name, kind) pairs.
    """
    if not isinstance(block, dict) or block.get("type") != "tool_use":
        return []
    key = block.get("id")
    if isinstance(key, str) and key:
        if key in seen:
            return []
        seen.add(key)
    inp = block.get("input") if isinstance(block.get("input"), dict) else {}
    if block.get("name") == "Skill" and isinstance(inp.get("skill"), str) and inp["skill"]:
        return [(inp["skill"], "skill_tool")]
    if block.get("name") == "Read":
        return [(n, "read") for n in SKILL_PATH.findall(str(inp.get("file_path") or ""))]
    if block.get("name") == "Bash":
        return [(n, "slice") for n in sliced_skills(str(inp.get("command") or ""))]
    return []


def skill_calls(tpath):
    """Count the skill use in one log file, by the reply (message id) that made each call. A tool_use block counts
    one time (its id), though the log repeats a reply on each content block; a block with no usable id counts each
    time. A line or block of an unexpected type is skipped, as in read_log. The SKILL.md path rule is the one of
    scripts/skill_use.py (a self-test keeps SKILL_PATH equal to its SKILL_FILE); this file counts only the shell
    commands of SLICE_COMMANDS, skill_use.py every shell command that names a SKILL.md.

    Args:
        tpath: the path of a log file.
    Returns:
        A dict of message id to {skill name: {"skill_tool": n, "read": n, "slice": n}}; a count of 0 is left out.
        "skill_tool" is a call of the Skill tool, "read" a Read of a SKILL.md file, "slice" a shell command with
        grep, sed, head, tail, cat or awk on a SKILL.md path (counted once for each skill file it names).
    """
    found, seen = {}, set()
    try:
        f = open(tpath, encoding="utf-8")
    except OSError:
        return found
    with f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("type") != "assistant" or not isinstance(d.get("message"), dict):
                continue
            m = d["message"]
            c = m.get("content")
            if not isinstance(m.get("id"), str) or not isinstance(c, list):
                continue
            for b in c:
                for name, kind in _block_skills(b, seen):
                    per = found.setdefault(m["id"], {}).setdefault(name, {})
                    per[kind] = per.get(kind, 0) + 1
    return found


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
    agent_id, skills = {}, skill_calls(tpath)
    for p in sorted(glob.glob(os.path.join(os.path.splitext(tpath)[0], "**", "*.jsonl"), recursive=True)):
        name = os.path.basename(p)
        aid = name[len("agent-"):-len(".jsonl")] if name.startswith("agent-") else ""
        sub = skill_calls(p)
        for k, v in read_log(p, "subagent")[0].items():
            if k not in msgs:
                msgs[k] = v
                agent[k], agent_id[k] = types.get(aid, "unknown"), aid
                if k in sub:
                    skills[k] = sub[k]
    prompts.sort()
    rows = {}
    for mid, (ts, model, u, src) in msgs.items():
        rows[mid] = {"message_id": mid, "timestamp": ts, "turn": bisect.bisect_right(prompts, ts) if ts else len(prompts),
                     "session_id": sid, "repo": repo, "model": model, "source": src, "agent": agent[mid],
                     "agent_id": agent_id.get(mid, ""),
                     "skill_use": json.dumps(skills[mid], sort_keys=True, separators=(",", ":")) if mid in skills else "",
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


def read_cost_record(path, sid):
    """The agents-pane record of this session, or None when there is no file.

    Args:
        path: the record file (<TOKEN_LOG_HOME>/cost/<session id>.json).
        sid: the session id the record must name.
    Returns:
        The record (a dict), or None when the file does not exist. Raises ValueError with the reason when the file
        does not parse, is not version 1, names another session, or has a part of the wrong type.
    """
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return None
    rec = json.loads(text)  # a ValueError when it does not parse (for example a half-written file)
    if not isinstance(rec, dict) or rec.get("version") != 1 or isinstance(rec.get("version"), bool):
        raise ValueError("not a version 1 record")
    if rec.get("session_id") != sid:
        raise ValueError("the record names another session")
    if not isinstance(rec.get("main"), dict) or not isinstance(rec.get("subagents", []), list) \
            or not isinstance(rec.get("limits", []), list):
        raise ValueError("main, subagents or limits has the wrong type")
    return rec


def cell(v):
    """A CSV cell: a number or a text as itself, anything else (None, a list, a dict, a bool) empty."""
    return v if isinstance(v, (int, float, str)) and not isinstance(v, bool) else ""


def csv_text(fields, rows):
    """The CSV text of a list of row dicts, header first."""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows({k: r.get(k, "") for k in fields} for r in rows)
    return out.getvalue()


def cost_csv(rec):
    """The costs/<session id>.csv snapshot of a record: one main row, then one row per subagent.

    Args:
        rec: a record from read_cost_record().
    Returns:
        The CSV text.
    """
    base = {"session_id": rec["session_id"], "written_at": cell(rec.get("written_at")),
            "session_usd": cell(rec.get("session_usd"))}
    m = rec["main"]
    rows = [{**base, "source": "main", "usd": cell(rec.get("main_usd")), **{k: cell(m.get(k)) for k in COST_TOKENS}}]
    for a in rec.get("subagents", []):
        if isinstance(a, dict):
            rows.append({**base, "source": "subagent", **{k: cell(a.get(k)) for k in COST_FIELDS[3:14]}})
    return csv_text(COST_FIELDS, rows)


def has_zone(ts):
    """True when ts is an ISO time with a time zone (UTC "Z" or an offset)."""
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).tzinfo is not None if isinstance(ts, str) else False
    except ValueError:
        return False


def limits_csv(rec, old):
    """The limits/<session id>.csv series: the rows already on the branch plus this record's readings, one row per
    (read_at, window); an earlier row is kept as it is.

    Args:
        rec: a record from read_cost_record().
        old: the CSV text of the file on the branch ("" when there is none).
    Returns:
        The CSV text, sorted by read_at and window, or "" when there is no row.
    """
    rows = {(r.get("read_at"), r.get("window")): r for r in csv.DictReader(io.StringIO(old))}
    at = rec.get("limits_read_at")
    for x in rec.get("limits", []) if has_zone(at) else []:  # a time with no zone cannot be placed: skipped
        p = x.get("percent_used") if isinstance(x, dict) else None
        if isinstance(p, (int, float)) and not isinstance(p, bool) and 0 <= p <= 100 \
                and isinstance(x.get("window"), str):  # NaN, text and values outside 0-100 are skipped
            rows.setdefault((at, x["window"]), {"session_id": rec["session_id"], "read_at": at, "window": x["window"],
                                                "percent_used": x["percent_used"], "resets_at": cell(x.get("resets_at"))})
    return csv_text(LIMIT_FIELDS, [rows[k] for k in sorted(rows, key=lambda k: (str(k[0]), str(k[1])))]) if rows else ""


# ---------------------------------------------------------------- hook and push --------------------------------------

def net_timeout():
    """Seconds for ls-remote, fetch or push: TOKEN_LOG_NET_TIMEOUT, else 600 (also for a value that is not a whole
    number of at least 1)."""
    try:
        v = int(os.environ.get("TOKEN_LOG_NET_TIMEOUT", ""))
    except ValueError:
        return 600
    return v if v >= 1 else 600


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
        except subprocess.TimeoutExpired as exc:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            raise RuntimeError(f"git {args[0]}: no answer in {net_timeout()} s") from exc
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
        rec = read_cost_record(os.path.join(home(), "cost", sid + ".json"), sid)
        if rec is None:
            return {}
        old = git(root, "show", f"{parent[0]}:limits/{sid}.csv", check=False) if parent else ""
        if not old and parent and git(root, "ls-tree", "--name-only", parent[0], f"limits/{sid}.csv", check=False):
            raise RuntimeError("the limits file on the branch cannot be read")  # never rewrite it without its rows
        limits = limits_csv(rec, old)
        return {f"costs/{sid}.csv": cost_csv(rec), **({f"limits/{sid}.csv": limits} if limits else {})}
    except Exception as e:  # a bad record never stops the rows push
        print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sid, "cost record skipped:", e, flush=True)
        return {}


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
        got = log_rows(sid, tpath, os.path.basename(root))
        if not got and has_replies(tpath):
            print(datetime.now(timezone.utc).isoformat(timespec="seconds"), sid, "ALARM: the session log has replies "
                  "but gave 0 rows (did its format change?)", flush=True)
        rows.update(got)
        if not rows:
            return "nothing to log"
        extra = cost_files(root, parent, sid) if costs else {}
        tree = write_tree(root, parent, {path: to_csv(rows), **extra})
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
UPDATE_FILES = ("token_log.py",)  # the installed files


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
    refs = [ln.split("\t", 1)[-1] for ln in r.stdout.splitlines() if r.returncode == 0]
    tags = [x[10:] for x in refs if x.startswith("refs/tags/") and re.fullmatch(r"v\d+\.\d+\.\d+", x[10:])]
    return max(tags, key=lambda t: tuple(int(x) for x in t[1:].split(".")), default=None)


def _fetch_release_checkout(tmp, url, tag):
    """Clone the kit release tag into tmp/k and return (returncode, stderr, src_dir)."""
    k = os.path.join(tmp, "k")  # the tag's full ref, not clone --branch: that takes a branch of the same name
    for args in (["init", "-q", k], ["-C", k, "fetch", "-q", "--depth", "1", url, "refs/tags/" + tag],
                 ["-C", k, "checkout", "-q", "FETCH_HEAD"]):
        r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=net_timeout(),
                           env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if r.returncode != 0:
            break
    return r.returncode, r.stderr, os.path.join(tmp, "k", "scripts")


def self_update(path, url=None, now=None):
    """Replace the installed hook file with the copy of the kit's newest release tag (release_tag()) when it differs
    and its self-test passes; at most once a day. Never main: only a release the Administrator tagged reaches every
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
        rc, err, src = _fetch_release_checkout(tmp, url, tag)
        names = [n for n in UPDATE_FILES if os.path.isfile(os.path.join(src, n))]
        if rc != 0 or "token_log.py" not in names:
            return "not updated: " + (err.strip()[-200:] or "no scripts/token_log.py")
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
        for n in names:
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


# ---------------------------------------------------------------- report and pricing ---------------------------------

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
WINDOW_HOURS = {"five_hour": 5, "seven_day": 7 * 24}  # the length of each plan-limit window


def row_cost(r):
    """The estimated cost of one row in USD, or None for a model with no price and no web search.

    Args:
        r: a row (a dict with FIELDS; token counts as text or int).
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


def fill_1h(rows):
    """Give each row from before the cache_write_1h_tokens column an estimate of it: its cache writes times the 1-hour
    share of the cache writes in the newer rows of the same source (main or subagent; 0 when there are none).

    Args:
        rows: a list of rows (dicts with FIELDS).
    Returns:
        (the rows, old ones replaced by copies with the estimate; {source: share}; the number of old rows).
    """
    write, hour = {}, {}
    for r in rows:
        if r.get("cache_write_1h_tokens") not in (None, ""):
            s = r.get("source") or ""
            write[s] = write.get(s, 0) + tokens(r.get("cache_creation_input_tokens"))
            hour[s] = hour.get(s, 0) + tokens(r.get("cache_write_1h_tokens"))
    share = {s: min(hour[s] / w, 1.0) for s, w in write.items() if w > 0}
    out, old = [], 0
    for r in rows:
        if r.get("cache_write_1h_tokens") in (None, ""):
            old += 1
            r = {**r, "cache_write_1h_tokens": str(int(tokens(r.get("cache_creation_input_tokens"))
                                                        * share.get(r.get("source") or "", 0.0)))}
        out.append(r)
    return out, share, old


def report(rows):
    """The report text: estimated cost by week, by repo, by source, agent and model, and per subagent task.

    Args:
        rows: a list of rows (dicts with FIELDS).
    Returns:
        The report as text, one table per part.
    """
    rows, share, old = fill_1h(rows)
    week, repo, group, task, unpriced = {}, {}, {}, {}, set()
    for r in rows:
        if row_cost({**r, "web_search_requests": 0}) is None:  # no token price; its web searches still count
            unpriced.add(r.get("model") or "unknown")
        c = row_cost(r) or 0.0
        w = week.setdefault(week_of(r.get("timestamp")), [0, 0.0, 0.0])
        w[0] += 1
        w[1 if r.get("source") == "main" else 2] += c
        p = repo.setdefault((r.get("repo") or "unknown").lower(), [0, 0.0])  # one repo, whatever its letter case
        p[0], p[1] = p[0] + 1, p[1] + c
        g = group.setdefault((r.get("source") or "", r.get("agent") or "", r.get("model") or ""), [0, 0, 0, 0, 0, 0.0])
        for i, x in enumerate([1, *(tokens(r.get(k)) for k in USAGE_KEYS), c]):  # calls, the 4 token counts, cost
            g[i] += x
        if r.get("agent_id"):
            t = task.setdefault(r.get("agent") or "unknown", {}).setdefault(r["agent_id"], [0, 0.0])
            t[0], t[1] = t[0] + 1, t[1] + c
    out = [f"Estimated cost in USD (prices as of {PRICES_AS_OF}; a proxy for the weekly usage limit)", "",
           "week (America/Chicago, Monday)  calls  main $  subagent $  total $"]
    out += [f"{k:<31} {v[0]:>5} {v[1]:>7.2f} {v[2]:>11.2f} {v[1] + v[2]:>8.2f}" for k, v in sorted(week.items())]
    out += ["", "repo (letter case ignored)       calls  total $"]
    out += [f"{k:<31} {v[0]:>5} {v[1]:>8.2f}" for k, v in sorted(repo.items(), key=lambda kv: -kv[1][1])]
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
    est = ", ".join(f"{k} {v:.0%}" for k, v in sorted(share.items())) or "none: priced as 5-minute"
    out += ["", f"Rows from before the cache_write_1h_tokens column ({old}): 1-hour share of their cache writes "
            f"estimated from the newer rows of the same source: {est}."] if old else []
    return "\n".join(out)


def report_rows(hook, root, ref, folder="sessions"):
    """Every row in <folder>/*.csv at a git ref.

    Args:
        hook: the token_log module (its git helper).
        root: the repo folder.
        ref: the git ref that holds the log branch's files.
        folder: sessions, costs or limits.
    Returns:
        A list of rows (dicts).
    """
    rows = []
    for f in hook.git(root, "ls-tree", "-r", "--name-only", ref, folder + "/").splitlines():
        if f.endswith(".csv"):
            rows += list(csv.DictReader(io.StringIO(hook.git(root, "show", f"{ref}:{f}"))))
    return rows


def sources(core, root):
    """The other repos whose log branch --report also reads: TOKEN_LOG_SOURCES (URLs separated by spaces; for repos
    whose names stay out of the kit, such as private ones), then "token_log_sources" of the kit.config.json next to the
    hook file, else of the repo's root. Read only: a fetch into a local ref, never a push.

    Args:
        core: the token_log module.
        root: the repo folder.
    Returns:
        The URLs, without repeats; a value that starts with "-" (a git option) is left out.
    """
    got = os.environ.get("TOKEN_LOG_SOURCES", "").split()
    for folder in (os.path.dirname(os.path.abspath(core.__file__)), root):
        try:
            with open(os.path.join(folder, core.KIT_CONFIG), encoding="utf-8") as f:
                listed = json.load(f).get("token_log_sources")
        except (OSError, ValueError, AttributeError):
            continue
        got += listed if isinstance(listed, list) else []
        break
    return list(dict.fromkeys(u for u in got if isinstance(u, str) and u.strip() and not u.startswith("-")))


def fetch_refs(core, root):
    """Fetch the log branch from the repo's origin, the private log repo (core.log_repo()) and each of sources(),
    each into its own ref. One that cannot be fetched (no branch there, or no access) is left out with a note on
    stderr, and a last stderr line counts the branches read, so a gap in the report is never silent.

    Args:
        core: the token_log module (its git helpers and settings).
        root: the repo folder.
    Returns:
        The refs that were fetched.
    """
    named = ["refs/token-log/report", "refs/token-log/report-private"]
    remotes = ["origin", core.log_repo(core.__file__), *sources(core, root)]
    refs = []
    for i, remote in enumerate(remotes):
        if not remote:
            continue
        ref = named[i] if i < len(named) else f"refs/token-log/report-source-{i - len(named)}"
        rc, _, err = core.git_net(root, "fetch", "-q", "--no-write-fetch-head", remote,
                                  f"+refs/heads/{core.branch_name()}:{ref}")
        if rc == 0:
            refs.append(ref)
        else:
            name, why = remote.rstrip("/").rsplit("/", 1)[-1], re.sub(r"\S+://\S+", "<url>", err)  # a URL: a token?
            print(f"token_log --report: not read: {name}: " + " / ".join(why.splitlines()[-3:]), file=sys.stderr)
    print(f"token_log --report: log branches read: {len(refs)} of {sum(map(bool, remotes))}", file=sys.stderr)
    return refs


def report_main(args):
    """Print the report for the repo in the current folder: fetch the log branch from origin and from the private log
    repo and merge them, or read the ref in args.

    Args:
        args: the arguments after --report: [] or [REF].
    Returns:
        The exit code: 0, or 1 when the repo or no log branch can be read.
    """
    core = sys.modules[__name__]
    root = core.git(os.getcwd(), "rev-parse", "--show-toplevel", check=False)
    if not root:
        print("token_log --report: not in a git repo", file=sys.stderr)
        return 1
    refs = args[:1] or fetch_refs(core, root)
    if not refs:
        print("token_log --report: no log branch could be read", file=sys.stderr)
        return 1
    try:
        got = {f: [r for ref in refs for r in report_rows(core, root, ref, f)] for f in ("sessions", "costs", "limits")}
    except RuntimeError as e:
        print(f"token_log --report: {e}", file=sys.stderr)
        return 1
    rows = list({r.get("message_id"): r for r in got["sessions"]}.values())  # a row in both places counts once
    newest = sorted(got["costs"], key=lambda r: r.get("written_at") or "")  # the newest snapshot of a session wins
    costs = list({(r.get("session_id"), r.get("source"), r.get("agent_id")): r for r in newest}.values())
    print(report(rows) + "\n\n" + limits_report(fill_1h(rows)[0], costs, got["limits"]))
    return 0


def parse_ts(ts):
    """An ISO time (UTC "Z" or an offset) as an aware datetime, or None."""
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return d if d.tzinfo else None


def local(d):
    """A datetime as "YYYY-MM-DD HH:MM" in America/Chicago."""
    from zoneinfo import ZoneInfo
    return d.astimezone(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M")


def readings(limits):
    """The account's plan-limit readings from every session's limits rows, one per (read_at, window).

    Args:
        limits: rows of limits/*.csv (dicts with LIMIT_FIELDS).
    Returns:
        {window: [(read time, percent used, resets_at in UTC to the minute or ""), ...] sorted by time}.
    """
    seen, out = set(), {}
    for r in limits:
        t, key = parse_ts(r.get("read_at")), (r.get("read_at"), r.get("window"))
        try:
            pct = float(r.get("percent_used"))
        except (TypeError, ValueError):
            continue
        if t is None or key in seen:
            continue
        seen.add(key)
        reset = parse_ts(r.get("resets_at"))  # to the minute, in UTC: one key per window period
        out.setdefault(r.get("window") or "", []).append((t, pct, reset.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%MZ") if reset else ""))
    return {w: sorted(v) for w, v in out.items()}


def periods(series, hours):
    """Mark the period of each reading of one window. A new period starts only when the reset time moves forward by
    at least half a window (an hour for a window of unknown length): a missing reset time, or one that moves by a
    minute, stays in the period before it, so no use is counted twice.

    Args:
        series: [(read time, percent used, resets_at)] of one window, sorted by time.
        hours: the window length in hours, or None.
    Returns:
        [(read time, percent used, period key, start of a new period: bool)]; the key is the period's first known
        resets_at ("" while none is known).
    """
    out, key, cur = [], "", None
    for t, pct, reset in series:
        r = parse_ts(reset)
        new = not out or (r is not None and cur is not None and r - cur >= timedelta(hours=(hours or 2) / 2))
        if r is not None and (new or cur is None):
            key, cur = reset, r
        out.append((t, pct, key, new))
    return out


def split_rises(series, hours, spend):
    """Split each rise of one window's percent used among the sessions, by their estimated $ in that time.

    Args:
        series: [(read time, percent used, resets_at)] of one window, sorted by time.
        hours: the window length in hours, or None (no known start: the first reading of a period is not split).
        spend: [(time, session id, estimated $)] of the logged rows, sorted by time.
    Returns:
        {period key: {session id or "(not attributed)": percent points}}; a fall is never split.
    """
    times, out, prev = [x[0] for x in spend], {}, None
    for t, pct, key, new in periods(series, hours):
        if new:  # a new period starts at 0 % at its window start
            start = parse_ts(key) - timedelta(hours=hours) if parse_ts(key) and hours else None
            base = (max(start, prev[0]) if prev and start else start, 0.0)
        else:
            base = prev
        prev = (t, pct)
        if base[0] is None or pct <= base[1]:
            continue
        share, rise = {}, pct - base[1]
        for _, sid, usd in spend[bisect.bisect_right(times, base[0]):bisect.bisect_right(times, t)]:
            share[sid] = share.get(sid, 0.0) + usd
        got, total = out.setdefault(key, {}), sum(share.values())
        for sid, usd in share.items() if total > 0 else [("(not attributed)", 1.0)]:
            got[sid] = got.get(sid, 0.0) + rise * usd / (total or 1.0)
    return out


def num(v):
    """A CSV cell as a float, or None when it is empty or not a number."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cost_per_session(costs):
    """Claude Code's /cost total of each session from costs/*.csv: session_usd; else, when the main row has a usd
    figure, the sum of the usd cells; else None (no total: a subagent-only sum is not the session's total).

    Args:
        costs: rows of costs/*.csv (dicts with COST_FIELDS).
    Returns:
        {session id: USD, or None for a record with no total}.
    """
    total, parts, main = {}, {}, set()
    for r in costs:
        sid, usd = r.get("session_id") or "", num(r.get("usd"))
        if r.get("source") == "main" and num(r.get("session_usd")) is not None:
            total[sid] = num(r.get("session_usd"))
        if r.get("source") == "main" and usd is not None:
            main.add(sid)
        parts[sid] = parts.get(sid, 0.0) + (usd or 0.0)
    return {sid: total[sid] if sid in total else parts[sid] if sid in main else None for sid in parts}


def cost_by_week(rows, costs):
    """The lines of "Claude Code /cost by week": the /cost total next to the hook's estimate, per week of a
    session's first row, and the sessions that have no /cost record.

    Args:
        rows: rows of sessions/*.csv.
        costs: rows of costs/*.csv.
    Returns:
        A list of report lines.
    """
    first, est, cc = {}, {}, cost_per_session(costs)
    for r in rows:
        sid = r.get("session_id") or ""
        first[sid] = min(first.get(sid, r.get("timestamp") or ""), r.get("timestamp") or "")
        est[sid] = est.get(sid, 0.0) + (row_cost(r) or 0.0)
    week = {}
    for sid in est:
        w = week.setdefault(week_of(first[sid]), [0, 0, 0.0, 0.0, 0.0])
        has = cc.get(sid) is not None
        w[0], w[1] = w[0] + 1, w[1] + has
        w[2 if has else 4] += est[sid]
        w[3] += cc[sid] if has else 0.0
    out = ["Claude Code /cost by week (sessions with a record: /cost $ next to the hook's estimate for the same sessions)",
           "week (Monday)  sessions  with /cost  hook $ (same)  /cost $  hook $ (no record)"]
    out += [f"{k:<14} {v[0]:>8} {v[1]:>10} {v[2]:>13.2f} {v[3]:>8.2f} {v[4]:>19.2f}" for k, v in sorted(week.items())]
    ratios = sorted(cc[sid] / est[sid] for sid in est if cc.get(sid) is not None and est[sid] > 0)
    if ratios:  # /cost also counts calls that are not in the session logs (seen 2026-11-25: up to 56 % more)
        k = (ratios[(len(ratios) - 1) // 2] + ratios[len(ratios) // 2]) / 2  # the median
        best = sum(v for v in cc.values() if v is not None) + sum(est[s] * k for s in est if cc.get(s) is None)
        out.append(f"best estimate, all weeks: {best:.2f} $ (/cost where recorded, else the hook's $ x {k:.2f}, "
                   f"the median /cost ratio of {len(ratios)} sessions)")
    missing = sorted(sid for sid in est if cc.get(sid) is None)
    if missing:
        out.append(f"no /cost record ({len(missing)}): " + ", ".join(m[:8] for m in missing[:20])
                   + (" ..." if len(missing) > 20 else ""))
    return out


def limits_report(rows, costs, limits):
    """The plan-limit and /cost parts of the report.

    Args:
        rows: rows of sessions/*.csv.
        costs: rows of costs/*.csv.
        limits: rows of limits/*.csv.
    Returns:
        The text of the three parts.
    """
    read = readings(limits)
    out = ["Plan limits (/usage, for the whole account): highest percent used of each 7-day window",
           "window resets (America/Chicago)  highest %  seen at           readings"]
    week = periods(read.get("seven_day", []), WINDOW_HOURS["seven_day"])
    for reset in sorted({x[2] for x in week}):
        top = max((x for x in week if x[2] == reset), key=lambda x: (x[1], x[0]))
        n = sum(1 for x in week if x[2] == reset)
        when = local(parse_ts(reset)) if parse_ts(reset) else "unknown"
        out.append(f"{when:<32} {top[1]:>9.1f}  {local(top[0])} {n:>8}")
    spend = sorted((parse_ts(r.get("timestamp")), r.get("session_id") or "", row_cost(r) or 0.0) for r in rows
                   if parse_ts(r.get("timestamp")))
    out += ["", "Limit used per session (estimate): each rise of a window's percent used, split among the sessions "
            "logged on this branch by their estimated $ in that time; other use of the account shows as not attributed",
            "window      resets (America/Chicago)  session   points"]
    for window, series in sorted(read.items()):
        for reset, got in sorted(split_rises(series, WINDOW_HOURS.get(window), spend).items()):
            when = local(parse_ts(reset)) if parse_ts(reset) else "unknown"
            out += [f"{window:<11} {when:<25} {sid if sid.startswith('(') else sid[:8]:<9} {pts:>6.2f}"
                    for sid, pts in sorted(got.items(), key=lambda kv: -kv[1])]
    return "\n".join(out + [""] + cost_by_week(rows, costs))


# ---------------------------------------------------------------- entry points ---------------------------------------

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
