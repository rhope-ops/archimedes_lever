"""The rows of the token log: reads a session log and its subagent logs into one row per API call (message id,
turn, source, agent, the token counts and the price facts), and writes them as CSV. The one home of the columns
(FIELDS). Kit only. One of the three hook files: token_log.py (the hook), this file (the rows), token_log_report.py.

token_log.py imports this file in the background push, never on the Stop path. An installed copy from before the
split has no such file: its push then fails with ImportError and runs the self-update at once, which installs this
file; the next push rebuilds every row from the logs, so no row is lost.
Inputs:  the session log path (JSON lines) and its <session>/**/*.jsonl subagent logs.
Outputs: {message_id: row} and its CSV text for token_log.push.
Prevents: double counts of one reply (the session log repeats its usage on each content block) and lost subagent rows
Network: none.
Writes: none.
Credentials: none.
Run:     imported by scripts/token_log.py; tested by its self-test (python3 scripts/token_log.py --test).
"""
import bisect
import csv
import glob
import io
import json
import os
import re

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


def skill_calls(tpath):
    """Count the skill use in one log file, by the reply (message id) that made each call. A tool_use block counts
    one time (its id), though the log repeats a reply on each content block; a block with no usable id counts each
    time. A line or block of an unexpected type is skipped, as in read_log. The same rules as scripts/skill_use.py.

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
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                key = b.get("id")
                if isinstance(key, str) and key:
                    if key in seen:
                        continue
                    seen.add(key)
                i = b.get("input") if isinstance(b.get("input"), dict) else {}
                hits = []  # (skill name, kind)
                if b.get("name") == "Skill" and isinstance(i.get("skill"), str) and i["skill"]:
                    hits.append((i["skill"], "skill_tool"))
                elif b.get("name") == "Read":
                    hits += [(n, "read") for n in SKILL_PATH.findall(str(i.get("file_path") or ""))]
                elif b.get("name") == "Bash":
                    hits += [(n, "slice") for n in sliced_skills(str(i.get("command") or ""))]
                for name, kind in hits:
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
