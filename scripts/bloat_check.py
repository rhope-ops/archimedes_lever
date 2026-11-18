#!/usr/bin/env python3
"""Cheap bloat and drift metrics for a project repo, and the audit due date. Report only, unless --record.

Usage:
    python3 scripts/bloat_check.py            # full report
    python3 scripts/bloat_check.py --brief    # one line (scripts/session_checkin.sh runs this)
    python3 scripts/bloat_check.py --time     # also run each timed command in .check.state.json and compare
    python3 scripts/bloat_check.py --time --record   # run them and store the new seconds as the baseline
    python3 scripts/bloat_check.py --strict   # exit 1 when a budget is over or the audit is due
    python3 scripts/bloat_check.py --rules    # rule counts against the caps, rule lines added or removed against
                                              # origin/main, and missing .claude/ paths; exit 1 when a cap is passed
                                              # or a path is missing (scripts/check.sh runs this)
    python3 scripts/bloat_check.py --rules --gate   # also fail when rule lines changed and no conflict-check
                                              # record in docs/reviews/ names their hash (scripts/check.sh full lane)
    python3 scripts/bloat_check.py --lint     # rule lint of every rule line: near-duplicates, vague words, untested
                                              # rules; report only (--rules lints the changed lines)
    python3 scripts/bloat_check.py --skills   # check each .claude/skills/*/SKILL.md: FAIL (exit 1) with no frontmatter,
                                              # no name or description, or a name that differs from its folder;
                                              # WARN (exit 0) for a description not starting "Use when"/"Use before",
                                              # over 1024 characters, a file over 150 lines, or an orphan skill
                                              # (name in neither AGENTS.md nor another SKILL.md); last line SKILLS PASS/FAIL
                                              # (code: scripts/bloat_check_skills.py)
    python3 scripts/bloat_check.py --compare NAME=SECONDS ...   # compare times that a script measured with their
                                              # baselines; one TIME or WARN line; never fails (scripts/check.sh,
                                              # session_checkin.sh and the pre-push hook run it); --record stores them
    python3 scripts/bloat_check.py --test     # self-test (scripts/bloat_check_test.py); prints BLOAT TEST PASS

It measures:
    session load  bytes and ~tokens (bytes / 4) of what every session loads: AGENTS.md, CLAUDE.md,
                  docs/NEXT_PROMPT.md, the `audit-start-read:` files, and the skill and agent names and descriptions.
                  Caps for every repo (KIT_CAPS; a project can lower one, never raise it): 5,000 tokens (warning at
                  4,500) and 200 lines of AGENTS.md; over a cap fails --rules
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
    handoff       docs/NEXT_PROMPT.md lines
    duplicates    normalized text lines of 80+ characters found in 2 or more tracked files
    big files     tracked files over the size budget
    audit due     days and commits on main since the last full audit (.check.state.json "audit": "last_audit")
    timings       (--time) wall time of each named command against its recorded baseline; (--compare) times that
                  a script measured itself: NAME is a timings key, NAME:STEP one of its "steps". Slower means over
                  max_slowdown (default +25%) and over min_slowdown_seconds (default 0.5 s), so noise on a small step
                  does not warn. A slowdown starts .claude/skills/efficiency/SKILL.md

Settings: the `audit-` lines of `.check` (scripts/check_settings.py reads them and lists the keys; all are optional,
and a line that is not valid fails --rules):
    audit-every-days: 14, audit-every-commits: 300, audit-ignore: ref/**, audit-start-read: <path>,
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
"""
import argparse
import datetime
import fnmatch
import re
import subprocess
import sys
import time
from pathlib import Path

import check_settings  # scripts/check_settings.py: the reader of .check and the reader and writer of .check.state.json

STATE = check_settings.STATE
START_READ = ["AGENTS.md", "CLAUDE.md", "docs/NEXT_PROMPT.md"]
DEFAULTS = check_settings.AUDIT_DEFAULTS  # the settings when .check has no `audit-` line
RULES_FILE = "AGENTS.md"
PROJECT_RULES = "## Project rules"
NOT_RULES = {"## Commands"}  # project-owned settings, not rules
RANKED = {"## Order of authority"}  # its numbered ranking of sources is not a rule count; a bullet there is
OPTIONAL = {"scripts/check.local.sh"}  # named in AGENTS.md, present only when the project has tests
TEXT_EXT = {".md", ".txt", ".py", ".sh", ".ps1", ".psm1", ".js", ".ts", ".json", ".yml", ".yaml", ".html", ".css",
            ".toml", ".ini", ".cfg", ".csv", ""}
