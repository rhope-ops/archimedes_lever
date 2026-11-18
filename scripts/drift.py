#!/usr/bin/env python3
"""Report how a project repo differs from the archimedes_lever baseline. Report only: it never writes.

Usage:
    python3 scripts/drift.py [--project DIR] [--baseline PATH_OR_URL] [--owner NAME] [--strict]
    python3 scripts/drift.py --test        # self-test; prints DRIFT TEST PASS

For each "## " section of the baseline AGENTS.md above "## Project rules" (owner name and header placeholders
applied as sync_baseline.py would; --owner NAME for a repo with no "- Owner:" line, as for sync), it prints one of:
    same       the project has the section with the same text (whitespace ignored)
    changed    the project has a section with that heading but other text; NN% = text similarity,
               "missing lines" = baseline lines not found anywhere in the project AGENTS.md
    missing    no section with that heading
"## Commands" is project-owned and only checked for presence.
The project's "- Tier:" line (sync_baseline.header_tier) picks the baseline text and files: a starter project is not
compared with the advanced parts. For each file sync_baseline.py copies: same, differs or missing. It also checks the .claude/settings.json deny rules
and hook events, the kit lock (.check.lock), and docs/LOG.md (present, and "LOG CHECK PASS" from scripts/log_check.py).

The numbers say where a repo has drifted, not which side is right: a project may keep its own wording on purpose
(for example a repo whose rules predate the baseline). Use the report to choose hand edits or a sync.
Exit 0 always, unless --strict and something is not "same" (exit 1).
Standard library only; it imports sync_baseline.py from this folder for the shared parsing.
"""
import argparse
import difflib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sync_baseline as sb  # noqa: E402

PROJECT_OWNED = {sb.COMMANDS_HEADING}


def norm(text):
    """text with each run of whitespace made one space, trimmed (so layout changes compare the same)."""
    return re.sub(r"\s+", " ", text).strip()


def sections(text, stop=None):
    """Return {heading_line: section_text} for '## ' headings outside code fences, up to `stop` if given."""
    marks = list(sb.headings(text))
    out = {}
    for i, (pos, line) in enumerate(marks):
        if stop and line == stop:
            break
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.setdefault(line, text[pos:end])
    return out


def baseline_head(base_text, proj_text, owner):
    """The baseline AGENTS.md above "## Project rules", with the project's header values, tier and owner applied."""
    cut = sb.find_heading(base_text, sb.RULES_HEADING)
    head = base_text[:cut] if cut >= 0 else base_text
    name, repo, purpose = sb.header_values(proj_text or "")
    tier = sb.header_tier(proj_text or "")
    for key, val in (("PROJECT_NAME", name), ("REPO", repo), ("PURPOSE", purpose), ("OWNER", sb.BASELINE_OWNER),
                     ("TIMEZONE", sb.header_timezone(proj_text or "")), ("TIER", tier)):
        if val:
            head = head.replace("{{" + key + "}}", val)
    return sb.apply_owner(sb.apply_tier(head, tier), owner)


def agents_rows(proj_text, head):
    """Rows for each baseline AGENTS.md section: same, changed (with similarity) or missing."""
    rows = []
    proj_secs = sections(proj_text)
    proj_lines = {norm(l) for l in proj_text.splitlines() if norm(l)}
    if not proj_text:
        rows.append(("AGENTS.md", "file", "missing", ""))
    for heading, body in sections(head).items():
        name = heading[3:]
        if heading not in proj_secs:
            rows.append(("AGENTS.md", name, "missing", ""))
            continue
        if heading in PROJECT_OWNED:
            rows.append(("AGENTS.md", name, "same", "project-owned; presence only"))
            continue
        a, b = norm(body), norm(proj_secs[heading])
        if a == b:
            rows.append(("AGENTS.md", name, "same", ""))
            continue
        ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        lines = [norm(l) for l in body.splitlines()[1:] if norm(l)]
        gone = sum(1 for l in lines if l not in proj_lines)
        rows.append(("AGENTS.md", name, "changed", f"{ratio:.0%} similar; {gone}/{len(lines)} baseline lines missing"))
    if sb.find_heading(proj_text, sb.RULES_HEADING) < 0 and proj_text:
        rows.append(("AGENTS.md", "Project rules", "missing", "no baseline layout; sync would migrate the whole file"))
    return rows


