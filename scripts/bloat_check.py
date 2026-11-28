#!/usr/bin/env python3
"""Cheap bloat and drift metrics for a project repo, and the audit due date. Report only, unless --record.

Prevents: the instruction files and the session load growing past their caps unseen, rule lines that change with no conflict
check, a path that AGENTS.md names and that is gone, a skill that is malformed, a tool file that no one searched a standard tool for (T1),
custom script lines that grow with no decision (T2), a kit text that writes the role word of one project (T6), and a check or rule change
that lands with no list of what it fails in the fleet (T5).

Usage:
    python3 scripts/bloat_check.py            # full report
    python3 scripts/bloat_check.py --brief    # one line (scripts/session_checkin.sh runs this)
    python3 scripts/bloat_check.py --time     # also run each timed command in .check.state.json and compare
    python3 scripts/bloat_check.py --time --record   # run them and store the new seconds as the baseline
    python3 scripts/bloat_check.py --strict   # exit 1 when a budget is over or the audit is due
    python3 scripts/bloat_check.py --rules    # rule counts against the caps, rule lines added or removed against
                                              # origin/main, missing .claude/ paths, tool rows (T1), script lines ratchet (T2),
                                              # old role word in kit-synced text (T6), and debt record (T5); exit 1 when a cap
                                              # is passed or a check fails (scripts/check.sh runs this)
    python3 scripts/bloat_check.py --rules --gate   # also fail when rule lines changed and no conflict-check or debt
                                              # record in docs/reviews/ names their hash (scripts/check.sh full lane)
    python3 scripts/bloat_check.py --lint     # rule lint of every rule line: near-duplicates, vague words, untested
                                              # rules; report only (--rules lints the changed lines)
    python3 scripts/bloat_check.py --skills   # check each .claude/skills/*/SKILL.md: FAIL (exit 1) with no frontmatter,
                                              # no name or description, or a name that differs from its folder;
                                              # WARN (exit 0) for a description not starting "Use when"/"Use before",
                                              # over 1024 characters, a file over 150 lines, or an orphan skill
                                              # (name in neither AGENTS.md nor another SKILL.md); last line SKILLS PASS/FAIL
    python3 scripts/bloat_check.py --compare NAME=SECONDS ...   # compare times that a script measured with their
                                              # baselines; one TIME or WARN line; never fails (scripts/check.sh,
                                              # session_checkin.sh and the pre-push hook run it); --record stores them
    python3 scripts/bloat_check.py --test     # self-test (scripts/bloat_check_test.py); prints BLOAT TEST PASS

It measures:
    session load  bytes and ~tokens (bytes / 4) of what every session loads: AGENTS.md, CLAUDE.md,
                  docs/NEXT_PROMPT.md, the `audit-start-read:` files, and the skill and agent names and descriptions.
                  Caps for every repo (KIT_CAPS; a project can lower one, never raise it): 5,500 tokens (warning at
                  5,000) and 200 lines of AGENTS.md; over a cap fails --rules
    third-party   the names and descriptions of the skills and agents that `.check` names in `audit-third-party:`
                  lines: counted apart from the session load, against their own kit cap of 1,500 tokens (the Administrator,
                  2026-11-20); over it fails --rules
    rules         list items in AGENTS.md (any marker, any indent; a wrapped line is part of its item): the kit
                  sections (the header, "## Commands" and the numbered ranking in "## Order of authority" are not
                  counted) and "## Project rules" (there a paragraph or a table row counts too), each against its
                  cap, so rules cannot grow unseen
    rule lint     (--lint all rules; --rules the changed ones, as WARN lines) a near-duplicate pair (similar text),
                  a vague word (VAGUE), and an untested rule: its section has no scenario in .claude/rule-tests.md
                  (column "Section") and the line names no script under scripts/ that enforces it. Warn only.
    conflict gate (--rules) rule lines added or removed against origin/main need a fresh-context conflict check
                  (.claude/skills/rule-change/SKILL.md); its record in docs/reviews/ holds the line
                  "rule-conflict-check: <hash>" that --rules prints. With --gate (the full lane) a missing record fails.
    pointers      each `.claude/...`, `scripts/...` and `docs/...` path in backticks and each relative link in
                  AGENTS.md exists (text moved to a skill is not lost)
    readme        (--rules) when the AGENTS.md "- Purpose:" line is filled in: no README.md fails; a README.md whose
                  first paragraph does not open with that purpose is a WARN line (AGENTS.md "One home")
    handoff       docs/NEXT_PROMPT.md lines
    duplicates    normalized text lines of 80+ characters found in 2 or more tracked files (not counted: the lines
                  of a generated block, between the marker lines "# >>> ... generated from ..." and "# <<< ...")
    big files     tracked files over the size budget
    audit due     days and commits on main since the last full audit (.check.state.json "audit": "last_audit")
    tool rows     (--rules, T1) each tool file the repo owns has a docs/tools.md row, whose first cell names it: 3 candidate tools,
                  or "none known" and the search terms; FAIL in the kit, WARN in a project
    script lines  (--rules, T2) the lines of scripts/*.py and *.sh against "script_lines": {"baseline": N} in the state file
                  (`cat scripts/*.py scripts/*.sh | wc -l`); over it fails, and so does a baseline above main's with no DECISIONS row;
                  below it fails unless "cap": true; no baseline: FAIL in the kit, SKIP in a project
    role word     (--rules, T6) kit-synced text in the kit says "the Administrator", not an old role word; FAIL in the kit, no check in a project
    debt record   (--rules --gate, T5, kit) changed rule lines, a check entry point added to scripts/check.sh and a lower
                  KIT_CAPS cap need a docs/reviews/*-debt.md file with the line "debt-check: <hash>" (the hash as the conflict gate)
    fleet audit   (kit, R3) AUDIT DUE (fleet): kit.config.json "fleet": {"last_audit": "YYYY-MM-DD"} missing, over 14 days old,
                  or older than a v* release tag at HEAD
    archive due   ARCHIVE DUE: the archivable files of docs/reviews/ reach 20 files or 200 KB; the folder's total size
                  does not count (the tests and limits: archive_due)
    timings       (--time) wall time of each named command against its recorded baseline; (--compare) times that
                  a script measured itself: NAME is a timings key, NAME:STEP one of its "steps". Slower means over
                  max_slowdown (default +25%) and over min_slowdown_seconds (default 0.5 s), so noise on a small step
                  does not warn. A slowdown starts .claude/skills/audit/SKILL.md "A slow run"

Settings: the `audit-` lines of `.check` (scripts/check_settings.py reads them and lists the keys; all are optional,
and a line that is not valid fails --rules):
    audit-every-days: 14, audit-every-commits: 300, audit-ignore: ref/**, audit-start-read: <path>,
    audit-duplicate-ignore: data/** (not read by the duplicate count only),
    audit-budget-<name>: <number> (handoff_lines 40, file_kb 500, duplicate_lines 20, rules 28, project_rules 15)
State: `.check.state.json` (tools write it; the full audit in .claude/skills/audit/SKILL.md sets "last_audit"):
    {"audit": {"last_audit": {"date": "YYYY-MM-DD", "commit": "<sha>", "report": "<path>"}},
     "timings": {"tests": {"cmd": "tests/run.sh", "seconds": 20.8, "max_slowdown": 0.25},
                 "check": {"cmd": "bash scripts/check.sh", "seconds": 4.5, "steps": {"check_content self-test": 4.1}},
                 "push-guard": {"seconds": 0.4}}}
A timing with no "cmd" is only compared (--compare), never run by --time.
The "rules" and "project_rules" bullet counts only warn.
A repo with no "last_audit" reports AUDIT DUE (never audited) once it is every_days or every_commits past its first
commit (a new project is not due on day one; an older project synced for the first time usually is).
Exit 0, unless --strict and something is over (exit 1). Standard library only. Needs git.
Network: none (it runs local git read commands; with --time it runs the timed commands of .check.state.json, which may use it).
Writes: .check.state.json, only with --record (the time baselines).
Credentials: none.
"""
import argparse
import ast
import datetime
import fnmatch
import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_lock  # noqa: E402 - the kit lock (changed_lines, kit_files)
import check_settings  # noqa: E402 - scripts/check_settings.py: the reader of .check and the reader and writer of .check.state.json
import log_check as plan  # noqa: E402 - scripts/log_check.py: the DECISIONS table cells

STATE = check_settings.STATE
DEFAULTS = check_settings.AUDIT_DEFAULTS  # the settings when .check has no `audit-` line
TEXT_EXT = {".md", ".txt", ".py", ".sh", ".ps1", ".psm1", ".js", ".ts", ".json", ".yml", ".yaml", ".html", ".css",
            ".toml", ".ini", ".cfg", ".csv", ""}
MIN_DUP = 80          # characters in a normalized line before it counts as a duplicate
MAX_SCAN = 1_000_000  # bytes; larger files are not scanned for duplicates

