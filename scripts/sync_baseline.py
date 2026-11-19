#!/usr/bin/env python3
"""Sync a project repo to the current rhope-ops/archimedes_lever baseline.

Run it from inside the project repo:
    python3 scripts/sync_baseline.py            # dry run: show the diff, write nothing
    python3 scripts/sync_baseline.py --apply    # write the files (commit them yourself)

Options:
    --baseline PATH_OR_URL   Baseline repo (default: https://github.com/rhope-ops/archimedes_lever)
    --name, --repo, --purpose   Header values, needed only when the project AGENTS.md has none.
    --timezone ZONE          IANA time zone for project log times, needed only when the project AGENTS.md has no
                             "- Time zone:" line (projects synced before 2026-11-11 have none).
    --owner NAME             Name agents use for the decider (default: the project's "- Owner:" line, else "the owner").
                             A public repo sets a role, for example --owner "the maintainer", so no real name is synced in.
    --tier starter|full      Kit tier (default: the project's "- Tier:" line, else "full", the only tier before 2026-11-13).
                             --tier full on a starter project adds the advanced parts (ADVANCED_FILES below, and a new
                             docs/LOG.md unless Project rules name a project log place).
                             --tier starter on a full project keeps the advanced files and lists them for you to delete.
    --set-tier starter|full  Bootstrap only: apply the tier to THIS repo in place (AGENTS.md blocks; in starter, delete
                             ADVANCED_FILES). No baseline, no diff.

Tiers (the owner, 2026-11-13): a starter project has the core rules, hooks and checks only. AGENTS.md marks text
for one tier with lines "<!-- full -->" ... "<!-- /full -->" and "<!-- starter -->" ... "<!-- /starter -->";
apply_tier() keeps the blocks for the project's tier and drops the marker lines.

What it changes:
    AGENTS.md              Baseline text above "## Project rules", with this project's header values.
                           Keeps this project's "## Commands" section and everything from "## Project rules" on.
                           An AGENTS.md without the baseline layout goes under "## Project rules" as it is.
    CLAUDE.md              Adds "@AGENTS.md" at the top if it is missing. Keeps the rest.
    scripts/session_checkin.sh, scripts/stop_check.py, scripts/worker_guard.py,
    .claude/skills/ (every kit skill), .claude/agents/worker.md, scout.md, reviewer.md
                           Replaced with the baseline copies.
    docs/FIRST_USE.md      Added when missing. A project may tune it (it holds the denylist places that the
                           session-start check names), so a copy the project changed is kept, with one line that
                           says it differs and how to compare. A copy that is byte for byte an earlier kit version
                           of the file was never tuned: it is replaced. This needs the baseline's git history; with
                           a baseline folder that is no git repo, a copy that differs is kept.
    scripts/log_check.py, scripts/timeline.py, scripts/check_content*.py, scripts/first_use_check.py,
    scripts/check.sh, scripts/bloat_check*.py, scripts/code_standard*.py, docs/code-standard.md, scripts/git-hooks/pre-push,
    .claude/rule-tests.md
                           Replaced with the baseline copies. A starter project gets none of ADVANCED_FILES. (.check is not copied: a project opts in itself.)
    .claude/settings.json  The kit's deny rules first (scripts/check_blocks.py), the kit's hook entries first in each
                           event (an older copy of a kit hook is replaced), and the baseline "sandbox" block when the
                           project has none. Keeps the project's own deny rules, hooks and all other settings.
    .check.lock            The kit lock: the kit version and commit, and a hash of each kit file and of the kit
                           sections of AGENTS.md (scripts/check_lock.py; scripts/check.sh fails on a difference).
    .gitignore             Adds the baseline lines. Keeps all other lines.
    docs/LOG.md            An Arcs table with the old columns (Arc | Span | Summary | Outcome) gets the story columns
                           Problem, Turning point and Lesson, each "-" (.claude/skills/project-log/SKILL.md). Rows are kept.
    docs/archimedes_lever-LICENSE.txt   The kit's license (MIT), which covers the copied files.
    Owner name             In baseline text only (AGENTS.md above "## Project rules" and the copied files, not this
                           script), "the owner" becomes the project owner ("The owner" becomes the owner with a capital
                           first letter). Project text is never renamed. A private repo may keep a real name
                           (--owner NAME); a public repo uses a role. Owner: letters, digits, space . _ , ( ) -
What it never changes: README.md, docs/ (except docs/FIRST_USE.md as said above, docs/code-standard.md and the kit
license), .check and all other files. A project's own code lives in its own files (scripts/check.local.sh,
scripts/check_content_local.py, scripts/code_standard_gate.py), which a sync never touches.
Standard library only. Needs git.
Network: the baseline repo, only when --baseline is a URL (one git clone); none for a local folder.
Writes: with --apply, the kit files of the project and its kit lock .check.lock (the list: "What it changes" above); without it, nothing.
Credentials: none itself; a clone uses the credentials git already has.
"""
import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_blocks  # noqa: E402 - the deny rules and the placeholder pattern
import check_lock  # noqa: E402 - the kit lock that a sync writes into the project
from sync_merge import REPLACED_HOOKS, changed_matchers, die, merge_lines, merge_settings, migrate_arcs  # noqa: E402,F401 - scripts/sync_merge.py
from sync_merge import (apply_tier, find_heading, header_timezone, header_tier, header_values,  # noqa: E402,F401
                        headings, section, valid_timezone)  # the AGENTS.md header helpers (drift.py reads them here)

