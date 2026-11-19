#!/usr/bin/env python3
"""Read a project's handoff and decisions files in the fleet format, for the fleet page and its format check.

Format: docs/reviews/2026-11-19-fleet-contract.md, section 2 (the owner, 2026-11-19); steps: the handoff skill.
A project turns the format on with the line `fleet: on` in `.check`. Without it, --check prints a SKIP line.

Usage:
    python3 scripts/fleet_harvest.py --check [ROOT]
        The format check (scripts/check.sh runs it when `.check` has `fleet: on`): exit 1 when a line in "Needs the
        owner", "Timeline" or a docs/DECISIONS.md row cannot be read; it prints the file, line number and reason.
    python3 scripts/fleet_harvest.py --harvest ROOT --repo NAME --url URL [--branch B] [--state FILE] [--cross FILE]
        Prints JSON {"writes": [...], "deletes": [...], "counts": {...}}: the project's repos row (always, with
        harvested_at) and the items that changed since the hashes in --state. The new hashes go to FILE.pending;
        after the page write succeeds, `--save-state FILE` moves them into FILE (a failed write is sent again). --cross: a JSON file {"pull_requests": [{title,
        url}], "sessions": [{title, url}]} from the scheduled session; an entry that the handoff file does not name
        becomes a "Not filed" item. Decision text on the page is the first sentence, at most 140 characters.
    python3 scripts/fleet_harvest.py --add-ids [ROOT]
        Adds the `ID` column to docs/DECISIONS.md: D1 = the oldest row. A file that has the column is left as it is.
    python3 scripts/fleet_harvest.py --test
        Self-test on fixture files in a temporary folder; prints FLEET TEST PASS.
Standard library only.
Network: none.
Writes: --harvest FILE.pending of --state; --save-state the --state file; --add-ids docs/DECISIONS.md; --test temporary folders.
Credentials: none.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

OPT_IN = "fleet: on"  # the `.check` line that turns the format on (contract section 1)
SUMMARY_MAX = 140  # characters of decision text on the page (contract section 3)
DATE = r"\d{4}-\d{2}-\d{2}"
UPDATED = re.compile(r"^Updated:\s*(" + DATE + r"(?: \d{2}:\d{2})?)")
NEXT = re.compile(r"^Next update:\s*(" + DATE + r"),\s*(.+)$")
TIMELINE = re.compile(r"^- (" + DATE + r") · (.+?) · (planned|done)\s*$")
NEED = re.compile(r"^- (D\d+) · (.+?) · Options: (.+?) · REC: (.+?)\s*$")
ROW = re.compile(r"^\|\s*(D\d+)\s*\|\s*(" + DATE + r")\s*\|(.*)\|\s*$")
ROW_START = re.compile(r"(?i)^\|\s*(D\d+\s*\||" + DATE + r"\s*\|)")  # any decision row, also one that ROW does not read
CELL_SPLIT = re.compile(r"(?<!\\)\|")  # a cell border; an escaped pipe (\|) stays inside the cell
NEEDED = ("Timeline", "Needs the owner")  # handoff sections the format check requires
NONE_LINE = re.compile(r"^-?\s*(none|nothing)\.?\s*$", re.I)


def opted_in(root):
    """True when `.check` in root has the line `fleet: on`."""
    f = root / ".check"
    return f.exists() and OPT_IN in (ln.strip() for ln in f.read_text(encoding="utf-8").splitlines())


def handoff_path(root):
    """The handoff file: docs/KIT_HANDOFF.md in the kit itself, else docs/NEXT_PROMPT.md."""
    kit = root / "docs/KIT_HANDOFF.md"
    return kit if kit.exists() else root / "docs/NEXT_PROMPT.md"


def sections(lines):
    """{heading: [(line number, text)]} of the `## ` sections of a Markdown file.

    Args:
        lines: the lines of the file.
    Returns:
        A dict from each heading text (without "## ") to its body lines, with 1-based line numbers.
    """
    out, cur = {}, None
    for n, ln in enumerate(lines, 1):
        if ln.startswith("## "):
            cur = re.sub(r"\s*\(.*\)\s*$", "", ln[3:].strip())  # "Needs the owner (2)" -> "Needs the owner"
            out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append((n, ln))
    return out


def summary(text):
    """The first sentence of a text, at most SUMMARY_MAX characters (an ellipsis marks a cut)."""
    first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    return first if len(first) <= SUMMARY_MAX else first[:SUMMARY_MAX - 1].rstrip() + "…"


def digest(text):
    """A short stable hash of a text (the page compares it to find a stale choice)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_body(body, pattern, name, unread):
    """The matches of pattern in the bullet lines of a section; other non-empty lines go to unread.

    Args:
        body: [(line number, text)] of one section.
        pattern: the regular expression that one line must match.
        name: the file and section name for an unread entry.
        unread: a list that gets (name, line number, reason) for each line that does not match.
    Returns:
        [(line number, match, text)] of the lines that match.
    """
    found = []
    for n, ln in body:
        s = ln.rstrip()
        if not s.strip() or NONE_LINE.match(s.strip()):
            continue
        m = pattern.match(s)
        if m:
            found.append((n, m, s))
        else:
            unread.append((name, n, "not in the fleet format"))
    return found