START_READ = ["AGENTS.md", "CLAUDE.md", "docs/NEXT_PROMPT.md"]
RULES_FILE = "AGENTS.md"
PROJECT_RULES = "## Project rules"
NOT_RULES = {"## Commands"}  # project-owned settings, not rules
RANKED = {"## Order of authority"}  # its numbered ranking of sources is not a rule count; a bullet there is
OPTIONAL = {"scripts/check.local.sh"}  # named in AGENTS.md, present only when the project has tests
VAGUE = ["appropriate", "appropriately", "as needed", "if needed", "when needed", "where possible", "if possible",
         "when possible", "properly", "reasonable", "be careful", "try to", "consider", "etc.", "best practice",
         "as much as", "usually", "generally", "ideally", "maybe", "might", "should"]
VALUE_OPTIONS = {"-o", "--output", "--out", "--outline"}  # options whose value is a file the command writes
NEAR_DUP = 0.6        # word overlap (Jaccard) from which two rule lines are a near-duplicate pair
RULE_TESTS = ".claude/rule-tests.md"
REVIEWS = "docs/reviews"

ITEM = re.compile(r"^\s*(?:[-*+]|(\d+)[.)])\s+(.*)$")
RULE_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")           # --- or * * *: a horizontal rule, not a rule
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")  # |---|---|: the row above it is a header
HEADING = re.compile(r"^\s*#{1,6}(\s|$)")                    # "### Sub"; "#1 priority: ..." is text, not a heading
EMPTY_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*$")         # a marker with no text
BOLD_LABEL = re.compile(r"^\s*\*\*([^*]+?)\.?\*\*")  # "**Delivery.** text": the label of a rule bullet

TOOL_EXT = (".py", ".sh", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".bat", ".cmd")
TOOL_SKIP = ("node_modules/", "vendor/", "dist/")   # not the repo's own tools
TOOLS_DOC = "docs/tools.md"
STATE_KEY = "script_lines"   # in .check.state.json: {"baseline": N, "command": ..., "measured": ..., "commit": ...}
# T2: the By cell of a baseline row: "the Administrator:", then the approval in quotes, then a date after the quote
APPROVED_BY = re.compile(r'the Administrator:\s*(?:"[^"\S\n]*[^"\s][^"\n]*"|“[^”\S\n]*[^”\s][^”\n]*”).*?(?<!\d)\d{4}-\d\d-\d\d(?!\d)', re.I)
ROLE_WORD = re.compile(r"\bthe[ ]owner\b|\bOwner's\b|\b[Tt]he[ ]Maintainer\b|\bMaintainer's\b|\b[Tt]he[ ]PAM\b|\b[Tt]he[ ]PFM\b")
DATED = re.compile(r"\((?:the )?(?:[Oo]wner|Administrator|Maintainer), \d{4}-\d{2}-\d{2}")   # an attribution that records a past role word stays as written
ROLE_ALLOW = {
    "scripts/bloat_check.py": [r"^ROLE_WORD = re\.compile\(", r"^DATED = re\.compile\("],
}
ENTRY = re.compile(r"(?:python3|bash)\s+(scripts/[\w.-]+\.(?:py|sh))|^[ \t]*(?:selftest|extension)\s+\S+\s+(scripts/[\w.-]+\.(?:py|sh))", re.M)
CAPS_FILE = "scripts/check_settings.py"
# The archive step (.claude/skills/audit/SKILL.md, item 16): the thresholds the Administrator approved on 2026-11-25
# (docs/reviews/2026-11-25-archival-inventory-kit.md), in decimal KB. The set "reaches" them (>=).
ARCHIVE_SET = (20, 200_000)       # the archivable files: count, bytes (no folder-total trigger: the Administrator, 2026-11-25)
ARCHIVE_DAYS = {True: 7, False: 14}   # days since the newest change: a plan (closed), the rest
HISTORY_DOCS = ("docs/DECISIONS.md", "docs/LOG.md", "docs/CHANGELOG.md")   # a link from these is history, not live
CHECK_READ = re.compile(r"(?:rule-conflict-check|debt-check): ")   # conflict_recorded reads these
HANDOFF_FILES = ("docs/KIT_HANDOFF.md", "docs/NEXT_PROMPT.md")
KEEP_NAMES = ("README.md", "archive-index.md")   # the folder's own guide and the archive index: never archived
OPEN_BOX = re.compile(r"\[ \]|\[~")
DONE_BOX = re.compile(r"\[[xX]\]")

# One home per rule (the Administrator, 2026-11-18): a rule that AGENTS.md states must not be stated again, or the other
# way round, in a skill or an agent file; those files link to it. Each row: (the rule, a pattern that shows a
# second statement, the files that may hold it). A match in any other skill or agent file fails scripts/check.sh.
SINGLE_HOME = [
    ("who merges a pull request",
     r"only the Administrator merges|the Administrator merges\b|never merges this pull request|the Administrator's merge is the approval", ["AGENTS.md"]),
    ("no direct push to main", r"merge to main by merge|\bPush main:|git checkout main && git merge|push to main and republish", ["AGENTS.md"]),
    ("the end-of-turn summary format", r"end-of-turn summary line:", ["AGENTS.md"]),
    # The hard rules (AGENTS.md "Hard rules", 2026-11-18). A pointer such as (AGENTS.md "Hard rules") or a description
    # of what a hook blocks has no "never ..." sentence and passes.
    ("hard rule: git history",
     r"\bnever (?:force[- ]?push|rebase\b|reset\b|stash\b|(?:git )?clean\b(?! up)|rewrite published history|discard work)"
     r"|\bnever push\b[^.\n]*(?:--no-verify|\bmain\b|default branch)", ["AGENTS.md"]),
    ("hard rule: guards and checks",
     r"\bnever (?:weaken a (?:check|hook|test|guard)|skip a (?:check|test)|repin\b|add an? (?:allow|skip|exemption)"
     r"|edit a generated report)", ["AGENTS.md"]),
    ("hard rule: rule text approval", r"\b(?:is|are) not approval\b", ["AGENTS.md"]),
    ("hard rule: the fresh review tier", r"tier no lower than|never review with a lower tier", ["AGENTS.md"]),
]

TIMING_DIRS = ("scripts/", "tests/")  # a timed command runs a file of the repo, from one of these folders
SHELL_CHARS = set(";|&`$()<>\n")


# ---------------------------------------------------------------- git and settings ------------------------------------

def git(root, *args):
    """Run git in root; return its output, or None when git fails or is missing."""
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def is_kit(root):
    """True in the kit itself: it has kit.config.json and no `.check.lock` (a synced project has the lock)."""
    return (root / "kit.config.json").is_file() and not (root / ".check.lock").exists()


def load_config(root):
    """The audit settings of .check, with "last_audit" and "timings" from .check.state.json; ValueError when a
    line is not valid or a file cannot be read (scripts/check_settings.py; KIT_CAPS budgets can only be lowered there)."""
    return check_settings.audit_config(root)


def ignored(rel, cfg, key="ignore"):
    """True when rel matches a glob of an `audit-ignore:` line (key "duplicate_ignore": `audit-duplicate-ignore:`)."""
    return any(fnmatch.fnmatch(rel, g) for g in cfg.get(key, []))


def dup_files(files, cfg):
    """The files the duplicate count reads: files without those an `audit-duplicate-ignore:` glob matches.

    Args:
        files: the repo-relative paths that scan_files gives.
        cfg: the audit settings.

    Returns:
        A list of repo-relative paths.
    """
    return [rel for rel in files if not ignored(rel, cfg, "duplicate_ignore")]


def norm(line):
    """line without list, quote, heading and table marks, whitespace made single, lower case (for duplicates)."""
    line = re.sub(r"^[\s>#|*\-+0-9.]+", "", line)
    return re.sub(r"\s+", " ", line).strip().lower()


def scan_files(root, cfg):
    """The tracked files that exist and are not ignored by the config."""
    out = git(root, "ls-files")
    return [rel for rel in (out.splitlines() if out else []) if not ignored(rel, cfg) and (root / rel).is_file()]


def duplicates(root, files):
    """Return [(normalized line, [files])] for long lines found in 2+ text files, most files first.

    Args:
        root: the repo root (a Path).
        files: the repo-relative paths to scan.

    Returns:
        A list of (normalized line, [files]).
    """
    seen = {}
    for rel in files:
        p = root / rel
        if p.suffix.lower() not in TEXT_EXT or p.stat().st_size > MAX_SCAN:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in counted_lines(text):
            n = norm(line)
            if len(n) >= MIN_DUP:
                seen.setdefault(n, set()).add(rel)
    dups = [(n, sorted(fs)) for n, fs in seen.items() if len(fs) > 1]
    return sorted(dups, key=lambda d: -len(d[1]))


def counted_lines(text):
    """Yield the lines of a text that the duplicate count reads. The lines between the marker lines
    "# >>> <name>: generated from <source> ..." and "# <<< <name>" (docs/code-standard.md C5) are a copy that a build
    script writes and checks: they are not counted, so a hand-made duplicate stays visible.

    Args:
        text: the text of one file.
    """
    generated = False
    for line in text.splitlines():
        mark = line.strip()
        if mark.startswith("# >>> ") and "generated from" in mark:
            generated = True
        elif mark.startswith("# <<< "):
            generated = False
        elif not generated:
            yield line


