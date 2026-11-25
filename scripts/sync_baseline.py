#!/usr/bin/env python3
"""Sync a project repo to the current kit baseline (the repo that kit.config.json "kit_url" names).

Prevents: a project that drifts from the kit: an old copy of a kit file, a missing kit lock, and a docs/DECISIONS.md with no
approval-quote marker (so the T6 check would read every old row).

Run it from inside the project repo:
    python3 scripts/sync_baseline.py            # dry run: show the diff, write nothing
    python3 scripts/sync_baseline.py --apply    # write the files (commit them yourself)

Options:
    --baseline PATH_OR_URL   Baseline repo (default: "kit_url" in kit.config.json, read by scripts/kit_config.py)
    --name, --repo, --purpose   Header values, needed only when the project AGENTS.md has none.
    --timezone ZONE          IANA time zone for project log times, needed only when the project AGENTS.md has no
                             "- Time zone:" line (projects synced before 2026-11-11 have none).
    --owner NAME             Name agents use for the decider (default: the project's "- Owner:" line, else "the Maintainer").
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

Before it writes (also in a dry run), it compares the kit files it would write with the project's .check.lock. When one differs from its lock hash, is an
override, or is not in the lock and differs from the kit's file, it writes nothing, names the files and exits 2, with the way forward
for each (a PROJECT.md beside a kit skill, AGENTS.md "Project rules", scripts/check.local.sh or .check, or the kit). With no .check.lock, an unreadable one, or a
missing kit file, it does not stop.

What it changes:
    AGENTS.md              Baseline text above "## Project rules", with this project's header values.
                           Keeps this project's "## Commands" section and everything from "## Project rules" on.
                           An AGENTS.md without the baseline layout goes under "## Project rules" as it is.
    CLAUDE.md              Adds "@AGENTS.md" at the top if it is missing. Keeps the rest.
    scripts/session_checkin.sh, scripts/stop_check.py, scripts/worker_guard.py,
    .claude/skills/ (every kit skill), scripts/check_instructions*.py, .claude/agents/worker.md, scout.md, reviewer.md
                           Replaced with the baseline copies.
    docs/FIRST_USE.md      Added when missing. A project may tune it (it holds the denylist places that the
                           session-start check names), so a copy the project changed is kept, with one line that
                           says it differs and how to compare. A copy that is byte for byte an earlier kit version
                           of the file was never tuned: it is replaced. This needs the baseline's git history; with
                           a baseline folder that is no git repo, a copy that differs is kept.
    scripts/log_check.py, scripts/timeline.py, scripts/fleet_harvest*.py, scripts/check_content*.py, scripts/first_use_check.py,
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
                           script), "the Maintainer" becomes the project owner ("The Maintainer" becomes the owner with a capital
                           first letter). Project text is never renamed. A private repo may keep a real name
                           (--owner NAME); a public repo uses a role. Owner: letters, digits, space . _ , ( ) -
    docs/DECISIONS.md      In a full project: the line `<!-- approval-quote-exempt-from: TEXT -->` above the Decisions table when it
                           is missing (TEXT: the Decision cell of the newest row), so the T6 check reads only new rows; with no '## Decisions'
                           heading, above the first table whose columns start Date | Decision | By or Date | Scope | Decision. Nothing else.
What it never changes: README.md, docs/ (except docs/FIRST_USE.md and docs/DECISIONS.md as said above, docs/code-standard.md and the kit
license), .check and all other files. A project's own code lives in its own files (scripts/check.local.sh,
scripts/check_content_local.py, scripts/check_instructions_local.py, scripts/code_standard_gate.py), which a sync
never touches.
Parts: scripts/sync_baseline_repo.py (the reads of the baseline repo, the diff), scripts/sync_baseline_stop.py (the stop before a write)
and scripts/sync_baseline_run.py (the writes). Standard library only. Needs git.
Network: the baseline repo, only when --baseline is a URL (one git clone); none for a local folder.
Writes: with --apply, the kit files of the project and its kit lock .check.lock (the list: "What it changes" above); without it, nothing.
Credentials: none itself; a clone uses the credentials git already has.
"""
import argparse
import itertools
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_blocks  # noqa: E402,F401 - the deny rules and the placeholder pattern
import check_lock  # noqa: E402 - the kit lock that a sync writes into the project
from sync_merge import REPLACED_HOOKS, changed_matchers, die, merge_lines, merge_settings, migrate_arcs  # noqa: E402,F401 - scripts/sync_merge.py
from sync_merge import (apply_tier, find_heading, header_short_name, header_timezone, header_tier, header_values,  # noqa: E402,F401
                        headings, section, valid_timezone)  # the AGENTS.md header helpers (drift.py reads them here)
