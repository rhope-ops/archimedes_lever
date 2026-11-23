#!/usr/bin/env python3
"""More self-test cases of scripts/token_log.py: the agent and agent_id columns, bad agent input, the report, the
prices and the self-update; and the sample log lines (msg, prompt, tool_result, append) that every case uses.
Kit only: projects do not get a copy.

Part of scripts/token_log_test.py (split out to keep each file under the line cap of docs/code-standard.md C4);
token_log_test.run() calls these cases on its shared fixture.
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


def msg(mid, ts, model="claude-test", side=False, n=1):
    """One assistant log line with usage n, 10n, 100n, 1000n."""
    u = {"input_tokens": n, "cache_creation_input_tokens": 10 * n, "cache_read_input_tokens": 100 * n,
         "output_tokens": 1000 * n}
    return json.dumps({"type": "assistant", "timestamp": ts, "isSidechain": side,
                       "message": {"id": mid, "model": model, "usage": u}})


def prompt(ts, text="hi"):
    """One user prompt log line."""
    return json.dumps({"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}})


def tool_result(ts):
    """One tool-result log line (not a prompt)."""
    return json.dumps({"type": "user", "timestamp": ts, "message": {"content": [{"type": "tool_result", "content": "x"}]}})


def append(path, *lines):
    """Append lines to a file."""
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")


def case_agent_type(fx):
    """A subagent row gets the type of its Agent call; a subagent with no matching call says "unknown".

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, logs = fx.root, fx.work, fx.logs
    t3 = os.path.join(root, "proj", "s3.jsonl")
    u = json.loads(msg("p1", "2026-01-02T01:00:00Z"))["message"]["usage"]
    call = {"type": "assistant", "timestamp": "2026-01-02T01:00:00Z",
            "message": {"id": "p1", "model": "claude-test", "usage": u,
                        "content": [{"type": "tool_use", "id": "tu1", "name": "Agent", "input": {"subagent_type": "scout"}}]}}
    done = {"type": "user", "timestamp": "2026-01-02T01:00:01Z", "toolUseResult": {"agentId": "ab1"},
            "message": {"content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "x"}]}}
    append(t3, prompt("2026-01-02T00:59:00Z"), json.dumps(call), json.dumps(done))
    os.makedirs(os.path.join(root, "proj", "s3", "subagents"))
    append(os.path.join(root, "proj", "s3", "subagents", "agent-ab1.jsonl"),
           msg("sa2", "2026-01-02T01:00:02Z", side=True))
    append(os.path.join(root, "proj", "s3", "subagents", "agent-zz9.jsonl"),
           msg("sa3", "2026-01-02T01:00:03Z", side=True))
    fx.hook(work, "s3", t3, logs)
    got = fx.remote_rows("s3") or []
    fx.expect("agent column: main row, matched subagent type, unmatched subagent",
              [(x["message_id"], x["agent"]) for x in got], [("p1", "main"), ("sa2", "scout"), ("sa3", "unknown")])
    fx.expect("agent_id column: empty for main, the subagent's id from its log file name",
              [x["agent_id"] for x in got], ["", "ab1", "zz9"])


def case_agent_type_bad_input(fx):
    """Each bad field alone: a non-text type, an unmapped id, a non-text id and a non-number count. Each row still
    pushes; the bad type and the unmapped id say "unknown".

    Args:
        fx: the shared test fixture (Fixture).
    """
    root, work, logs = fx.root, fx.work, fx.logs
    t4 = os.path.join(root, "proj", "s4.jsonl")
    u = json.loads(msg("p", "2026-01-02T02:00:00Z"))["message"]["usage"]

    def asst(mid, ts, content=None, usage=u):
        """One assistant log line with this id, time, content and usage."""
        m = {"id": mid, "model": "claude-test", "usage": usage}
        if content is not None:
            m["content"] = content
        return json.dumps({"type": "assistant", "timestamp": ts, "message": m})

    def use(tid, name, sub):
        """One tool_use block: an Agent or Task call with a subagent type."""
        return {"type": "tool_use", "id": tid, "name": name, "input": {"subagent_type": sub}}

    def result(ts, agent, tool_use_id):
        """One tool_result line with the agent id and the tool_use id it answers."""
        return json.dumps({"type": "user", "timestamp": ts, "toolUseResult": {"agentId": agent},
                           "message": {"content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "x"}]}})

    append(t4, prompt("2026-01-02T01:59:00Z"),
           asst("pA", "2026-01-02T02:00:00Z", [use("tA", "Task", {"a": 1})]),  # a dict type
           result("2026-01-02T02:00:01Z", "abA", "tA"),
           asst("pB", "2026-01-02T02:00:02Z", [use("tB", "Agent", "scout")]),
           result("2026-01-02T02:00:03Z", "abB", {"a": 1}),  # a dict tool_use_id: abB stays unmapped
           asst("pC", "2026-01-02T02:00:04Z", [use("tC", "Agent", "scout")]),
           result("2026-01-02T02:00:05Z", ["q"], "tC"),  # a list agentId
           asst(["x"], "2026-01-02T02:00:06Z"),  # a list message id: no row
           asst("pD", "2026-01-02T02:00:07Z"),
           asst("pE", "2026-01-02T02:00:08Z", usage=dict(u, input_tokens="abc")),  # a non-number count
           asst("pF", "2026-01-02T02:00:09Z", usage=dict(u, input_tokens=float("inf"))))  # an infinite count
    d = os.path.join(root, "proj", "s4", "subagents")
    os.makedirs(d)
    append(os.path.join(d, "agent-abA.jsonl"), msg("saA", "2026-01-02T02:00:10Z", side=True))
    append(os.path.join(d, "agent-abB.jsonl"), msg("saB", "2026-01-02T02:00:11Z", side=True))
    fx.hook(work, "s4", t4, logs)
    got = fx.remote_rows("s4") or []
    fx.expect("bad fields: each row still pushes; a dict type and an unmapped id say unknown",
              [(x["message_id"], x["agent"]) for x in got],
              [("pA", "main"), ("pB", "main"), ("pC", "main"), ("pD", "main"), ("pE", "main"),
               ("pF", "main"), ("saA", "unknown"), ("saB", "unknown")])
    fx.expect("non-number and infinite counts: counted as 0",
              [x["input_tokens"] for x in got if x["message_id"] in ("pE", "pF")], ["0", "0"])


def case_report(fx):
    """Price weights (longest prefix, cache write 1.25 x input), weeks in America/Chicago, tasks, unpriced models.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    row = {"model": "claude-opus-5-5", "input_tokens": "1000000", "cache_creation_input_tokens": "1000000",
           "cache_read_input_tokens": "1000000", "output_tokens": "1000000"}
    fx.expect("row cost: opus-5-5 is 4 + 5 + 0.20 + 20", round(tl.row_cost(row), 2), 29.2)
    fx.expect("row cost: unknown model is None", tl.row_cost({**row, "model": "claude-test"}), None)
    fx.expect("week: Sunday 23:00 Chicago is the week of the Monday before",
              tl.week_of("2026-11-23T05:00:00Z"), "2026-11-16")
    fx.expect("week: bad timestamp", tl.week_of("not a time"), "unknown")
    rows = [{**row, "source": "main", "agent": "main", "timestamp": "2026-11-17T12:00:00Z"},
            {**row, "source": "subagent", "agent": "scout", "agent_id": "a1", "model": "claude-haiku-5-5",
             "timestamp": "2026-11-17T12:00:00Z"},
            {**row, "source": "subagent", "agent": "scout", "agent_id": "a1", "model": "claude-haiku-5-5",
             "timestamp": "2026-11-17T12:00:01Z"},
            {**row, "source": "main", "model": "claude-test", "timestamp": ""}]
    text = tl.report(rows)
    fx.expect("report: week line with main and subagent cost",
              "2026-11-16                          3   29.20        7.35    36.55" in text, True)
    fx.expect("report: one scout task of 2 calls", any(l.split()[:3] == ["scout", "1", "2.0"] for l in text.splitlines()),
              True)
    fx.expect("report: unpriced model listed", text.splitlines()[-3],
              "no token price (tokens counted as 0, web searches counted): claude-test")
    fx.expect("report: footer counts the old rows priced as 5-minute cache writes", text.splitlines()[-1],
              "Rows from before the cache_write_1h_tokens column (4): cache writes priced as 5-minute.")
    new = [{**r, "cache_write_1h_tokens": "0"} for r in rows]
    fx.expect("report: no old-row footer when every row has the column",
              "cache_write_1h_tokens" in tl.report(new), False)
    fx.expect("report: footer for 1 old row among new rows",
              tl.report(new + rows[:1]).splitlines()[-1].endswith("column (1): cache writes priced as 5-minute."), True)
    searched = {**row, "model": "claude-test", "web_search_requests": "3", "source": "main",
                "timestamp": "2026-11-17T12:00:00Z", "cache_write_1h_tokens": "0"}
    fx.expect("row cost: unknown model with 3 web searches is the search fee only",
              round(tl.row_cost(searched), 6), 0.03)
    text = tl.report([searched])
    fx.expect("report: search fee of an unknown model in the week total",
              "2026-11-16                          1    0.03        0.00     0.03" in text, True)
    fx.expect("report: unknown model with searches still listed as no token price",
              text.splitlines()[-1].endswith(": claude-test"), True)
    old = {k: v for k, v in rows[0].items() if k not in ("agent", "agent_id")}  # a row from before the columns
    merged = list(csv.DictReader(io.StringIO(tl.to_csv({"m1": {**old, "message_id": "m1"}}))))
    fx.expect("old row without agent and agent_id: merged with empty values",
              (merged[0]["agent"], merged[0]["agent_id"]), ("", ""))
    fx.expect("old row: in the report", "29.20" in tl.report(merged), True)


def case_prices(fx):
    """Cost cases from the price list: 1-hour writes, Haiku 5.5 long prompts, fast mode, web search, US geo, old rows.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl = fx.tl
    M = 1_000_000

    def cost(model, **kw):
        """Cost of one row of this model with these fields (token counts default to 0)."""
        r = {"model": model, "input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
             "output_tokens": 0}
        return round(tl.row_cost({**r, **kw}), 6)
    fx.expect("5-minute cache write: 1.25 x input", cost("claude-opus-5", cache_creation_input_tokens=M), 6.25)
    fx.expect("1-hour cache write: 2 x input",
              cost("claude-opus-5", cache_creation_input_tokens=M, cache_write_1h_tokens=M), 10.0)
    fx.expect("cache write split: half 1-hour, half 5-minute",
              cost("claude-opus-5", cache_creation_input_tokens=M, cache_write_1h_tokens=M // 2), 8.125)
    fx.expect("Haiku 5.5 prompt of 100,000 tokens: short price", cost("claude-haiku-5-5", input_tokens=100_000), 0.01)
    fx.expect("Haiku 5.5 prompt of 100,001 tokens: long price", cost("claude-haiku-5-5", input_tokens=100_001), 0.050001)
    fx.expect("Haiku 5.5 prompt length counts cache reads and writes",
              cost("claude-haiku-5-5", cache_read_input_tokens=60_000, cache_creation_input_tokens=40_001), round(60_000 * 0.05 / M + 40_001 * 0.625 / M, 6))
    fx.expect("fast mode Opus 5.5: input 8, output 40",
              cost("claude-opus-5-5", input_tokens=M, output_tokens=M, speed="fast"), 48.0)
    fx.expect("fast mode Opus 5.5: 1-hour cache write is 2 x fast input",
              cost("claude-opus-5-5", cache_creation_input_tokens=M, cache_write_1h_tokens=M, speed="fast"), 16.0)
    fx.expect("fast mode on a model with no fast price: normal price",
              cost("claude-sonnet-5", input_tokens=M, speed="fast"), 2.0)
    fx.expect("3 web searches add $0.03", cost("claude-opus-5", web_search_requests=3), 0.03)
    fx.expect("inference_geo us adds 10%", cost("claude-opus-5", output_tokens=M, inference_geo="us"), 27.5)
    fx.expect("inference_geo us: web search fee not raised",
              cost("claude-opus-5", web_search_requests=10, inference_geo="us"), 0.1)
    fx.expect("inference_geo us: not on Opus 4.5", cost("claude-opus-4-5", output_tokens=M, inference_geo="us"), 25.0)
    fx.expect("old row without the new columns: cache write as 5-minute",
              cost("claude-opus-5", cache_creation_input_tokens=M), 6.25)
    fx.expect("Opus 4.1 and Opus 4 (retired): 15 / 75", (cost("claude-opus-4-1-20250805", input_tokens=M),
              cost("claude-opus-4-20250514", output_tokens=M)), (15.0, 75.0))
    fx.expect("Opus 4.7: 5 / 25", (cost("claude-opus-4-7", input_tokens=M), cost("claude-opus-4-7", output_tokens=M)),
              (5.0, 25.0))
    t5 = os.path.join(fx.root, "proj", "s5.jsonl")
    u = {"input_tokens": 1, "cache_creation_input_tokens": 10, "cache_read_input_tokens": 0, "output_tokens": 1,
         "cache_creation": {"ephemeral_5m_input_tokens": 4, "ephemeral_1h_input_tokens": 6}, "speed": "fast",
         "server_tool_use": {"web_search_requests": 2}, "inference_geo": "us"}
    append(t5, prompt("2026-01-03T00:00:00Z"),
           json.dumps({"type": "assistant", "timestamp": "2026-01-03T00:00:01Z",
                       "message": {"id": "q1", "model": "claude-opus-5-5", "usage": u}}))
    fx.hook(fx.work, "s5", t5, fx.logs)
    got = fx.remote_rows("s5") or [{}]
    fx.expect("log to row: 1-hour part, speed, web searches, geo recorded",
              [got[0].get(k) for k in ("cache_write_1h_tokens", "speed", "web_search_requests", "inference_geo")],
              ["6", "fast", "2", "us"])
    fx.expect("a row from before the new columns still parses and prices",
              tl.row_cost({k: v for k, v in got[0].items() if k not in tl.FIELDS[13:]}) is not None, True)


def case_self_update(fx):
    """Self-update: a newer copy replaces the file; once a day; a copy that does not compile is not used.

    Args:
        fx: the shared test fixture (Fixture).
    """
    tl, root = fx.tl, fx.root
    kit, target = os.path.join(root, "kit"), os.path.join(root, "installed", "token_log.py")
    os.makedirs(os.path.join(kit, "scripts"))
    os.makedirs(os.path.dirname(target))
    append(target, "old = 1")
    append(os.path.join(kit, "scripts", "token_log.py"), "import sys", "sys.exit(0)  # new")
    fx.sh(root, "git", "init", "-q", "-b", "main", kit)
    fx.sh(kit, "git", "add", ".")
    fx.sh(kit, "git", "commit", "-q", "-m", "kit")
    os.environ["TOKEN_LOG_HOME"] = os.path.join(root, "update-home")
    fx.expect("self-update: newer copy replaces the file", tl.self_update(target, kit, now=1e9), "updated")
    fx.expect("self-update: file has the new text", open(target).read(), "import sys\nsys.exit(0)  # new\n")
    fx.expect("self-update: second check the same day is skipped", tl.self_update(target, kit, now=1e9 + 60), "skipped")
    fx.expect("self-update: next day, same copy", tl.self_update(target, kit, now=1e9 + 90000), "up to date")
    with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
        f.write("import sys\nsys.exit(1)  # compiles, fails its self-test\n")
    fx.sh(kit, "git", "commit", "-q", "-am", "fails")
    fx.expect("self-update: a copy whose self-test fails is not used",
              tl.self_update(target, kit, now=1e9 + 200000).startswith("not updated: self-test failed"), True)
    fx.expect("self-update: file kept", open(target).read(), "import sys\nsys.exit(0)  # new\n")
    part = os.path.join(kit, "scripts", "token_log_rows.py")  # the split (kit 11.0.0): parts install with the file
    with open(os.path.join(kit, "scripts", "token_log.py"), "w") as f:
        f.write("import sys\nsys.exit(0)  # new 2\n")
    append(part, "rows = 1")
    fx.sh(kit, "git", "add", ".")
    fx.sh(kit, "git", "commit", "-q", "-m", "parts")
    fx.expect("self-update: the parts and the file install", tl.self_update(target, kit, now=1e9 + 300000), "updated")
    fx.expect("self-update: the part is next to the file",
              open(os.path.join(os.path.dirname(target), "token_log_rows.py")).read(), "rows = 1\n")
    os.remove(os.path.join(os.path.dirname(target), "token_log_rows.py"))
    fx.expect("self-update: a missing part is not up to date", tl.self_update(target, kit, now=1e9 + 400000), "updated")
    case_kit_url(fx, kit, target)


def case_kit_url(fx, kit, target):
    """Self-update installs kit.config.json; kit_url() reads TOKEN_LOG_KIT_URL, the installed file, the session repo.

    Args:
        fx: the shared test fixture (Fixture).
        kit: the test kit repo of case_self_update.
        target: the installed token_log.py of case_self_update.
    """
    tl, root = fx.tl, fx.root
    with open(os.path.join(kit, "kit.config.json"), "w") as f:  # kit 11.0.0: the kit address lives in kit.config.json
        f.write('{"kit_url": "https://example.invalid/sample-org/sample-kit"}')
    fx.sh(kit, "git", "add", ".")
    fx.sh(kit, "git", "commit", "-q", "-m", "config")
    tl.self_update(target, kit, now=1e9 + 500000)
    sibling = os.path.join(os.path.dirname(target), "kit.config.json")
    fx.expect("self-update: kit.config.json installs next to the file", os.path.isfile(sibling), True)
    saved = {k: os.environ.pop(k, None) for k in ("TOKEN_LOG_KIT_URL", "CLAUDE_PROJECT_DIR")}
    try:
        fx.expect("kit_url: read from the installed kit.config.json", tl.kit_url(target),
                  "https://example.invalid/sample-org/sample-kit")
        os.environ["TOKEN_LOG_KIT_URL"] = "https://example.invalid/other"
        fx.expect("kit_url: TOKEN_LOG_KIT_URL wins", tl.kit_url(target), "https://example.invalid/other")
        del os.environ["TOKEN_LOG_KIT_URL"]
        os.remove(sibling)
        os.environ["CLAUDE_PROJECT_DIR"] = kit
        fx.expect("kit_url: else the session repo's kit.config.json", tl.kit_url(target),
                  "https://example.invalid/sample-org/sample-kit")
        os.environ["CLAUDE_PROJECT_DIR"] = os.path.join(root, "installed")
        fx.expect("kit_url: no source gives None", tl.kit_url(target), None)
        fx.expect("self-update: no kit address does nothing",
                  tl.self_update(target, now=1e9 + 600000).startswith("not updated: no kit address"), True)
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
