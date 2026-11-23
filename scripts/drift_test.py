#!/usr/bin/env python3
"""Self-test cases of scripts/drift.py (run by `python3 scripts/drift.py --test`; kept in its own file so drift.py
stays under the line cap of docs/code-standard.md C4). Kit only: projects do not get a copy.

It compares sample projects with this baseline repo: a legacy AGENTS.md, a synced one with the Maintainer renamed, a
copied file, the tiers, the settings merge, the place of the project log, the short name, a sync that keeps the
project's own files, and the files a project may tune.
Input: this baseline repo (its AGENTS.md must still hold its placeholders; elsewhere the test is skipped).
Output: one ok/FAIL line per case, then DRIFT TEST PASS or FAIL; run() returns the exit code.
Usage:   imported by scripts/drift.py (--test); `python3 -m unittest` and pytest find DriftTest.
Network: none.
Writes: temporary folders only.
Credentials: none.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sync_baseline as sb  # noqa: E402
from drift import file_rows, log_kept_elsewhere, report, sections  # noqa: E402 - scripts/drift.py, the code under test


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


def last_section(base):
    """Name of the last baseline AGENTS.md section above "Project rules" that is neither the first nor project-owned."""
    names = [h[3:] for h in sections((base / "AGENTS.md").read_text(), sb.RULES_HEADING)]
    return [n for n in names if n not in ("Order of authority", sb.COMMANDS_HEADING[3:])][-1]


def legacy_and_synced_cases(proj, base, results):
    """A legacy AGENTS.md drifts; a synced one with the Maintainer renamed is the same, also a copied file.

    Args:
        proj: an empty temporary project folder.
        base: the baseline folder.
        results: the list that gets True or False for each case.
    """
    get = lambda item: status(proj, base, item)  # noqa: E731
    last = last_section(base)
    (proj / "AGENTS.md").write_text("# Old rules\n\n## Order of authority\n\nBe careful.\n")
    expect(results, "legacy file: Project rules missing", get(("AGENTS.md", "Project rules")), "missing")
    expect(results, "changed section", get(("AGENTS.md", "Order of authority")), "changed")
    expect(results, "missing section", get(("AGENTS.md", last)), "missing")
    expect(results, "missing copied file", get(("file", "scripts/stop_check.py")), "missing")
    expect(results, "never synced", get(("pin", ".check.lock")), "missing")
    text = filled((base / "AGENTS.md").read_text(), (("PROJECT_NAME", "Demo"), ("REPO", "D/d"), ("PURPOSE", "P"),
                  ("OWNER", "the maintainer"), ("TIMEZONE", "Europe/Berlin")))
    (proj / "AGENTS.md").write_text(sb.apply_owner(sb.apply_tier(text.replace("{{TIER}}", "full"), "full"), "the maintainer"))
    expect(results, "synced section, owner renamed", get(("AGENTS.md", last)), "same")
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
    """sync merge of .claude/settings.json: the kit's deny rules and hook entries first; the project's own are kept.

    Args:
        tmp: an empty temporary folder.
        base: the baseline folder.
        results: the list that gets True or False for each case.
    """
    kit_pre = json.loads((base / ".claude/settings.json").read_text())["hooks"]["PreToolUse"]
    kit_cmd = kit_pre[0]
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
           [pre[0] == kit_cmd, own in pre, old_kit not in pre, len(pre)], [True, True, True, len(kit_pre) + 1])
    same(results, "merge: a mixed entry keeps only the project's command",
           [h["command"] for e in stop[1:] for h in e["hooks"]], ["python3 tools/own_stop.py"])
    same(results, "merge: the matcher of a replaced kit entry is noted", sb.REPLACED_HOOKS, ["^(Agent|mcp__slack__post)$"])
    kit_matcher = next(e.get("matcher") for e in json.loads((base / ".claude/settings.json").read_text())["hooks"]["PreToolUse"])
    same(results, "merge: a replaced entry with the kit's own matcher gets no note",
         sb.changed_matchers(["^(Agent|mcp__slack__post)$", kit_matcher], base / ".claude/settings.json"), ["^(Agent|mcp__slack__post)$"])
    deny = got["permissions"]["deny"]
    same(results, "merge: the kit deny rules first, the project's rule last",
           [deny[:len(sb.check_blocks.DENY)] == sb.check_blocks.DENY, deny[-1]], [True, "Bash(own rule*)"])


def log_place_cases(results):
    """The log row: a "- Project log" line that names a URL or a path means the log is kept elsewhere."""
    line = "- Project log: https://claude.ai/artifact/XXXX (private Claude doc; the Administrator, 2026-11-14). Never in this repo.\n"
    same(results, "log elsewhere: a URL", log_kept_elsewhere("## Project rules\n\n" + line), True)
    same(results, "log elsewhere: a path, any case", log_kept_elsewhere("- project LOG: notes/private/log.md\n"), True)
    same(results, "log elsewhere: the old wording", log_kept_elsewhere("- Project log location: the wiki\n"), True)
    same(results, "log elsewhere: the bold-label form", log_kept_elsewhere("- **Project log.** https://claude.ai/artifact/XXXX (private).\n"), True)
    same(results, "log elsewhere: a line with no place", log_kept_elsewhere("- Project log: kept short.\n"), False)
    same(results, "log elsewhere: another rule that names a URL", log_kept_elsewhere("- Docs: https://example.com/x\n"), False)


def run_apply(proj, base):
    """Run sync_baseline.py --apply in the project folder, with no GIT_* variables; return the exit code."""
    env = {k: v for k, v in __import__("os").environ.items() if not k.startswith("GIT_")}
    r = subprocess.run([sys.executable, str(pathlib.Path(sb.__file__)), "--apply", "--baseline", str(base)],
                       cwd=proj, env=env, capture_output=True, text=True)
    return r.returncode


def apply_keeps_project_files_case(tmp, base, results):
    """A sync --apply keeps a skill's PROJECT.md and the project's own hook entry in settings.json, unchanged.

    Args:
        tmp: an empty temporary folder.
        base: the baseline folder.
        results: the list that gets True or False for each case.
    """
    proj = tmp / "apply"
    (proj / ".claude/skills/deliver").mkdir(parents=True)
    project_md = proj / ".claude/skills/deliver/PROJECT.md"
    project_md.write_text("Project addition to the deliver skill.\n")
    own = {"matcher": "^Bash$", "hooks": [{"type": "command", "command": "python3 tools/own_hook.py"}]}
    (proj / ".claude/settings.json").write_text(json.dumps({"hooks": {"PostToolUse": [own]}}))
    (proj / "AGENTS.md").write_text("# Demo: agent instructions\n\n- Repo: D/d\n- Purpose: P\n- Owner: the maintainer\n"
                                    "- Time zone: UTC\n- Tier: full\n\n## Commands\n\n- Test: none.\n\n## Project rules\n\n- Own rule.\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t" + "@" + "users.noreply.github.com"]
    for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "start"]):
        subprocess.run(git + cmd, cwd=proj, check=True, capture_output=True)
    code = run_apply(proj, base)
    got = json.loads((proj / ".claude/settings.json").read_text())["hooks"]["PostToolUse"]
    same(results, "apply: exit 0, PROJECT.md and the own hook entry kept",
         [code, project_md.read_text(), own in got], [0, "Project addition to the deliver skill.\n", True])


def tier_cases(proj, base, results):
    """A starter project is not compared with the advanced parts; apply_tier, header_tier and set_tier work.

    Args:
        proj: an empty temporary project folder.
        base: the baseline folder.
        results: the list that gets True or False for each case.
    """
    get = lambda item: status(proj, base, item)  # noqa: E731
    text = filled((base / "AGENTS.md").read_text(), (("PROJECT_NAME", "Demo"), ("REPO", "D/d"), ("PURPOSE", "P"),
                  ("OWNER", "the Maintainer"), ("TIMEZONE", "UTC"), ("TIER", "starter")))
    (proj / "AGENTS.md").write_text(sb.apply_tier(text, "starter"))
    expect(results, "starter: no Project log section expected", get(("AGENTS.md", "Project log")), "absent")
    same(results, "starter: no Project log bullet", "**Project log.**" in (proj / "AGENTS.md").read_text(), False)
    expect(results, "starter: last section same", get(("AGENTS.md", last_section(base))), "same")
    expect(results, "starter: advanced file not expected", get(("file", ".claude/skills/delegate/SKILL.md")), "absent")
    expect(results, "starter: no log row", get(("log", "docs/LOG.md")), "absent")
    full = sb.apply_tier(text.replace("- Tier: starter", "- Tier: full"), "full")
    good = "<!--" not in full.replace("<!-- Fill in", "").replace("<!-- This project", "") and ("## Project log" in full or "**Project log.**" in full)
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
    good = not left and "- Tier: starter" in agents and "## Project log" not in agents and "**Project log.**" not in agents and "<!-- full" not in agents
    print(("ok   " if good else "FAIL ") + f"set_tier starter: advanced files gone ({len(left)} left), AGENTS.md filtered")
    results.append(good)


def tunable_cases(tmp, results):
    """The files a project may tune, against a small baseline repo with two commits: a sync adds a missing file,
    replaces an earlier kit version (with or without the Maintainer word applied), keeps a tuned file and says how to
    compare; the drift report gives the same states.

    Args:
        tmp: an empty temporary folder.
        results: the list that gets True or False for each case.
    """
    base, proj = tmp / "kit", tmp / "proj"
    rels = ["docs/A_SAMPLE.md", "docs/B_SAMPLE.md", "docs/FIRST_USE.md"]  # two sample names and the kit's one tunable file
    kept, sb.COPY_IF_MISSING = sb.COPY_IF_MISSING, rels  # the drift report reads this list
    try:
        run = lambda *a: subprocess.run(["git", "-C", str(base), "-c", "user.email=t@example.invalid", "-c", "user.name=t",  # noqa: E731
                                         "-c", "commit.gpgsign=false", *a], check=True, capture_output=True)
        for version in ("one", "two"):
            for rel in rels:
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_text(f"Version {version} of {rel}. Ask the Maintainer.\n")
            if version == "one":
                run("init", "-q")
            run("add", "-A")
            run("commit", "-q", "-m", version)
        v1 = lambda rel: f"Version one of {rel}. Ask the Maintainer.\n"  # noqa: E731
        put = lambda rel, text: ((proj / rel).parent.mkdir(parents=True, exist_ok=True), (proj / rel).write_text(text))  # noqa: E731
        put(rels[0], sb.apply_owner(v1(rels[0]), "the maintainer"))   # an earlier kit version, as a sync wrote it
        put(rels[2], v1(rels[2]) + "Our own place for the list.\n")    # tuned
        new, notes = sb.plan_if_missing(base, proj, rels, "the maintainer")
        same(results, "tunable: an earlier kit version is replaced, a missing file is added, a tuned file is kept",
             new, {rels[0]: f"Version two of {rels[0]}. Ask the maintainer.\n", rels[1]: f"Version two of {rels[1]}. Ask the maintainer.\n"})
        same(results, "tunable: one line for the replaced file, one for the kept file with the compare command",
             [n.split(":")[0] for n in notes] + [notes[1].endswith(f"Compare: diff {base}/{rels[2]} {rels[2]}"), "replaced" in notes[0]],
             [rels[0], rels[2], True, True])
        state = lambda rel: status_of(proj, base, rel)  # noqa: E731
        same(results, "tunable: drift names the three states and a missing file",
             [state(r) for r in rels], ["older", "missing", "tuned"])
        put(rels[2], v1(rels[2]))   # FIRST_USE.md is never renamed: the plain earlier version is an older copy too
        put(rels[1], f"Version two of {rels[1]}. Ask the maintainer.\n")
        same(results, "tunable: the plain earlier version is older; the current version is the same",
             [state(rels[2]), state(rels[1]), sorted(sb.plan_if_missing(base, proj, rels, "the maintainer")[0])], ["older", "same", [rels[0], rels[2]]])
        shutil.rmtree(base / ".git")
        new, notes = sb.plan_if_missing(base, proj, rels, "the maintainer")
        same(results, "tunable: a baseline with no git history keeps each file that differs, and says so",
             [new, len(notes), all("no git history" in n for n in notes), state(rels[0])], [{}, 2, True, "differs"])
    finally:
        sb.COPY_IF_MISSING = kept


def status_of(proj, base, rel):
    """The status of one file row of the drift report (the files only, so the sample baseline needs no AGENTS.md)."""
    return {item: s for _, item, s, _ in file_rows(proj, base, "full", "the maintainer")}.get(rel, "absent")


def short_name_cases(base, results):
    """The "- Short name:" header (kit 4.0.0): the line, a placeholder, the fallback, --short-name, and a synced header.

    Args:
        base: the baseline folder (its AGENTS.md has the {{SHORT_NAME}} placeholder).
        results: the list that gets one bool per case.
    """
    cases = (
        ("the line wins", sb.header_short_name("- Short name: RADE\n", "Other"), "RADE"),
        ("a placeholder falls back to the name", sb.header_short_name("- Short name: {{SHORT_NAME}}\n", "ICF Companion"), "ICF"),
        ("no line: the first word of the name", sb.header_short_name("# x\n", "SEC2 (Security+ Companion)"), "SEC2"),
        ("no line and no name", sb.header_short_name(None, None), None),
    )
    for label, got, want in cases:
        results.append(got == want)
        print(("ok   " if got == want else "FAIL ") + f"short name: {label} (got {got!r})")
    proj = ("# No More Beyond: agent instructions\n\n- Repo: o/r\n- Purpose: P\n- Time zone: UTC\n- Tier: full\n"
            "\n## Project rules\n")
    base_text = (base / "AGENTS.md").read_text()
    for label, flag, want in (("--short-name wins over the name", "NMB", "- Short name: NMB\n"),
                              ("a sync fills the first word", None, "- Short name: No\n")):
        args = argparse.Namespace(name=None, repo=None, purpose=None, timezone=None, short_name=flag)
        good = want in sb.build_agents(base_text, proj, args, "the Maintainer")
        results.append(good)
        print(("ok   " if good else "FAIL ") + f"short name: {label}")


def run():
    """Compare sample projects with this baseline repo; prints one line per case and DRIFT TEST PASS or FAIL.

    Returns:
        0 when every case passes or the test is skipped, else 1.
    """
    base = pathlib.Path(__file__).resolve().parent.parent
    if "{{PROJECT_NAME}}" not in (base / "AGENTS.md").read_text():
        print("DRIFT TEST SKIP: the self-test needs the baseline repo (the kit, kit.config.json kit_repo); run it there")
        return 0
    results = []
    with tempfile.TemporaryDirectory() as d:
        proj = pathlib.Path(d)
        legacy_and_synced_cases(proj, base, results)
        tier_cases(proj, base, results)
        settings_merge_cases(proj, base, results)
        log_place_cases(results)
        short_name_cases(base, results)
        apply_keeps_project_files_case(proj, base, results)
    with tempfile.TemporaryDirectory() as d:
        tunable_cases(pathlib.Path(d), results)
    ok = all(results)
    print("DRIFT TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


class DriftTest(unittest.TestCase):
    """The cases of `python3 scripts/drift.py --test`, for `python3 -m unittest` and pytest."""

    def test_self_test(self):
        """Every case passes (or the test is skipped outside the baseline repo)."""
        self.assertEqual(run(), 0)