def parse_handoff(text, name):
    """The fleet fields of a handoff file.

    Args:
        text: the file text.
        name: the file name, for unread entries.
    Returns:
        A dict: updated, next_update ({date, text} or None), timeline, needs, steps, unread.
    """
    lines = text.splitlines()
    unread = []
    updated = next((m.group(1) for m in map(UPDATED.match, lines) if m), None)
    nxt = next((m for m in map(NEXT.match, lines) if m), None)
    sec = sections(lines)
    unread += [(name, 0, "missing section: ## " + h) for h in NEEDED if h not in sec]
    timeline = [{"date": m.group(1), "text": summary(m.group(2)), "state": m.group(3)}
                for _, m, _ in parse_body(sec.get("Timeline", []), TIMELINE, name + " Timeline", unread)]
    needs = [{"id": m.group(1), "text": m.group(2).strip(), "options": [o.strip() for o in m.group(3).split("/")],
              "rec": m.group(4).strip(), "line": n, "raw": s}
             for n, m, s in parse_body(sec.get("Needs the owner", []), NEED, name + " Needs the owner", unread)]
    steps = [summary(re.sub(r"^(\d+\.|-)\s*", "", ln.strip())) for _, ln in sec.get("Open (in order)", [])
             if re.match(r"^(\d+\.|-)\s", ln.strip())]
    return {"updated": updated, "next_update": {"date": nxt.group(1), "text": nxt.group(2).strip()} if nxt else None,
            "timeline": timeline, "needs": needs, "steps": steps, "unread": unread}


def parse_decisions(text, name):
    """The rows of a decisions table that has the ID column.

    Args:
        text: the text of docs/DECISIONS.md.
        name: the file name, for unread entries.
    Returns:
        (rows, unread): rows is [{id, date, text, by, line, raw}]; unread is [(name, line number, reason)].
    """
    rows, unread = [], []
    lines = text.splitlines()
    head = next((i for i, ln in enumerate(lines) if re.match(r"^\|\s*(ID|Date)\s*\|", ln)), len(lines))
    end = next((i for i in range(head + 1, len(lines)) if not lines[i].startswith("|")), len(lines))
    for n, ln in enumerate(lines[head + 2:end], head + 3):  # the decisions table only; other tables are not read
        if not ROW_START.match(ln):
            continue
        m = ROW.match(ln.rstrip("\r"))
        cells = CELL_SPLIT.split(m.group(3)) if m else []
        if not m or len(cells) != 3:
            unread.append((name, n, "a decision row needs 5 cells: ID | Date | Decision | By | Replaces"))
            continue
        rows.append({"id": m.group(1), "date": m.group(2), "text": cells[0].strip().replace("\\|", "|"), "by": cells[1].strip(),
                     "line": n, "raw": ln})
    return rows, unread


