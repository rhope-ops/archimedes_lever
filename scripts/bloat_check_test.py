#!/usr/bin/env python3
"""Self-test of scripts/bloat_check.py (run by `python3 scripts/bloat_check.py --test`).

It builds small sample repos in temporary folders and proves each measure: duplicates, big files, the audit due date
(also for a repo never audited, a new repo and a shallow clone), timings, the rule count by place, the caps, the
paths AGENTS.md names, the README check, the third-party budget, the conflict gate, the rule lint, the start-read
warning, --compare and --record, the settings in `.check` and the state in `.check.state.json`, the skills check,
tool rows (T1), script lines ratchet (T2), role word (T6), debt record (T5), fleet audit (R3) and archive due.
Input: the bloat_check module. Output: BLOAT TEST PASS, or an AssertionError naming the case. Needs git.
Network: none.
Writes: temporary repos only.
Credentials: none.
"""
import argparse
import contextlib
import datetime
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_settings

LONG = "This line is long enough to count as a duplicate when it shows up in two different files of a repo."


def git_in(folder, *args):
    """Run one git command in folder as a throwaway test user; fail the test on an error."""
    subprocess.run(["git", "-C", folder, "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True,
                   capture_output=True)


def git_in_out(folder, *args):
    """The output of one git command in folder, stripped."""
    return subprocess.run(["git", "-C", folder, *args], check=True, capture_output=True, text=True).stdout.strip()


def settings(root, lines="", **state):
    """Write the repo's .check (setting lines) and replace its .check.state.json with these parts."""
    (root / check_settings.CHECK).write_text(lines)
    (root / check_settings.STATE).write_text(json.dumps(state))


def sample_repo(bloat, root):
    """A repo with a duplicate line, a long handoff, a big file and settings with low budgets; returns its config.

    Args:
        bloat: the module under test.
        root: an empty temporary folder (a Path).

    Returns:
        The audit settings of the sample repo.
    """
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "AGENTS.md").write_text(f"# A\n- {LONG}\n")
    (root / "docs").mkdir()
    (root / "docs/NEXT_PROMPT.md").write_text(f"{LONG.upper()}\n" + "x\n" * 45)
    (root / "big.txt").write_text("y" * 3000)
    (root / "scripts").mkdir()
    (root / "scripts/ok.sh").write_text("exit 0\n")  # the timed commands must start with "bash scripts/"
    (root / "scripts/fail.sh").write_text("exit 1\n")
    settings(root, "audit-budget-file_kb: 2\naudit-budget-session_load_tokens: 10\n",
             audit={"last_audit": {"date": "2026-01-01"}}, timings={"t": {"cmd": "bash scripts/ok.sh", "seconds": 5}})
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return bloat.load_config(root)


def sample_kit(d, files):
    """A sample repo in folder d with these files ({path: text}) and kit.config.json, committed and set as origin/main.

    Args:
        d: an empty temporary folder (a Path).
        files: the files to write.

    Returns:
        The folder d.
    """
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    for rel, text in {"kit.config.json": "{}", **files}.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text)
    git_in(d, "add", "-A")
    git_in(d, "commit", "-qm", "base")
    git_in(d, "update-ref", "refs/remotes/origin/main", "HEAD")
    return d


def generated_block_cases(bloat, root, cfg):
    """Duplicates: the lines of a marked generated block are not counted; a line after its end marker is.

    Args:
        bloat: the module under test.
        root: the sample repo of sample_repo (a Path); it is left as it was.
        cfg: its audit settings.
    """
    gen = "x = 1\n# >>> blk: generated from src by build (do not edit)\n" + "g" * 90 + "\n# <<< blk\n"
    (root / "g1.ps1").write_text(gen)
    (root / "g2.ps1").write_text(gen + "h" * 90 + "\n")
    (root / "g3.ps1").write_text("h" * 90 + "\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    assert len(bloat.duplicates(root, bloat.scan_files(root, cfg))) == 2, "generated block not counted; a line after its end marker is"
    for g in ("g1.ps1", "g2.ps1", "g3.ps1"):
        (root / g).unlink()
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)


def metrics_cases(bloat, root, cfg):
    """Duplicates, big files, the audit due date by days, and a never-audited repo with no commits."""
    files = bloat.scan_files(root, cfg)
    assert len(bloat.duplicates(root, files)) == 1, "duplicate across files, case and bullets ignored"
    assert [f for f, _ in bloat.big_files(root, files, 2)] == ["big.txt"], "big file"
    assert "days since" in bloat.audit_due(root, cfg, datetime.date(2026, 2, 1)), "due by days"
    assert bloat.audit_due(root, cfg, datetime.date(2026, 1, 5)) == "", "not due"
    never = {**cfg, "last_audit": None}
    assert bloat.audit_due(root, never, datetime.date(2026, 1, 5)) == "never audited", "no commits: due"
    return never


def duplicate_ignore_cases(bloat, root, cfg):
    """Duplicates: a file an `audit-duplicate-ignore:` glob matches is not read by the duplicate count, and stays in
    the files the other measures read; `audit-ignore:` is a separate list.

    Args:
        bloat: the module under test.
        root: the sample repo of sample_repo (a Path); its .check is left as it was.
        cfg: its audit settings.
    """
    keep = (root / check_settings.CHECK).read_text()
    (root / check_settings.CHECK).write_text(keep + "audit-duplicate-ignore: docs/*\naudit-duplicate-ignore: x.md\n")
    got = bloat.load_config(root)
    files = bloat.scan_files(root, got)
    assert "docs/NEXT_PROMPT.md" in files and "docs/NEXT_PROMPT.md" not in bloat.dup_files(files, got), "only the count skips it"
    assert bloat.duplicates(root, bloat.dup_files(files, got)) == [] and len(bloat.duplicates(root, files)) == 1, \
        "the duplicate in the ignored file is not counted"
    assert got["ignore"] == [] and bloat.ignored("x.md", got, "duplicate_ignore"), "a list apart from audit-ignore"
    (root / check_settings.CHECK).write_text(keep)


def never_audited_cases(bloat, never):
    """A never-audited repo: not due when new, due by days or commits, and always due as a shallow clone.

    Args:
        bloat: the module under test.
        never: the audit settings of a repo with no last audit.
    """
    with tempfile.TemporaryDirectory() as n:
        subprocess.run(["git", "init", "-q", n], check=True)
        env = {**os.environ, "GIT_AUTHOR_DATE": "2026-01-01T12:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T12:00:00Z"}
        subprocess.run(["git", "-C", n, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty",
                        "-m", "first"], check=True, env=env)
        first = datetime.date(2026, 1, 1)
        assert bloat.audit_due(Path(n), never, first) == "", "never audited, new repo: not due yet"
        assert bloat.audit_due(Path(n), never, first + datetime.timedelta(days=14)).startswith("never audited;"), "due by days"
        assert bloat.audit_due(Path(n), {**never, "every_commits": 1}, first).startswith("never audited;"), "due by commits"
        subprocess.run(["git", "-C", n, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty",
                        "-m", "second"], check=True, env=env)
        s = str(Path(n).parent / (Path(n).name + "-shallow"))
        subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + n, s], check=True, capture_output=True)
        try:
            assert bloat.audit_due(Path(s), never, first) == "never audited", "shallow clone: due"
        finally:
            subprocess.run(["rm", "-rf", s], check=True)


