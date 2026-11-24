#!/usr/bin/env python3
"""The merges of scripts/sync_baseline.py: a sync does not replace these project files, it adds the kit's part to them.
Kept apart so sync_baseline.py stays under the line cap of docs/code-standard.md C4. Kit only.

What it gives:
  merge_settings   .claude/settings.json: the kit's deny rules and hook entries first, the project's own kept
  migrate_arcs     docs/LOG.md: an old 4-column Arcs table gets the story columns
  merge_lines      .gitignore: the kit's lines added at the top
  die              print an error and exit 1 (sync_baseline.py uses it too)
  headings, find_heading, section, header_values, valid_timezone, header_timezone, header_tier, apply_tier
                   read and set the parts of an AGENTS.md text (sync_baseline.py imports them; drift.py reads them there)
Inputs:  the baseline's file and the project's file (paths), or a text. Outputs: the merged text; nothing is written.
Run:     imported by scripts/sync_baseline.py; proved by `python3 scripts/drift.py --test`.
Prevents: a sync replaces a project's own settings, log table or ignore lines instead of adding the kit's part, so project content is lost
Network: none.
Writes: none.
Credentials: none.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_blocks  # noqa: E402 - the deny rules


def die(msg):
    """Print the error to stderr and exit 1."""
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def merge_settings(base_path, proj_path):
    """The project settings.json plus the baseline deny rules, missing hook events and sandbox block.

    Args:
        base_path: the baseline's .claude/settings.json (a Path).
        proj_path: the project's .claude/settings.json (a Path; it may not exist).

    Returns:
        The merged settings as JSON text.
    """
    base = json.loads(base_path.read_text())
    try:
        proj = json.loads(proj_path.read_text()) if proj_path.exists() else {}
    except json.JSONDecodeError as e:
        die(f".claude/settings.json is not valid JSON ({e}); fix it first")
    if not isinstance(proj, dict):
        die(".claude/settings.json must be a JSON object; fix it first")
    if not isinstance(proj.get("permissions"), dict):
        if proj.get("permissions") not in (None,):
            die('.claude/settings.json "permissions" must be an object; fix it first')
        proj["permissions"] = {}
    deny = proj["permissions"].get("deny")
    if deny is None:
        deny = proj["permissions"]["deny"] = []
    if not isinstance(deny, list):
        die('.claude/settings.json "permissions.deny" must be a list; fix it first')
    # The kit's deny rules (scripts/check_blocks.py DENY) come first, in the kit's order; the project's own follow.
    kit = check_blocks.DENY + [r for r in base.get("permissions", {}).get("deny", []) if r not in check_blocks.DENY]
    deny[:] = kit + [r for r in deny if r not in kit]
    # Sandbox: add the baseline block only when the project has none (a project's own block is kept whole).
    if "sandbox" in base and "sandbox" not in proj:
        proj["sandbox"] = base["sandbox"]
    # Hooks: add a baseline hook event only when the project has no hook for that event.
    base_hooks = base.get("hooks") or {}
    if base_hooks:
        hooks = proj.get("hooks")
        if hooks is None:
            hooks = proj["hooks"] = {}
        if not isinstance(hooks, dict):
            die('.claude/settings.json "hooks" must be an object; fix it first')
        # The kit's hook entries come first and replace older copies of themselves; the project's own entries follow.
        for event, entries in base_hooks.items():
            hooks[event] = entries + [e for e in map(own_part, hooks.get(event) or []) if e and e not in entries]
    return json.dumps(proj, indent=2, ensure_ascii=False) + "\n"


KIT_HOOK_COMMANDS = ("scripts/pii_guard.py", "scripts/check_content.py", "scripts/check.sh --hook",
                     "scripts/stop_check.py", "scripts/first_use_check.py", "scripts/check.sh --kit-install")
REPLACED_HOOKS = []  # matchers of older kit hook entries that a sync replaced (main() prints them)


def own_part(entry):
    """The project's own part of a settings.json hook entry: the entry without the commands that run a kit script
    (the kit's entry runs those). None when nothing is left: an older copy of a kit hook. Its matcher is noted, so
    the project can see tool names it had added to it.

    Args:
        entry: one hook entry of the project's settings.json.

    Returns:
        The entry, the entry with only the project's own commands, or None.
    """
    if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
        return entry
    own = [h for h in entry["hooks"] if not any(k in json.dumps(h) for k in KIT_HOOK_COMMANDS)]
    if len(own) == len(entry["hooks"]):
        return entry
    if not own:
        if entry.get("matcher"):
            REPLACED_HOOKS.append(entry["matcher"])
        return None
    return {**entry, "hooks": own}


def changed_matchers(replaced, kit_settings):
    """The matchers of replaced hook entries that the kit's own settings do not have: only those can hold tool
    names a project added, so only those are worth a note.

    Args:
        replaced: matchers collected in REPLACED_HOOKS.
        kit_settings: the path of the kit's .claude/settings.json.

    Returns:
        The matchers, in order, that no kit hook entry uses.
    """
    try:
        data = json.loads(Path(kit_settings).read_text())
    except (OSError, ValueError):
        return list(replaced)
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return list(replaced)
    kit = {e.get("matcher") for entries in hooks.values() if isinstance(entries, list) for e in entries if isinstance(e, dict)}
    return [m for m in replaced if m not in kit]


NEW_ARCS = "| Arc | Span | Summary | Problem | Turning point | Outcome | Lesson |"


def migrate_arcs(text):
    """Add the story columns to an old 4-column Arcs table; return the text unchanged when there is none.

    Args:
        text: the text of a docs/LOG.md.

    Returns:
        The text with the story columns added, or unchanged.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        head = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if head != [c.lower() for c in ("Arc", "Span", "Summary", "Outcome")]:
            continue
        lines[i] = NEW_ARCS
        j = i + 1
        if j < len(lines) and re.fullmatch(r"\s*\|(\s*:?-+:?\s*\|){4}\s*", lines[j]):
            lines[j] = "|---|---|---|---|---|---|---|"
            j += 1
        while j < len(lines) and lines[j].strip().startswith("|"):
            cells = re.split(r"(?<!\\)\|", lines[j].strip())[1:-1]
            if len(cells) == 4:
                a, span, summary, outcome = (c.strip() for c in cells)
                lines[j] = f"| {a} | {span} | {summary} | - | - | {outcome} | - |"
            j += 1
        break
    return "\n".join(lines)


def merge_lines(base_path, proj_path):
    """The project .gitignore with the baseline lines it lacks added at the top."""
    lines = proj_path.read_text().splitlines() if proj_path.exists() else []
    add = [l for l in base_path.read_text().splitlines() if l.strip() and l not in lines]
    # Baseline lines go first, so a later project exception (for example "!.env.example") still wins.
    return "\n".join(add + lines) + "\n"


# ---------------------------------------------------------------- AGENTS.md header helpers ----------------------------

def headings(text):
    """Yield (offset, line) for each '## ' heading line outside ``` code fences."""
    pos, fenced = 0, False
    for line in text.splitlines(True):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            yield pos, line.rstrip()
        pos += len(line)


def find_heading(text, heading):
    """Offset of the heading line `heading` outside code fences, or -1."""
    for pos, line in headings(text):
        if line == heading:
            return pos
    return -1


def section(text, heading):
    """Return the block from `heading` to the next '## ' heading (outside code fences), or None."""
    start = find_heading(text, heading)
    if start < 0:
        return None
    for pos, _ in headings(text):
        if pos > start:
            return text[start:pos]
    return text[start:]


def header_values(text):
    """The (name, repo, purpose) values from an AGENTS.md header; None for each one missing."""
    name = re.search(r"^# (.+?): agent instructions\s*$", text, re.M)
    repo = re.search(r"^- Repo: (.+?)\s*$", text, re.M)
    purpose = re.search(r"^- Purpose: (.+?)\s*$", text, re.M)
    return (name and name.group(1), repo and repo.group(1), purpose and purpose.group(1))


def valid_timezone(name):
    """An IANA name the system knows (UTC always passes, also where the time zone database is missing).

    Args:
        name: the time zone name to test.
    Returns:
        True when the name is usable, else False.
    """
    if name == "UTC":
        return True
    if not re.fullmatch(r"[A-Za-z0-9_+/-]+", name):
        return False
    try:
        import zoneinfo
        zoneinfo.ZoneInfo(name)
        return True
    except Exception:
        return False


def header_timezone(text):
    """The project's "- Time zone:" value, or None."""
    tz = re.search(r"^- Time zone: (.+?)\s*$", text or "", re.M)
    return tz and tz.group(1)


def header_short_name(text, name=None):
    """The project's "- Short name:" value (the first part of each session title).

    Args:
        text: the text of an AGENTS.md (may be None).
        name: the project name, used when the line is missing or still a placeholder.
    Returns:
        The value; else the first word of `name` (for example "ICF" from "ICF Companion"); else None.
    """
    found = re.search(r"^- Short name:[ \t]*(\S.*?)\s*$", text or "", re.M)  # blank value = missing, as in the check-in
    if found and not found.group(1).startswith("{{"):
        return found.group(1)
    return name.split()[0] if name and name.split() else None


def header_tier(text):
    """The project's "- Tier:" value; "full" for projects made before tiers existed."""
    tier = re.search(r"^- Tier: (starter|full)\s*$", text or "", re.M | re.I)
    return tier.group(1).lower() if tier else "full"


def apply_tier(text, tier):
    """Keep the marked blocks for `tier`, drop the other tier's blocks, and drop every marker line."""
    other = "starter" if tier == "full" else "full"
    text = re.sub(rf"(?ms)^<!-- {other} -->\n.*?^<!-- /{other} -->\n", "", text)
    return re.sub(rf"(?m)^<!-- /?{tier} -->\n", "", text)
