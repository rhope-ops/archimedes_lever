"""The report of the token log: the price tables and the --report command (estimated cost by week, by source, agent
and model, and per subagent task; the plan limits, the limit used per session and Claude Code's /cost by week). Kit only. One of the three hook files: token_log.py (the hook),
token_log_rows.py (the rows), this file.

token_log.py imports this file only for --report: the Stop hook path never imports it, so an installed copy that has
only token_log.py keeps working, and its self-update fetches this file.
Inputs:  the files sessions/, costs/ and limits/ of the log branch (from token_log.py), a git ref for --report.
Outputs: the report text on stdout.
Prevents: a rise in estimated cost by week, model or agent that no one sees until the usage limit stops work
Network: --report fetches the log branch from origin and from the private log repo through token_log.git_net; none in
         the self-test.
Writes: none.
Credentials: none (git uses the repo's own remote).
Run:     python3 scripts/token_log.py --report [REF]
"""
import csv
import io
import os
import sys
from datetime import date, datetime, timezone

from token_log_rows import USAGE_KEYS, tokens

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


def row_cost(r):
    """The estimated cost of one row in USD, or None for a model with no price and no web search.

    Args:
        r: a row (a dict with the token_log_rows.FIELDS; token counts as text or int).
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
        rows: a list of rows (dicts with the token_log_rows.FIELDS).
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


def fetch_refs(core, root):
    """Fetch the log branch from the repo's origin and from the private log repo (core.log_repo()), each into its own
    ref. One that cannot be fetched (no branch there, or no access) is left out with a note on stderr.

    Args:
        core: the token_log module (its git helpers and settings).
        root: the repo folder.
    Returns:
        The refs that were fetched (none, one or two).
    """
    refs = []
    for remote, ref in (("origin", "refs/token-log/report"), (core.log_repo(core.__file__), "refs/token-log/report-private")):
        if not remote:
            continue
        rc, _, err = core.git_net(root, "fetch", "-q", "--no-write-fetch-head", remote,
                                  f"+refs/heads/{core.branch_name()}:{ref}")
        if rc == 0:
            refs.append(ref)
        else:
            print(f"token_log --report: not read: {'origin' if remote == 'origin' else 'the private log repo'}: "
                  + (err.splitlines() or [""])[-1], file=sys.stderr)
    return refs


def report_main(args):
    """Print the report for the repo in the current folder: fetch the log branch from origin and from the private log
    repo and merge them, or read the ref in args.

    Args:
        args: the arguments after --report: [] or [REF].
    Returns:
        The exit code: 0, or 1 when the repo or no log branch can be read.
    """
    import token_log as core  # the git helpers; a plain import, as this file is only loaded next to token_log.py
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
    costs = list({(r.get("session_id"), r.get("source"), r.get("agent_id")): r for r in got["costs"]}.values())
    print(report(rows) + "\n\n" + limits_report(rows, costs, got["limits"]))
    return 0


WINDOW_HOURS = {"five_hour": 5, "seven_day": 7 * 24}  # the length of each plan-limit window


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
        limits: rows of limits/*.csv (dicts with the token_log_rows.LIMIT_FIELDS).
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
    from datetime import timedelta
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
    import bisect
    from datetime import timedelta
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
        costs: rows of costs/*.csv (dicts with the token_log_rows.COST_FIELDS).
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