def strict_cases(bloat, root, cfg, strict):
    """A fast timed command is ok, and --strict fails when a budget is over."""
    rows, slow = bloat.run_timings(root, cfg, record=False)
    assert not slow and "ok" in rows[0], "fast command is ok"
    with contextlib.redirect_stdout(io.StringIO()):
        assert bloat.report(root, strict, datetime.date(2026, 1, 5)) == 1, "strict fails when over budget"


def report_cases(bloat, root, cfg, strict):
    """The start-read warning, an unknown audit commit, a bad config, and --time --record.

    Args:
        bloat: the module under test.
        root: the sample repo of sample_repo (a Path).
        cfg: its audit settings.
        strict: the options of a --strict run (an argparse.Namespace).
    """
    settings(root, "audit-budget-session_load_warn_tokens: 1\n", audit={"last_audit": {"date": "2026-01-01"}})
    w = io.StringIO()
    with contextlib.redirect_stdout(w):
        bloat.report(root, argparse.Namespace(brief=True, time=False, record=False, strict=False), datetime.date(2026, 1, 5))
    assert "over warning" in w.getvalue() and "over: session load" not in w.getvalue(), "warning, not over"
    with contextlib.redirect_stdout(io.StringIO()):
        assert bloat.audit_due(root, {**cfg, "last_audit": {"date": "2026-01-01", "commit": "f" * 40}},
                               datetime.date(2026, 1, 5)) == "", "unknown commit alone is not due"
        (root / bloat.STATE).write_text("{bad")
        assert bloat.report(root, strict, datetime.date(2026, 1, 5)) == 1, "bad state file: message, no traceback"
        settings(root, "audit-budget-file_kbs: 9\n")
        assert bloat.report(root, strict, datetime.date(2026, 1, 5)) == 1, "unknown audit- key: message, no traceback"
        settings(root)
        (root / check_settings.OLD_AUDIT).write_text("{}")
        assert bloat.main_rules(root) == 1, "the old settings file fails --rules until it is migrated"
        (root / check_settings.OLD_AUDIT).unlink()
        settings(root, audit={"last_audit": {"date": "2026-01-01"}}, timings={"f": {"cmd": "bash scripts/fail.sh"}, "t": {"cmd": "bash scripts/ok.sh"}})
        bloat.report(root, argparse.Namespace(brief=True, time=True, record=True, strict=False))
    saved = check_settings.load_state(root)
    assert "seconds" not in saved["timings"]["f"] and saved["timings"]["t"]["seconds"] is not None, "record skips failed commands"
    assert saved["audit"]["last_audit"]["date"] == "2026-01-01", "--time --record keeps the other parts of the state"


def compare_cases(bloat, root):
    """--compare: within the limit, a slowdown, no baseline, --record, and --time skips a timing with no cmd.

    Args:
        bloat: the module under test.
        root: the sample repo (a Path).
    """
    tc = {"timings": {"check": {"seconds": 4.0, "steps": {"a": 2.0, "tiny": 0.1}}}}
    line, slow = bloat.compare_times(json.loads(json.dumps(tc)), [("check", 4.4), ("check:a", 2.4), ("check:tiny", 0.3)])
    assert not slow and line.startswith("TIME  baseline: 3 of 3"), "within +25%, or under 0.5 s slower: ok"
    line, slow = bloat.compare_times(json.loads(json.dumps(tc)), [("check", 5.2), ("check:a", 2.0), ("check:new", 1.0)])
    assert slow == ["check 5.2 s (baseline 4.0 s, +30%)"] and line.startswith("WARN") and "skills/audit/SKILL.md" in line, \
        "a slowdown warns and names the skill"
    line, _ = bloat.compare_times(json.loads(json.dumps(tc)), [("check:new", 1.0)])
    assert "no baseline yet for 1 (check:new)" in line and "Record a baseline" in line, "no baseline: says how to record one"
    rec = json.loads(json.dumps(tc))
    bloat.compare_times(rec, [("check", 3.0), ("check:new", 1.0), ("other", 0.2)], record=True)
    assert rec["timings"]["check"]["seconds"] == 3.0 and rec["timings"]["check"]["steps"]["new"] == 1.0 and rec["timings"]["other"]["seconds"] == 0.2, \
        "record stores wall, step and a new key"
    settings(root, code_standard={"debt": {}}, **tc)
    with contextlib.redirect_stdout(io.StringIO()):
        assert bloat.main_compare(root, ["check:a=9", "bad"], False) == 0, "a bad item: no failure"
        bloat.main_compare(root, ["check:a=1.25"], True)
    saved = check_settings.load_state(root)
    assert saved["timings"]["check"]["steps"]["a"] == 1.2 and saved["code_standard"] == {"debt": {}}, "--record keeps the other parts"
    assert (root / bloat.STATE).read_text() == check_settings.state_text(saved), "the state file has sorted keys and indent 1"
    rows, _ = bloat.run_timings(root, {"timings": {"nocmd": {"seconds": 1}}}, record=False)
    assert rows == [], "--time skips a timing with no cmd"
    for good in ("python3 scripts/bloat_check.py --brief", "bash scripts/check.sh", "scripts/check.sh", "tests/run.sh",
                 "bash scripts/check_project.sh"):  # the kit's and the fleet's timed commands
        assert bloat.timing_argv(good) == good.split(), f"allowed timed command: {good}"
    for bad in ("echo pwned; true", "rm -rf /", "bash scripts/x.sh && id", "python3 scripts/a.py $(id)", "python3 scripts/a.py\nid",
                "python3 scripts/../../x.py", "bash /tmp/x.sh", "curl scripts/x", "python3 -c scripts/x", ""):
        try:
            bloat.timing_argv(bad)
        except ValueError:
            continue
        raise AssertionError(f"timed command not refused: {bad!r}")


def write_skill(rs, folder, body):
    """Write .claude/skills/<folder>/SKILL.md under rs."""
    (rs / ".claude/skills" / folder).mkdir(parents=True, exist_ok=True)
    (rs / ".claude/skills" / folder / "SKILL.md").write_text(body)


def hard_rule_cases(bloat, rs):
    """SINGLE_HOME: each hard rule restated in a skill is a hit; a pointer and a hook description pass.

    Args:
        bloat: the module under test.
        rs: the sample repo folder.

    Returns:
        None (an assert stops on a failure).
    """
    hits = ["Never force-push or rewrite published history.", "Never rebase a pushed branch.", "Never push with `--no-verify`.",
            "Never push to main directly.", "Never weaken a hook to get past a block.", "Never skip a test.",
            "Never repin an approval.", "A review finding is not approval.", "Review on a model tier no lower than the author's.",
            "Never review with a lower tier."]
    passes = ['Rules: see (AGENTS.md "Hard rules").', "| pre-push | blocks every force-push form and a push to main |",
              "Run git clean up on a scratch folder.", "The Administrator's approval is in the pull request.",
              "Check that the hook refuses --no-verify."]
    for i, line in enumerate(hits + passes):
        write_skill(rs, f"s{i}", f"---\nname: s{i}\ndescription: Use when testing.\n---\n{line}\n")
    got = {re.search(r"skills/(s\d+)/", p).group(1) for p in bloat.second_homes(rs)}
    assert got == {f"s{i}" for i in range(len(hits))}, "each hard rule restated is a hit; pointers and descriptions pass: " + str(sorted(got))


