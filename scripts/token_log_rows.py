"""The row part of scripts/token_log.py: reads a session log and its subagent logs into one row per API call
(message id, turn, source, agent, the token counts and the price facts). Split out so that token_log.py stays under
the C4 file cap.

token_log.py loads this file on first use. An installed copy from before the split has no such file: its background
push then fails with ImportError and runs the self-update at once, which installs this file; the next push rebuilds
every row from the logs, so no row is lost.
Inputs:  the session log path (JSON lines) and its <session>/**/*.jsonl subagent logs.
Outputs: {message_id: row} for token_log.push.
Prevents: double counts of one reply (the session log repeats its usage on each content block) and lost subagent rows
Network: none.
Writes: none.
Credentials: none.
Run:     loaded by scripts/token_log.py; tested by its self-test (python3 scripts/token_log.py --test).
"""
import bisect
import glob
import json
import os

core = None  # scripts/token_log.py as a module: set by its loader before any call here


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
    if not isinstance(c, str) or not c.strip() or c.lstrip().startswith(core.NOT_PROMPTS):
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
        A dict of message id to the row (a dict with the core.FIELDS).
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
                     **{k: tokens(u.get(k)) for k in core.USAGE_KEYS}, **price_facts(u)}
    return rows