VAGUE = ["appropriate", "appropriately", "as needed", "if needed", "when needed", "where possible", "if possible",
         "when possible", "properly", "reasonable", "be careful", "try to", "consider", "etc.", "best practice",
         "as much as", "usually", "generally", "ideally", "maybe", "might", "should"]
VALUE_OPTIONS = {"-o", "--output", "--out", "--outline"}  # options whose value is a file the command writes
NEAR_DUP = 0.6        # word overlap (Jaccard) from which two rule lines are a near-duplicate pair
RULE_TESTS = ".claude/rule-tests.md"
REVIEWS = "docs/reviews"
MIN_DUP = 80          # characters in a normalized line before it counts as a duplicate
MAX_SCAN = 1_000_000  # bytes; larger files are not scanned for duplicates


def git(root, *args):
    """Run git in root; return its output, or None when git fails or is missing."""
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def load_config(root):
    """The audit settings of .check, with "last_audit" and "timings" from .check.state.json; ValueError when a
    line is not valid or a file cannot be read (scripts/check_settings.py; KIT_CAPS budgets can only be lowered there)."""
    return check_settings.audit_config(root)


def ignored(rel, cfg):
    """True when rel matches a glob of an `audit-ignore:` line."""
    return any(fnmatch.fnmatch(rel, g) for g in cfg.get("ignore", []))


def start_read(root, cfg):
    """Return (lines, bytes, ~tokens, [(file, bytes)] largest first) of what every session loads: the start-read
    files, and the names and descriptions of the skills and agents (one entry; Claude Code lists them at start)."""
    import bloat_check_skills  # scripts/bloat_check_skills.py: kept apart (code standard C4)
    lines, size = 0, bloat_check_skills.listing_bytes(root)
    files = [("skill and agent descriptions", size)] if size else []
    for rel in START_READ + cfg.get("start_read", []):
        p = root / rel
        if p.is_file():
            b = p.read_bytes()
            lines += b.count(b"\n")
            size += len(b)
            files.append((rel, len(b)))
    return lines, size, size // 4, sorted(files, key=lambda f: -f[1])


ITEM = re.compile(r"^\s*(?:[-*+]|(\d+)[.)])\s+(.*)$")
RULE_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")           # --- or * * *: a horizontal rule, not a rule
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")  # |---|---|: the row above it is a header
HEADING = re.compile(r"^\s*#{1,6}(\s|$)")                    # "### Sub"; "#1 priority: ..." is text, not a heading
EMPTY_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*$")         # a marker with no text


BOLD_LABEL = re.compile(r"^\s*\*\*([^*]+?)\.?\*\*")  # "**Delivery.** text": the label of a rule bullet


def bold_label(text):
    """The bold label that starts a rule bullet, without its trailing dot ("Delivery"), or None."""
    m = BOLD_LABEL.match(text)
    return m.group(1).strip() if m else None


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
        elif not sec:
            continue
        elif not line.strip() or HEADING.match(line) or RULE_HR.match(line) or EMPTY_ITEM.match(line):
            open_item = False
        elif TABLE_SEP.match(line) and "-" in line and "|" in line:
            if open_item and rows and "|" in rows[-1][1]:
                rows.pop()  # the header row of a table
            open_item = False
        else:
            m = ITEM.match(line)
            indented = line[:1] in (" ", "\t")
            if m:
                counted = sec not in NOT_RULES and not (sec in RANKED and m.group(1))
                rows.append([sec, m.group(2).strip(), counted, bold_label(m.group(2)) or sec[3:].strip()])
                open_item = True
            elif open_item and not line.lstrip().startswith("|") and (indented or sec != PROJECT_RULES):
                rows[-1][1] += " " + line.strip()  # a wrapped line belongs to the item above it
            elif sec == PROJECT_RULES:
                rows.append([sec, line.strip(), True, bold_label(line) or sec[3:].strip()])
                open_item = True
    if with_sections:
        return [(key, t) for _, t, c, key in rows if c]
    kit = [t for s_, t, c, _ in rows if c and s_ != PROJECT_RULES]
    project = [t for s_, t, c, _ in rows if c and s_ == PROJECT_RULES]
    return kit, project, [r[1] for r in rows]


def words(line):
    """The set of lower-case words of 3+ characters in line (for the near-duplicate measure)."""
    return set(re.findall(r"[a-z0-9][a-z0-9'-]{2,}", line.lower()))


