#!/usr/bin/env python3
"""Report how a project repo differs from the archimedes_lever baseline. Report only: it never writes.

Usage:
    python3 scripts/drift.py [--project DIR] [--baseline PATH_OR_URL] [--owner NAME] [--strict]
    python3 scripts/drift.py --test        # self-test (cases: scripts/drift_test.py); prints DRIFT TEST PASS

For each "## " section of the baseline AGENTS.md above "## Project rules" (owner name and header placeholders
applied as sync_baseline.py would; --owner NAME for a repo with no "- Owner:" line, as for sync), it prints one of:
    same       the project has the section with the same text (whitespace ignored)
    changed    the project has a section with that heading but other text; NN% = text similarity,
               "missing lines" = baseline lines not found anywhere in the project AGENTS.md
    missing    no section with that heading
"## Commands" is project-owned and only checked for presence.
The project's "- Tier:" line (sync_baseline.header_tier) picks the baseline text and files: a starter project is not
compared with the advanced parts. For each file sync_baseline.py copies: same, differs or missing. For a file a
project may tune (sync_baseline.COPY_IF_MISSING): same, older (an earlier kit version that the project never changed:
a sync replaces it), tuned (the project changed it: a sync keeps it) or differs (the baseline has no git history to
tell which). It also checks the .claude/settings.json deny rules and hook events, the kit lock (.check.lock), and
docs/LOG.md (present, and "LOG CHECK PASS" from scripts/log_check.py).

The numbers say where a repo has drifted, not which side is right: a project may keep its own wording on purpose
(for example a repo whose rules predate the baseline). Use the report to choose hand edits or a sync.
Exit 0 always, unless --strict and something is not "same" (exit 1).
Standard library only; it imports sync_baseline.py from this folder for the shared parsing.
Network: the baseline repo, only when --baseline is a URL (one git clone); none for a local folder and in the self-test.
Writes: none (the self-test: temporary folders).
Credentials: none itself; a clone uses the credentials git already has.
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
    """The baseline AGENTS.md above "## Project rules", with the project's header values, tier and owner applied.

    Args:
        base_text: the text of the baseline AGENTS.md.
        proj_text: the text of the project's AGENTS.md (may be empty).
        owner: the owner word to put in place of the baseline's.
    Returns:
        The baseline text above "## Project rules" as a string.
    """
    cut = sb.find_heading(base_text, sb.RULES_HEADING)
    head = base_text[:cut] if cut >= 0 else base_text
    name, repo, purpose = sb.header_values(proj_text or "")
    tier = sb.header_tier(proj_text or "")
    for key, val in (("PROJECT_NAME", name), ("REPO", repo), ("PURPOSE", purpose), ("OWNER", sb.BASELINE_OWNER),
                     ("TIMEZONE", sb.header_timezone(proj_text or "")), ("TIER", tier),
                     ("SHORT_NAME", sb.header_short_name(proj_text, name))):
        if val:
            head = head.replace("{{" + key + "}}", val)
    return sb.apply_owner(sb.apply_tier(head, tier), owner)


def agents_rows(proj_text, head):
    """Rows for each baseline AGENTS.md section: same, changed (with similarity) or missing.

    Args:
        proj_text: the text of the project's AGENTS.md (may be empty).
        head: the baseline text from baseline_head().
    Returns:
        A list of ("AGENTS.md", section, status, detail) rows.
    """
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


TUNABLE = {"same": ("same", ""), "missing": ("missing", ""),
           "older": ("older", "an earlier kit version, never changed here: a sync replaces it"),
           "tuned": ("tuned", "changed by this project: a sync keeps it"),
           "unknown": ("differs", "may be tuned per project (the baseline has no git history to tell)")}


def file_rows(project, base, tier, owner):
    """Rows for each file sync_baseline.py copies in this tier.

    Args:
        project: the project folder.
        base: the baseline folder.
        tier: the project's tier.
        owner: the project's owner word.

    Returns:
        A list of ("file", path, status, detail): same, differs or missing; for a file a project may tune: same,
        older, tuned, differs or missing (sync_baseline.copy_state).
    """
    rows = []
    copy_files, copy_if_missing = sb.tier_files(tier)
    for rel in copy_files:
        src, dst = base / rel, project / rel
        if not src.exists():
            continue
        if not dst.exists():
            rows.append(("file", rel, "missing", ""))
            continue
        want = src.read_text()
        if rel not in sb.NO_OWNER_RENAME:
            want = sb.apply_owner(want, owner)
        rows.append(("file", rel, "same" if want == dst.read_text() else "differs", ""))
    for rel in copy_if_missing:
        if (base / rel).exists():
            rows.append(("file", rel, *TUNABLE[sb.copy_state(base, project, rel, owner)[0]]))
    return rows


def settings_rows(project, base):
    """Rows for the .claude/settings.json deny rules and hook events of the baseline.

    Args:
        project: the project folder.
        base: the baseline folder.
    Returns:
        A list of ("settings", item, status, detail) rows (empty when the baseline has no settings file).
    """
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
    """The row for the kit lock (.check.lock): missing, or same/differs against the baseline's HEAD.

    Args:
        project: the project folder.
        base: the baseline folder.
    Returns:
        One ("pin", ".check.lock", status, detail) row.
    """
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


LOG_ELSEWHERE_RE = re.compile(r"(?im)^\s*-\s*(?:\*\*)?project log\b[^\n]*?(https?://\S+|(?<![\w/])[\w.~-]*/[\w./~-]+)")


def log_kept_elsewhere(rules):
    """True when the Project rules name another place for the log: a line "- Project log ..." with a URL or a path
    (or, as before 2026-11-18, the words "project log location")."""
    return bool(LOG_ELSEWHERE_RE.search(rules) or re.search(r"(?i)project log location", rules))


def log_rows(project, base, proj_text, tier):
    """The row for docs/LOG.md (none in the starter tier): kept elsewhere, missing, or the log check's verdict.

    Args:
        project: the project folder.
        base: the baseline folder.
        proj_text: the text of the project's AGENTS.md.
        tier: the project's tier.
    Returns:
        A list with one ("log", "docs/LOG.md", status, detail) row, or an empty list.
    """
    log = project / "docs/LOG.md"
    checker = base / "scripts/log_check.py"
    rules = sb.section(proj_text, sb.RULES_HEADING) or ""
    if tier == "starter":
        return []  # no project log in the starter tier
    if not log.exists() and log_kept_elsewhere(rules):
        return [("log", "docs/LOG.md", "same", "kept elsewhere, named in Project rules")]
    if not log.exists():
        return [("log", "docs/LOG.md", "missing", "Project rules name no other place")]
    if checker.exists():
        r = subprocess.run([sys.executable, str(checker), str(log)], capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or ["?"])[-1]
        return [("log", "docs/LOG.md", "same" if r.returncode == 0 else "differs", last)]
    return []


def report(project, base, owner=None):
    """Return (rows, not_same_count). rows = list of (area, item, status, detail).

    Args:
        project: the project folder.
        base: the baseline folder.
        owner: the owner word, or None to read it from the project.
    Returns:
        (rows, not_same): the rows and the count of rows whose status is not "same".
    """
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


def self_test():
    """Compare sample projects with this baseline repo (the cases: scripts/drift_test.py); prints one line per
    case and DRIFT TEST PASS or FAIL.

    Returns:
        0 when every case passes or the test is skipped, else 1.
    """
    import drift_test  # scripts/drift_test.py: kept apart (docs/code-standard.md C4)
    return drift_test.run()


def main():
    """Parse the options; run the self-test, or fetch the baseline and print the drift report.

    Returns:
        The exit code: 0, or 1 when --strict is set and anything differs.
    """
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