def read_project(root):
    """The parsed handoff and decisions of a project folder: (handoff dict, decision rows, all unread entries)."""
    hp, dp = handoff_path(root), root / "docs/DECISIONS.md"
    h = parse_handoff(hp.read_text(encoding="utf-8") if hp.exists() else "", hp.name)
    if not hp.exists():
        h["unread"] = [(hp.name, 0, "missing file")]
    rows, bad = parse_decisions(dp.read_text(encoding="utf-8"), dp.name) if dp.exists() else ([], [])
    return h, rows, h["unread"] + bad


def check(root):
    """--check: print the format findings of a project that opted in; return the exit code (1 on a finding).

    Args:
        root: the project folder.
    Returns:
        0 when the files can be read in full or the project has not opted in, else 1.
    """
    if not opted_in(root):
        print("SKIP  fleet format (no `" + OPT_IN + "` line in .check)")
        return 0
    h, rows, unread = read_project(root)
    for name, n, why in unread:
        print("FLEET " + name + ":" + str(n) + ": " + why)
    ids = [r["id"] for r in rows] + [d["id"] for d in h["needs"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print("FLEET an ID is used more than once (in DECISIONS.md rows and \"Needs the owner\" together): " + ", ".join(dup))
    unset = [f for f, v in (("Updated:", h["updated"]), ("Next update:", h["next_update"])) if not v]
    print("fleet: %d open, %d resolved, %d lines not read%s" % (len(h["needs"]), len(rows), len(unread),
          "; not set: " + ", ".join(unset) if unset else ""))
    return 1 if unread or dup else 0


def not_filed(cross, text):
    """The entries of the cross-check input that the handoff text does not name (by URL or by title).

    Args:
        cross: {"pull_requests": [...], "sessions": [...]}, each entry {title, url}.
        text: the handoff file text.
    Returns:
        [{text, url, source}] for the page's "Not filed" items.
    """
    out = []
    for source in ("pull_requests", "sessions"):
        for e in cross.get(source, []):
            url, title = e.get("url", ""), e.get("title", "")
            num = re.search(r"/pull/(\d+)/?$", url)
            if num:  # a pull request: its whole URL, or "#<n>" as a whole number; never its title
                named = whole(url, text) or re.search(r"(?<![\w/#])#" + num.group(1) + r"(?!\d)", text)
            else:  # a session: its whole URL or its whole title
                named = whole(url, text) or whole(title, text)
            if not named:
                out.append({"text": summary(title or url), "url": url, "source": source})
    return out


def whole(needle, text):
    """True when needle is in text with no letter, digit or slash right before or after it (https://s/1 is not https://s/12)."""
    return bool(needle) and re.search(r"(?<![\w/])" + re.escape(needle) + r"(?![\w/])", text) is not None


def source_commit(root):
    """The short commit of the project folder (git rev-parse), or "" when it is no git checkout."""
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def documents(root, repo, url, cross, branch="main"):
    """{path: data} of every page document of one project (contract section 3).

    Args:
        root: the project folder.
        repo: the project name on the page.
        url: the repo URL on GitHub, for links to lines.
        cross: the cross-check input (see not_filed), or {}.
        branch: the branch the links point at.
    Returns:
        A dict from document path (repos/<repo> and items/<repo>~<id>) to its fields.
    """
    h, rows, unread = read_project(root)
    key = repo.replace("/", "_")
    hp = handoff_path(root).relative_to(root).as_posix()
    blob = url + "/blob/" + branch + "/"
    docs = {}
    for r in rows:
        docs["items/" + key + "~" + r["id"]] = {
            "repo": repo, "id": r["id"], "kind": "resolved", "date": r["date"], "summary": summary(r["text"]),
            "by": r["by"], "approved": not r["by"].startswith("Agent"), "options": [], "rec": "",
            "url": blob + "docs/DECISIONS.md#L" + str(r["line"]), "hash": digest(r["raw"])}
    for d in h["needs"]:
        docs["items/" + key + "~" + d["id"]] = {
            "repo": repo, "id": d["id"], "kind": "open", "date": h["updated"] or "", "summary": summary(d["text"]),
            "by": "", "approved": False, "options": d["options"], "rec": d["rec"],
            "url": blob + hp + "#L" + str(d["line"]), "hash": digest(d["raw"])}
    text = (root / hp).read_text(encoding="utf-8") if (root / hp).exists() else ""
    docs["repos/" + key] = {"repo": repo, "last_update": h["updated"], "next_update": h["next_update"],
                            "timeline": h["timeline"], "open_steps": h["steps"], "open_count": len(h["needs"]),
                            "unread_lines": len(unread), "not_filed": not_filed(cross, text)}
    return docs


def harvest(root, repo, url, state_file, cross, branch="main"):
    """--harvest: the repos row and the items changed since the last run, as one JSON object.

    Args:
        root: the project folder.
        repo: the project name on the page.
        url: the repo URL on GitHub.
        state_file: a JSON file {path: hash} of the last run, or None (then every document is written). The new
            hashes go to <state_file>.pending; --save-state moves them in after the page write succeeds.
        cross: the cross-check input, or {}.
        branch: the branch the links point at.
    Returns:
        {"writes": [{path, op, data}], "deletes": [path], "counts": {...}}. The repos row is always written, as a
        merge update with harvested_at and source_commit, so other fields there are kept and the page shows its age.
    """
    docs = documents(root, repo, url, cross, branch)
    key = "/" + repo.replace("/", "_")
    mine = lambda p: p.endswith(key) or ("~" in p and p.split("~")[0].endswith(key))  # noqa: E731 (this repo's paths)
    old = json.loads(state_file.read_text(encoding="utf-8")) if state_file and state_file.exists() else {}
    new = {p: digest(json.dumps(d, sort_keys=True)) for p, d in docs.items()}
    writes = [{"path": p, "op": "update" if p.startswith("repos/") else "set", "data": docs[p]}
              for p in sorted(docs) if p.startswith("repos/") or old.get(p) != new[p]]
    for w in writes:
        if w["path"].startswith("repos/"):
            w["data"].update(harvested_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             source_commit=source_commit(root))
    deletes = sorted(p for p in old if mine(p) and p not in new)
    if state_file:
        pending = pathlib.Path(str(state_file) + ".pending")
        base = json.loads(pending.read_text(encoding="utf-8")) if pending.exists() else old  # another repo's pending run
        keep = {p: v for p, v in base.items() if not mine(p)}  # other repos that share this state file
        pending.write_text(json.dumps({**keep, **new}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    items = sum(1 for w in writes if w["path"].startswith("items/"))
    return {"writes": writes, "deletes": deletes, "counts": {"documents": len(docs), "items_changed": items, "deleted": len(deletes)}}


def save_state(state_file):
    """--save-state: move <state_file>.pending into state_file (after the page write succeeded); return 0, or 1 if none."""
    pending = pathlib.Path(str(state_file) + ".pending")
    if not pending.exists():
        print("no " + pending.name + ": run --harvest first")
        return 1
    pending.replace(state_file)
    return 0


def add_ids(root):
    """--add-ids: add the ID column to the first table of docs/DECISIONS.md (D1 = the oldest row, the last one).

    Args:
        root: the project folder.
    Returns:
        The number of rows that got an ID (0 when the file already has the column). Line endings are kept.
    """
    f = root / "docs/DECISIONS.md"
    with open(f, encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines(keepends=True)
    if any(re.match(r"^\|\s*ID\s*\|", ln) for ln in lines):
        return 0
    head = next((i for i, ln in enumerate(lines) if re.match(r"^\|\s*Date\s*\|", ln)), None)
    if head is None:
        return 0
    end = next((i for i in range(head + 2, len(lines)) if not lines[i].startswith("|")), len(lines))
    rows = [i for i in range(head + 2, end) if re.match(r"^\|\s*" + DATE + r"\s*\|", lines[i])]
    for k, i in enumerate(reversed(rows), 1):
        lines[i] = "| D" + str(k) + " " + lines[i]
    lines[head] = "| ID " + lines[head]
    lines[head + 1] = "|---" + lines[head + 1]
    with open(f, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(lines))
    return len(rows)


HANDOFF_OK = """# Next prompt
Updated: 2026-11-19 14:50 by a session.
Next update: 2026-11-25, the pilot result

## State
- main: abc1234

## Timeline

- 2026-11-20 · Kit pull request · done
- 2026-12-01 · Pilot · planned

## Open (in order)

1. Build the page. Then test it.

## Needs the owner

- D3 · Drop the old export? · Options: yes / no · REC: yes
- D4 · Tag v4.0.0 (see #12) · Options: done / not done · REC: done
"""
DECISIONS_OLD = """# Decisions

| Date | Decision | By | Replaces |
|---|---|---|---|
| 2026-11-19 | Keep CSV. It works. | the owner | - |
| 2026-11-18 | Use semantic versions. | Agent | - |
"""


def make_project(base, handoff, decisions, opt_in=True):
    """A fixture project folder under base, with the given files; returns its path."""
    root = pathlib.Path(tempfile.mkdtemp(dir=base))
    (root / "docs").mkdir()
    (root / "docs/NEXT_PROMPT.md").write_text(handoff, encoding="utf-8")
    (root / "docs/DECISIONS.md").write_text(decisions, encoding="utf-8")
    (root / ".check").write_text("code-c2: full\n" + (OPT_IN + "\n" if opt_in else ""), encoding="utf-8")
    return root


def quiet(fn, *args):
    """Run fn(*args) with its printed lines caught; returns (result, printed text)."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = fn(*args)
    return res, buf.getvalue()


def test_cases(base):
    """The self-test cases; returns a list of (name, passed).

    Args:
        base: a temporary folder for the fixture projects.
    Returns:
        [(case name, True when it passed)].
    """
    out = []
    ok = lambda name, cond: out.append((name, bool(cond)))  # noqa: E731 (one-line recorder)
    p = make_project(base, HANDOFF_OK, DECISIONS_OLD)
    ok("add-ids numbers 2 rows", add_ids(p) == 2)
    text = (p / "docs/DECISIONS.md").read_text(encoding="utf-8")
    ok("oldest row is D1", "| D1 | 2026-11-18 |" in text and "| D2 | 2026-11-19 |" in text and "| ID | Date |" in text)
    ok("add-ids leaves a file with IDs", add_ids(p) == 0)
    code, printed = quiet(check, p)
    ok("a valid project passes the check", code == 0 and "2 open, 2 resolved, 0 lines not read" in printed)
    h, rows, _ = read_project(p)
    ok("next update read", h["next_update"] == {"date": "2026-11-25", "text": "the pilot result"})
    ok("timeline read", [t["state"] for t in h["timeline"]] == ["done", "planned"])
    ok("options split", h["needs"][0]["options"] == ["yes", "no"] and h["needs"][0]["rec"] == "yes")
    ok("summary is the first sentence", summary("Keep CSV. It works.") == "Keep CSV.")
    ok("summary is cut at 140", len(summary("x" * 300)) == SUMMARY_MAX)
    bad = make_project(base, HANDOFF_OK.replace("- D3 · Drop", "- Drop"), DECISIONS_OLD)
    code, printed = quiet(check, bad)
    ok("a need without an ID fails", code == 1 and "NEXT_PROMPT.md Needs the owner:" in printed)
    ok("rows without IDs fail", printed.count("DECISIONS.md:") == 2)
    off = make_project(base, "x", "y", opt_in=False)
    code, printed = quiet(check, off)
    ok("no opt-in: SKIP", code == 0 and printed.startswith("SKIP"))
    out += harvest_cases(base, p) + edge_cases(base)
    return out


def harvest_cases(base, p):
    """The --harvest self-test cases on the fixture project p; returns [(name, passed)].

    Args:
        base: a temporary folder for the state file.
        p: a fixture project with IDs.
    Returns:
        [(case name, True when it passed)].
    """
    out = []
    ok = lambda name, cond: out.append((name, bool(cond)))  # noqa: E731 (one-line recorder)
    state = pathlib.Path(base) / "state.json"
    cross = {"pull_requests": [{"title": "Tag", "url": "https://x/pull/12"}, {"title": "New thing", "url": "https://x/pull/13"}],
             "sessions": [{"title": "Kit · Fleet · 2026-11-19", "url": "https://s/1"}]}
    first = harvest(p, "demo", "https://github.com/o/demo", state, cross)
    ok("first run writes every document", first["counts"] == {"documents": 5, "items_changed": 4, "deleted": 0})
    ok("state waits for --save-state", not state.exists() and save_state(state) == 0 and state.exists())
    second = harvest(p, "demo", "https://github.com/o/demo", state, cross)
    save_state(state)
    ok("second run: 0 items, the repos row only", second["counts"]["items_changed"] == 0 and not second["deletes"]
       and [w["path"] for w in second["writes"]] == ["repos/demo"])
    repo = [w for w in first["writes"] if w["path"] == "repos/demo"][0]["data"]
    ok("repos row has its age", repo["harvested_at"].endswith("Z") and "source_commit" in repo and repo["unread_lines"] == 0)
    ok("unfiled PR and session found, filed PR not", [n["url"] for n in repo["not_filed"]] == ["https://x/pull/13", "https://s/1"])
    agent = [w["data"] for w in first["writes"] if w["path"] == "items/demo~D1"][0]
    ok("an Agent row is not approved", agent["approved"] is False and agent["kind"] == "resolved")
    ok("links point at the line", agent["url"].endswith("/blob/main/docs/DECISIONS.md#L6"))
    other = harvest(p, "other", "https://github.com/o/other", state, {})
    ok("a shared state file: no delete of another repo", not other["deletes"])
    save_state(state)
    hp = p / "docs/NEXT_PROMPT.md"
    hp.write_text(hp.read_text(encoding="utf-8").replace("- D4 · Tag v4.0.0 (see #12) · Options: done / not done · REC: done\n", ""),
                  encoding="utf-8")
    third = harvest(p, "demo", "https://github.com/o/demo", state, cross)
    ok("a closed need is deleted", third["deletes"] == ["items/demo~D4"])
    pr1 = {"pull_requests": [{"title": "Fix", "url": "https://x/pull/1"}]}
    ok("#1 is not #12", not_filed(pr1, "see #12. Fix") != [] and not_filed(pr1, "see https://x/pull/12") != [])
    ok("#1 is named", not_filed(pr1, "see #1.") == [] and not_filed(pr1, "(https://x/pull/1)") == [])
    ok("a session URL needs its end", not_filed({"sessions": [{"title": "T", "url": "https://s/1"}]}, "https://s/12") != [])
    return out


def edge_cases(base):
    """Self-test cases for lines the format check must fail, and --add-ids edge cases; returns [(name, passed)].

    Args:
        base: a temporary folder for the fixture projects.
    Returns:
        [(case name, True when it passed)].
    """
    out = []
    ok = lambda name, cond: out.append((name, bool(cond)))  # noqa: E731 (one-line recorder)
    rows = "| ID | Date | Decision | By | Replaces |\n|---|---|---|---|---|\n| D1 | 2026-11-18 | A. | the owner | - |\n"
    dup_need = HANDOFF_OK.replace("- D4 · Tag", "- D3 · Tag")
    ok("two needs with one ID fail", quiet(check, make_project(base, dup_need, rows))[0] == 1)
    ok("a need with a row's ID fails", quiet(check, make_project(base, HANDOFF_OK.replace("- D4 ·", "- D1 ·"), rows))[0] == 1)
    bad_date = rows + "| D9 | 19.11.2026 | y | the owner | - |\n| D8 | | z | the owner | - |\n"
    code, printed = quiet(check, make_project(base, HANDOFF_OK, bad_date))
    ok("rows with a bad or empty date fail", code == 1 and printed.count("DECISIONS.md:") == 2)
    ok("an escaped pipe is shown plain", read_project(make_project(base, HANDOFF_OK, rows.replace("| A. |", "| A \\| B. |")))[1][0]["text"] == "A | B.")
    ok("a lowercase ID row fails", quiet(check, make_project(base, HANDOFF_OK, rows + "| d4 | 2026-11-19 | x | the owner | - |\n"))[0] == 1)
    ok("an escaped pipe stays in its cell", quiet(check, make_project(base, HANDOFF_OK, rows.replace("| A. |", "| A \\| B. |")))[0] == 0)
    ok("a missing section fails", quiet(check, make_project(base, HANDOFF_OK.replace("## Timeline", "## Plan"), rows))[0] == 1)
    ok("a counted heading is read", quiet(check, make_project(base, HANDOFF_OK.replace("## Needs the owner", "## Needs the owner (2)"), rows))[0] == 0)
    p = make_project(base, HANDOFF_OK, DECISIONS_OLD.replace("\n", "\r\n") + "\r\n| Date | Other |\r\n|---|---|\r\n| 2026-01-01 | x |\r\n")
    ok("add-ids numbers only the first table", add_ids(p) == 2)
    ok("after add-ids the check passes (a second table is not read)", quiet(check, p)[0] == 0)
    raw = (p / "docs/DECISIONS.md").read_bytes()
    ok("add-ids keeps CRLF and the second table", b"| D1 | 2026-11-18 |" in raw and b"\r\n| 2026-01-01 | x |\r\n" in raw and b"\n\n" not in raw)
    return out


def selftest():
    """--test: run the cases in a temporary folder; print each failure and FLEET TEST PASS or FAIL; return the code."""
    with tempfile.TemporaryDirectory() as base:
        results = test_cases(base)
    failed = [n for n, passed in results if not passed]
    for n in failed:
        print("FAIL  " + n)
    print(("FLEET TEST PASS: %d cases" % len(results)) if not failed else "FLEET TEST FAIL: %d of %d" % (len(failed), len(results)))
    return 1 if failed else 0


def main(argv=None):
    """Parse the options and run the chosen mode; return its exit code.

    Args:
        argv: the arguments (default: sys.argv[1:]).
    Returns:
        The exit code.
    """
    ap = argparse.ArgumentParser(description="Fleet format check and harvest (see the file header).")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", nargs="?", const=".", metavar="ROOT")
    mode.add_argument("--harvest", metavar="ROOT")
    mode.add_argument("--add-ids", nargs="?", const=".", metavar="ROOT")
    mode.add_argument("--save-state", type=pathlib.Path, metavar="FILE")
    mode.add_argument("--test", action="store_true")
    ap.add_argument("--repo")
    ap.add_argument("--url")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--state", type=pathlib.Path)
    ap.add_argument("--cross", type=pathlib.Path)
    a = ap.parse_args(argv)
    if a.test:
        return selftest()
    if a.check:
        return check(pathlib.Path(a.check))
    if a.save_state:
        return save_state(a.save_state)
    if a.add_ids:
        print("added IDs to %d rows" % add_ids(pathlib.Path(a.add_ids)))
        return 0
    if not (a.repo and a.url):
        ap.error("--harvest needs --repo and --url")
    cross = json.loads(a.cross.read_text(encoding="utf-8")) if a.cross else {}
    print(json.dumps(harvest(pathlib.Path(a.harvest), a.repo, a.url.rstrip("/"), a.state, cross, a.branch), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