def tested_sections(root):
    """Rule keys that have a scenario: the "Section" column of .claude/rule-tests.md (a bold bullet label, else a heading)."""
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
    Returns WARN lines: near-duplicate pairs, vague words, untested rules."""
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
    import hashlib
    text = "\n".join(sorted("+" + l for l in added) + sorted("-" + l for l in removed))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def conflict_recorded(root, h):
    """True when a file in docs/reviews/ holds the line "rule-conflict-check: <h>"."""
    d = root / REVIEWS
    return d.is_dir() and any(f"rule-conflict-check: {h}" in f.read_text(encoding="utf-8", errors="replace")
                              for f in d.rglob("*.md"))


def missing_pointers(root, text):
    """Paths that AGENTS.md names and that do not exist: each `.claude/...`, `scripts/...` and `docs/...` path
    inside backticks (also after a command word: `python3 scripts/x.py --test`), and relative link targets. Not a
    path to check: the value of an output option (`-o docs/out.html`: a file the command makes; VALUE_OPTIONS); a line number
    (`scripts/a.py:12`) and a pipe or ; or & after a path are cut off."""
    text = re.sub(r"(?ms)^<!-- starter -->\n.*?^<!-- /starter -->\n", "", text)
    names = set()
    for span in re.findall(r"`([^`\n]+)`", text):
        words = re.split(r"[\s|;&]+", span)
        for prev, w in zip([""] + words, words):
            w = re.sub(r"(:\d+)+$", "", w.rstrip(".,;:)"))
            if re.match(r"(?:\.claude|scripts|docs)/", w) and prev not in VALUE_OPTIONS:
                names.add(w)
    names -= OPTIONAL
    names |= {t.split("#")[0] for t in re.findall(r"\]\(([^)\s]+)\)", text)
              if "://" not in t and not t.startswith(("#", "mailto:"))}
    return sorted(n for n in names if n and not re.search(r"[<>*{]", n) and not (root / n).exists())


def rules_report(root, cfg, gate=False):
    """Return (lines to print, problems). Problems fail scripts/check.sh: a cap passed, a missing path, and with gate
    (the full lane) rule lines changed against origin/main with no conflict-check record in docs/reviews/."""
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
    if load > b["session_load_tokens"]:
        problems.append(f"session load over the cap (~{load:,} > {b['session_load_tokens']:,} tokens: the start-read files "
                        "plus the skill and agent descriptions)")
    elif load > b["session_load_warn_tokens"]:
        out.append(f"WARN  session load ~{load:,} tokens is over the warning ({b['session_load_warn_tokens']:,}); trim before the cap")
    # The bullet counts only warn (the owner, 2026-11-18): the line and load caps are the limits.
    if len(kit) > b["rules"]:
        out.append(f"WARN  {len(kit)} rule bullets (guide {b['rules']})")
    if len(project) > b["project_rules"]:
        out.append(f"WARN  {len(project)} project rule bullets (guide {b['project_rules']})")
    import bloat_check_skills  # scripts/bloat_check_skills.py: kept apart (code standard C4)
    problems += bloat_check_skills.second_homes(root)
    old = None
    for ref in ("origin/main", "origin/master"):
        old = git(root, "show", f"{ref}:{RULES_FILE}")
        if old is not None:
            break
    if old is not None:
        import check_lock  # in a synced project the kit checked the locked kit lines: only "Project rules" count here
        part = 1 if check_lock.kit_text_locked(root) else 2
        every = (kit, project, every)[part]
        was = set(rule_lines(old)[part])
        now = set(every)
        added, removed = [l for l in every if l not in was], sorted(was - now)
        for mark, lines in (("+", added), ("-", removed)):
            out += [f"  {mark} {l}" for l in lines]  # the whole line: a change near its end must show
        if was != now:
            out.append("  (rule lines changed against the default branch: each one needs the owner's approval of its exact text)")
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
    gone = missing_pointers(root, text)
    if gone:
        problems.append("missing paths named in AGENTS.md: " + ", ".join(gone))
    for pr in problems:
        out.append(f"RULES FAIL:  {pr}")
    return out, problems


def norm(line):
    """line without list, quote, heading and table marks, whitespace made single, lower case (for duplicates)."""
    line = re.sub(r"^[\s>#|*\-+0-9.]+", "", line)
    return re.sub(r"\s+", " ", line).strip().lower()


def scan_files(root, cfg):
    """The tracked files that exist and are not ignored by the config."""
    out = git(root, "ls-files")
    return [rel for rel in (out.splitlines() if out else []) if not ignored(rel, cfg) and (root / rel).is_file()]


def duplicates(root, files):
    """Return [(normalized line, [files])] for long lines found in 2+ text files, most files first."""
    seen = {}
    for rel in files:
        p = root / rel
        if p.suffix.lower() not in TEXT_EXT or p.stat().st_size > MAX_SCAN:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            n = norm(line)
            if len(n) >= MIN_DUP:
                seen.setdefault(n, set()).add(rel)
    dups = [(n, sorted(fs)) for n, fs in seen.items() if len(fs) > 1]
    return sorted(dups, key=lambda d: -len(d[1]))


def big_files(root, files, kb):
    """Return [(file, KB)] of the files over kb kilobytes, largest first."""
    return sorted(((rel, (root / rel).stat().st_size // 1024) for rel in files
                   if (root / rel).stat().st_size > kb * 1024), key=lambda f: -f[1])


def audit_due(root, cfg, today):
    """Why the full audit is due (days or commits since the last one, or never audited), or "" when it is not."""
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


def run_timings(root, cfg, record):
    """Run each timed command that has a cmd; return (report rows, names slower or failed); record stores the new seconds."""
    rows, slow = [], []
    for name, t in cfg.get("timings", {}).items():
        if not t.get("cmd"):
            continue  # measured by the script that runs it (--compare)
        t0 = time.monotonic()
        rc = subprocess.run(t["cmd"], shell=True, cwd=root, capture_output=True).returncode
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
    Warn only: a slowdown is reported, never a failure (the owner, 2026-11-16)."""
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
                ". Next: .claude/skills/efficiency/SKILL.md (a measured slowdown starts it)"), slow
    tail = f"; no baseline yet for {len(new)} ({', '.join(new)}): .claude/skills/efficiency/SKILL.md, Record a baseline" if new else ""
    return f"TIME  baseline: {n - len(new)} of {n} within the limit{tail}", []