# scripts/sync_baseline_repo.py: the reads of the baseline repo and the diff (kept apart, docs/code-standard.md C4).
from sync_baseline_repo import (baseline_sha, dod_files, get_baseline, git, header_owner, kit_history, log_stamp,  # noqa: E402,F401
                                log_template, show_diff)
# scripts/sync_baseline_run.py: the write side (the placeholder stop, the leftovers report, the files and the kit lock).
from sync_baseline_run import check_placeholders, report_leftovers, write_files, write_lock  # noqa: E402,F401
# scripts/sync_baseline_stop.py: the check side (the stop before a write when a kit file holds a project change).
from sync_baseline_stop import stop_on_changed_kit_files, unlocked_kit_files  # noqa: E402,F401

import kit_config  # noqa: E402 - scripts/kit_config.py: the one home of the kit addresses (kit.config.json)
DEFAULT_BASELINE = kit_config.value("kit_url")  # None when kit.config.json is missing: parse_args stops
RULES_HEADING = "## Project rules"
COMMANDS_HEADING = "## Commands"
COPY_FILES = ["scripts/session_checkin.sh", "scripts/stop_check.py", "scripts/check_blocks.py", "scripts/check_lock.py", "scripts/check_content_test_blocks.py",
              "scripts/worker_guard.py", "scripts/worker_guard_scan.py", "scripts/worker_guard_scan_samples.json", "scripts/log_check.py", "scripts/log_check_plan.py", "scripts/timeline.py", "scripts/fleet_harvest.py", "scripts/fleet_harvest_test.py", "scripts/check_content.py", "scripts/first_use_check.py",
              "scripts/fleet_harvest_parse.py",
              "scripts/check_content_scan.py", "scripts/check_content_hook.py", "scripts/check_content_test.py",
              "scripts/check_content_finders.py", "scripts/check_content_test_local.py", "scripts/check_settings_test.py",
              "scripts/check_content_scan_settings.py", "scripts/check_content_scan_words.py", "scripts/check_content_test_cli.py",
              "scripts/check.sh", "scripts/check_settings.py", "scripts/check_settings_read.py", "scripts/bloat_check.py", "scripts/bloat_check_skills.py", "scripts/bloat_check_test.py",
              "scripts/bloat_check_rules.py", "scripts/bloat_check_files.py", "scripts/skill_use.py", "scripts/bloat_check_timing.py", "scripts/bloat_check_test_rules.py",
              "ruff.toml", ".pylintrc", "scripts/code_standard.py", "scripts/code_standard_test.py", "scripts/code_standard_docs.py", "scripts/code_standard_parse.py",
              "scripts/code_standard_rules.py", "scripts/code_standard_ratchet.py", "scripts/code_standard_test_gate.py", "scripts/code_standard_test_docs.py",
              "scripts/code_standard_strict.py", "scripts/code_standard_strict_test.py",
              "docs/code-standard.md", "scripts/git-hooks/pre-push",
              "scripts/fulcrum_palette.py", "docs/brand/fulcrum.json", "docs/brand/fulcrum.css", "scripts/build_site.py", "scripts/build_site_html.py",
              ".claude/skills/delegate/SKILL.md", ".claude/skills/audit/SKILL.md", ".claude/skills/project-log/SKILL.md", ".claude/rule-tests.md", ".github/workflows/check.yml",
              ".claude/skills/deliver/SKILL.md", ".claude/skills/personal-data/SKILL.md", ".claude/skills/rule-change/SKILL.md",
              ".claude/skills/data-change/SKILL.md", ".claude/skills/verify/SKILL.md", ".claude/skills/verify/measure.mjs",
              ".claude/skills/handoff/SKILL.md",
              ".claude/skills/kit-update/SKILL.md", ".claude/skills/instructions/SKILL.md",
              "scripts/check_instructions.py", "scripts/check_instructions_test.py", "scripts/check_instructions_steps.py",
              ".claude/agents/worker.md", ".claude/agents/scout.md", ".claude/agents/reviewer.md"]
# A file a project may tune: added when missing, replaced when the project's copy is an earlier kit version, else kept
# (copy_state). (The kit's agent files are kit files since 2026-11-18: an old copy can restate a rule; a project adds
# an agent of its own under its own name.)
COPY_IF_MISSING = ["docs/FIRST_USE.md"]
# The DoD group (fleet v2 DEC 4): added only when the project's .check has `dod-security: on`, and only when the project
# has no copy (never replaced, never in the kit lock: a project tunes its own scan paths). ICF-Source has it off.
DOD_FILES = ["SECURITY.md", ".github/dependabot.yml", ".github/workflows/security.yml"]
COPY_NOTES = []  # one line for each COPY_IF_MISSING file that a sync replaces or keeps (main() prints them)
BASELINE_OWNER = "the Maintainer"  # role word in baseline text; no real name lives in the baseline
# Never rename the owner inside this script: it holds BASELINE_OWNER as a literal.
# first_use_check.py and docs/FIRST_USE.md use "the owner" as an answer option and a role: keep them as written
# (bootstrap.sh skips them too).