def file_rows(project, base, tier, owner):
    """Rows for each file sync_baseline.py copies in this tier: same, differs or missing."""
    rows = []
    copy_files, copy_if_missing = sb.tier_files(tier)
    for rel in copy_files + copy_if_missing:
        src, dst = base / rel, project / rel
        if not src.exists():
            continue
        if not dst.exists():
            rows.append(("file", rel, "missing", ""))
            continue
        want = src.read_text()
        if rel not in sb.NO_OWNER_RENAME:
            want = sb.apply_owner(want, owner)
        rows.append(("file", rel, "same" if want == dst.read_text() else "differs",
                     "may be tuned per project" if rel in sb.COPY_IF_MISSING and want != dst.read_text() else ""))
    return rows


def settings_rows(project, base):
    """Rows for the .claude/settings.json deny rules and hook events of the baseline."""
    rows = []
    bset, pset = base / ".claude/settings.json", project / ".claude/settings.json"
    if bset.exists():
        try:
            b = json.loads(bset.read_text())
            p = json.loads(pset.read_text()) if pset.exists() else {}
            deny_missing = [r for r in b.get("permissions", {}).get("deny", [])
                            if r not in (p.get("permissions") or {}).get("deny", [])]
            rows.append(("settings", "deny rules", "same" if not deny_missing else "differs",
                         f"{len(deny_missing)} missing: {', '.join(deny_missing)}" if deny_missing else ""))
            for event in (b.get("hooks") or {}):
                mine = (p.get("hooks") or {}).get(event) or []
                gone = [e for e in b["hooks"][event] if e not in mine]
                rows.append(("settings", f"hook {event}", "missing" if not mine else "differs" if gone else "same",
                             "the project's entries differ from the kit's hook" if mine and gone else ""))
        except (ValueError, AttributeError) as e:
            rows.append(("settings", ".claude/settings.json", "differs", f"not valid JSON ({e})"))
    return rows


def pin_row(project, base):
    """The row for the kit lock (.check.lock): missing, or same/differs against the baseline's HEAD."""
    try:
        base_sha = sb.git("rev-parse", "HEAD", cwd=base)
    except subprocess.CalledProcessError:
        base_sha = None
    try:
        lock = sb.check_lock.load(project)
    except ValueError:
        lock = None
    if lock is None:
        return ("pin", ".check.lock", "missing", "never synced with the kit lock")
    sha = str(lock.get("commit", ""))
    same = bool(base_sha) and base_sha.startswith(sha[:7]) and sha[:7] != ""
    return ("pin", ".check.lock", "same" if same else "differs",
            f"pinned {sha[:7] or '?'}, baseline {base_sha[:7] if base_sha else '?'}")


def log_rows(project, base, proj_text, tier):
    """The row for docs/LOG.md (none in the starter tier): kept elsewhere, missing, or the log check's verdict."""
    log = project / "docs/LOG.md"
    checker = base / "scripts/log_check.py"
    rules = sb.section(proj_text, sb.RULES_HEADING) or ""
    if tier == "starter":
        return []  # no project log in the starter tier
    if not log.exists() and re.search(r"(?i)project log location", rules):
        return [("log", "docs/LOG.md", "same", "kept elsewhere, named in Project rules")]
    if not log.exists():
        return [("log", "docs/LOG.md", "missing", "Project rules name no other place")]
    if checker.exists():
        r = subprocess.run([sys.executable, str(checker), str(log)], capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or ["?"])[-1]
        return [("log", "docs/LOG.md", "same" if r.returncode == 0 else "differs", last)]
    return []


def report(project, base, owner=None):
    """Return (rows, not_same_count). rows = list of (area, item, status, detail)."""
    proj_agents = project / "AGENTS.md"
    proj_text = proj_agents.read_text() if proj_agents.exists() else ""
    owner = owner or sb.header_owner(proj_text) or sb.BASELINE_OWNER
    base_text = (base / "AGENTS.md").read_text()
    rows = agents_rows(proj_text, baseline_head(base_text, proj_text, owner))
    tier = sb.header_tier(proj_text)
    rows += file_rows(project, base, tier, owner)
    rows += settings_rows(project, base)
    rows.append(pin_row(project, base))
    rows += log_rows(project, base, proj_text, tier)
    not_same = sum(1 for r in rows if r[2] != "same")
    return rows, not_same


def print_report(project, rows, not_same):
    """Print one line per row and the DRIFT summary line."""
    print(f"Drift report: {project}")
    width = max(len(f"{a}: {i}") for a, i, _, _ in rows) if rows else 10
    for area, item, status, detail in rows:
        print(f"  {status:8} {(area + ': ' + item):<{width}}  {detail}".rstrip())
    print(f"DRIFT: {not_same} of {len(rows)} item(s) not the same as the baseline")