def skills_cases(bloat, rs):
    """--skills: a clean pass, each FAIL case, each WARN case, orphans and a folded description.

    Args:
        bloat: the module under test.
        rs: an empty temporary folder for the sample skills (a Path).
    """
    (rs / "AGENTS.md").write_text("Skills: ok, nodesc, noname, wrongname, nofm, longone, warnone.\n")
    good = "---\nname: {}\ndescription: Use when testing.\n---\nbody\n"
    write_skill(rs, "ok", good.format("ok"))
    with contextlib.redirect_stdout(io.StringIO()) as w:
        assert bloat.main_skills(rs) == 0, "clean skill passes"
    assert w.getvalue().strip() == "SKILLS PASS: 1 skills, 0 warnings", "clean pass line"
    write_skill(rs, "nofm", "no frontmatter\n")
    write_skill(rs, "nodesc", "---\nname: nodesc\n---\n")
    write_skill(rs, "noname", "---\ndescription: Use when x.\n---\n")
    write_skill(rs, "wrongname", "---\nname: other\ndescription: Use when x.\n---\n")
    rows, fails, _, _ = bloat.skills_report(rs)
    assert fails == 4 and sum(r.startswith("FAIL") for r in rows) == 4, "each FAIL case"
    with contextlib.redirect_stdout(io.StringIO()) as w:
        assert bloat.main_skills(rs) == 1, "a malformed skill fails"
    assert w.getvalue().strip().splitlines()[-1].startswith("SKILLS FAIL:"), "fail line"
    for f in ("nofm", "nodesc", "noname", "wrongname"):
        (rs / ".claude/skills" / f / "SKILL.md").unlink()
    write_skill(rs, "warnone", "---\nname: warnone\ndescription: Does things.\n---\n")
    write_skill(rs, "longone", "---\nname: longone\ndescription: Use before " + "x" * 1030 + "\n---\n" + "l\n" * 150)
    write_skill(rs, "orphan", good.format("orphan"))
    rows, fails, warns, n = bloat.skills_report(rs)
    txt = "\n".join(rows)
    assert fails == 0 and n == 4 and warns == 4, "four WARN cases, no FAIL"
    assert all(r.startswith("  WARN") for r in rows), "WARN lines are indented"
    assert 'warnone/SKILL.md: description does not start' in txt, "WARN: description start"
    assert "longone/SKILL.md: description is 1041 characters" in txt and "longone/SKILL.md: 154 lines" in txt, "WARN: long description and file"
    assert "orphan/SKILL.md: orphan" in txt, "WARN: orphan"
    (rs / ".claude/skills/warnone/SKILL.md").write_text("---\nname: warnone\ndescription: Does things.\n---\nSee orphan.\n")
    assert "orphan/SKILL.md: orphan" not in "\n".join(bloat.skills_report(rs)[0]), "a mention in another SKILL.md is no orphan"
    assert bloat.skill_frontmatter("---\nname: f\ndescription: >\n  Use when folded.\n---\n")["description"] == "Use when folded.", \
        "a folded description keeps no > marker"


def rule_count_cases(bloat):
    """Rules: count by place; header, Commands, fences, comments, starter blocks, rankings and tables.

    Args:
        bloat: the module under test.
    """
    rule_lines = bloat.rule_lines
    sample = ("# T\n\n- Repo: x\n\n## Git safety\n\n- Rule one.\n- Rule two.\n<!-- starter -->\n- Starter only.\n"
              "<!-- /starter -->\n```\n- in a fence\n```\n\n## Commands\n\n- Build: none.\n\n## Project rules\n\n"
              "<!-- - a comment -->\n- Project rule.\n")
    kit, project, every = rule_lines(sample)
    assert kit == ["Rule one.", "Rule two."] and project == ["Project rule."], "header, Commands, fences, comments and starter blocks are not rules"
    assert "Build: none." in every, "the list of changed lines also covers sections that are not counted"
    assert rule_lines("## A\n\n- Rule start\n  continues with a | b here.\n")[0] == ["Rule start continues with a | b here."], \
        "a continuation with a pipe stays in its rule (a change to it shows)"
    keyed = rule_lines("## Hard rules\n\n- **Git history.** Never x.\n- **The Administrator may change anything** here.\n- Plain.\n\n"
                       "## Project rules\n\n- **Own.** P.\n", with_sections=True)
    assert [k for k, _ in keyed] == ["Git history", "The Administrator may change anything", "Hard rules", "Own"], \
        "a bold label is the lint key, without its dot; else the heading"
    kit, project, _ = rule_lines("## A\n\n* Star.\n1. Numbered.\n  - Nested.\nA paragraph.\n\n"
                                 "## Project rules\n\n+ Plus.\n  wrapped.\nA rule as a paragraph.\n")
    assert kit == ["Star.", "Numbered.", "Nested. A paragraph."] and project == ["Plus. wrapped.", "A rule as a paragraph."], \
        "every list marker counts; in the kit a line right below an item continues it, in Project rules only an indented one"
    _, project, _ = rule_lines("## Project rules\n\nRule one.\nRule two.\nRule three.\n\n- Bullet.\nAfter a bullet.\n\n#1 priority: never do X.\n")
    assert project == ["Rule one.", "Rule two.", "Rule three.", "Bullet.", "After a bullet.", "#1 priority: never do X."], \
        "Project rules: unindented lines are rules each; '#1' is text, not a heading"
    _, project, _ = rule_lines("## Project rules\n\nRule | Why\n--- | ---\nT one | x\nT two | y\n\n| R | W |\n|---|---|\n| T three | z |\n-\n")
    assert project == ["T one | x", "T two | y", "| T three | z |"], "tables without leading pipes: one rule per row; a lone '-' removes no row"
    kit, project, every = rule_lines("## Order of authority\n\n1. The Administrator.\n2. This file.\n- A bullet here counts.\n\n## B\n\n"
                                     "- One rule,\n  wrapped.\n~~~\n- in a tilde fence\n~~~\n* * *\n---\n### Sub\n\n"
                                     "## Project rules\n\n### Group\n\n- P one,\n  wrapped.\n\nA paragraph rule\nover two lines.\n\n---\n\n"
                                     "| Rule | Why |\n|---|---|\n| T one | x |\n| T two | y |\n")
    assert kit == ["A bullet here counts.", "One rule, wrapped."], \
        "the ranking is not counted, a bullet in that section is; wraps, fences, rules and sub-headings are not rules"
    assert project == ["P one, wrapped.", "A paragraph rule", "over two lines.", "| T one | x |", "| T two | y |"], \
        "Project rules: wrapped bullet 1, an unindented paragraph line 1 each, table rows without header and separator"
    assert "The Administrator." in every, "ranking lines are still listed when they change"


