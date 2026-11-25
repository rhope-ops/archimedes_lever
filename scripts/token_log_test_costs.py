#!/usr/bin/env python3
"""Self-test cases of the /cost and /usage records in the token log: the agents-pane record
<TOKEN_LOG_HOME>/cost/<session id>.json becomes costs/<session id>.csv (a snapshot) and limits/<session id>.csv (a
series) in the same commit as the session's rows; a bad record is skipped; the report splits each rise of a plan
limit among the sessions. Kit only: projects do not get a copy.

The fixture and the sample log lines are in scripts/token_log_test.py (split by subject, to keep each file under the
line cap of docs/code-standard.md C4); token_log_test.run() calls these cases on its fixture.
Input: the shared test fixture of token_log_test.py. Output: one PASS or FAIL line per case. Needs git.
Usage:   imported by scripts/token_log_test.py (run by `python3 scripts/token_log.py --test`); no command line.
Network: none.
Writes: temporary repos only.
Credentials: none.
"""
import csv
import io
import json
import os
import subprocess
import tempfile
import types
from datetime import datetime, timezone

from token_log_test import append, msg, prompt


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
    costs = [{"session_id": "sessA", "source": "main", "usd": "1.0", "session_usd": "2.5"}]
    text = rep.limits_report(rows, costs, []).splitlines()
    fx.expect("report: best estimate: /cost where recorded, else the hook's $ x the median ratio (2.50 + 1.00 x 1.25)",
              [ln for ln in text if ln.startswith("best estimate")],
              ["best estimate, all weeks: 3.75 $ (/cost where recorded, else the hook's $ x 1.25, the median /cost "
               "ratio of 1 sessions)"])
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