DEFAULT_BASELINE = "https://github.com/rhope-ops/archimedes_lever"
RULES_HEADING = "## Project rules"
COMMANDS_HEADING = "## Commands"
COPY_FILES = ["scripts/session_checkin.sh", "scripts/stop_check.py", "scripts/check_blocks.py", "scripts/check_lock.py", "scripts/check_content_test_blocks.py",
              "scripts/worker_guard.py", "scripts/log_check.py", "scripts/timeline.py", "scripts/check_content.py", "scripts/first_use_check.py",
              "scripts/check_content_scan.py", "scripts/check_content_hook.py", "scripts/check_content_test.py",
              "scripts/check_content_finders.py", "scripts/check_content_test_local.py", "scripts/check_settings_test.py",
              "scripts/check.sh", "scripts/check_settings.py", "scripts/bloat_check.py", "scripts/bloat_check_skills.py", "scripts/bloat_check_test.py",
              "scripts/bloat_check_rules.py",
              "scripts/code_standard.py", "scripts/code_standard_test.py", "scripts/code_standard_docs.py", "scripts/code_standard_parse.py",
              "docs/code-standard.md", "scripts/git-hooks/pre-push",
              ".claude/skills/delegate/SKILL.md", ".claude/skills/audit/SKILL.md", ".claude/skills/project-log/SKILL.md", ".claude/rule-tests.md", ".github/workflows/check.yml",
              ".claude/skills/deliver/SKILL.md", ".claude/skills/personal-data/SKILL.md", ".claude/skills/rule-change/SKILL.md",
              ".claude/skills/data-change/SKILL.md", ".claude/skills/verify/SKILL.md", ".claude/skills/verify/measure.mjs",
              ".claude/skills/efficiency/SKILL.md", ".claude/skills/handoff/SKILL.md",
              ".claude/skills/kit-update/SKILL.md",
              ".claude/agents/worker.md", ".claude/agents/scout.md", ".claude/agents/reviewer.md"]
# A file a project may tune: added when missing, replaced when the project's copy is an earlier kit version, else kept
# (copy_state). (The kit's agent files are kit files since 2026-11-18: an old copy can restate a rule; a project adds
# an agent of its own under its own name.)
COPY_IF_MISSING = ["docs/FIRST_USE.md"]
COPY_NOTES = []  # one line for each COPY_IF_MISSING file that a sync replaces or keeps (main() prints them)
BASELINE_OWNER = "the owner"  # role word in baseline text; no real name lives in the baseline
# Never rename the owner inside this script: it holds BASELINE_OWNER as a literal.
# first_use_check.py and docs/FIRST_USE.md use "the owner" as an answer option and a role: keep them as written
# (bootstrap.sh skips them too).
def log_template(base):
    """The blank project log: docs/templates/LOG.md (the kit's docs/LOG.md is its own log); older baselines: docs/LOG.md."""
    t = base / "docs/templates/LOG.md"
    return t if t.exists() else base / "docs/LOG.md"