def third_party_cases(bloat, ro, caps):
    """The `audit-third-party` globs: a matched skill folder or agent file leaves the session load and counts
    against its own cap (the Administrator, 2026-11-20).

    Args:
        bloat: the bloat_check module.
        ro: a temporary repo that holds the skill `s` (a 400-character description).
        caps: the default audit settings.
    """
    agents = ro / ".claude/agents"
    agents.mkdir(parents=True)
    (agents / "vendor-a.md").write_text("---\nname: vendor-a\ndescription: " + "e" * 200 + "\n---\nBody.\n")
    both = bloat.listing_bytes(ro)
    assert bloat.listing_bytes(ro, [".claude/*"])[1] == 0, "no lock (or the kit clone): nothing is third-party"
    (ro / ".check.lock").write_text("{bad json")
    assert bloat.listing_bytes(ro, [".claude/*"])[1] == 0, "an unreadable lock fails closed"
    (ro / ".check.lock").write_text("{}")
    assert bloat.listing_bytes(ro, [".claude/*"])[1] == 0, "a lock with no files list fails closed"
    (ro / ".check.lock").write_text(json.dumps({"files": {}}))
    assert bloat.listing_bytes(ro, [".claude/*"])[1] == 0, "a lock with an empty files list fails closed"
    (ro / ".check.lock").write_text(json.dumps({"files": {"scripts/x.py": "x"}}))
    assert both[1] == 0 and both[0] >= 600, "without globs every skill and agent is the project's own"
    split = bloat.listing_bytes(ro, [".claude/skills/s", ".claude/agents/vendor-*.md"])
    assert split[0] == 0 and split[1] == both[0], "a matched skill folder and agent file count apart"
    assert bloat.listing_bytes(ro, [".claude/skills/s/"])[1] > 0, "a trailing slash matches the folder"
    (ro / ".check.lock").write_text(json.dumps({"files": {".claude/skills/s/SKILL.md": "x"}}))
    assert bloat.listing_bytes(ro, [".claude/skills/*"])[1] == 0, "a kit-locked skill is never third-party"
    (ro / ".check.lock").write_text(json.dumps({"files": {"scripts/x.py": "x"}}))
    cfg = {**caps, "third_party": [".claude/skills/s", ".claude/agents/vendor-a.md"]}
    assert bloat.start_read(ro, cfg)[2] < bloat.start_read(ro, caps)[2], "third-party descriptions leave the session load"
    rows, problems = bloat.rules_report(ro, cfg)
    assert "third-party ~" in rows[0] and not any("third-party" in p for p in problems), "under its cap: reported only"
    assert "third-party" not in bloat.rules_report(ro, caps)[0][0], "no globs: no third-party report"
    tight = {**cfg, "budgets": {**caps["budgets"], "third_party_tokens": 10}}
    assert any("third-party skills and agents over their cap" in p for p in bloat.rules_report(ro, tight)[1]), \
        "over its own cap fails"
    (ro / ".check.lock").unlink()
    assert bloat.rules_report(ro, tight)[1] == bloat.rules_report(ro, caps)[1], "with no lock nothing leaves the load"
    (agents / "vendor-a.md").unlink()
    agents.rmdir()


def readme_cases(bloat, ro, caps):
    """The "One home" default (README.md part): a filled Purpose needs README.md (fail) that opens with it (warn); a template skips it.

    Args:
        bloat: the module under test.
        ro: the sample repo of caps_and_paths_cases (a Path), with no README.md.
        caps: audit settings with the default budgets.
    """
    (ro / "AGENTS.md").write_text("# P: agent instructions\n\n- Purpose: {{PURPOSE}}\n\n## A\n\n- Rule.\n")
    assert bloat.rules_report(ro, caps)[1] == [], "a template Purpose skips the README check"
    (ro / "AGENTS.md").write_text("# P: agent instructions\n\n- Purpose: Track the widgets of a unit.\n\n## A\n\n- Rule.\n")
    assert any("no README.md" in p for p in bloat.rules_report(ro, caps)[1]), "a filled Purpose with no README.md fails"
    (ro / "README.md").write_text("# P\n\n![logo](a.png)\n\nSomething else entirely.\n")
    rows, problems = bloat.rules_report(ro, caps)
    assert not problems and any("does not open with" in r for r in rows), "another opening only warns"
    (ro / "README.md").write_text("# P\n\n[![b](x)](y)\n<p>x</p>\n\ntrack the widgets\nof a unit, with tools.\n\nMore.\n")
    rows, problems = bloat.rules_report(ro, caps)
    assert not problems and not any("does not open with" in r for r in rows), "an opening that starts with the purpose passes"
    (ro / "README.md").write_text("\ufeff---\nt: x\n---\nTitle\n=====\n\n> Track the **widgets** of a unit.\n")
    assert not any("does not open with" in r for r in bloat.rules_report(ro, caps)[0]), "BOM, front matter, setext, quote"
    (ro / "AGENTS.md").write_text("# P: agent instructions\n\n- Purpose: Track\n\n## A\n\n- Rule.\n")
    (ro / "README.md").write_text("# P\n\nTracker for nothing.\n")
    assert any("does not open with" in r for r in bloat.rules_report(ro, caps)[0]), "the purpose matches whole words only"
    (ro / "README.md").unlink()
    (ro / "AGENTS.md").write_text("# P: agent instructions\n\n- Purpose:\n- Owner: me\n\n## A\n\n- Rule.\n")
    assert bloat.rules_report(ro, caps)[1] == [], "an empty Purpose does not take the next line"
    (ro / "AGENTS.md").write_text("# P: agent instructions\n\n- Purpose: Track things.\n\n## A\n\n- Rule.\n")
    (ro / "readme.md").write_text("# P\n\nTrack things.\n")
    rows, problems = bloat.rules_report(ro, caps)
    assert not problems and not any("does not open" in r for r in rows), "a lower-case readme.md counts"
    (ro / "readme.md").unlink()


def _missing_paths_cases(bloat, ro, caps):
    """Check missing paths named in AGENTS.md and existing paths passing.

    Args:
        bloat: the module under test.
        ro: the sample repo (a Path).
        caps: audit settings with the default budgets.
    """
    subprocess.run(["rm", "-rf", str(ro / ".claude")], check=True)
    (ro / "AGENTS.md").write_text(
        "## A\n\n- See `.claude/skills/x/SKILL.md` and [doc](docs/gone.md), [web](https://e.example/a), `.claude/skills/<name>/`, "
        "`scripts/gone.sh --fast`, `scripts/check.local.sh`, `python3 scripts/gone2.py --test`, `scripts/tool.sh -o docs/out.html`, "
        "`scripts/gone2.py:12`, `scripts/gone.sh|tee x`, `bash -x scripts/gone3.sh`, "
        "`x --output docs/a.md --out docs/b.md --outline docs/c.md`.\n")
    rows, problems = bloat.rules_report(ro, caps)
    assert problems == ["missing paths named in AGENTS.md: .claude/skills/x/SKILL.md, docs/gone.md, scripts/gone.sh, "
                        "scripts/gone2.py, scripts/gone3.sh, scripts/tool.sh"], \
        "missing paths (also after a command word, with a line number or a pipe), not URLs, patterns, optional files or option values"
    (ro / ".claude/skills/x").mkdir(parents=True)
    (ro / ".claude/skills/x/SKILL.md").write_text("x")
    (ro / "docs").mkdir()
    (ro / "docs/gone.md").write_text("x")
    (ro / "scripts").mkdir()
    for s in ("gone.sh", "gone2.py", "tool.sh", "gone3.sh"):
        (ro / "scripts" / s).write_text("x")
    assert bloat.rules_report(ro, caps)[1] == [], "paths exist: pass"