def status(proj, base, item):
    """(status, detail) of one (area, item) in the report of proj, or ("absent", "")."""
    rows, _ = report(proj, base)
    return {(a, i): (s, det) for a, i, s, det in rows}.get(item, ("absent", ""))


def expect(results, name, got, want):
    """Print one ok/FAIL line for a (status, detail) against the wanted status; record the result."""
    good = got[0] == want
    print(("ok   " if good else "FAIL ") + f"{name}: {got[0]} {got[1]}".rstrip())
    results.append(good)


def filled(text, values):
    """text with each {{KEY}} placeholder in values replaced."""
    for k, v in values:
        text = text.replace("{{" + k + "}}", v)
    return text


def legacy_and_synced_cases(proj, base, results):
    """A legacy AGENTS.md drifts; a synced one with the owner renamed is the same, also a copied file."""
    get = lambda item: status(proj, base, item)  # noqa: E731
    (proj / "AGENTS.md").write_text("# Old rules\n\n## Git safety\n\nBe careful.\n")
    expect(results, "legacy file: Project rules missing", get(("AGENTS.md", "Project rules")), "missing")
    expect(results, "changed section", get(("AGENTS.md", "Git safety")), "changed")
    expect(results, "missing section", get(("AGENTS.md", "Delegation")), "missing")
    expect(results, "missing copied file", get(("file", "scripts/stop_check.py")), "missing")
    expect(results, "never synced", get(("pin", ".check.lock")), "missing")
    text = filled((base / "AGENTS.md").read_text(), (("PROJECT_NAME", "Demo"), ("REPO", "D/d"), ("PURPOSE", "P"),
                  ("OWNER", "the maintainer"), ("TIMEZONE", "Europe/Berlin")))
    (proj / "AGENTS.md").write_text(sb.apply_owner(sb.apply_tier(text.replace("{{TIER}}", "full"), "full"), "the maintainer"))
    expect(results, "synced section, owner renamed", get(("AGENTS.md", "Delegation")), "same")
    expect(results, "Project rules present", get(("AGENTS.md", "Project rules")), "absent")
    (proj / "scripts").mkdir()
    (proj / "scripts/stop_check.py").write_text(sb.apply_owner((base / "scripts/stop_check.py").read_text(), "the maintainer"))
    expect(results, "copied file, owner renamed", get(("file", "scripts/stop_check.py")), "same")
    text = filled((base / "AGENTS.md").read_text().replace("- Owner: {{OWNER}}\n", ""),
                  (("PROJECT_NAME", "Demo"), ("REPO", "D/d"), ("PURPOSE", "P"), ("TIMEZONE", "UTC")))
    (proj / "AGENTS.md").write_text(sb.apply_owner(text, "Sam"))
    rows, _ = report(proj, base, "Sam")
    expect(results, "no Owner line, --owner Sam", {(a, i): (s, d) for a, i, s, d in rows}[("AGENTS.md", "Order of authority")], "same")


def same(results, name, got, want):
    """Record and print one case of the settings merge: got must equal want."""
    results.append(got == want)
    print(("ok   " if got == want else "FAIL ") + name + ("" if got == want else f": got {got}"))


def settings_merge_cases(tmp, base, results):
    """sync merge of .claude/settings.json: the kit's deny rules and hook entries first; the project's own are kept."""
    kit_cmd = json.loads((base / ".claude/settings.json").read_text())["hooks"]["PreToolUse"][0]
    own = {"matcher": "^Bash$", "hooks": [{"type": "command", "command": "python3 tools/own_guard.py"}]}
    mixed = {"hooks": [{"type": "command", "command": "python3 scripts/stop_check.py"},
                       {"type": "command", "command": "python3 tools/own_stop.py"}]}
    old_kit = {"matcher": "^(Agent|mcp__slack__post)$", "hooks": [{"type": "command", "command": "python3 scripts/pii_guard.py --hook"}]}
    path = tmp / "settings.json"
    path.write_text(json.dumps({"permissions": {"deny": ["Bash(own rule*)"]},
                                "hooks": {"PreToolUse": [old_kit, own], "Stop": [mixed]}}))
    sb.REPLACED_HOOKS.clear()
    got = json.loads(sb.merge_settings(base / ".claude/settings.json", path))
    pre, stop = got["hooks"]["PreToolUse"], got["hooks"]["Stop"]
    same(results, "merge: the kit hook first, the project's own entry kept, the older kit copy gone",
           [pre[0] == kit_cmd, own in pre, old_kit not in pre, len(pre)], [True, True, True, 2])
    same(results, "merge: a mixed entry keeps only the project's command",
           [h["command"] for e in stop[1:] for h in e["hooks"]], ["python3 tools/own_stop.py"])
    same(results, "merge: the matcher of a replaced kit entry is noted", sb.REPLACED_HOOKS, ["^(Agent|mcp__slack__post)$"])
    deny = got["permissions"]["deny"]
    same(results, "merge: the kit deny rules first, the project's rule last",
           [deny[:len(sb.check_blocks.DENY)] == sb.check_blocks.DENY, deny[-1]], [True, "Bash(own rule*)"])