# Advanced parts: a starter project has none of these (one list for bootstrap, sync and drift).
ADVANCED_FILES = [".claude/skills/delegate/SKILL.md", ".claude/agents/scout.md", ".claude/agents/worker.md",
                  ".claude/skills/project-log/SKILL.md", "docs/LOG.md", "scripts/log_check.py", "scripts/timeline.py",
                  ".claude/skills/audit/SKILL.md", "scripts/bloat_check.py", "scripts/bloat_check_skills.py", "scripts/bloat_check_rules.py",
                  "scripts/bloat_check_test.py", ".claude/rule-tests.md",
                  ".claude/skills/efficiency/SKILL.md"]
# Moved or renamed in the kit (to .claude/skills/ on 2026-11-16; the guard to check_content on 2026-11-18; run-verify
# and ui-verify merged into verify, and port renamed kit-update, on 2026-11-18): a project synced before then still
# has the old copies.
MOVED_FILES = [".claude/orchestration.md", ".claude/bloat-audit.md", ".claude/project-log.md",
               "scripts/pii_guard.py", "scripts/pii_guard_scan.py", "scripts/pii_guard_hook.py",
               "scripts/pii_guard_test.py", ".github/workflows/pii-guard.yml",
               ".claude/skills/run-verify/SKILL.md", ".claude/skills/ui-verify/SKILL.md",
               ".claude/skills/ui-verify/measure.mjs", ".claude/skills/port/SKILL.md"]
TIERS = ("starter", "full")
NO_OWNER_RENAME = {"scripts/sync_baseline.py", "scripts/first_use_check.py", "docs/FIRST_USE.md"}
OWNER_RE = r"[A-Za-z0-9 ._,()-]+"  # safe inside Python strings, JSON and Markdown


def git(*args, cwd=None):
    """Run git and return its stripped stdout; raise on failure."""
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def get_baseline(src, tmp):
    """The baseline folder: `src` itself when it is a folder, else a clone of it in `tmp` (with its history: an older
    kit copy of a file is known by it, copy_state).

    Args:
        src: a baseline folder or a git URL.
        tmp: a temporary folder to clone into.
    Returns:
        The path of the baseline folder.
    """
    path = Path(src)
    if path.is_dir():
        return path.resolve()
    dest = Path(tmp) / "baseline"
    try:
        git("clone", "--quiet", src, str(dest))
    except subprocess.CalledProcessError as e:
        die(f"cannot clone baseline {src}: {e.stderr.strip()}")
    return dest


def tier_files(tier):
    """Files the kit copies for this tier."""
    skip = set(ADVANCED_FILES) if tier == "starter" else set()
    return [f for f in COPY_FILES if f not in skip], [f for f in COPY_IF_MISSING if f not in skip]


def set_tier(root, tier):
    """Bootstrap step: apply the tier to this repo in place."""
    agents = root / "AGENTS.md"
    agents.write_text(apply_tier(agents.read_text(), tier).replace("{{TIER}}", tier))
    if tier == "starter":
        for rel in ADVANCED_FILES:
            (root / rel).unlink(missing_ok=True)
    print(f"Tier: {tier}" + (f" ({len(ADVANCED_FILES)} advanced files removed)" if tier == "starter" else ""))


def log_stamp(zone):
    """'YYYY-MM-DD HH:MM' now, in the project time zone (UTC when the zone database is missing)."""
    import datetime
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(zone)
    except Exception:
        tz = datetime.timezone.utc
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")


def header_owner(text):
    """The project's "- Owner:" value, or None."""
    owner = re.search(r"^- Owner: (.+?)\s*$", text or "", re.M)
    return owner and owner.group(1)