def caps_and_paths_cases(bloat, ro, caps):
    """A repo with origin/main: a swap of rule lines is listed, both caps fail, missing paths fail.

    Args:
        bloat: the module under test.
        ro: an empty temporary folder for the sample repo (a Path).
        caps: audit settings with the default budgets.
    """
    o = str(ro)
    git_in(o, "init", "-q", "-b", "main")
    (ro / "AGENTS.md").write_text("## A\n\n- Old rule.\n- Kept rule.\n\n## Project rules\n\n")
    git_in(o, "add", "-A")
    git_in(o, "commit", "-q", "-m", "a")
    git_in(o, "update-ref", "refs/remotes/origin/main", "HEAD")
    (ro / "AGENTS.md").write_text("## A\n\n- New rule.\n- Kept rule.\n\n## Project rules\n\n- P1.\n")
    rows, problems = bloat.rules_report(ro, caps)
    assert not problems, "at the cap is not over"
    assert any(r.startswith("  + New rule.") for r in rows) and any(r.startswith("  - Old rule.") for r in rows), "a swap is listed"
    (ro / "AGENTS.md").write_text("## A\n\n- New rule.\n- Kept rule.\n- Third.\n\n## Project rules\n\n- P1.\n- P2.\n")
    rows, problems = bloat.rules_report(ro, caps)
    assert not problems and sum(r.startswith("WARN  ") and "rule bullets (guide" in r for r in rows) == 2, "the bullet counts only warn"
    tight = {"budgets": {**caps["budgets"], "rules_file_lines": 3, "session_load_tokens": 5}}
    rows, problems = bloat.rules_report(ro, tight)
    assert len(problems) == 2 and "over the line cap (10 > 3)" in problems[0] and "session load over the cap" in problems[1], \
        "the line cap and the load cap fail"
    warned = {"budgets": {**caps["budgets"], "session_load_warn_tokens": 5}}
    assert any("over the warning" in r for r in bloat.rules_report(ro, warned)[0]) and not bloat.rules_report(ro, warned)[1], "the load warning only warns"
    settings(ro, "audit-budget-rules_file_lines: 50\naudit-ignore: ref/**\n")
    cfg = bloat.load_config(ro)
    assert cfg["budgets"]["session_load_tokens"] == 5500 and cfg["budgets"]["rules_file_lines"] == 50, "a project can lower a kit cap"
    assert bloat.ignored("ref/a/b.md", cfg) and not bloat.ignored("docs/a.md", cfg), "audit-ignore globs are read"
    for bad in ("audit-budget-session_load_tokens: 999999\n", "audit-budget-third_party_tokens: 1501\n",
                "audit-budget-rule_file_lines: 50\n", "audit-every-days: soon\n"):
        settings(ro, bad)
        with contextlib.redirect_stdout(io.StringIO()) as w:
            assert bloat.main_rules(ro) == 1 and bad.split(":")[0] in w.getvalue(), "a raised kit cap, an unknown key and a bad value fail --rules: " + bad
    (ro / check_settings.CHECK).unlink()
    (ro / check_settings.STATE).unlink()
    skill = ro / ".claude/skills/s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: s\ndescription: " + "d" * 400 + "\n---\nAn agent never merges this.\n")
    assert bloat.start_read(ro, caps)[2] >= 100, "skill names and descriptions count in the session load"
    third_party_cases(bloat, ro, caps)
    table = [("agents merge", r"never merges", ["AGENTS.md"])]
    assert bloat.second_homes(ro, table) == [
        'second home of a rule: .claude/skills/s/SKILL.md:5 states "agents merge"; its home is AGENTS.md: link to it'], \
        "a rule stated again in a skill is a problem"
    assert bloat.second_homes(ro, [("x", r"never merges", [".claude/skills/s/SKILL.md"])]) == [], "the home file may state it"
    _missing_paths_cases(bloat, ro, caps)
    readme_cases(bloat, ro, caps)


def conflict_gate_cases(bloat, ro, caps):
    """Conflict gate: changed rule lines need a record that names their hash; without --gate only a WARN line.

    Args:
        bloat: the module under test.
        ro: the sample repo of caps_and_paths_cases (a Path).
        caps: audit settings with the default budgets.
    """
    (ro / "AGENTS.md").write_text("## A\n\n- New rule.\n- Kept rule.\n\n## Project rules\n\n")
    h = bloat.conflict_hash(["New rule."], ["Old rule."])
    assert h == bloat.conflict_hash(["New rule."], ["Old rule."]) != bloat.conflict_hash(["Old rule."], ["New rule."]), \
        "the hash keeps + and - apart"
    rows, problems = bloat.rules_report(ro, caps)
    assert not problems and any(r.startswith("WARN") and h in r for r in rows), "no record, no gate: a WARN line with the hash"
    rows, problems = bloat.rules_report(ro, caps, gate=True)
    assert len(problems) == 1 and h in problems[0], "no record, gate: fails"
    (ro / "docs").mkdir(exist_ok=True)
    (ro / "docs/reviews").mkdir()
    (ro / "docs/reviews/r.md").write_text(f"Result: no conflict.\nrule-conflict-check: {'0' * 12}\n")
    assert bloat.rules_report(ro, caps, gate=True)[1], "a record for other lines does not count"
    (ro / "docs/reviews/r.md").write_text(f"Result: no conflict.\nrule-conflict-check: {h}\n")
    rows, problems = bloat.rules_report(ro, caps, gate=True)
    assert not problems and any("conflict check: recorded" in r for r in rows), "a record with the hash passes"
    (ro / "AGENTS.md").write_text("## A\n\n- Old rule.\n- Kept rule.\n\n## Project rules\n\n")
    assert not bloat.rules_report(ro, caps, gate=True)[1], "no changed lines: no gate"


def lint_cases(bloat, ro):
    """Lint: near-duplicates, vague words, untested rules (a section with no scenario, no script named).

    Args:
        bloat: the module under test.
        ro: the sample repo (a Path).
    """
    (ro / ".claude").mkdir(exist_ok=True)
    (ro / ".claude/rule-tests.md").write_text("| # | Rule tested | Section | Prompt |\n|---|---|---|---|\n| 1 | x | Tested; Other | p |\n")
    rules = [("Tested", "Never push to main without the full check lane passing first."),
             ("Tested", "Never push to main without the full check lane passing."),
             ("Tested", "Use the right tool where possible."),
             ("Untested", "Keep the handoff short."), ("Untested", "The hook enforces it: `scripts/x.sh`."),
             ("Other", "Run `git clean` never.")]
    flags = bloat.lint(ro, rules)
    assert sum("near-duplicate" in f for f in flags) == 1, "one near-duplicate pair"
    assert [f for f in flags if "vague" in f] == ['WARN  rule lint: vague (where possible): "Use the right tool where possible."'], \
        "vague word; text in backticks is not read"
    assert [f for f in flags if "untested" in f] == [
        'WARN  rule lint: untested (no scenario for "Untested" in .claude/rule-tests.md, no script named): "Keep the handoff short."'], \
        "untested: no scenario and no script; a ';' list of sections counts each"
    assert bloat.lint(ro, rules, only={"Keep the handoff short."}) == [f for f in flags if "handoff" in f], "only: the changed lines"
    (ro / ".claude/rule-tests.md").unlink()
    assert not [f for f in bloat.lint(ro, rules) if "untested" in f], "no rule-tests file (starter tier): no untested flags"
    (ro / "AGENTS.md").write_text("## A\n\n- New rule.\n- Kept rule.\n\n## Project rules\n\n- See `.claude/skills/x/SKILL.md` and "
                                  "[doc](docs/gone.md), `scripts/gone.sh`, `scripts/gone2.py`, `scripts/tool.sh`.\n")
    with contextlib.redirect_stdout(io.StringIO()):
        assert bloat.main_rules(ro) == 0, "--rules passes"
        assert bloat.main_lint(ro) == 0, "--lint never fails"
        (ro / "AGENTS.md").write_text("## A\n\n" + "- r.\n" * 29)
        assert bloat.main_rules(ro) == 0, "--rules passes over the bullet guide of 28 (a warning)"
        (ro / "AGENTS.md").write_text("## A\n\n" + "- r.\n" * 199)
        assert bloat.main_rules(ro) == 1, "--rules fails over the default cap of 200 lines"