# Advanced parts: a starter project has none of these (one list for bootstrap, sync and drift).
ADVANCED_FILES = [".claude/skills/delegate/SKILL.md", ".claude/agents/scout.md", ".claude/agents/worker.md",
                  ".claude/skills/project-log/SKILL.md", "docs/LOG.md", "scripts/log_check.py", "scripts/log_check_plan.py", "scripts/timeline.py",
                  ".claude/skills/audit/SKILL.md", "scripts/bloat_check.py", "scripts/bloat_check_skills.py", "scripts/bloat_check_rules.py", "scripts/bloat_check_files.py",
                  "scripts/bloat_check_test.py", ".claude/rule-tests.md", "scripts/skill_use.py",
                  "scripts/bloat_check_timing.py", "scripts/bloat_check_test_rules.py"]
# Moved or renamed in the kit (to .claude/skills/ on 2026-11-16; the guard to check_content on 2026-11-18; run-verify
# and ui-verify merged into verify, and port renamed kit-update, on 2026-11-18; efficiency merged into audit in
# kit 6.0.0): a project synced before then still
# has the old copies.
MOVED_FILES = [".claude/orchestration.md", ".claude/bloat-audit.md", ".claude/project-log.md",
               "scripts/pii_guard.py", "scripts/pii_guard_scan.py", "scripts/pii_guard_hook.py",
               "scripts/pii_guard_test.py", ".github/workflows/pii-guard.yml",
               ".claude/skills/run-verify/SKILL.md", ".claude/skills/ui-verify/SKILL.md",
               ".claude/skills/ui-verify/measure.mjs", ".claude/skills/port/SKILL.md",
               ".claude/skills/efficiency/SKILL.md", "scripts/fulcrum_tokens.py"]  # renamed to fulcrum_palette.py in 11.0.0 (a secret scan read its name as a key)
TIERS = ("starter", "full")
NO_OWNER_RENAME = {"scripts/sync_baseline.py", "scripts/first_use_check.py", "docs/FIRST_USE.md"}
OWNER_RE = r"[A-Za-z0-9 ._,()-]+"  # safe inside Python strings, JSON and Markdown


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


def apply_owner(text, owner):
    """Replace the baseline role word (BASELINE_OWNER, and its form with a capital T) with the project owner."""
    if owner == BASELINE_OWNER:
        return text
    cap = owner[:1].upper() + owner[1:]
    # One pass with word boundaries: "the ownership" stays, and an owner that contains the role word is not re-replaced.
    word = re.escape(BASELINE_OWNER.split(" ", 1)[1])
    return re.sub(r"\b([Tt])he " + word + r"\b", lambda m: cap if m.group(1) == "T" else owner, text)