def apply_owner(text, owner):
    """Replace the baseline role word ("the owner", "The owner") with the project owner."""
    if owner == BASELINE_OWNER:
        return text
    cap = owner[:1].upper() + owner[1:]
    # One pass with word boundaries: "the ownership" stays, and an owner that contains the role word is not re-replaced.
    return re.sub(r"\b([Tt])he owner\b", lambda m: cap if m.group(1) == "T" else owner, text)


def kit_history(base, rel):
    """The earlier versions of a baseline file, from the baseline's git history.

    Args:
        base: the baseline folder.
        rel: the file's path in it.

    Returns:
        A list of the file's bytes at each commit that changed it, newest first; None when the baseline folder is
        not the top of a git repo (no history to read).
    """
    try:
        if Path(git("rev-parse", "--show-toplevel", cwd=base)).resolve() != Path(base).resolve():
            return None
        shas = git("log", "--format=%H", "--", rel, cwd=base).split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    shown = [subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=base, capture_output=True) for sha in shas]
    return [r.stdout for r in shown if r.returncode == 0]   # a commit that deleted the file has no version


def copy_state(base, root, rel, owner):
    """The state of a project's copy of a COPY_IF_MISSING file against the kit.

    Args:
        base: the baseline folder.
        root: the project folder.
        rel: the file's path.
        owner: the project's owner word.

    Returns:
        (state, text): text is the kit's file as a sync writes it (owner word applied), state is one of
        "missing" (the project has no copy), "same" (its copy is the kit's file), "older" (its copy is byte for byte
        an earlier kit version, with or without the owner word applied: never tuned), "tuned" (anything else) and
        "unknown" (it differs, and the baseline has no git history to tell an older copy from a tuned one).
    """
    text = (base / rel).read_text()
    text = text if rel in NO_OWNER_RENAME else apply_owner(text, owner)
    path = root / rel
    if not path.exists():
        return "missing", text
    mine = path.read_bytes()
    if mine == text.encode():
        return "same", text
    old = kit_history(base, rel)
    if old is None:
        return "unknown", text
    forms = set()
    for data in old:
        forms.add(data)
        forms.add(apply_owner(data.decode("utf-8", "replace"), owner).encode())   # as an earlier sync wrote it
    return ("older" if mine in forms else "tuned"), text


def plan_if_missing(base, root, rels, owner, src=None):
    """What a sync does with the files a project may tune (COPY_IF_MISSING).

    Args:
        base: the baseline folder.
        root: the project folder.
        rels: the paths to look at.
        owner: the project's owner word.
        src: the --baseline value, for the compare command (None: the baseline folder).

    Returns:
        (new, notes): new maps each path to write (missing, or an older kit copy) to its text; notes has one line
        for each file that is replaced or kept although it differs.
    """
    new, notes = {}, []
    there = Path(src).is_dir() if src else True
    kit = str(Path(src).resolve() if src and there else base) if there else "<a clone of the kit>"
    for rel in rels:
        if not (base / rel).exists():
            continue
        state, text = copy_state(base, root, rel, owner)
        if state in ("missing", "older"):
            new[rel] = text
        if state == "older":
            notes.append(f"{rel}: the project's copy is an earlier kit version that was never changed here; it is replaced.")
        elif state in ("tuned", "unknown"):
            why = ("this project changed it" if state == "tuned" else
                   "the baseline folder has no git history, so an older kit copy cannot be told from a tuned one")
            notes.append(f"{rel}: kept; it differs from the kit's file ({why}). Compare: diff {kit}/{rel} {rel}")
    return new, notes