def ratchet_cases(bloat, root):
    """T2: script lines over the baseline fail; a baseline above main's needs a DECISIONS row that names it.

    Args:
        bloat: the module bloat_check.
        root: the sample repo (a Path) with 2 script lines.
    """
    assert bloat.script_lines(root) == 2, "the T2 measure"
    rows, problems = bloat.ratchet_report(root)
    assert not rows and len(problems) == 1 and "no \"script_lines\" baseline" in problems[0], "the kit with no baseline fails: %s" % problems
    (root / ".check.lock").write_text("{}")
    rows, problems = bloat.ratchet_report(root)
    assert not problems and len(rows) == 1 and rows[0].startswith("SKIP") and "plan P5" in rows[0], "a project with no baseline: a SKIP line"
    (root / ".check.lock").unlink()
    (root / check_settings.STATE).write_text(json.dumps({"script_lines": {"baseline": 2}}))
    assert not bloat.ratchet_report(root)[1], "at the baseline: passes"
    (root / "scripts/a.py").write_text("x\nx\n")
    problems = bloat.ratchet_report(root)[1]
    assert len(problems) == 1 and "pass the baseline 2 (+1)" in problems[0] and "By the Administrator" in problems[0], problems
    git_in(root, "add", "-A")
    git_in(root, "commit", "-qm", "state")
    git_in(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    (root / check_settings.STATE).write_text(json.dumps({"script_lines": {"baseline": 3}}))
    problems = bloat.ratchet_report(root)[1]
    assert len(problems) == 1 and "rose from 2 to 3" in problems[0], "a higher baseline needs a row: %s" % problems
    (root / "docs").mkdir(exist_ok=True)
    good = 'the Administrator: "Approve 3" (2026-11-23 18:10)'
    cases = [("baseline 3 \\| wc", good, True), ("baseline 3.", good, True),
             ("baseline 31", good, False), ("baseline 3.5", good, False), ("v3", good, False), ("1.3", good, False),
             ("baseline 3", "Agent: the Administrator 3", False), ("baseline 3", "the Administrator (2026-11-23)", False),
             ("baseline 3", 'the Administrator: "3"', False), ("baseline 3", 'the Administrator\'s agent: "3" 2026-11-23', False),
             ("baseline 3", 'the Administrator-bot: "3" 2026-11-23', False), ("baseline 3", 'the Administrator: agent wrote "3" 2026-11-23', False),
             ("baseline 3", 'the Administrator: "2026-11-23"', False), ("baseline 3", '“Approve 3” 2026-11-23', False),
             ("baseline 3", 'The Administrator: “Approve 3” 2026-11-23', True)]
    for decision, by, ok in cases:
        (root / "docs/DECISIONS.md").write_text(f"| 2026-11-23 | Script lines {decision} | {by} |\n")
        git_in(root, "add", "-A")
        assert (not bloat.ratchet_report(root)[1]) == ok, f"T2 row ({decision} | {by}) should {'pass' if ok else 'fail'}"
    (root / check_settings.STATE).write_text(json.dumps({"script_lines": {"baseline": 4}}))
    problems = bloat.ratchet_report(root)[1]
    assert any("below the baseline 4 (-1)" in x and '"baseline": 3' in x for x in problems), "freed lines lower the baseline: %s" % problems
    (root / check_settings.STATE).write_text(json.dumps({"script_lines": {"baseline": 4, "cap": True}}))
    assert not any("below the baseline" in x for x in bloat.ratchet_report(root)[1]), "a cap baseline allows fewer lines"


def role_cases(bloat, root):
    """T6: kit-synced text with an old role word fails in the kit; a dated attribution and the kept lines do not.

    Args:
        bloat: the module bloat_check.
        root: the sample kit repo (a Path).
    """
    o_word, m_word = "the " + "owner", "the " + "Maintainer"
    (root / "scripts/sync_baseline.py").write_text('COPY_FILES = ["docs/x.md"]\nCOPY_IF_MISSING = []\n')
    (root / "docs/x.md").write_text(f"{o_word} decides\nRule ({o_word}, 2026-11-23: ok)\n{m_word}'s word\nthe Administrator\n")
    rows, problems = bloat.role_report(root)
    assert not rows and len(problems) == 1 and "2 line(s)" in problems[0] and "docs/x.md:1, docs/x.md:3" in problems[0], problems
    (root / "scripts/sync_baseline.py").write_text('COPY_FILES = ["docs/x.md"]\nCOPY_IF_MISSING = []\n')
    (root / "docs/x.md").write_text(f"{o_word} decides\nRule ({o_word}, 2026-11-23: ok)\n{m_word}'s word\nthe Administrator\n")
    (root / ".check.lock").write_text("{}")
    assert bloat.role_report(root) == ([], []), "a project keeps its own role word"
    (root / ".check.lock").unlink()
    (root / "docs/x.md").write_text("the Administrator\n")
    assert bloat.role_report(root) == ([], []), "Administrator passes"
    (root / "docs/x.md").write_text(f"{m_word} decides\nRule ({m_word}, 2026-11-23: ok)\n")
    problems = bloat.role_report(root)[1]
    assert len(problems) == 1 and "1 line(s)" in problems[0] and "docs/x.md:1" in problems[0], "the old role word fails: %s" % problems


def file_check_cases(bloat, d):
    """The file checks of --rules: T1 tool rows, T2 script lines ratchet, T6 role word.

    Args:
        bloat: the module under test.
        d: an empty temporary folder (a Path).
    """
    table = "| File | Job | Candidates |\n|---|---|---|\n"
    root = sample_kit(d, {"scripts/a.py": "x\n", "scripts/b.sh": "x\n", "tools/c.js": "x\n", "node_modules/v.js": "x\n"})
    assert bloat.tool_files(root) == ["scripts/a.py", "scripts/b.sh", "tools/c.js"], "tool files: any folder, not vendor"
    problems = bloat.tool_report(root)[1]
    assert len(problems) == 1 and "3 tool file(s)" in problems[0], "the kit: no docs/tools.md fails"
    (root / "docs").mkdir()
    (root / "docs/tools.md").write_text(table + "| scripts/a.py | a | ruff, pylint, radon |\n| `b.sh` | b | none known (searched: shell lint) |\n"
                                        "| tools/c.js | c | one, two |\n")
    problems = bloat.tool_report(root)[1]
    assert len(problems) == 1 and "1 tool file(s)" in problems[0] and "tools/c.js" in problems[0], "2 candidates is not 3: %s" % problems
    (root / "docs/tools.md").write_text(table + "| a.py, b.sh, tools/c.js | all | one, two |\n| tools/c.js | c | none known |\n")
    assert "3 tool file(s)" in bloat.tool_report(root)[1][0], "a files cell is not a candidates cell; none known needs search terms"
    (root / "docs/tools.md").write_text(table + "| scripts/a.py | a | x, y, z |\n| b.sh | b | none known (terms: q) |\n| tools/c.js | c | x; y; z |\n")
    assert bloat.tool_report(root) == ([], []), "3 candidates, or none known with terms: every row counts"
    (root / "docs/tools.md").write_text(table + "| other.py | calls scripts/a.py and b.sh; tools/c.js too | x, y, z |\n"
                                        "| scripts/a.py | a | one, two |\n| b.sh | b | none known |\n| tools/c.js | c | x, y |\n")
    assert "3 tool file(s)" in bloat.tool_report(root)[1][0], "a name in a cell that is not the first one does not count (T1)"
    (root / "docs/tools.md").unlink()
    (root / ".check.lock").write_text(json.dumps({"files": {"scripts/a.py": "h"}}))
    warns, problems = bloat.tool_report(root)
    assert not problems and len(warns) == 1 and "2 tool file(s)" in warns[0], "a project: WARN, and a kit-locked file is not listed"
    (root / ".check.lock").unlink()
    ratchet_cases(bloat, root)
    role_cases(bloat, root)


def debt_gate_cases(bloat, d, caps):
    """T5: in the kit, changed rule lines, a new check.sh entry point and a lower KIT_CAPS cap each need a docs/reviews/*-debt.md
    file with "debt-check: <hash>"; the hash is the conflict hash for rule lines alone; a project has no such gate.

    Args:
        bloat: the module under test.
        d: an empty temporary folder (a Path).
        caps: audit settings with the default budgets.
    """
    base = {"AGENTS.md": "## A\n\n- Old rule.\n\n## Project rules\n\n", "scripts/check.sh": "python3 scripts/a.py\n",
            "scripts/check_settings.py": 'KIT_CAPS = ("c1",)\nAUDIT_DEFAULTS = {"budgets": {"c1": 5, "c2": 9}}\n'}
    root = sample_kit(d, base)

    def debt():
        """Return T5 gate problems for root."""
        return [p for p in bloat.rules_report(root, caps, gate=True)[1] if "T5" in p]
    assert debt() == [] and bloat.debt_triggers(root) == [], "nothing changed: no gate"
    (root / "AGENTS.md").write_text("## A\n\n- New rule.\n\n## Project rules\n\n")
    h = bloat.conflict_hash(["New rule."], ["Old rule."])
    assert len(debt()) == 1 and f"debt-check: {h}" in debt()[0], "a changed rule line needs the record, with the conflict hash"
    (root / "docs/reviews").mkdir(parents=True)
    (root / "docs/reviews/r.md").write_text(f"debt-check: {h}\n")
    assert len(debt()) == 1, "a record outside a *-debt.md file does not count"
    (root / "docs/reviews/r-debt.md").write_text(f"debt-check: {h}\n")
    assert debt() == [], "a *-debt.md record with the hash passes"
    (root / "AGENTS.md").write_text(base["AGENTS.md"])
    (root / "scripts/check.sh").write_text("python3 scripts/a.py\nrun x python3 scripts/b.py\nselftest n scripts/c.py -- python3 scripts/c.py --test\n")
    assert bloat.debt_triggers(root) == ["check entry point scripts/b.py", "check entry point scripts/c.py"], "new entry points"
    h = bloat.conflict_hash(["check entry point scripts/b.py", "check entry point scripts/c.py"], [])
    assert len(debt()) == 1 and f"debt-check: {h}" in debt()[0], "the hash covers the entry points"
    (root / "scripts/check.sh").write_text(base["scripts/check.sh"])
    (root / "scripts/check_settings.py").write_text('KIT_CAPS = ("c1", "c3")\nAUDIT_DEFAULTS = {"budgets": {"c1": 4, "c2": 9, "c3": 1}}\n')
    assert bloat.debt_triggers(root) == ["stricter kit cap c1", "stricter kit cap c3"], "a lower cap and a new cap"
    (root / "scripts/check_settings.py").write_text('KIT_CAPS = ("c1",)\nAUDIT_DEFAULTS = {"budgets": {"c1": 6, "c2": 1}}\n')
    assert debt() == [], "a higher kit cap, or a lower cap that is not a kit cap, needs no record"
    (root / "AGENTS.md").write_text("## A\n\n- New rule.\n\n## Project rules\n\n")
    (root / "docs/reviews/r-debt.md").unlink()
    (root / "kit.config.json").unlink()
    assert debt() == [], "a project (not the kit): no debt gate"


def fleet_cases(bloat, d):
    """R3: the fleet audit is due in the kit when kit.config.json has no `fleet.last_audit`, when it is more than 14 days old, or
    when HEAD carries a release tag (v*) dated after it; a project never reports it; the --brief line carries it.

    Args:
        bloat: the module under test.
        d: an empty temporary folder (a Path).
    """
    root = sample_kit(d, {"AGENTS.md": "## A\n\n- r.\n"})

    def due(today):
        """Return fleet audit due reason on today."""
        return bloat.fleet_audit_due(root, datetime.date.fromisoformat(today))
    assert "no fleet.last_audit" in due("2026-11-23"), "no date: due"
    (root / "kit.config.json").write_text('{"fleet": {"last_audit": "2999-01-01"}}')
    assert due("2999-01-15") == "" and "15 days since 2999-01-01" in due("2999-01-16"), "due after 14 days, not on the 14th"
    git_in(root, "tag", "v1.0.0")
    assert due("2999-01-02") == "", "a tag older than the audit: not due"
    (root / "kit.config.json").write_text('{"fleet": {"last_audit": "2000-01-01"}}')
    assert "kit release v1.0.0 is newer than 2000-01-01" in due("2000-01-02"), "a release tag at HEAD newer than the audit: due"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bloat.report(root, argparse.Namespace(brief=True, time=False, record=False, strict=False))
    assert "AUDIT DUE (fleet: " in buf.getvalue() and "kit release v1.0.0" in buf.getvalue(), "the brief line (the kit check-in) says so: %s" % buf.getvalue()
    (root / "kit.config.json").unlink()
    assert due("2026-11-23") == "", "a project: never"


def archive_due_cases(bloat, root, files):
    """ARCHIVE DUE on the sample repo of archive_cases (4 files archivable on 2026-01-19): the archivable count and bytes
    "reach" their limits (>=). The limits are put back after the cases.

    Args:
        bloat: the module under test.
        root: the sample repo of archive_cases (a Path).
        files: its tracked files.
    """
    day = datetime.date(2026, 1, 19)
    old = bloat.ARCHIVE_SET
    found = sum(b for _, b in bloat.archivable(root, files, day))
    assert bloat.archive_due(root, files, day) == "", "4 files and %d bytes: not due" % found
    bloat.ARCHIVE_SET = (4, 10**9)
    assert bloat.archive_due(root, files, day).startswith("4 files, 0 KB archivable"), "the count reaches it"
    bloat.ARCHIVE_SET = (10**9, found)
    assert bloat.archive_due(root, files, day).startswith("4 files"), "the bytes reach it"
    bloat.ARCHIVE_SET = (10**9, found + 1)
    assert bloat.archive_due(root, files, day) == "", "the bytes do not reach found + 1"
    bloat.ARCHIVE_SET = old


def archive_cases(bloat, d):
    """ARCHIVE DUE: a unit of docs/reviews/ is archivable when it is old enough (14 days; 7 for a closed plan), no live text
    names it (a link from a history doc does not count; a link from an open plan does) and no check reads it; a plan is
    closed only with a checked box and no open box; a folder is one unit, as old as its newest file; the line prints at 20
    archivable files or 200 KB (reached), never for the folder's total size; a shallow clone makes no age test.

    Args:
        bloat: the module under test.
        d: an empty temporary folder (a Path).
    """
    root = sample_kit(d, {"AGENTS.md": "## A\n\n- r.\n"})
    rev = root / "docs/reviews"
    (rev / "fix").mkdir(parents=True)
    texts = {"old.md": "x", "linked.md": "x", "record.md": "rule-conflict-check: abc", "list-coverage.md": "x",
             "open-plan.md": "- [ ] step; evidence: ev.md", "ev.md": "x", "nobox-plan.md": "Status: approved",
             "wip-plan.md": "- [x] a\n- [~] b", "done-plan.md": "- [x] step; see old.md", "fix/a.md": "x", "fix/b.md": "x",
             "README.md": "x", "archive-index.md": "x"}
    for rel, text in texts.items():
        (rev / rel).write_text(text)
    (root / "README.md").write_text("See docs/reviews/linked.md.")
    (root / "docs/LOG.md").write_text("History: old.md.")
    (root / "docs/KIT_HANDOFF.md").write_text("Open: none.")

    def commit(day):
        """Commit all files on day."""
        subprocess.run(["git", "-C", root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", day],
                       check=True, env={**os.environ, "GIT_COMMITTER_DATE": day + "T12:00:00"})
    git_in(root, "add", "-A")
    commit("2026-01-01")
    (rev / "fix/b.md").write_text("xy")
    commit("2026-01-05")
    files = git_in_out(root, "ls-files").splitlines()

    def names(today):
        """Return sorted archivable paths on today."""
        return sorted(p for p, _ in bloat.archivable(root, files, datetime.date.fromisoformat(today)))
    assert names("2026-01-07") == [], "6 days: nothing"
    assert names("2026-01-08") == ["docs/reviews/done-plan.md"], "7 days: the closed plan only: %s" % names("2026-01-08")
    assert names("2026-01-15") == ["docs/reviews/done-plan.md", "docs/reviews/old.md"], \
        "the folder is 10 days old; archive-index.md is kept: %s" % names("2026-01-15")
    assert names("2026-01-19") == ["docs/reviews/done-plan.md", "docs/reviews/fix/a.md", "docs/reviews/fix/b.md",
                                   "docs/reviews/old.md"], \
        "never: a live link, a record, a coverage list, README.md, archive-index.md, an open plan or its evidence"
    archive_due_cases(bloat, root, files)
    (root / "docs/KIT_HANDOFF.md").write_text("Open: other work.")   # the plan closed long ago; the handoff changes later
    commit("2026-01-20")
    assert "docs/reviews/done-plan.md" not in names("2026-01-26"), "6 days after the handoff change: the plan stays"
    assert "docs/reviews/done-plan.md" in names("2026-01-27"), "7 days after it: archivable"
    (rev / "new.md").write_text("x")
    git_in(root, "add", "docs/reviews/new.md")
    files = git_in_out(root, "ls-files").splitlines()
    assert "docs/reviews/new.md" not in names("2027-01-01"), "a file with no commit: no age, not archivable"
    (root / ".git/shallow").write_text(git_in_out(root, "rev-parse", "HEAD") + "\n")
    day = datetime.date(2026, 1, 19)
    assert bloat.archivable(root, files, day) is None, "a shallow clone: age unknown"
    assert bloat.archive_due(root, files, day) == "", "a shallow clone: not due"


def archive_volume_cases(bloat, d):
    """ARCHIVE DUE at the real limits: 201 files a check reads (over 1 MB, 0 archivable) print nothing; with 19 old
    archivable files, nothing; with 20, the line, and the --brief line carries it.

    Args:
        bloat: the module under test.
        d: an empty temporary folder (a Path).
    """
    root = sample_kit(d, {"AGENTS.md": "## A\n\n- r.\n"})
    (root / "docs/reviews").mkdir(parents=True)
    for i in range(201):
        (root / f"docs/reviews/r{i}.md").write_text(f"rule-conflict-check: {i}\n" + "x" * 5000)
    plain = [f"docs/reviews/n{i}.md" for i in range(20)]
    for rel in plain:
        (root / rel).write_text("x")
    git_in(root, "add", "-A")
    subprocess.run(["git", "-C", root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "old"], check=True,
                   env={**os.environ, "GIT_COMMITTER_DATE": "2026-01-01T12:00:00"})
    files, day = git_in_out(root, "ls-files").splitlines(), datetime.date(2026, 2, 1)
    keep = [r for r in files if r not in plain]
    assert bloat.archive_due(root, keep, day) == "", "a large folder (201 files, over 1 MB), 0 archivable: nothing"
    assert bloat.archive_due(root, keep + plain[:19], day) == "", "19 archivable files: nothing"
    assert bloat.archive_due(root, files, day).startswith("20 files, 0 KB archivable"), "20 archivable files: due"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bloat.report(root, argparse.Namespace(brief=True, time=False, record=False, strict=False))
    assert "ARCHIVE DUE (20 files, 0 KB archivable)" in buf.getvalue(), "the brief line says so: %s" % buf.getvalue()


def run(bloat):
    """Run every case against the module bloat in temporary repos; print BLOAT TEST PASS (an assert stops on a failure).

    Args:
        bloat: the module under test (scripts/bloat_check.py).

    Returns:
        The exit code 0 (an assert stops on a failure).
    """
    # The host's git config (forced signing, -c on the command line) must not change the cases.
    for k in ("GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"):
        os.environ.pop(k, None)
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    strict = argparse.Namespace(brief=False, time=False, record=False, strict=True)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        cfg = sample_repo(bloat, root)
        generated_block_cases(bloat, root, cfg)
        never_audited_cases(bloat, metrics_cases(bloat, root, cfg))
        duplicate_ignore_cases(bloat, root, cfg)
        strict_cases(bloat, root, cfg, strict)
        rule_count_cases(bloat)
        caps = {"budgets": {**bloat.DEFAULTS["budgets"], "rules": 2, "project_rules": 1}}
        with tempfile.TemporaryDirectory() as o:
            caps_and_paths_cases(bloat, Path(o), caps)
            conflict_gate_cases(bloat, Path(o), caps)
            lint_cases(bloat, Path(o))
        for name, cases in (("files", file_check_cases), ("debt", debt_gate_cases), ("fleet", fleet_cases),
                            ("archive", archive_cases), ("volume", archive_volume_cases)):
            with tempfile.TemporaryDirectory() as o:
                cases(bloat, Path(o), *([caps] if name == "debt" else []))
        report_cases(bloat, root, cfg, strict)
        compare_cases(bloat, root)
    with tempfile.TemporaryDirectory() as d:
        skills_cases(bloat, Path(d))
    with tempfile.TemporaryDirectory() as d:
        hard_rule_cases(bloat, Path(d))
    print("BLOAT TEST PASS")


class BloatCheckTest(unittest.TestCase):
    """The cases of `python3 scripts/bloat_check.py --test`, for `python3 -m unittest` and pytest."""

    def test_self_test(self):
        """Every case passes on the bloat_check module; the git settings that run() changes are put back after it."""
        import bloat_check  # scripts/bloat_check.py: imported here, so a plain import of this file loads nothing
        saved = dict(os.environ)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(saved)))
        run(bloat_check)
