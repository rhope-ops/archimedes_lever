#!/usr/bin/env python3
"""The skills check of scripts/bloat_check.py (`python3 scripts/bloat_check.py --skills`; kept in its own file so the
check stays under the line cap of docs/code-standard.md C4).

Input: the repo root; it reads each .claude/skills/*/SKILL.md and AGENTS.md. Output: FAIL lines (no frontmatter, no
name or description, a name that differs from its folder), indented WARN lines (description start or length, file
length, orphan skill) and the last line SKILLS PASS or SKILLS FAIL; exit 1 on a FAIL. Standard library only.
Network: none.
Writes: none.
Credentials: none.
"""
import ast
import fnmatch
import json
import re

import bloat_check_rules as brules   # scripts/bloat_check_rules.py: the reader of git
import check_settings   # scripts/check_settings.py: the reader of .check.state.json


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


# One home per rule (the Maintainer, 2026-11-18): a rule that AGENTS.md states must not be stated again, or the other
# way round, in a skill or an agent file; those files link to it. Each row: (the rule, a pattern that shows a
# second statement, the files that may hold it). A match in any other skill or agent file fails scripts/check.sh.
SINGLE_HOME = [
    ("who merges a pull request", r"only the Maintainer merges|the Maintainer merges\b|never merges this pull request|the Maintainer's merge is the approval", ["AGENTS.md"]),
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


# ---- The repo's own files, apart from the rule lines of AGENTS.md (bloat_check_rules.py): the tool rows (T1), the script
# lines ratchet (T2), the role word in kit-synced text (T6) and the triggers of the fleet debt record (T5). The seam:
# rules_report reads AGENTS.md; this part reads the other files. Plan: docs/reviews/2026-11-23-tool-retirement-plan.md.
TOOL_EXT = (".py", ".sh", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".bat", ".cmd")
TOOL_SKIP = ("node_modules/", "vendor/", "dist/")   # not the repo's own tools
TOOLS_DOC = "docs/tools.md"
STATE_KEY = "script_lines"   # in .check.state.json: {"baseline": N, "command": ..., "measured": ..., "commit": ...}
ROLE_WORD = re.compile(r"\bthe owner\b|\bOwner's\b")
DATED = re.compile(r"\(the owner, \d{4}-\d{2}-\d{2}")   # an attribution that records a past role word stays as written
# The files that hold the check itself name the word they look for: allowed whole (re.compile(".")).
ROLE_ALLOW = {**{f: re.compile(".") for f in ("scripts/bloat_check.py", "scripts/bloat_check_skills.py", "scripts/bloat_check_test_rules.py")},
              "scripts/sync_baseline.py": re.compile(r'Never rename the owner inside this script|use "the owner" as an answer option'),
              "scripts/sync_baseline_cli_test.py": re.compile(r'"the owner"|the owner word')}   # the literals the sync swaps
ENTRY = re.compile(r"(?:python3|bash)\s+(scripts/[\w.-]+\.(?:py|sh))|^[ \t]*(?:selftest|extension)\s+\S+\s+(scripts/[\w.-]+\.(?:py|sh))", re.M)
CAPS_FILE = "scripts/check_settings_read.py"


def is_kit(root):
    """True in the kit itself: it has kit.config.json and no `.check.lock` (a synced project has the lock)."""
    return (root / "kit.config.json").is_file() and not (root / ".check.lock").exists()


def tool_files(root):
    """The tool files the repo owns: tracked scripts of a known extension in any folder, not a vendor folder, not a kit
    file of the lock (the kit's own docs/tools.md lists those).

    Args:
        root: the repo root (a Path).

    Returns:
        The sorted repo-relative paths.
    """
    out = brules.git(root, "ls-files")
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
        A list of (row text, text of its candidates cell).
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
            rows.append((line, cells[col] if col < len(cells) else ""))
    return rows


def tool_report(root):
    """T1: each tool file needs a docs/tools.md row that names it and holds 3 candidates, or "none known" with search terms.

    Args:
        root: the repo root (a Path).

    Returns:
        (WARN lines, problems): a problem in the kit, a WARN line in a project (the debt: plan section 3, T5 table).
    """
    rows = tools_rows(root)
    ok = [t for t, cand in rows if re.search(r"none known\W*\w", cand, re.I) or len([x for x in re.split(r"[;,]", cand) if x.strip()]) >= 3]
    bare = [f for f in tool_files(root) if not any(f in t or re.search(r"(?<![\w/.-])" + re.escape(f.rsplit("/", 1)[-1]) + r"(?![\w-])", t) for t in ok)]
    if not bare:
        return [], []
    line = (f"{len(bare)} tool file(s) have no {TOOLS_DOC} row with 3 candidate tools, or \"none known\" and the search terms (T1: search "
            f"first), for example {', '.join(bare[:3])}")
    return ([], [line]) if is_kit(root) else ([f"WARN  {line}"], [])


def script_lines(root):
    """The newline count of scripts/*.py and scripts/*.sh: `cat scripts/*.py scripts/*.sh | wc -l` (the T2 measure)."""
    return sum(p.read_bytes().count(b"\n") for pat in ("*.py", "*.sh") for p in sorted((root / "scripts").glob(pat)))


def ratchet_report(root):
    """T2: the script lines may not pass the baseline in .check.state.json; a higher baseline than on main needs a docs/DECISIONS.md
    row By the Maintainer with the number. No baseline in the state: not checked.

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
        return [], []
    n, problems = script_lines(root), []
    if n > base:
        problems.append(f"custom script lines {n} pass the baseline {base} (+{n - base}): a higher baseline needs a docs/DECISIONS.md "
                        f"row By the Maintainer with the number {n} (T2 ratchet)")
    ref = brules.git(root, "merge-base", "HEAD", "origin/main")
    old = brules.git(root, "show", f"{ref}:{check_settings.STATE}") if ref else None
    try:
        was = json.loads(old).get(STATE_KEY, {}).get("baseline") if old else None
    except (ValueError, AttributeError):
        was = None
    if isinstance(was, int) and base > was:
        rows = (brules.git(root, "diff", ref, "--", "docs/DECISIONS.md") or "").splitlines()
        if not any(r.startswith("+") and str(base) in r and "Maintainer" in r for r in rows):
            problems.append(f"the script lines baseline rose from {was} to {base} with no new docs/DECISIONS.md row By the Maintainer that names {base}")
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
    """T6, WARN only, in the kit: kit-synced text says "the Maintainer", not "the owner" or "Owner's" (the sync swaps the role word
    per project). Allowed: a dated attribution "(the owner, YYYY-MM-DD" and the literals of ROLE_ALLOW.

    Args:
        root: the repo root (a Path).

    Returns:
        A list of WARN lines (one line: the count and the first places).
    """
    if not is_kit(root):
        return []
    hits = []
    for rel in sorted(synced_files(root)):
        p = root / rel
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines() if p.is_file() else [], 1):
            allow = ROLE_ALLOW.get(rel)
            if ROLE_WORD.search(DATED.sub("", line)) and not (allow and allow.search(line)):
                hits.append(f"{rel}:{n}")
    if not hits:
        return []
    return [f"WARN  {len(hits)} line(s) of kit-synced text use the role word \"the owner\" or \"Owner's\" (T6: write \"the Maintainer\"; the sync "
            f"swaps it): {', '.join(hits[:5])}{' ...' if len(hits) > 5 else ''}"]


def caps_of(text):
    """Read KIT_CAPS and the budgets of AUDIT_DEFAULTS from a scripts/check_settings_read.py text, as literals (never run).

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
        base = {f: brules.git(root, "show", f"{ref}:{f}") for f in ("scripts/check.sh", CAPS_FILE)}
        if base["scripts/check.sh"] is not None:
            break
    entries = lambda text: {a or b for a, b in ENTRY.findall(text or "")}
    if base["scripts/check.sh"] is not None:
        now = entries((root / "scripts/check.sh").read_text(encoding="utf-8", errors="replace"))
        out += [f"check entry point {e}" for e in sorted(now - entries(base["scripts/check.sh"]))]
    old, new = caps_of(base[CAPS_FILE] or ""), caps_of((root / CAPS_FILE).read_text(encoding="utf-8", errors="replace"))
    if old and new:
        out += [f"stricter kit cap {k}" for k in new[0] if k not in old[0] or new[1].get(k, 0) < old[1].get(k, 0)]
    return sorted(out)


def file_report(root):
    """The file checks of `--rules`: the tool rows (T1), the script lines ratchet (T2) and the role word (T6).

    Args:
        root: the repo root (a Path).

    Returns:
        (lines to print, problems).
    """
    warns, problems = tool_report(root)
    rows, found = ratchet_report(root)
    return rows + warns + role_report(root), problems + found