def build_agents(base_text, proj_text, args, owner, tier="full"):
    """The new AGENTS.md: baseline text with this project's header values, Commands section and Project rules.

    Args:
        base_text: the text of the baseline AGENTS.md.
        proj_text: the text of the project's AGENTS.md, or None when it has none.
        args: the parsed command line (--name, --repo, --purpose, --timezone).
        owner: the owner word to apply.
        tier: the kit tier to apply (default "full").
    Returns:
        The text of the new AGENTS.md.
    """
    found = header_values(proj_text) if proj_text else (None, None, None)
    name = args.name or found[0]
    repo = args.repo or found[1]
    purpose = args.purpose or found[2]
    timezone = args.timezone or header_timezone(proj_text)
    missing = [k for k, v in (("--name", name), ("--repo", repo), ("--purpose", purpose), ("--timezone", timezone)) if not v]
    if missing:
        die("the project AGENTS.md header lacks a value; give " + ", ".join(missing))

    cut = find_heading(base_text, RULES_HEADING)
    if cut < 0:
        die(f"the baseline AGENTS.md has no '{RULES_HEADING}' heading")
    head = base_text[:cut]
    for key, val in (("PROJECT_NAME", name), ("REPO", repo), ("PURPOSE", purpose), ("TIMEZONE", timezone), ("TIER", tier)):
        head = head.replace("{{" + key + "}}", val)
    head = apply_tier(head, tier)
    if "{{OWNER}}" in head:
        head = head.replace("{{OWNER}}", BASELINE_OWNER)

    head = apply_owner(head, owner)  # baseline text only; the project's own Commands and rules stay as written

    rules_at = find_heading(proj_text, RULES_HEADING) if proj_text else -1
    legacy = proj_text is not None and rules_at < 0
    if proj_text and not legacy:
        own_commands = section(proj_text, COMMANDS_HEADING)
        base_commands = section(head, COMMANDS_HEADING)
        if own_commands and base_commands:
            if not own_commands.endswith("\n\n"):
                own_commands = own_commands.rstrip("\n") + "\n\n"
            head = head.replace(base_commands, own_commands)
        tail = proj_text[rules_at:]
    else:
        tail = RULES_HEADING + "\n\n"
        if legacy and proj_text.strip():
            tail += "<!-- Migrated from the old AGENTS.md by sync_baseline.py. Review it: delete what the baseline now covers. -->\n\n"
            tail += proj_text.strip() + "\n"
    return head + tail


def parse_args():
    """Read the command line; stop when --timezone is not a known IANA name.

    Returns:
        The parsed command line (argparse.Namespace).
    """
    ap = argparse.ArgumentParser(description="Sync this project to the archimedes_lever baseline.")
    ap.add_argument("--apply", action="store_true", help="write the files (default: dry run)")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--name")
    ap.add_argument("--repo")
    ap.add_argument("--purpose")
    ap.add_argument("--owner")
    ap.add_argument("--timezone", help="IANA time zone for project log times, for example Europe/Berlin")
    ap.add_argument("--tier", choices=TIERS, help="kit tier (default: the project's - Tier: line, else full)")
    ap.add_argument("--set-tier", choices=TIERS, help="bootstrap only: apply the tier to this repo in place")
    ap.add_argument("--lock-here", action="store_true", help="bootstrap only: write the kit lock for this repo as it is")
    args = ap.parse_args()
    if args.timezone and not valid_timezone(args.timezone):
        die(f"time zone {args.timezone!r} is not a known IANA name (for example UTC, Europe/Berlin)")
    return args


def baseline_sha(base):
    """The baseline commit, marked when its folder has uncommitted changes or is not a git repo.

    Args:
        base: the baseline folder (a Path).
    Returns:
        The commit hash, with a note when the folder has uncommitted changes, or an "unknown" text.
    """
    try:
        if Path(git("rev-parse", "--show-toplevel", cwd=base)).resolve() != base.resolve():
            raise subprocess.CalledProcessError(1, "git")
        sha = git("rev-parse", "HEAD", cwd=base)
        if git("status", "--porcelain", cwd=base):
            sha += " (with uncommitted baseline changes)"
        return sha
    except subprocess.CalledProcessError:
        return "unknown (baseline folder is not a git repo)"


def check_placeholders(root):
    """Stop when AGENTS.md, README.md or docs/*.md still holds a {{PLACEHOLDER}} (bootstrap has not run)."""
    for f in [root / "AGENTS.md", root / "README.md", *sorted(root.glob("docs/*.md"))]:
        rel = f.relative_to(root)
        if f.is_file() and check_blocks.placeholders([f]):
            die(f"{rel} still has template placeholders; run scripts/bootstrap.sh first")