def decisions_marker(text):
    """Add the line `<!-- approval-quote-exempt-from: <newest row's Decision cell> -->` above the Decisions table when it is missing.
    Rows from the one it names down are older than the T6 check and are not checked (scripts/log_check_plan.py).

    Args:
        text: the text of docs/DECISIONS.md.

    Returns:
        The text with the marker, or the same text when it has the marker, has no Decisions table, or the table has no row.
    """
    if re.search(r"<!--\s*approval-quote-exempt-from:", text):
        return text
    lines = text.split("\n")
    head = next((i + 1 for i, l in enumerate(lines) if re.match(r"##\s+Decisions\s*$", l)), None)
    table = next((i for i in range(head or len(lines), len(lines)) if lines[i].lstrip().startswith("|")), None)
    if head is None:   # no '## Decisions': the first Date | Decision | By or Date | Scope | Decision table (log_check_plan.py)
        table = next((i for i, l in enumerate(lines) if re.match(r"^\s*\|\s*date\s*\|\s*(?:decision\s*\|\s*by|scope\s*\|\s*decision)\s*\|",
                                                                 l, re.I)), None)
    if table is None:
        return text
    dec = 2 if re.match(r"^\s*\|\s*date\s*\|\s*scope\s*\|", lines[table], re.I) else 1   # the Decision cell: the marker names it
    rows = list(itertools.takewhile(lambda l: l.lstrip().startswith("|"), lines[table + 2:]))   # table + 1: the separator row
    row = re.split(r"(?<!\\)\|", rows[0].strip().strip("|")) if rows else []
    first = row[dec].strip().replace("\\|", "|") if len(row) > dec else ""
    if not first or "-->" in first:
        return text
    return "\n".join(lines[:table] + [f"<!-- approval-quote-exempt-from: {first} -->", ""] + lines[table:])


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
        args: the parsed command line (--name, --repo, --purpose, --timezone, --short-name).
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
    short = getattr(args, "short_name", None) or header_short_name(proj_text, name)  # session titles start with it
    for key, val in (("PROJECT_NAME", name), ("REPO", repo), ("PURPOSE", purpose), ("TIMEZONE", timezone), ("TIER", tier),
                     ("SHORT_NAME", short)):
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
    ap.add_argument("--short-name", help="the first part of each session title, for example RADE (default: the project's "
                    "- Short name: line, else the first word of the project name)")
    ap.add_argument("--tier", choices=TIERS, help="kit tier (default: the project's - Tier: line, else full)")
    ap.add_argument("--set-tier", choices=TIERS, help="bootstrap only: apply the tier to this repo in place")
    ap.add_argument("--lock-here", action="store_true", help="bootstrap only: write the kit lock for this repo as it is")
    args = ap.parse_args()
    if not args.baseline:
        ap.error("no --baseline given and no \"kit_url\" in kit.config.json (scripts/kit_config.py)")
    if args.timezone and not valid_timezone(args.timezone):
        die(f"time zone {args.timezone!r} is not a known IANA name (for example UTC, Europe/Berlin)")
    return args


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


def project_owner(root, args):
    """The owner word of this sync: --owner, else the project's "- Owner:" line, else the baseline's word.

    Args:
        root: the project folder.
        args: the parsed command line.
    Returns:
        The owner word; the sync stops when it holds a character that the baseline text cannot hold.
    """
    proj_agents = root / "AGENTS.md"
    owner = args.owner or header_owner(proj_agents.read_text() if proj_agents.exists() else "") or BASELINE_OWNER
    if not re.fullmatch(OWNER_RE, owner):
        die(f"owner {owner!r}: use letters, digits, space . _ , ( ) - only")
    return owner


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
    owner = project_owner(root, args)
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
    new.update(dod_files(base, root, DOD_FILES))
    tuned, notes = plan_if_missing(base, root, copy_if_missing, owner, args.baseline)
    new.update(tuned)
    COPY_NOTES[:] = notes
    decisions = root / "docs/DECISIONS.md"
    if "scripts/log_check_plan.py" in copy_files and decisions.is_file():
        marked = decisions_marker(decisions.read_text())
        if marked != decisions.read_text():
            new["docs/DECISIONS.md"] = marked
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


def main():
    """Sync the project: show the diff (dry run) or write it (--apply); or apply --set-tier or --lock-here in place."""
    args = parse_args()
    try:
        root = Path(git("rev-parse", "--show-toplevel"))
    except subprocess.CalledProcessError:
        die("run this inside the project git repo")
    if args.set_tier:
        set_tier(root, args.set_tier)
        return
    if args.lock_here:  # bootstrap: this clone of the kit becomes a project; lock its kit files as they are now
        write_lock(root, root, COPY_FILES, COPY_FILES)
        return

    with tempfile.TemporaryDirectory() as tmp:
        base = get_baseline(args.baseline, tmp)
        if base.resolve() == root.resolve():
            die("this is the baseline repo itself; run the script in a project repo")
        print(f"Kit baseline: {baseline_sha(base)}. A sync writes the kit lock {check_lock.LOCK} (the kit version and a "
              "hash of each kit file); the project does not keep the sync tools.")
        check_placeholders(root)
        new, tier = planned_files(base, root, args)
        stop_on_changed_kit_files(base, root, new, project_owner(root, args), COPY_FILES, copy_state)
        changed = show_diff(root, new)
        report_leftovers(root, tier, ADVANCED_FILES, MOVED_FILES)
        for note in COPY_NOTES:
            print(note)
        for matcher in changed_matchers(REPLACED_HOOKS, base / ".claude/settings.json"):
            print("An older kit hook entry is replaced by the kit's. If you had added tool names to its matcher, add a "
                  f"hook entry of your own for them. The old matcher: {matcher}")
        if not changed:
            print("No changes: the project already matches the baseline.")
            if args.apply:
                write_lock(base, root, new, COPY_FILES)
            return
        print(f"\n{len(changed)} file(s) to change: {', '.join(changed)}")
        if not args.apply:
            print("Dry run: nothing written. Run again with --apply to write.")
            return
        write_files(base, root, new, changed, COPY_FILES)


if __name__ == "__main__":
    main()