def tier_cases(proj, base, results):
    """A starter project is not compared with the advanced parts; apply_tier, header_tier and set_tier work."""
    get = lambda item: status(proj, base, item)  # noqa: E731
    text = filled((base / "AGENTS.md").read_text(), (("PROJECT_NAME", "Demo"), ("REPO", "D/d"), ("PURPOSE", "P"),
                  ("OWNER", "the owner"), ("TIMEZONE", "UTC"), ("TIER", "starter")))
    (proj / "AGENTS.md").write_text(sb.apply_tier(text, "starter"))
    expect(results, "starter: no Project log section expected", get(("AGENTS.md", "Project log")), "absent")
    expect(results, "starter: Delegation same", get(("AGENTS.md", "Delegation")), "same")
    expect(results, "starter: advanced file not expected", get(("file", ".claude/skills/delegate/SKILL.md")), "absent")
    expect(results, "starter: no log row", get(("log", "docs/LOG.md")), "absent")
    full = sb.apply_tier(text.replace("- Tier: starter", "- Tier: full"), "full")
    good = "<!--" not in full.replace("<!-- Fill in", "").replace("<!-- This project", "") and "## Project log" in full
    print(("ok   " if good else "FAIL ") + "apply_tier full: markers gone, Project log kept")
    results.append(good)
    good = sb.header_tier("- Tier: Starter\n") == "starter" and sb.header_tier("# old\n") == "full"
    print(("ok   " if good else "FAIL ") + "header_tier: any case; no line = full")
    results.append(good)
    st = proj / "st"
    (st / ".claude").mkdir(parents=True)
    (st / "AGENTS.md").write_text((base / "AGENTS.md").read_text())
    for rel in sb.ADVANCED_FILES:
        (st / rel).parent.mkdir(parents=True, exist_ok=True)
        (st / rel).write_text("x")
    with __import__("contextlib").redirect_stdout(__import__("io").StringIO()):
        sb.set_tier(st, "starter")
    left = [r for r in sb.ADVANCED_FILES if (st / r).exists()]
    agents = (st / "AGENTS.md").read_text()
    good = not left and "- Tier: starter" in agents and "## Project log" not in agents and "<!-- full" not in agents
    print(("ok   " if good else "FAIL ") + f"set_tier starter: advanced files gone ({len(left)} left), AGENTS.md filtered")
    results.append(good)


def self_test():
    """Compare sample projects with this baseline repo; prints one line per case and DRIFT TEST PASS or FAIL."""
    base = pathlib.Path(__file__).resolve().parent.parent
    if "{{PROJECT_NAME}}" not in (base / "AGENTS.md").read_text():
        print("DRIFT TEST SKIP: the self-test needs the baseline repo (rhope-ops/archimedes_lever); run it there")
        return 0
    results = []
    with tempfile.TemporaryDirectory() as d:
        proj = pathlib.Path(d)
        legacy_and_synced_cases(proj, base, results)
        tier_cases(proj, base, results)
        settings_merge_cases(proj, base, results)
    ok = all(results)
    print("DRIFT TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    """Parse the options; run the self-test, or fetch the baseline and print the drift report."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project", default=".", help="project repo folder (default: current folder)")
    ap.add_argument("--baseline", default=sb.DEFAULT_BASELINE, help="baseline folder or git URL")
    ap.add_argument("--owner", help="owner name for a project AGENTS.md without a \"- Owner:\" line")
    ap.add_argument("--strict", action="store_true", help="exit 1 when anything is not the same")
    ap.add_argument("--test", action="store_true", help="run the self-test")
    a = ap.parse_args()
    if a.test:
        return self_test()
    project = pathlib.Path(a.project).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        base = sb.get_baseline(a.baseline, tmp)
        rows, not_same = report(project, base, a.owner)
        print_report(project, rows, not_same)
    return 1 if a.strict and not_same else 0


if __name__ == "__main__":
    sys.exit(main())