def new_log(base, root, proj_text, agents_text, owner, tier):
    """The docs/LOG.md text to write: a new log on a starter-to-full upgrade, or the Arcs migration; else None.

    Args:
        base: the baseline folder.
        root: the project folder.
        proj_text: the text of the project's AGENTS.md, or None.
        agents_text: the text of the new AGENTS.md.
        owner: the owner word to apply.
        tier: the kit tier to apply.
    Returns:
        The new text of docs/LOG.md, or None when it does not change.
    """
    log = root / "docs/LOG.md"
    result = None
    rules = section(proj_text, RULES_HEADING) if proj_text is not None else ""
    upgrading = tier == "full" and header_tier(proj_text or "") == "starter"
    if upgrading and not log.is_file() and not re.search(r"(?i)project log", rules or "") and log_template(base).exists():
        zone = header_timezone(agents_text) or "UTC"
        stamp = log_stamp(zone)
        text = re.sub(r"(?m)^> Template: first use fills in.*\n", "", log_template(base).read_text())  # kit-only note, as bootstrap.sh
        name, _, _ = header_values(agents_text)
        for key, val in (("PROJECT_NAME", name or "Project"), ("TIMEZONE", zone),
                         ("DATE", stamp[:10]), ("TIME", stamp[11:])):
            text = text.replace("{{" + key + "}}", val)
        result = apply_owner(text, owner)
    if log.is_file():
        migrated = migrate_arcs(log.read_text())
        if migrated != log.read_text():
            result = migrated
    return result


def planned_files(base, root, args):
    """Map each project path to its synced text, and return it with the tier.

    Args:
        base: the baseline folder.
        root: the project folder.
        args: the parsed command line.
    Returns:
        (new, tier): a dict of project path to the synced text, and the tier.
    """
    proj_agents = root / "AGENTS.md"
    proj_text = proj_agents.read_text() if proj_agents.exists() else None
    owner = args.owner or header_owner(proj_text or "") or BASELINE_OWNER
    if not re.fullmatch(OWNER_RE, owner):
        die(f"owner {owner!r}: use letters, digits, space . _ , ( ) - only")
    tier = args.tier or header_tier(proj_text or "")
    copy_files, copy_if_missing = tier_files(tier)
    new = {}
    new["AGENTS.md"] = build_agents((base / "AGENTS.md").read_text(), proj_text, args, owner, tier)
    claude = root / "CLAUDE.md"
    old_claude = claude.read_text() if claude.exists() else ""
    if not any(l.strip() == "@AGENTS.md" for l in old_claude.splitlines()):
        new["CLAUDE.md"] = "@AGENTS.md\n" + ("\n" + old_claude if old_claude.strip() else "")
    for rel in copy_files:
        if (base / rel).exists():
            text = (base / rel).read_text()
            new[rel] = text if rel in NO_OWNER_RENAME else apply_owner(text, owner)
    tuned, notes = plan_if_missing(base, root, copy_if_missing, owner, args.baseline)
    new.update(tuned)
    COPY_NOTES[:] = notes
    if (base / ".claude/settings.json").exists():
        new[".claude/settings.json"] = merge_settings(base / ".claude/settings.json", root / ".claude/settings.json")
    if (base / ".gitignore").exists():
        new[".gitignore"] = merge_lines(base / ".gitignore", root / ".gitignore")
    log_text = new_log(base, root, proj_text, new["AGENTS.md"], owner, tier)
    if log_text is not None:
        new["docs/LOG.md"] = log_text
    if (base / "LICENSE").exists():
        new["docs/archimedes_lever-LICENSE.txt"] = (base / "LICENSE").read_text()
    return new, tier


def show_diff(root, new):
    """Print a unified diff for each file that would change; return their paths.

    Args:
        root: the project folder.
        new: a dict of project path to the synced text.
    Returns:
        The list of paths whose text would change.
    """
    changed = []
    for rel, text in new.items():
        path = root / rel
        old = path.read_text() if path.exists() else ""
        if old == text:
            continue
        changed.append(rel)
        sys.stdout.writelines(difflib.unified_diff(
            old.splitlines(True), text.splitlines(True), f"a/{rel}", f"b/{rel}"))
        if not text.endswith("\n"):
            print()
    return changed


