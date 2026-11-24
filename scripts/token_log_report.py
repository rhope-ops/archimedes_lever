"""The report part of scripts/token_log.py: the price tables and the --report command (estimated cost by week, by
source, agent and model, and per subagent task). Split out so that token_log.py stays under the C4 file cap.

token_log.py loads this file only when the report or a price is needed (its module __getattr__): the Stop hook path
never imports it, so an installed copy that has only token_log.py keeps working, and its self-update fetches this file.
Inputs:  rows of the token log CSV (from token_log.py), a git ref for --report.
Outputs: the report text on stdout.
Prevents: a rise in estimated cost by week, model or agent that no one sees until the usage limit stops work
Network: --report fetches the log branch through token_log.git_net; none in the self-test.
Writes: none.
Credentials: none (git uses the repo's own remote).
Run:     python3 scripts/token_log.py --report [REF]
"""
import csv
import io
import os
import sys
from datetime import date, datetime

core = None  # scripts/token_log.py as a module: set by its loader before any call here

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
        r: a row (a dict with the core.FIELDS; token counts as text or int).
    Returns:
        The cost as a float (only the web search fee for a model with no token price), or None.
    """
    key = max((k for k in PRICES if (r.get("model") or "").startswith(k)), key=len, default=None)
    search = core.tokens(r.get("web_search_requests")) * WEB_SEARCH_USD
    if key is None:
        return search or None
    inp, out, read, geo = PRICES[key]
    n, write = [core.tokens(r.get(k)) for k in core.USAGE_KEYS], core.tokens(r.get("cache_creation_input_tokens"))
    if key in LONG_PRICES and sum(n[:3]) > LONG_PROMPT:
        inp, out, read = LONG_PRICES[key]
    if r.get("speed") == "fast" and key in FAST_PRICES:
        read, (inp, out) = read * FAST_PRICES[key][0] / inp, FAST_PRICES[key]
    w1h = min(max(core.tokens(r.get("cache_write_1h_tokens")), 0), write)  # an old row has none: all writes are 5-minute
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
        rows: a list of rows (dicts with the core.FIELDS).
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
        for i, x in enumerate([1, *(core.tokens(r.get(k)) for k in core.USAGE_KEYS), c]):  # calls, the 4 token counts, cost
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
    """Every row in sessions/*.csv at a core.git ref.

    Args:
        root: the repo folder.
        ref: the core.git ref that holds the log branch's files.
    Returns:
        A list of rows (dicts).
    """
    rows = []
    for f in core.git(root, "ls-tree", "-r", "--name-only", ref, "sessions/").splitlines():
        if f.endswith(".csv"):
            rows += list(csv.DictReader(io.StringIO(core.git(root, "show", f"{ref}:{f}"))))
    return rows


def report_main(args):
    """Print the report for the repo in the current folder: fetch the log branch, or read the ref in args.

    Args:
        args: the arguments after --report: [] or [REF].
    Returns:
        The exit code: 0, or 1 when the repo or the branch cannot be read.
    """
    root = core.git(os.getcwd(), "rev-parse", "--show-toplevel", check=False)
    if not root:
        print("token_log --report: not in a git repo", file=sys.stderr)
        return 1
    ref = args[0] if args else "refs/token-log/report"
    if not args:
        rc, _, err = core.git_net(root, "fetch", "-q", "--no-write-fetch-head", "origin",
                             f"+refs/heads/{core.branch_name()}:{ref}")
        if rc != 0:
            print("token_log --report: fetch: " + err, file=sys.stderr)
            return 1
    try:
        print(report(report_rows(root, ref)))
    except RuntimeError as e:
        print(f"token_log --report: {e}", file=sys.stderr)
        return 1
    return 0