def main_compare(root, items, record):
    """--compare: print one TIME or WARN line for NAME=SECONDS items; --record stores them. Always 0."""
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


def save_timings(root, timings):
    """Write timings into .check.state.json and keep its other parts."""
    check_settings.save_part(root, "timings", timings)


def report(root, args, today=None):
    """Print the full report (or the --brief line); return 1 with --strict when something is over or the audit is due."""
    today = today or datetime.date.today()
    try:
        cfg = load_config(root)
        due = audit_due(root, cfg, today)
    except (ValueError, TypeError, KeyError) as e:
        print(f"bloat:       settings unreadable ({e}); fix it, then run scripts/bloat_check.py")
        return 1 if args.strict else 0
    b = cfg["budgets"]
    files = scan_files(root, cfg)
    s_lines, s_bytes, s_tok, s_files = start_read(root, cfg)
    hp = root / "docs/NEXT_PROMPT.md"
    h_lines = hp.read_bytes().count(b"\n") if hp.exists() else 0
    dups = duplicates(root, files)
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

    tail = (f"AUDIT DUE ({due}): tell the owner and ask whether to run the audit skill (.claude/skills/audit/SKILL.md, "
            "about 1 hour of agent time); never start it unasked") if due else "audit not due"
    if args.brief:
        print(f"bloat:       {r_rows[0][13:]} · duplicate lines "
              f"{len(dups)} · big files {len(big)} · over: {', '.join(over) or 'none'}{' · ' + warn if warn else ''} · {tail}")
    else:
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
    return 1 if args.strict and (over or due) else 0


def main_lint(root):
    """--lint: print the rule lint of every rule line and a LINT count line. Always 0 (warn only)."""
    p = root / RULES_FILE
    rules = rule_lines(p.read_text(encoding="utf-8", errors="replace"), with_sections=True) if p.is_file() else []
    rows = lint(root, rules)
    print("\n".join(rows + [f"LINT: {len(rows)} flag(s) in {len(rules)} rule lines (warn only)"]))
    return 0


def main_rules(root, gate=False):
    """--rules: print the rule counts, changed lines and problems, then RULES PASS or RULES FAIL; 1 on a problem."""
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
    """Parse the options and run the chosen mode; return its exit code."""
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
        import bloat_check_test  # scripts/bloat_check_test.py: kept apart (code standard C4)
        bloat_check_test.run(sys.modules[__name__])
        return 0
    root = Path(git(Path(args.project), "rev-parse", "--show-toplevel") or args.project)
    if args.lint:
        return main_lint(root)
    if args.skills:
        import bloat_check_skills  # scripts/bloat_check_skills.py: kept apart (code standard C4)
        return bloat_check_skills.main_skills(root)
    if args.rules:
        return main_rules(root, args.gate)
    if args.compare:
        return main_compare(root, args.compare, args.record)
    return report(root, args)


if __name__ == "__main__":
    sys.exit(main())