def report_leftovers(root, tier):
    """List the advanced files a starter project keeps and old copies of moved files, for deletion by hand.

    Args:
        root: the project folder.
        tier: the kit tier.
    """
    if tier == "starter":
        extra = [f for f in ADVANCED_FILES if (root / f).exists()]
        if extra:
            print(f"Tier starter: these advanced files are not synced; delete them by hand if you want: {', '.join(extra)}")
    old = [f for f in MOVED_FILES if (root / f).exists()]
    if old:
        print(f"These files moved or were renamed in the kit; delete the old copies by hand: {', '.join(old)}")
    old = [f for f in (".pii-guard", ".code-standard.json", ".bloat-audit.json") if (root / f).exists()]
    if old:
        print(f"Old settings files ({', '.join(old)}): run 'python3 scripts/check_settings.py --migrate' (it moves "
              "them into .check and .check.state.json; the lines of .check stay as they are).")


def write_files(base, root, new, changed):
    """Write the changed files (with the baseline's file mode for scripts); stop when the project is not committed.

    Args:
        base: the baseline folder.
        root: the project folder.
        new: a dict of project path to the synced text.
        changed: the paths to write.
    """
    if git("status", "--porcelain", cwd=root):
        die("the project has uncommitted changes; commit them first")
    for rel in changed:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new[rel])
        if rel.endswith((".sh", ".py")) or rel.startswith("scripts/git-hooks/"):
            shutil.copymode(base / rel, path) if (base / rel).exists() else None
    version = write_lock(base, root, new)
    print(f"Written, with the kit lock {check_lock.LOCK} (kit version {version}). Review with 'git diff', then commit and push.")


def write_lock(base, root, files):
    """Write the kit lock of the project for the kit files among `files`; return the kit version."""
    version = (base / "KIT_VERSION").read_text().strip() if (base / "KIT_VERSION").exists() else "unknown"
    check_lock.write(root, check_lock.build(root, [r for r in files if r in COPY_FILES], version,
                                            baseline_sha(base).split()[0]))
    return version


def main():
    """Sync the project: show the diff (dry run) or write it (--apply); or apply --set-tier in place."""
    args = parse_args()
    try:
        root = Path(git("rev-parse", "--show-toplevel"))
    except subprocess.CalledProcessError:
        die("run this inside the project git repo")
    if args.set_tier:
        set_tier(root, args.set_tier)
        return
    if args.lock_here:  # bootstrap: this clone of the kit becomes a project; lock its kit files as they are now
        write_lock(root, root, COPY_FILES)
        return

    with tempfile.TemporaryDirectory() as tmp:
        base = get_baseline(args.baseline, tmp)
        if base.resolve() == root.resolve():
            die("this is the baseline repo itself; run the script in a project repo")
        print(f"Kit baseline: {baseline_sha(base)}. A sync writes the kit lock {check_lock.LOCK} (the kit version and a "
              "hash of each kit file); the project does not keep the sync tools.")
        check_placeholders(root)
        new, tier = planned_files(base, root, args)
        changed = show_diff(root, new)
        report_leftovers(root, tier)
        for note in COPY_NOTES:
            print(note)
        for matcher in changed_matchers(REPLACED_HOOKS, base / ".claude/settings.json"):
            print("An older kit hook entry is replaced by the kit's. If you had added tool names to its matcher, add a "
                  f"hook entry of your own for them. The old matcher: {matcher}")
        if not changed:
            print("No changes: the project already matches the baseline.")
            if args.apply:
                write_lock(base, root, new)
            return
        print(f"\n{len(changed)} file(s) to change: {', '.join(changed)}")
        if not args.apply:
            print("Dry run: nothing written. Run again with --apply to write.")
            return
        write_files(base, root, new, changed)


if __name__ == "__main__":
    main()