def big_files(root, files, kb):
    """Return [(file, KB)] of the files over kb kilobytes, largest first."""
    return sorted(((rel, (root / rel).stat().st_size // 1024) for rel in files
                   if (root / rel).stat().st_size > kb * 1024), key=lambda f: -f[1])


# ---------------------------------------------------------------- skills and session load -----------------------------

def skill_frontmatter(text):
    """Returns {key: value} of the YAML frontmatter (simple `key: value`, indented continuation lines), or None.

    Args:
        text: the text of a SKILL.md file.

    Returns:
        A dict {key: value}, or None when the file has no frontmatter.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None
    fm, key = {}, None
    for ln in lines[1:end]:
        m = re.match(r"([A-Za-z_-]+):\s*(.*)$", ln)
        if m and not ln[0].isspace():
            key = m.group(1)
            fm[key] = m.group(2).strip()
        elif key and ln.strip():
            head = "" if fm[key] in (">", "|", ">-", "|-") else fm[key]  # a block marker is not part of the text
            fm[key] = (head + " " + ln.strip()).strip()
    for k, v in fm.items():
        fm[k] = "" if v in (">", "|", ">-", "|-") else v.strip("\"'")
    return fm


def _skill_warnings(name, text, fm, agents, texts):
    """Return the warning messages for one parsed skill.

    Args:
        name: skill folder name.
        text: raw text of SKILL.md.
        fm: parsed YAML frontmatter dict.
        agents: text of AGENTS.md.
        texts: mapping of all skill names to SKILL.md text.

    Returns:
        A list of warning strings for the skill.
    """
    desc = fm.get("description", "")
    warn = []
    if desc and not desc.startswith(("Use when", "Use before")):
        warn.append('description does not start with "Use when" or "Use before"')
    if len(desc) > 1024:
        warn.append(f"description is {len(desc)} characters (over 1024)")
    n = len(text.splitlines())
    if n > 150:
        warn.append(f"{n} lines (over 150)")
    pat = r"(?<![\w-])" + re.escape(name) + r"(?![\w-])"
    if not re.search(pat, agents) and not any(re.search(pat, t) for o, t in texts.items() if o != name):
        warn.append("orphan: name not mentioned in AGENTS.md or another SKILL.md")
    return warn


def skills_report(root):
    """Returns (lines, fails, warns, count) for .claude/skills/*/SKILL.md.

    Args:
        root: the repo root (a Path).

    Returns:
        (lines to print, the number of FAIL lines, the number of WARN lines, the number of skills).
    """
    files = sorted((root / ".claude/skills").glob("*/SKILL.md"))
    texts = {f.parent.name: f.read_text(encoding="utf-8", errors="replace") for f in files}
    agents = (root / "AGENTS.md").read_text(encoding="utf-8", errors="replace") if (root / "AGENTS.md").is_file() else ""
    out, fails, warns = [], 0, 0
    for name, text in texts.items():
        rel = f".claude/skills/{name}/SKILL.md"
        fm = skill_frontmatter(text)
        if fm is None:
            out.append(f"FAIL  {rel}: no YAML frontmatter")
            fails += 1
            continue
        bad = [f"no {k}" for k in ("name", "description") if not fm.get(k)]
        if fm.get("name") and fm["name"] != name:
            bad.append(f"name \"{fm['name']}\" differs from folder \"{name}\"")
        if bad:
            out.append(f"FAIL  {rel}: {', '.join(bad)}")
            fails += 1
        warn = _skill_warnings(name, text, fm, agents, texts)
        for w in warn:
            out.append(f"  WARN  {rel}: {w}")
        warns += len(warn)
    return out, fails, warns, len(texts)


def main_skills(root):
    """Print the skills report and its last line; return 1 when a skill is malformed, else 0."""
    rows, fails, warns, n = skills_report(root)
    print("\n".join(rows + [f"SKILLS FAIL: {fails} skill(s) malformed, {n} skills, {warns} warnings" if fails
                           else f"SKILLS PASS: {n} skills, {warns} warnings"]))
    return 1 if fails else 0


def kit_files(root):
    """The skill and agent files that can never count as third-party: the kit files in a project's `.check.lock`.
    It fails closed: with no lock (the kit clone itself has none), a lock that cannot be read, or a lock with no files,
    every skill and agent file there is one, so a glob cannot move the kit's own text out of the session load.

    Args:
        root: the repo root (a Path).

    Returns:
        A set of repo-relative paths.
    """
    found = sorted((root / ".claude/skills").glob("*/SKILL.md")) + sorted((root / ".claude/agents").glob("*.md"))
    every = {f.relative_to(root).as_posix() for f in found}
    try:
        files = json.loads((root / ".check.lock").read_text(encoding="utf-8")).get("files")
    except (ValueError, OSError, AttributeError):
        return every
    return set(files) if isinstance(files, dict) and files else every


def listing_bytes(root, third_party=()):
    """Bytes of the names and descriptions of .claude/skills/*/SKILL.md and .claude/agents/*.md: Claude Code puts
    them in every session's context, so they count toward the session load.

    Args:
        root: the repo root (a Path).
        third_party: the `audit-third-party` globs; a skill folder or agent file they match is counted apart,
            except a kit file (in `.check.lock`, or in the kit itself): a glob cannot move the kit's own text out.

    Returns:
        (bytes of the own skills and agents, bytes of the third-party ones).
    """
    own = third = 0
    kit = kit_files(root) if third_party else set()
    for f in sorted((root / ".claude/skills").glob("*/SKILL.md")) + sorted((root / ".claude/agents").glob("*.md")):
        fm = skill_frontmatter(f.read_text(encoding="utf-8", errors="replace")) or {}
        size = len((fm.get("name", "") + fm.get("description", "")).encode())
        rel = f.relative_to(root).as_posix()
        names = (rel, rel.rsplit("/", 1)[0]) if rel.endswith("/SKILL.md") else (rel,)
        if rel not in kit and any(fnmatch.fnmatchcase(n, g.rstrip("/")) for n in names for g in third_party):
            third += size
        else:
            own += size
    return own, third


def second_homes(root, table=None):
    """Problems for each SINGLE_HOME rule found in a skill or agent file that is not its home.

    Args:
        root: the repo root (a folder path).
        table: the rules to look for, as (label, pattern, home files); None = SINGLE_HOME.

    Returns:
        One problem line for each place found.
    """
    files = sorted((root / ".claude/skills").glob("*/SKILL.md")) + sorted((root / ".claude/agents").glob("*.md"))
    out = []
    for label, pattern, homes in (SINGLE_HOME if table is None else table):
        rx = re.compile(pattern, re.IGNORECASE)
        for f in files:
            rel = f.relative_to(root).as_posix()
            if rel in homes:
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    out.append(f"second home of a rule: {rel}:{n} states \"{label}\"; its home is {homes[0]}: link to it")
    return out


# ---------------------------------------------------------------- rule census and lint --------------------------------

def start_read(root, cfg):
    """Return (lines, bytes, ~tokens, [(file, bytes)] largest first) of what every session loads: the start-read
    files, and the names and descriptions of the skills and agents (one entry; Claude Code lists them at start).

    Args:
        root: the repo root (a Path).
        cfg: the audit settings (its "start_read" list adds files).

    Returns:
        (lines, bytes, ~tokens, [(file, bytes)] largest first).
    """
    lines, size = 0, listing_bytes(root, cfg.get("third_party", []))[0]
    files = [("skill and agent descriptions", size)] if size else []
    for rel in START_READ + cfg.get("start_read", []):
        p = root / rel
        if p.is_file():
            b = p.read_bytes()
            lines += b.count(b"\n")
            size += len(b)
            files.append((rel, len(b)))
    return lines, size, size // 4, sorted(files, key=lambda f: -f[1])


def bold_label(text):
    """The bold label that starts a rule bullet, without its trailing dot ("Delivery"), or None."""
    m = BOLD_LABEL.match(text)
    return m.group(1).strip() if m else None


def _parse_rule_line(line, rows, sec, open_item):
    """Handle one active non-fence line inside a section of AGENTS.md and return updated open_item.

    Args:
        line: current line of AGENTS.md.
        rows: collected [section, text, counted, lint_key] entries, modified in place.
        sec: active ## section header string.
        open_item: True when a rule item above can collect continuation lines.

    Returns:
        Updated open_item boolean.
    """
    if not line.strip() or HEADING.match(line) or RULE_HR.match(line) or EMPTY_ITEM.match(line):
        return False
    if TABLE_SEP.match(line) and "-" in line and "|" in line:
        if open_item and rows and "|" in rows[-1][1]:
            rows.pop()  # the header row of a table
        return False
    m = ITEM.match(line)
    indented = line[:1] in (" ", "\t")
    if m:
        counted = sec not in NOT_RULES and not (sec in RANKED and m.group(1))
        rows.append([sec, m.group(2).strip(), counted, bold_label(m.group(2)) or sec[3:].strip()])
        return True
    if open_item and not line.lstrip().startswith("|") and (indented or sec != PROJECT_RULES):
        rows[-1][1] += " " + line.strip()  # a wrapped line belongs to the item above it
        return open_item
    if sec == PROJECT_RULES:
        rows.append([sec, line.strip(), True, bold_label(line) or sec[3:].strip()])
        return True
    return open_item


def rule_lines(text, with_sections=False):
    """Return (kit, project, every): the rule lines of an AGENTS.md text, by where they are.
    With with_sections: [(key, text)], where key is the bold label of a bullet ("**Delivery.** ..." gives "Delivery"),
    else the "## " heading name; the lint matches it to the "Section" column of .claude/rule-tests.md.

    A rule line is a list item with any marker ("- ", "* ", "+ ", "1. ") at any indent; a line that follows it with
    no blank line between is its continuation, not a new rule. kit = items under a "## " heading above
    "## Project rules" (not the header, not NOT_RULES sections; in RANKED sections the numbered ranking is not
    counted, a bullet is); project = items under "## Project rules", and there also each paragraph and each table
    row (not the header row), so a rule that is not a bullet still counts; there a line continues the item above it
    only when it is indented (an unindented line is a new rule: a count may be too high, never too low); every = the
    items of all sections, for the list of changed lines. Not counted anywhere: blank lines, "###" sub-headings,
    horizontal rules, table separator rows (they contain "|"), markers with no text, lines in ``` or ~~~ fences,
    <!-- comments -->. In the kit itself the file marks tier text
    with <!-- starter --> blocks: those are dropped, so the count is the full tier.

    Args:
        text: the text of an AGENTS.md.
        with_sections: True to get (key, line) pairs of every rule line instead.

    Returns:
        (kit, project, every), each a list of rule lines; with with_sections a list of (key, line).
    """
    text = re.sub(r"(?ms)^<!-- starter -->\n.*?^<!-- /starter -->\n", "", text)
    text = re.sub(r"(?s)<!--.*?-->", "", text)
    rows, sec, fenced, open_item = [], None, False, False  # rows: [section, text, counted, lint key]
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced, open_item = not fenced, False
        elif fenced:
            continue
        elif line.startswith("## "):
            sec, open_item = line.rstrip(), False
        elif sec:
            open_item = _parse_rule_line(line, rows, sec, open_item)
    if with_sections:
        return [(key, t) for _, t, c, key in rows if c]
    kit = [t for s_, t, c, _ in rows if c and s_ != PROJECT_RULES]
    project = [t for s_, t, c, _ in rows if c and s_ == PROJECT_RULES]
    return kit, project, [r[1] for r in rows]


def words(line):
    """The set of lower-case words of 3+ characters in line (for the near-duplicate measure)."""
    return set(re.findall(r"[a-z0-9][a-z0-9'-]{2,}", line.lower()))


def tested_sections(root):
    """Rule keys that have a scenario: the "Section" column of .claude/rule-tests.md (a bold bullet label, else a heading).

    Args:
        root: the repo root (a Path).

    Returns:
        The set of rule keys, or None when there is no rule-tests file.
    """
    p = root / RULE_TESTS
    if not p.is_file():
        return None
    out, col = set(), None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col is None and "Section" in cells:
            col = cells.index("Section")
        elif col is not None and len(cells) > col and not TABLE_SEP.match(line):
            out |= {c.strip() for c in cells[col].split(";")}
    return out


def lint(root, rules, only=None):
    """Rule lint, warn only. rules: [(section, text)]; only: the lines to report on (None = all).
    Returns WARN lines: near-duplicate pairs, vague words, untested rules.

    Args:
        root: the repo root (a Path).
        rules: the (section, text) pairs of the rule lines.
        only: the lines to report on; None = all.

    Returns:
        A list of WARN lines.
    """
    tested = tested_sections(root)
    out = []
    for i, (_, a) in enumerate(rules):
        for _, b in rules[i + 1:]:
            if only is not None and a not in only and b not in only:
                continue
            wa, wb = words(a), words(b)
            j = len(wa & wb) / len(wa | wb) if wa | wb else 0
            if j >= NEAR_DUP:
                out.append(f"WARN  rule lint: near-duplicate ({j:.0%} same words): \"{a[:70]}\" ~ \"{b[:70]}\"")
    for sec, t in rules:
        if only is not None and t not in only:
            continue
        low = " " + re.sub(r"`[^`]*`", " ", t.lower()) + " "
        hits = [v for v in VAGUE if re.search(r"(?<![a-z])" + re.escape(v) + r"(?![a-z])", low)]
        if hits:
            out.append(f"WARN  rule lint: vague ({', '.join(hits)}): \"{t[:90]}\"")
        if tested is not None and sec not in tested and not re.search(r"`scripts/[^`]+`|Enforced by", t):
            out.append(f"WARN  rule lint: untested (no scenario for \"{sec}\" in {RULE_TESTS}, no script named): \"{t[:80]}\"")
    return out


def conflict_hash(added, removed):
    """The hash a conflict-check record names: the changed rule lines, sorted, + and - kept apart."""
    text = "\n".join(sorted("+" + ln for ln in added) + sorted("-" + ln for ln in removed))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def conflict_recorded(root, h, label="rule-conflict-check", pattern="*.md"):
    """True when a file of docs/reviews/ that matches pattern holds the line "<label>: <h>".

    Args:
        root: the repo root (a Path).
        h: the hash of the changed rule lines (conflict_hash).
        label: the line label; the debt record uses "debt-check".
        pattern: the file name pattern; the debt record uses "*-debt.md".

    Returns:
        True when a record names the hash.
    """
    d = root / REVIEWS
    return d.is_dir() and any(f"{label}: {h}" in f.read_text(encoding="utf-8", errors="replace")
                              for f in d.rglob(pattern))


def missing_pointers(root, text):
    """Paths that AGENTS.md names and that do not exist: each `.claude/...`, `scripts/...` and `docs/...` path
    inside backticks (also after a command word: `python3 scripts/x.py --test`), and relative link targets. Not a
    path to check: the value of an output option (`-o docs/out.html`: a file the command makes; VALUE_OPTIONS); a line number
    (`scripts/a.py:12`) and a pipe or ; or & after a path are cut off.

    Args:
        root: the repo root (a Path).
        text: the text of AGENTS.md.

    Returns:
        The sorted list of the missing paths.
    """
    text = re.sub(r"(?ms)^<!-- starter -->\n.*?^<!-- /starter -->\n", "", text)
    names = set()
    for span in re.findall(r"`([^`\n]+)`", text):
        parts = re.split(r"[\s|;&]+", span)
        for prev, w in zip([""] + parts, parts, strict=False):
            w = re.sub(r"(:\d+)+$", "", w.rstrip(".,;:)"))
            if re.match(r"(?:\.claude|scripts|docs)/", w) and prev not in VALUE_OPTIONS:
                names.add(w)
    names -= OPTIONAL
    names |= {t.split("#")[0] for t in re.findall(r"\]\(([^)\s]+)\)", text)
              if "://" not in t and not t.startswith(("#", "mailto:"))}
    return sorted(n for n in names if n and not re.search(r"[<>*{]", n) and not (root / n).exists())


def changed_lines(root, parts):
    """The rule lines added and removed against the default branch (the kit lines too, unless the lock holds them).

    Args:
        root: the repo root (a Path).
        parts: (kit, project, every), the rule lines of AGENTS.md now (rule_lines).

    Returns:
        (added, removed), or None when the default branch has no AGENTS.md to compare with.
    """
    old = None
    for ref in ("origin/main", "origin/master"):
        old = git(root, "show", f"{ref}:{RULES_FILE}")
        if old is not None:
            break
    if old is None:
        return None
    part = 1 if check_lock.kit_text_locked(root) else 2
    was = set(rule_lines(old)[part])
    return [ln for ln in parts[part] if ln not in was], sorted(was - set(parts[part]))


def changed_rules(root, text, parts, gate):
    """The part of the rules report on rule lines that changed against the default branch: the lines, the state of
    their conflict check, and the lint of the added ones.

    Args:
        root: the repo root (a Path).
        text: the text of AGENTS.md now.
        parts: (kit, project, every), the rule lines of that text (rule_lines).
        gate: True in the full lane: a missing conflict-check record is a problem, not a WARN line.

    Returns:
        (lines to print, problems).
    """
    out, problems = [], []
    found = changed_lines(root, parts)
    if found is None:
        return out, problems
    added, removed = found
    for mark, lines in (("+", added), ("-", removed)):
        out += [f"  {mark} {ln}" for ln in lines]  # the whole line: a change near its end must show
    if added or removed:
        out.append("  (rule lines changed against the default branch: each one needs the Administrator's approval of its exact text)")
        h = conflict_hash(added, removed)
        if conflict_recorded(root, h):
            out.append(f"  conflict check: recorded (rule-conflict-check: {h})")
        else:
            need = (f"no fresh-context conflict check for these lines: run it (.claude/skills/rule-change/SKILL.md) "
                    f"and record the line \"rule-conflict-check: {h}\" in {REVIEWS}/")
            if gate:
                problems.append(need)
            else:
                out.append(f"WARN  {need} (the full lane fails without it)")
        out += lint(root, rule_lines(text, with_sections=True), only=set(added))
    return out, problems


def readme_opening(text):
    """The first paragraph of a README text, for the AGENTS.md "One home" check.

    Skipped before it: YAML front matter, headings (ATX and setext), images, badges, HTML lines and blank lines. A
    blockquote marker is taken off. The lines of the paragraph are joined by spaces.

    Args:
        text: the README text (a leading BOM is ignored).

    Returns:
        The first paragraph, or "" when there is none.
    """
    lines = text.lstrip("\ufeff").splitlines()
    if lines and lines[0].strip() == "---":  # YAML front matter: skip to its closing line
        close = next((i for i, x in enumerate(lines[1:], 1) if x.strip() in ("---", "...")), None)
        lines = lines[close + 1:] if close else lines
    para = []
    for line in lines:
        s = re.sub(r"^(>\s?)+", "", line.strip()).strip()
        if para and re.fullmatch(r"=+|-+", s):  # setext underline: the paragraph so far was a heading
            para = []
            continue
        if not s or s.startswith(("#", "![", "[![", "<")):
            if para:
                break
            continue
        para.append(s)
    return " ".join(para)


def plain_words(s):
    """Lower-case s with Markdown emphasis and code marks removed, spaces collapsed and a trailing period dropped."""
    return " ".join(re.sub(r"[*_`]", "", s).lower().split()).rstrip(".")


def readme_report(root, text):
    """The AGENTS.md "One home" default: README.md exists and opens with the "- Purpose:" value of AGENTS.md.

    Checked only when that value is filled in (empty, or the kit template's {{PURPOSE}}, is not). A missing README.md
    (any letter case) is a problem; an opening that does not start with the purpose, as whole words, is a WARN line
    (the rule is enforced in part).

    Args:
        root: the repo root (a Path).
        text: the text of AGENTS.md.

    Returns:
        (lines to print, problems).
    """
    m = re.search(r"^- Purpose:[ \t]*(\S.*?)[ \t]*$", text, re.M)
    if not m or "{{" in m.group(1):
        return [], []
    readme = next((f for f in sorted(root.iterdir()) if f.is_file() and f.name.lower() == "readme.md"), None)
    if readme is None:
        return [], ["no README.md: it opens with the AGENTS.md \"Purpose\" line (AGENTS.md \"One home\")"]
    want, got = plain_words(m.group(1)), plain_words(readme_opening(readme.read_text(encoding="utf-8", errors="replace")))
    if not (got.startswith(want) and (len(got) == len(want) or not got[len(want)].isalnum())):
        return [f"WARN  {readme.name} does not open with the AGENTS.md \"Purpose\" line; update it (AGENTS.md \"One home\")"], []
    return [], []


def _census_rules_report(root, cfg, gate=False):
    """The rule census of `--rules`: AGENTS.md caps, session load, third-party budget, second homes, changed lines,
    missing paths and README opening.

    Args:
        root: the repo root (a Path).
        cfg: the audit settings (its budgets are the caps).
        gate: True in the full lane.

    Returns:
        (lines to print, problems).
    """
    p = root / RULES_FILE
    if not p.is_file():
        return [f"rules:       no {RULES_FILE}"], []
    text = p.read_text(encoding="utf-8", errors="replace")
    b = cfg["budgets"]
    kit, project, every = rule_lines(text)
    n_lines, load = len(text.splitlines()), start_read(root, cfg)[2]
    out = [f"rules:       {RULES_FILE} {n_lines} lines (cap {b['rules_file_lines']}) · session load ~{load:,} tokens "
           f"(cap {b['session_load_tokens']:,}) · {len(kit)} rule bullets · Project rules {len(project)}"]
    problems = []
    if n_lines > b["rules_file_lines"]:
        problems.append(f"{RULES_FILE} over the line cap ({n_lines} > {b['rules_file_lines']})")
    if cfg.get("third_party"):
        third = listing_bytes(root, cfg["third_party"])[1] // 4
        out[0] += f" · third-party ~{third:,} tokens (cap {b['third_party_tokens']:,})"
        if third > b["third_party_tokens"]:
            problems.append(f"third-party skills and agents over their cap (~{third:,} > {b['third_party_tokens']:,} "
                            "tokens: the `audit-third-party` entries in .check)")
    if load > b["session_load_tokens"]:
        problems.append(f"session load over the cap (~{load:,} > {b['session_load_tokens']:,} tokens: the start-read files "
                        "plus the skill and agent descriptions)")
    elif load > b["session_load_warn_tokens"]:
        out.append(f"WARN  session load ~{load:,} tokens is over the warning ({b['session_load_warn_tokens']:,}); trim before the cap")
    # The bullet counts only warn (the Administrator, 2026-11-18): the line and load caps are the limits.
    if len(kit) > b["rules"]:
        out.append(f"WARN  {len(kit)} rule bullets (guide {b['rules']})")
    if len(project) > b["project_rules"]:
        out.append(f"WARN  {len(project)} project rule bullets (guide {b['project_rules']})")
    problems += second_homes(root)
    rows, found = changed_rules(root, text, (kit, project, every), gate)
    out += rows
    problems += found
    gone = missing_pointers(root, text)
    if gone:
        problems.append("missing paths named in AGENTS.md: " + ", ".join(gone))
    rows, found = readme_report(root, text)
    out += rows
    problems += found
    return out, problems


def main_lint(root):
    """--lint: print the rule lint of every rule line and a LINT count line. Always 0 (warn only)."""
    p = root / RULES_FILE
    rules = rule_lines(p.read_text(encoding="utf-8", errors="replace"), with_sections=True) if p.is_file() else []
    rows = lint(root, rules)
    print("\n".join(rows + [f"LINT: {len(rows)} flag(s) in {len(rules)} rule lines (warn only)"]))
    return 0


# ---------------------------------------------------------------- file checks and archive due -------------------------

def tool_files(root):
    """The tool files the repo owns: tracked scripts of a known extension in any folder, not a vendor folder, not a kit
    file of the lock (the kit's own docs/tools.md lists those).

    Args:
        root: the repo root (a Path).

    Returns:
        The sorted repo-relative paths.
    """
    out = git(root, "ls-files")
    own = {rel for rel in (out.splitlines() if out else [])
           if rel.lower().endswith(TOOL_EXT) and not any(("/" + rel).find("/" + s) >= 0 for s in TOOL_SKIP)}
    try:
        locked = json.loads((root / ".check.lock").read_text(encoding="utf-8")).get("files") or {}
    except (ValueError, OSError, AttributeError):
        locked = {}
    return sorted(own - set(locked))


def tools_rows(root):
    """The data rows of the tables in docs/tools.md; the candidates column is the one whose header has "candidate".

    Args:
        root: the repo root (a Path).

    Returns:
        A list of (text of the first cell, text of the candidates cell).
    """
    p = root / TOOLS_DOC
    rows, col = [], None
    for line in (p.read_text(encoding="utf-8", errors="replace").splitlines() if p.is_file() else []):
        if not line.lstrip().startswith("|"):
            col = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        hit = [i for i, c in enumerate(cells) if "candidate" in c.lower()]
        if hit:
            col = hit[0]
        elif col is not None and not re.fullmatch(r"[\s|:-]+", line):
            rows.append((cells[0], cells[col] if col < len(cells) else ""))
    return rows


def names_tool(cell, rel):
    """True when the first cell of a docs/tools.md row names the tool file: its repo path, or its base name as a whole word.

    Args:
        cell: the text of the first cell of the row.
        rel: the repo-relative path of the tool file.

    Returns:
        True when the cell names the file.
    """
    base = r"(?<![\w/.-])" + re.escape(rel.rsplit("/", 1)[-1]) + r"(?![\w-])"
    return rel in cell or bool(re.search(base, cell))


def tool_report(root):
    """T1: each tool file needs a docs/tools.md row whose first cell names it and whose candidates cell holds 3 candidates, or
    "none known" with search terms. A name in another cell (the job, the callers) does not count.

    Args:
        root: the repo root (a Path).

    Returns:
        (WARN lines, problems): a problem in the kit, a WARN line in a project (the debt: plan section 3, T5 table).
    """
    ok = [first for first, cand in tools_rows(root)
          if re.search(r"none known\W*\w", cand, re.I) or len([x for x in re.split(r"[;,]", cand) if x.strip()]) >= 3]
    bare = [f for f in tool_files(root) if not any(names_tool(first, f) for first in ok)]
    if not bare:
        return [], []
    line = (f"{len(bare)} tool file(s) have no {TOOLS_DOC} row whose first cell names them and holds 3 candidate tools, or \"none known\" "
            f"and the search terms (T1: search first), for example {', '.join(bare[:3])}")
    return ([], [line]) if is_kit(root) else ([f"WARN  {line}"], [])


def script_lines(root):
    """The newline count of scripts/*.py and scripts/*.sh: `cat scripts/*.py scripts/*.sh | wc -l` (the T2 measure)."""
    return sum(p.read_bytes().count(b"\n") for pat in ("*.py", "*.sh") for p in sorted((root / "scripts").glob(pat)))


def ratchet_report(root):
    """T2: the script lines may not pass the baseline in .check.state.json; a higher baseline than on main needs a docs/DECISIONS.md
    row By the Administrator with the number. No baseline in the state: a problem in the kit, a SKIP line in a project (the sync sets it:
    plan P5).

    Args:
        root: the repo root (a Path).

    Returns:
        (rows, problems).
    """
    try:
        part = check_settings.load_state(root).get(STATE_KEY)
        base = part["baseline"] if isinstance(part, dict) else None
    except (ValueError, KeyError):
        return [], [f"{check_settings.STATE}: \"{STATE_KEY}\" needs a \"baseline\" number"]
    if base is None:
        if is_kit(root):
            return [], [f"{check_settings.STATE} has no \"{STATE_KEY}\" baseline: the script lines are not checked (T2)"]
        return [f"SKIP  scripts:     no \"{STATE_KEY}\" baseline in {check_settings.STATE} (the sync sets it: plan P5)"], []
    n, problems = script_lines(root), []
    if n > base:
        problems.append(f"custom script lines {n} pass the baseline {base} (+{n - base}): a higher baseline needs a docs/DECISIONS.md "
                        f"row By the Administrator with the number {n} (T2 ratchet)")
    elif n < base and not part.get("cap"):   # "cap": true makes the baseline a ceiling only (the Administrator, 2026-11-25)
        problems.append(f"custom script lines {n} are below the baseline {base} (-{base - n}): set \"baseline\": {n} in "
                        f"{check_settings.STATE} in this change, so the freed lines do not return with no decision (T2 ratchet)")
    ref = git(root, "merge-base", "HEAD", "origin/main")
    old = git(root, "show", f"{ref}:{check_settings.STATE}") if ref else None
    try:
        was = json.loads(old).get(STATE_KEY, {}).get("baseline") if old else None
    except (ValueError, AttributeError):
        was = None
    if isinstance(was, int) and base > was:
        rows = [plan.cells(r[1:]) for r in (git(root, "diff", ref, "--", "docs/DECISIONS.md") or "").splitlines() if r.startswith("+|")]
        number = re.compile(rf"(?<![\w.,])(?:{base}|{base:,})(?![\w]|[.,]\d)")   # 18142 or 18,142; not 181420, 1.18142 or 18142.5
        if not any(len(c) > 2 and number.search(c[1]) and APPROVED_BY.match(c[2]) for c in rows):
            problems.append(f"the script lines baseline rose from {was} to {base} with no new docs/DECISIONS.md row that names {base}, "
                            "By the Administrator: the approval in quotes, then its date")
    return [f"scripts:     {n} lines in scripts/*.py and *.sh (baseline {base})"], problems


def synced_files(root):
    """The kit-synced text of the kit itself: COPY_FILES and COPY_IF_MISSING of scripts/sync_baseline.py (read, never run), and AGENTS.md.

    Args:
        root: the repo root (a Path).

    Returns:
        A set of repo-relative paths.
    """
    out = {"AGENTS.md"}
    try:
        tree = ast.parse((root / "scripts/sync_baseline.py").read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return out
    for node in tree.body:
        names = [t.id for t in getattr(node, "targets", []) if isinstance(t, ast.Name)]
        if {"COPY_FILES", "COPY_IF_MISSING"} & set(names):
            out |= set(ast.literal_eval(node.value))
    return out


def role_report(root):
    """T6, in the kit: kit-synced text says "the Administrator", not the old role words (the sync swaps the word per project). A FAIL
    in the kit. Allowed: a dated attribution and the lines of ROLE_ALLOW. A project has no such check:
    its synced text holds that project's own role word.

    Args:
        root: the repo root (a Path).

    Returns:
        (lines to print, problems): one problem with the count and the first places.
    """
    if not is_kit(root):
        return [], []
    hits = []
    for rel in sorted(synced_files(root)):
        p = root / rel
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines() if p.is_file() else [], 1):
            if ROLE_WORD.search(DATED.sub("", line)) and not any(re.search(a, line) for a in ROLE_ALLOW.get(rel, ())):
                hits.append(f"{rel}:{n}")
    return [], [f"{len(hits)} line(s) of kit-synced text use an old role word (T6: write \"the Administrator\"; the sync swaps it): "
                f"{', '.join(hits[:5])}{' ...' if len(hits) > 5 else ''}"] if hits else []


def caps_of(text):
    """Read KIT_CAPS and the budgets of AUDIT_DEFAULTS from a scripts/check_settings.py text, as literals (never run).

    Args:
        text: the text of the file.

    Returns:
        (KIT_CAPS tuple, budgets dict), or None when unreadable.
    """
    found = {}
    try:
        for node in ast.parse(text).body:
            for t in getattr(node, "targets", []):
                if isinstance(t, ast.Name) and t.id in ("KIT_CAPS", "AUDIT_DEFAULTS"):
                    found[t.id] = ast.literal_eval(node.value)
        return tuple(found["KIT_CAPS"]), found["AUDIT_DEFAULTS"]["budgets"]
    except (SyntaxError, KeyError, ValueError, TypeError):
        return None


def debt_triggers(root):
    """T5, in the kit: lines that need the fleet debt record besides the changed rule lines, against origin/main: a check entry point
    that scripts/check.sh runs now and did not, and a KIT_CAPS cap that is new or lower.

    Args:
        root: the repo root (a Path).

    Returns:
        A list of text lines, sorted (the input of the debt-check hash with the changed rule lines).
    """
    if not is_kit(root) or not (root / "scripts/check.sh").is_file():
        return []
    out, base = [], {}
    for ref in ("origin/main", "origin/master"):
        base = {f: git(root, "show", f"{ref}:{f}") for f in ("scripts/check.sh", CAPS_FILE)}
        if base["scripts/check.sh"] is not None:
            break
    def entries(text):
        """Return script entry points matched in check.sh text."""
        return {a or b for a, b in ENTRY.findall(text or "")}
    if base["scripts/check.sh"] is not None:
        now = entries((root / "scripts/check.sh").read_text(encoding="utf-8", errors="replace"))
        out += [f"check entry point {e}" for e in sorted(now - entries(base["scripts/check.sh"]))]
    old, new = caps_of(base[CAPS_FILE] or ""), caps_of((root / CAPS_FILE).read_text(encoding="utf-8", errors="replace"))
    if old and new:
        out += [f"stricter kit cap {k}" for k in new[0] if k not in old[0] or new[1].get(k, 0) < old[1].get(k, 0)]
    return sorted(out)


def debt_record(root, parts, gate):
    """T5, in the kit: changed rule lines, a check entry point added to scripts/check.sh and a stricter KIT_CAPS cap need a file
    docs/reviews/*-debt.md with the line "debt-check: <hash>" (what the change fails today in every fleet repo, and its fix plan).
    The hash is the conflict-check hash for rule lines alone; debt_triggers' lines join it. As the conflict record: WARN, or in the
    full lane a problem.

    Args:
        root: the repo root (a Path).
        parts: (kit, project, every), the rule lines of AGENTS.md now.
        gate: True in the full lane.

    Returns:
        (lines to print, problems).
    """
    changed = changed_lines(root, parts)
    if changed is None:
        return [], []
    added, removed = changed
    extra = debt_triggers(root)
    if not is_kit(root) or not (added or removed or extra):
        return [], []
    out = [f"  debt check: {x}" for x in extra]
    h = conflict_hash(added + extra, removed)
    if conflict_recorded(root, h, "debt-check", "*-debt.md"):
        return out + [f"  debt check: recorded (debt-check: {h})"], []
    need = (f"no fleet debt list for these changes (T5): list what each changed rule line, new check and stricter cap fails today in "
            f"every fleet repo, with a fix plan, and record the line \"debt-check: {h}\" in a {REVIEWS}/*-debt.md file")
    return (out, [need]) if gate else (out + [f"WARN  {need} (the full lane fails without it)"], [])


def file_report(root):
    """The file checks of `--rules`: the tool rows (T1), the script lines ratchet (T2) and the role word (T6).

    Args:
        root: the repo root (a Path).

    Returns:
        (lines to print, problems).
    """
    warns, problems = tool_report(root)
    rows, found = ratchet_report(root)
    more, role = role_report(root)
    return rows + warns + more, problems + found + role


def last_changes(root):
    """The date of the last commit of each file of docs/reviews/ (the dates of a cut history are not the real dates).

    Args:
        root: the repo root (a Path).

    Returns:
        {path: "YYYY-MM-DD"}; None in a shallow clone or with no git history (no age test is made).
    """
    if git(root, "rev-parse", "--is-shallow-repository") != "false":
        return None
    dates, day = {}, ""
    for line in (git(root, "log", "--name-only", "--format=@%cs", "--", REVIEWS) or "").splitlines():
        if line.startswith("@"):
            day = line[1:]
        elif line:
            dates.setdefault(line, day)   # newest commit first: the first date seen is the last change
    return dates


def archivable(root, files, today):
    """The files of docs/reviews/ that the approved retention schedule lets a script archive (plan 2026-11-25-archival-plan.md).

    A unit is a file or a folder directly under docs/reviews/. It is archivable when no live text names it, no check reads it
    (a `rule-conflict-check:` or `debt-check:` line, a `*-coverage.md` list), each plan in it is closed, and its newest
    change is ARCHIVE_DAYS old (14 days; for a plan 7 days, also after the last change of the handoff). Live text: the tracked files outside docs/reviews/,
    DECISIONS.md, LOG.md and CHANGELOG.md, and the open plans in docs/reviews/. A plan (`*-plan.md`) is closed when it has
    a checked box (`[x]`) and no open box (`[ ]`, `[~`); a plan with no box is open. A person decides the tests a script
    cannot (audit skill, section "The archive step").

    Args:
        root: the repo root (a Path).
        files: the tracked files that exist (paths from the root).
        today: the date to count from (a datetime.date).

    Returns:
        [(path, bytes)] of the archivable files; None when the age is unknown (a shallow clone).
    """
    def read(rel):
        """Read a UTF-8 file relative to root."""
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    texts = {rel: read(rel) for rel in files if rel.startswith(REVIEWS + "/")}
    dates = last_changes(root) if texts else {}
    if dates is None:
        return None
    # A plan closes when the handoff stops naming it, an edit that leaves the plan file as it is: count its 7 days from
    # the last change of the plan and of the handoff files, whichever is newer.
    handoff = git(root, "log", "-1", "--format=%cs", "--", *HANDOFF_FILES) or "0001-01-01"
    closed = {rel for rel, t in texts.items() if rel.endswith("-plan.md") and DONE_BOX.search(t) and not OPEN_BOX.search(t)}
    live = "\n".join([read(rel) for rel in files if rel not in texts and rel not in HISTORY_DOCS]
                     + [t for rel, t in texts.items() if rel.endswith("-plan.md") and rel not in closed])
    units, out = {}, []
    for rel in texts:
        units.setdefault(rel.split("/")[2], []).append(rel)
    for name, rels in units.items():
        plan_unit = any(r.endswith("-plan.md") for r in rels)
        if (name in live or name in KEEP_NAMES or any(CHECK_READ.search(texts[r]) or r.endswith("-coverage.md") for r in rels)
                or any(r.endswith("-plan.md") and r not in closed for r in rels) or any(r not in dates for r in rels)):
            continue
        age = (today - max(datetime.date.fromisoformat(d) for d in [dates[r] for r in rels] + [handoff] * plan_unit)).days
        if age >= ARCHIVE_DAYS[plan_unit]:
            out += [(r, (root / r).stat().st_size) for r in rels]
    return out


def archive_due(root, files, today):
    """Why the archive step is due, or "": the archivable set reaches ARCHIVE_SET. The size of docs/reviews/ does not count
    (files a check reads stay there for good). A shallow clone has no age test, so it is never due.

    Args:
        root: the repo root (a Path).
        files: every tracked file (`git ls-files`, with no `audit-ignore:` glob: an ignored file can hold a live link).
        today: the date to count from (a datetime.date).

    Returns:
        The reason as a text, or "".
    """
    found = archivable(root, [r for r in files if (root / r).is_file()], today)
    if found and (len(found) >= ARCHIVE_SET[0] or sum(b for _, b in found) >= ARCHIVE_SET[1]):
        return f"{len(found)} files, {sum(b for _, b in found) // 1000} KB archivable"
    return ""


def rules_report(root, cfg, gate=False):
    """The full report of `--rules`: the rule census, the file checks and the debt record, then a
    RULES FAIL line for each problem.

    Args:
        root: the repo root (a Path).
        cfg: the audit settings (its budgets are the caps).
        gate: True in the full lane: a missing conflict-check or debt record is a problem, not a WARN line.

    Returns:
        (lines to print, problems).
    """
    out, problems = _census_rules_report(root, cfg, gate)
    path = root / RULES_FILE
    if path.is_file():
        rows, found = file_report(root)
        drows, dfound = debt_record(root, rule_lines(path.read_text(encoding="utf-8", errors="replace")), gate)
        out, problems = out + rows + drows, problems + found + dfound
    return out + [f"RULES FAIL:  {pr}" for pr in problems], problems


# ---------------------------------------------------------------- timings and audit due -------------------------------

def timing_argv(cmd):
    """The argument list of a timed command (no shell, CWE-78): [python3|bash] <scripts/ or tests/ path> [args].

    ValueError for a shell character, another program, an absolute path or "..".
    """
    argv = shlex.split(cmd) if not SHELL_CHARS & set(cmd) else []
    path = argv[1] if argv[:1] in (["python3"], ["bash"]) and len(argv) > 1 else (argv[0] if argv else "")
    if not path.startswith(TIMING_DIRS) or ".." in path.split("/"):
        raise ValueError(f"timed command not allowed (shell character, or not a scripts/ or tests/ file): {cmd!r}")
    return argv


def run_timings(root, cfg, record):
    """Run each timed command that has a cmd; return (report rows, names slower or failed); record stores the new seconds.

    Args:
        root: the repo root (a Path).
        cfg: the audit settings, with "timings".
        record: True to store the new seconds in cfg.

    Returns:
        (report rows, names of the commands that were slower or failed).
    """
    rows, slow = [], []
    for name, t in cfg.get("timings", {}).items():
        if not t.get("cmd"):
            continue  # measured by the script that runs it (--compare)
        t0 = time.monotonic()
        rc = subprocess.run(timing_argv(t["cmd"]), cwd=root, capture_output=True).returncode
        secs = round(time.monotonic() - t0, 1)
        base = t.get("seconds")
        limit = t.get("max_slowdown", 0.25)
        verdict = "FAILED" if rc else "new" if base is None else ("SLOWER" if secs > base * (1 + limit) else "ok")
        if verdict in ("SLOWER", "FAILED"):
            slow.append(name)
        rows.append(f"  {name}: {secs} s (baseline {base or '-'} s, limit +{int(limit * 100)}%, exit {rc}) {verdict}")
        if record and not rc:
            t["seconds"] = secs
    return rows, slow


def compare_times(cfg, pairs, record=False):
    """pairs: [(name, seconds)]; name is a timings key, or "key:step" for one of its "steps". Returns (line, slow).
    Warn only: a slowdown is reported, never a failure (the Administrator, 2026-11-16).

    Args:
        cfg: the audit settings, with "timings"; record changes it in place.
        pairs: the (name, seconds) pairs that a script measured.
        record: True to store the seconds as the new baselines.

    Returns:
        (one TIME or WARN line, the texts of the slower ones).
    """
    timings = cfg.setdefault("timings", {})
    slow, new, n = [], [], 0
    for name, secs in pairs:
        key, _, step = name.partition(":")
        entry = timings.setdefault(key, {}) if record else timings.get(key, {})
        base = entry.get("steps", {}).get(step) if step else entry.get("seconds")
        limit = entry.get("max_slowdown", 0.25)
        floor = entry.get("min_slowdown_seconds", 0.5)
        if base is None:
            new.append(name)
        elif secs > base * (1 + limit) and secs - base >= floor:
            slow.append(f"{step or key} {secs} s (baseline {base} s, +{round((secs / base - 1) * 100) if base else 999}%)")
        n += 1
        if record:
            if step:
                entry.setdefault("steps", {})[step] = secs
            else:
                entry["seconds"] = secs
    if record:
        return f"TIME  baseline recorded for {n} time(s) in {STATE}", []
    if slow:
        return ("WARN  slower than the baseline: " + "; ".join(slow) +
                ". Next: .claude/skills/audit/SKILL.md, A slow run (a measured slowdown starts it)"), slow
    tail = f"; no baseline yet for {len(new)} ({', '.join(new)}): .claude/skills/audit/SKILL.md, Record a baseline" if new else ""
    return f"TIME  baseline: {n - len(new)} of {n} within the limit{tail}", []


def save_timings(root, timings):
    """Write timings into .check.state.json and keep its other parts."""
    check_settings.save_part(root, "timings", timings)


def fleet_audit_due(root, today, every_days=14):
    """Why the fleet audit is due, or "" when it is not (the kit only: R3). Due when kit.config.json has no `fleet.last_audit`
    date, when that date is more than every_days old, or when HEAD carries a kit release tag (v*) dated after it.

    Args:
        root: the repo root (a Path).
        today: the date to count from (a datetime.date).
        every_days: the days after which the audit is due again.

    Returns:
        The reason as a text, or "".
    """
    if not is_kit(root):
        return ""
    try:
        last = datetime.date.fromisoformat(json.loads((root / "kit.config.json").read_text(encoding="utf-8"))["fleet"]["last_audit"])
    except (ValueError, KeyError, TypeError, OSError):
        return "no fleet.last_audit date in kit.config.json"
    reasons = [f"{(today - last).days} days since {last}"] if (today - last).days > every_days else []
    for tag in (git(root, "tag", "--points-at", "HEAD", "--list", "v[0-9]*", "--format=%(creatordate:short) %(refname:short)") or "").splitlines():
        if tag.split()[0] > last.isoformat():
            reasons.append(f"kit release {tag.split()[1]} is newer than {last}")
    return "; ".join(reasons)


def audit_due(root, cfg, today):
    """Why the full audit is due (days or commits since the last one, or never audited), or "" when it is not.

    Args:
        root: the repo root (a Path).
        cfg: the audit settings, with "last_audit".
        today: the date to count from (a datetime.date).

    Returns:
        The reason as a text, or "".
    """
    last = cfg.get("last_audit") or {}
    if not last.get("date"):
        # Never audited: due once the repo is every_days or every_commits past its first commit (kit default, 2026-11-13),
        # so a new project does not report AUDIT DUE on day one. No history readable, or a shallow clone (its oldest
        # commit is a cut, not the first commit): due.
        if git(root, "rev-parse", "--is-shallow-repository") == "true":
            return "never audited"
        first = git(root, "log", "--max-parents=0", "--format=%cs")
        count = git(root, "rev-list", "--count", "HEAD")
        if not first or not count:
            return "never audited"
        start = min(datetime.date.fromisoformat(d) for d in first.split())
        days = (today - start).days
        if days >= int(cfg["every_days"]) or int(count) >= int(cfg["every_commits"]):
            return f"never audited; {days} days and {count} commits since the first commit"
        return ""
    reasons = []
    days = (today - datetime.date.fromisoformat(last["date"])).days
    if days >= int(cfg["every_days"]):
        reasons.append(f"{days} days since {last['date']}")
    if last.get("commit"):
        n = git(root, "rev-list", "--count", f"{last['commit']}..HEAD")
        if n is not None and int(n) >= int(cfg["every_commits"]):
            reasons.append(f"{n} commits since {last['commit'][:7]}")
    return "; ".join(reasons)


# ---------------------------------------------------------------- entry points ----------------------------------------

def main_compare(root, items, record):
    """--compare: print one TIME or WARN line for NAME=SECONDS items; --record stores them. Always 0.

    Args:
        root: the repo root (a Path).
        items: the NAME=SECONDS arguments.
        record: True to store them as the new baselines.

    Returns:
        The exit code 0.
    """
    try:
        cfg = load_config(root)
        pairs = [(i.rsplit("=", 1)[0], round(float(i.rsplit("=", 1)[1]), 1)) for i in items]
    except (ValueError, TypeError, KeyError, IndexError) as e:
        print(f"TIME  baseline: not compared ({e})")
        return 0
    line, _ = compare_times(cfg, pairs, record)
    if record:
        save_timings(root, cfg["timings"])
    print(line)
    return 0


def report(root, args, today=None):
    """Print the full report (or the --brief line).

    Args:
        root: the repo root (a Path).
        args: the parsed options (brief, time, record, strict).
        today: the date to count the audit from; None = today.

    Returns:
        The exit code: 1 with --strict when something is over or the audit is due, else 0.
    """
    today = today or datetime.date.today()
    try:
        cfg = load_config(root)
        due = audit_due(root, cfg, today)
    except (ValueError, TypeError, KeyError) as e:
        print(f"bloat:       settings unreadable ({e}); fix it, then run scripts/bloat_check.py")
        return 1 if args.strict else 0
    b = cfg["budgets"]
    files = scan_files(root, cfg)
    _, s_bytes, s_tok, s_files = start_read(root, cfg)
    hp = root / "docs/NEXT_PROMPT.md"
    h_lines = hp.read_bytes().count(b"\n") if hp.exists() else 0
    dups = duplicates(root, dup_files(files, cfg))
    big = big_files(root, files, b["file_kb"])
    over = []
    # The session load cap and its warning are reported by rules_report (they fail scripts/check.sh --rules).
    warn = "session load over warning" if b.get("session_load_warn_tokens", 0) < s_tok <= b["session_load_tokens"] else ""
    if h_lines > b["handoff_lines"]:
        over.append("handoff")
    if len(dups) > b["duplicate_lines"]:
        over.append("duplicates")
    if big:
        over.append("big files")
    r_rows, r_problems = rules_report(root, cfg)
    over += r_problems
    t_rows, slow = run_timings(root, cfg, args.record) if args.time else ([], [])
    over += [f"timing {n}" for n in slow]
    if args.record and args.time:
        save_timings(root, cfg.get("timings", {}))

    tail = (f"AUDIT DUE ({due}): tell the Administrator and ask whether to run the audit skill (.claude/skills/audit/SKILL.md, "
            "about 1 hour of agent time); never start it unasked") if due else "audit not due"
    fleet = fleet_audit_due(root, today)
    if fleet:
        tail += (f" · AUDIT DUE (fleet: {fleet}): tell the Administrator and ask whether to run the fleet audit "
                 "(.claude/skills/audit/SKILL.md, section Fleet audit); never start it unasked")
    archive = archive_due(root, (git(root, "ls-files") or "").splitlines(), today)
    if archive:
        tail += (f" · ARCHIVE DUE ({archive}): tell the Administrator and ask whether to run the archive step "
                 "(.claude/skills/audit/SKILL.md, section The archive step); never start it unasked")
    if args.brief:
        print(f"bloat:       {r_rows[0][13:]} · duplicate lines "
              f"{len(dups)} · big files {len(big)} · over: {', '.join(over) or 'none'}{' · ' + warn if warn else ''} · {tail}")
    else:
        print_full(b, (s_bytes, s_tok, s_files), r_rows, h_lines, dups, big, t_rows, over, warn, tail)
    return 1 if args.strict and (over or due) else 0


def print_full(b, load, r_rows, h_lines, dups, big, t_rows, over, warn, tail):
    """Print the full report from what report() measured.

    Args:
        b: the budgets of the audit settings.
        load: the session load as (bytes, ~tokens, [(file, bytes)]).
        r_rows: the lines of the rules report.
        h_lines: the line count of the handoff.
        dups: the duplicate lines, as duplicates() gives them.
        big: the big files, as big_files() gives them.
        t_rows: the timing rows (--time), or [].
        over: the names of what is over its budget.
        warn: the warning text, or "".
        tail: the audit line.
    """
    s_bytes, s_tok, s_files = load
    print(f"session load: {s_bytes:,} bytes, ~{s_tok:,} tokens (cap {b['session_load_tokens']:,})")
    for rel, size in s_files:
        print(f"  {rel}: {size:,} bytes")
    print(r_rows[0])
    moved = sum(1 for r in r_rows if r.startswith(("  + ", "  - ")))
    if moved:
        print(f"  {moved} rule line(s) added or removed against the default branch (list: --rules)")
    print(f"handoff:     docs/NEXT_PROMPT.md {h_lines} lines (budget {b['handoff_lines']})")
    print(f"duplicates:  {len(dups)} lines of {MIN_DUP}+ characters in 2+ files (budget {b['duplicate_lines']})")
    for n, fs in dups[:10]:
        print(f"  {len(fs)} files: {', '.join(fs[:4])}{' ...' if len(fs) > 4 else ''} :: {n[:70]}")
    print(f"big files:   {len(big)} over {b['file_kb']} KB" + "".join(f"\n  {r}: {k} KB" for r, k in big[:10]))
    if t_rows:
        print("timings:\n" + "\n".join(t_rows))
    print(f"over budget: {', '.join(over) or 'none'}")
    if warn:
        print(f"warning:     {warn} ({b['session_load_warn_tokens']:,} tokens); trim rules before the cap")
    print(tail)


def main_rules(root, gate=False):
    """--rules: print the rule counts, changed lines and problems, then RULES PASS or RULES FAIL; 1 on a problem.

    Args:
        root: the repo root (a Path).
        gate: True in the full lane: a missing conflict-check record fails.

    Returns:
        The exit code: 0 pass, 1 on a problem.
    """
    try:
        cfg = load_config(root)
    except (ValueError, TypeError, KeyError) as e:
        print(f"rules:       settings unreadable ({e}); fix it first")
        return 1
    rows, problems = rules_report(root, cfg, gate)
    print("\n".join(rows))
    print("RULES FAIL" if problems else "RULES PASS")
    return 1 if problems else 0


def main():
    """Parse the options and run the chosen mode; return its exit code.

    Returns:
        The exit code of the chosen mode.
    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    ap.add_argument("--rules", action="store_true")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--compare", nargs="+", metavar="NAME=SECONDS")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--skills", action="store_true")
    ap.add_argument("--project", default=".")
    args = ap.parse_args()
    if args.test:
        import bloat_check_test
        bloat_check_test.run(sys.modules[__name__])
        return 0
    root = Path(git(Path(args.project), "rev-parse", "--show-toplevel") or args.project)
    if args.lint:
        return main_lint(root)
    if args.skills:
        return main_skills(root)
    if args.rules:
        return main_rules(root, args.gate)
    if args.compare:
        return main_compare(root, args.compare, args.record)
    return report(root, args)


if __name__ == "__main__":
    sys.exit(main())
