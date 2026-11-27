"""The scanner of check_content.py: the patterns and finders, the readers of the word lists (names, terms) and of
the settings file (`.check`; the old name `.pii-guard` is still read), and the scans of a text, of files and of commits.

Inputs: text, repo-relative paths or git rev-list arguments; the word lists (environment or file) and the settings file.
Outputs: findings as (where, line number, kind, masked value) tuples; nothing is printed here.
Run: not run alone; check_content.py and check_content_test.py import it (the checks, tiers and limits are described in
the check_content.py header).

A project's own finders (the extension point): when the file scripts/check_content_local.py stands next to this one,
the scanner loads it. The kit has no such file, and the kit's own patterns stay the default. The module defines one
or both of these names (a kind is one of email, secret, phone, id, milhost, dodid, marking):
    REPLACE = {kind: [finder, ...]}   these finders take the place of the kit's finders for that kind (at least one)
    ADD     = {kind: [finder, ...]}   these finders run after the finders of that kind
    finder(line) -> an iterable of (start, end, value): the span of each match in the line of text, and the text
                    that is the finding (it is masked in the output and compared with the allowed strings)
The kinds milhost, dodid and marking run only in the DoD tier, whoever finds them. The module must not import this
scanner when it is loaded (its own self-test may); `python3 scripts/check_content_local.py --test` is that self-test,
and scripts/check.sh runs it when the file has one. A module that cannot be imported, or that has neither name in this
shape, makes every scan fail (LOCAL_ERROR; scan_text raises LocalError) and the hook block: the scanner never falls
back to the kit's patterns, and never to no check. The result line of a scan and --status say when a module is active.
Prevents: a secret or personal datum in a text, a file or a commit goes unseen, or a broken project finder falls back to no check
Network: none (it runs local git read commands).
Writes: none.
Credentials: none; it reads the name denylist and the terms list from an environment variable or a file.
"""
import bisect
import fnmatch
import hashlib
import importlib.util
import itertools
import os
import pathlib
import re
import subprocess
import sys
import unicodedata

# ---------------------------------------------------------------- settings (.check / .pii-guard) --------------------

MAX_BYTES = 2_000_000

WARN_OPTION = "denylist: warn"  # settings option line; first_use_check.py reads it too

# A tier line, also in a wrong form. After any leading punctuation (a bullet, a quote, a bracket):
#   - the word profile, unless a character of a name follows it (profile.example.org and profile-x stay allowed values);
#   - or one word, at most one punctuation mark, and the value dod (a misspelt key such as "profil: dod").
# Every form other than `profile: dod` is unknown and fails the scan.
_TIER = r"[\W_]*(?:profile(?![A-Za-z0-9._/-])|(?!skip\b|block\b|denylist\b)[A-Za-z_-]{1,40}\s*[^\w\s.]?\s*dod[\W_]*$)"
PROFILE_LINE = re.compile(r"(?i)^" + _TIER)
# A setting of the code standard or the audit (`code-max-file-lines: 600`, `audit-ignore: ref/**`): `code-` or `audit-`,
# a key and a colon. scripts/check_settings.py reads these lines; here they are option lines and never tier lines.
SETTING_LINE = re.compile(r"(?i)^(?:code|audit)-[A-Za-z0-9_-]+\s*:")
OPTION_LINE = re.compile(r"(?i)^(?:" + _TIER + r"|denylist\s*:)")  # option lines, never allowed values
OPTION_MAX = 200  # a longer line is never an option line: the patterns above only ever see short lines (no slow match)

MAX_BYTES_LINE = re.compile(r"(?i)^content-max-bytes\s*:\s*([0-9]{1,9})\s*$")
MAX_BYTES_CEILING = 50_000_000  # a larger value is ignored: the scan of one file must stay fast

BOTH_FILES = "profile: <both .check and .pii-guard exist>"  # load_allow adds it; it reads as an unknown tier line
UNREADABLE = "profile: <the settings file is not UTF-8 text>"  # load_allow adds it; it reads as an unknown tier line
UNKNOWN_PROFILE = ("unknown profile line in .check (or .pii-guard), or the file is not UTF-8 text: the only tier line is "
                   "`profile: dod`. Correct or remove the line, or save the file as UTF-8; if both .check and .pii-guard "
                   "exist, move the lines of .pii-guard into .check and delete it. The check does not guess a tier.")
CONFIG_NAMES = (".check", ".pii-guard")  # the settings file; the second is the name before 2026-11-18, still read
BLOCKED = "the settings file has a `block:` line for this path: this file must not be committed or sent"


def max_bytes_of(allow):
    """The size limit of one scanned file: the `content-max-bytes: <number>` line of the settings file, else MAX_BYTES.

    A project raises it so that its large text files are scanned instead of reported as unscanned (a higher limit
    scans more, so it never weakens the check). The line is not an option line: the callers that drop option lines
    keep it, so the limit reaches the scan; as an allowed string it only allows its own text. It is never a tier line.
    A value below MAX_BYTES, above MAX_BYTES_CEILING or not a number is ignored, and MAX_BYTES applies.

    Args:
        allow: the lines of the settings file (load_allow).
    Returns:
        The limit in bytes.
    """
    for v in allow:
        m = MAX_BYTES_LINE.match(v) if len(v) <= OPTION_MAX else None
        if m and MAX_BYTES <= int(m.group(1)) <= MAX_BYTES_CEILING:
            return int(m.group(1))
    return MAX_BYTES


def is_tier_line(v):
    """True when this settings line is a tier line, in any form (short lines only; never a `code-` or `audit-` setting)."""
    return len(v) <= OPTION_MAX and bool(PROFILE_LINE.match(v)) and not SETTING_LINE.match(v)


def is_option_line(v):
    """True when this settings line is an option line (tier, denylist, or a `code-` or `audit-` setting), never an
    allowed value."""
    return len(v) <= OPTION_MAX and bool(OPTION_LINE.match(v) or SETTING_LINE.match(v))


def profile_of(allow):
    """Tier from the settings lines: "minimum" (no profile line), "dod", or "unknown" (any other value: the caller
    fails, so a wrong spelling cannot lower the tier in silence). Case, and spacing around the colon, do not matter."""
    lines = [v for v in allow if is_tier_line(v)]
    if not lines:
        return "minimum"
    return "dod" if all(re.fullmatch(r"(?i)profile\s*:\s*dod", v) for v in lines) else "unknown"


def dod_mode(root):
    """True when the settings file in the working tree has a profile line (an unknown value counts: fail closed)."""
    return profile_of(load_allow(root)) != "minimum"


def warn_mode(root):
    """True when the settings file in the working tree has the option line `denylist: warn` and no profile line."""
    allow = load_allow(root)
    return WARN_OPTION in allow and profile_of(allow) == "minimum"


def _exists(root, name, ref=None):
    """True when the file exists in the working tree, or at the git ref."""
    if ref:
        return subprocess.run(["git", "cat-file", "-e", f"{ref}:{name}"], cwd=root, capture_output=True).returncode == 0
    return (pathlib.Path(root) / name).is_file()


def config_name(root, ref=None):
    """The name of the settings file that exists (working tree, or at a git ref), or None: the first of CONFIG_NAMES."""
    return next((name for name in CONFIG_NAMES if _exists(root, name, ref)), None)


def load_allow(root, ref=None):
    """The lines of the settings file (working tree, or the file at a git ref such as the PR base): allowed exact
    strings, and the `skip:`, `block:`, `denylist:`, `profile:`, `code-` and `audit-` lines.

    Args:
        root: the repo root (a folder path).
        ref: a git ref to read the file from; None = the working tree.

    Returns:
        The set of lines; it also holds a marker when the file cannot be read or both file names exist.
    """
    name = config_name(root, ref)
    both = name == CONFIG_NAMES[0] and _exists(root, CONFIG_NAMES[1], ref)
    if name is None:
        data = b""
    elif ref:
        r = subprocess.run(["git", "show", f"{ref}:{name}"], cwd=root, capture_output=True)
        data = r.stdout if r.returncode == 0 else b""
    else:
        data = (pathlib.Path(root) / name).read_bytes()
    # The file must be clean UTF-8 text. Anything else (UTF-16 from a Windows shell, a NUL, bytes that do not decode)
    # could hide the tier line, so it adds UNREADABLE: profile_of then says "unknown" and the scan fails.
    bad = data.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\0" in data
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text, bad = data.decode("utf-8", "replace"), True
    # Invisible format characters (zero-width space, a second byte-order mark) are dropped: they must not hide a line.
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    # A comment starts at the line start or after whitespace, so "skip: docs/#1.txt" keeps its "#".
    vals = (re.split(r"(?:^|\s)#", line, maxsplit=1)[0].strip() for line in text.splitlines())
    # Both files present: the old one could hold the tier line that the new one lacks, so the scan fails.
    return {v for v in vals if v} | ({UNREADABLE} if bad else set()) | ({BOTH_FILES} if both else set())


def _covers(path, allow, key):
    """True when a `<key> <path or glob>` line covers this repo-relative path: the glob matches the whole path or
    the file name, or the line names a folder above it. A bare "*" or "**" is ignored."""
    globs = [a[len(key):].strip() for a in allow if a.startswith(key)]
    globs = [g for g in globs if g.strip("*/")]
    if key == "block:":  # a block line matches in any letter case (A.XLSX is the same file type as a.xlsx)
        path, globs = path.lower(), [g.lower() for g in globs]
    base = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(path, g) or path.startswith(g.rstrip("/") + "/")
               or (key == "block:" and "/" not in g and fnmatch.fnmatchcase(base, g)) for g in globs)


def skipped(path, allow):
    """True when a `skip: <path or glob>` line covers this repo-relative path (a bare "*" would switch the scan off)."""
    return _covers(path, allow, "skip:")


def blocked(path, allow):
    """True when a `block: <path or glob>` line names this repo-relative path: a file that must not be committed or
    sent (a data export, a spreadsheet). A glob with no "/" also matches the file name in any folder (`block: *.xlsx`)."""
    return _covers(path, allow, "block:")


# ---------------------------------------------------------------- word lists (names, terms, fingerprint) ------------

MISSING_HELP = ("no denylist found. Add your names (comma or newline separated), never in a repo or a chat: "
                "a cloud session: environment variable PII_GUARD_DENYLIST in the cloud environment's settings; "
                "GitHub Actions: repository secret PII_GUARD_DENYLIST; your computer: ~/.config/pii-guard/denylist.txt. "
                "See docs/FIRST_USE.md.")


def _clean_entry(w):
    """Drop one wrapping pair of <> or quotes: a placeholder copied as "<Name>" must still match "Name"."""
    w = w.strip()
    if len(w) > 2 and (w[0], w[-1]) in (("<", ">"), ('"', '"'), ("'", "'")):
        w = w[1:-1].strip()
    return w


def parse_denylist(raw):
    """Entries shorter than 2 characters, or with no letter or digit, are dropped: they would flag ordinary text."""
    words = (_clean_entry(line.split("#", 1)[0]) for line in re.split(r"[\n,]", raw or ""))
    return [w for w in words if len(w) >= 2 and re.search(r"[A-Za-z0-9]", w)]


def denylist_source():
    """Return (raw text, where it came from) for the first source with at least one entry, or ("", None).
    first_use_check.py imports this, so both scripts agree on what counts as a denylist.

    Returns:
        (raw text, where it came from), or ("", None).
    """
    raw = os.environ.get("PII_GUARD_DENYLIST", "")
    if parse_denylist(raw):
        return raw, "environment variable PII_GUARD_DENYLIST"
    path = os.environ.get("PII_GUARD_DENYLIST_FILE") or os.path.expanduser("~/.config/pii-guard/denylist.txt")
    try:
        text = pathlib.Path(path).read_text(errors="replace") if os.path.isfile(path) else ""
    except OSError:
        text = ""
    if parse_denylist(text):
        return text, "file " + path
    return "", None


def terms_source():
    """Return (raw text, where it came from) for the Administrator's own blocked terms (words that are not personal data:
    a client, a code name), or ("", None). Same format and places as the name denylist, under other names; optional.

    Returns:
        (raw text, where it came from), or ("", None).
    """
    raw = os.environ.get("CHECK_TERMS", "")
    if parse_denylist(raw):
        return raw, "environment variable CHECK_TERMS"
    path = os.environ.get("CHECK_TERMS_FILE") or os.path.expanduser("~/.config/check/terms.txt")
    try:
        text = pathlib.Path(path).read_text(errors="replace") if os.path.isfile(path) else ""
    except OSError:
        text = ""
    if parse_denylist(text):
        return text, "file " + path
    return "", None


def load_terms():
    """The Administrator's blocked terms from the first source that has any, or []."""
    return parse_denylist(terms_source()[0])


def fingerprint(words):
    """8 hex characters over the normalized list: equal for every copy of the same list, and shows no entry."""
    norm = sorted({w.lower() for w in words})
    return hashlib.sha256("\n".join(norm).encode()).hexdigest()[:8]


def load_denylist():
    """The denylist entries from the first source that has any, or []."""
    return parse_denylist(denylist_source()[0])


# ---------------------------------------------------------------- patterns and finders ------------------------------

# EMAIL is the pattern; emails() finds its matches. A plain EMAIL.finditer tries every start of a long run of
# local-part characters, so its time grows with the square of the run (200 KB took 26 s, longer than the hook timeout).
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_LOCAL = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._%+-")


def emails(line):
    """The matches of EMAIL.finditer (leftmost, non-overlapping) in linear time. A local part cannot hold an "@", so
    each match ends its local part at one "@": walk the "@" signs in order, start the local part at the start of its
    run (not before the end of the last match), and match once from there.

    Args:
        line: one line of text.
    """
    pos, at = 0, line.find("@")
    while at != -1:
        start = at
        while start > pos and line[start - 1] in _LOCAL:
            start -= 1
        m = EMAIL.match(line, start) if start < at else None
        if m:
            yield m
            pos = m.end()
            at = line.find("@", pos)
        else:
            at = line.find("@", at + 1)


PHONE = [
    re.compile(r"(?<![\w./-])\(?\d{3}\)?[-. ]\d{3}[-.]\d{4}(?![\w-])"),
    re.compile(r"(?<![\w./-])\(\d{3}\) ?\d{3}[-. ]\d{4}(?![\w-])"),
    re.compile(r"(?<![\w+])\+\d{1,3}[ -]\(?\d{1,4}\)?[ -]\d{2,4}[ -]\d{3,4}(?![\w-])"),
    re.compile(r"(?i)\b(?:phone|tel|cell|mobile|fax|call)\b\D{0,20}?(\+?1?[ .-]?\d{3}[ .-]?\d{3}[ .-]?\d{4})\b"),
    re.compile(r"(?<![\w+])\+1\d{10}\b"),
]
SSN = re.compile(r"(?<![\w-])\d{3}-\d{2}-\d{4}(?![\w-])")
SSN_KW = re.compile(r"(?i)\b(?:SSN|social security)\b\D{0,20}?(\d{3}[ -]?\d{2}[ -]?\d{4})\b")
# Custom secret provider token regexes (GitHub, GitLab, AWS, Anthropic, OpenAI, Google, Slack, Stripe) were retired
# as redundant with gitleaks (`security.yml`, `scripts/check.sh`). Keep private-key PEM headers for the PreToolUse hook
# and pre-push scan, plus the `secret` extension point for project-local finders (`scripts/check_content_local.py`).
SECRET = [re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")]
# DoD tier (`profile: dod`). MILHOST may not start inside a host name (after "x."): a match at every label was
# quadratic ("a." * 10,000 took 0.8 s). The marks are split in the source so this file does not flag itself.
MILHOST = re.compile(
    r"(?i)(?<![A-Za-z0-9-])(?<![A-Za-z0-9-]\.)(?:(?:[a-z0-9-]+\.)+mil(?![A-Za-z0-9-]|\.[A-Za-z0-9])"   # any host under the military domain
    r"|(?:[a-z0-9-]+\.)*sharepoint-mil\.us\b|(?:[a-z0-9-]+\.)*dod\.teams\.microsoft\.us\b)")          # DoD cloud tenant hosts
MARKING_LONG = [re.compile(r) for r in (   # the marks that are phrases: they may also stand over two lines (find_split_marking)
    r"(?i)\bcontrolled\s+unclassified\s+" r"information\b", r"(?i)\bfor\s+official\s+use\s+" r"only\b")]
MARKING = [re.compile(r) for r in (
    r"\bCUI/" r"/", r"^[^A-Za-z0-9]*CU" r"I[^A-Za-z0-9]*$", MARKING_LONG[0].pattern,
    r"^[^A-Za-z0-9]*(?:SEC" r"RET|CONFID" r"ENTIAL|UNCLASS" r"IFIED)[^A-Za-z0-9]*$",  # one word alone on its line, upper case
    r"(?i)^[^A-Za-z0-9]*TOP\s+SEC" r"RET[^A-Za-z0-9]*$",                               # two words alone on a line, any case
    r"\bFO" r"UO\b", MARKING_LONG[1].pattern, r"\bNOF" r"ORN\b",
    r"(?i)\b(?:SECRET|CONFIDENTIAL|UNCLASSIFIED)/" r"/",
)]
_DODID_KW = r"(?<![A-Za-z])(?:DOD[\s_-]*ID|EDIPI|CAC)(?![A-Za-z])"  # also dod_id, and DODID joined to the number
DODID = [re.compile(r"(?i)" + _DODID_KW + r"\D{0,20}?(\d{10})(?!\d)"),          # keyword, then the number
         re.compile(r"(?i)(?<!\d)(\d{10})(?!\d)\D{0,20}?" + _DODID_KW)]        # the number, then the keyword
ALLOWED_EMAIL = re.compile(
    r"(?i)(@users\.noreply\.github\.com$|^(no-?reply)@|@example\.(com|org|net)$|\.(example|invalid|test|localhost)$)")

KINDS = ("email", "secret", "phone", "id", "milhost", "dodid", "marking")   # the order of the findings of one line
DOD_KINDS = ("milhost", "dodid", "marking")                                  # run only in the DoD tier (`profile: dod`)


def find_email(line):
    """Yield (start, end, address) for each mail address that is not an allowed form (noreply, example domains)."""
    for m in emails(line):
        if not ALLOWED_EMAIL.search(m.group()):
            yield m.start(), m.end(), m.group()


def find_secret(line):
    """Yield (start, end, text) for each private-key header (SECRET)."""
    for rx in SECRET:
        for m in rx.finditer(line):
            yield m.start(), m.end(), m.group()


def find_phone(line):
    """Yield (start, end, number) for each phone number (PHONE), without the punctuation around it (allow lines are
    stripped the same way)."""
    for rx in PHONE:
        for m in rx.finditer(line):
            g = m.lastindex or 0
            yield m.start(g), m.end(g), m.group(g).strip(" .-")


def find_id(line):
    """Yield (start, end, number) for each SSN shape, and each 9 digits next to an SSN keyword."""
    for m in SSN.finditer(line):
        yield m.start(), m.end(), m.group()
    for m in SSN_KW.finditer(line):
        yield m.start(1), m.end(1), m.group(1)


def find_milhost(line):
    """Yield (start, end, host) for each military or DoD cloud host name (MILHOST)."""
    for m in MILHOST.finditer(line):
        yield m.start(), m.end(), m.group()


def find_dodid(line):
    """Yield (start, end, number) for each 10 digits next to a DoD ID keyword (DODID)."""
    for rx in DODID:
        for m in rx.finditer(line):
            yield m.start(1), m.end(1), m.group(1)


def find_marking(line):
    """Yield (start, end, mark) for each controlled-information or classification mark (MARKING)."""
    for rx in MARKING:
        for m in rx.finditer(line):
            yield m.start(), m.end(), m.group().strip()


def find_split_marking(first, second):
    """Yield (start, end, mark) for each phrase mark (MARKING_LONG) that stands over the end of `first` and the start of
    `second`, two lines in a row. The mark is read with one space at the break; start and end are in `first` plus that
    space plus `second` (the lines without the blanks at the break).

    Args:
        first: a line of text.
        second: the line after it.
    """
    head = first.rstrip()
    joined = head + " " + second.lstrip()
    for rx in MARKING_LONG:
        for m in rx.finditer(joined):
            if m.start() < len(head) < m.end() - 1:
                yield m.start(), m.end(), m.group()


def find_split_dodid(first, second):
    """Yield (start, end, number) for each DoD ID keyword and 10-digit number (DODID) that stand over the end of
    `first` and the start of `second`, two lines in a row. The lines are joined as in find_split_marking; start and end
    are those of the number in the joined text.

    Args:
        first: a line of text.
        second: the line after it.
    """
    head = first.rstrip()
    joined = head + " " + second.lstrip()
    for rx in DODID:
        for m in rx.finditer(joined):
            if m.start() < len(head) < m.end() - 1:
                yield m.start(1), m.end(1), m.group(1)


# (kind, the kit's finder of one line, the finder of two lines in a row): scan_text runs a two-line finder only while the
# kit's one-line finder of its kind is in use. A blank line between the two lines is a paragraph break: not joined.
SPLIT_FINDERS = (("marking", find_marking, find_split_marking), ("dodid", find_dodid, find_split_dodid))

KIT_FINDERS = {"email": [find_email], "secret": [find_secret], "phone": [find_phone], "id": [find_id],
               "milhost": [find_milhost], "dodid": [find_dodid], "marking": [find_marking]}

# Gates (speed only, never a finding): for each kind, patterns of which one matches wherever a kit finder of that kind
# can match. Each is a part of one of that kind's patterns with its look-arounds, anchors and \b removed (removing them
# only lets more text match), with the same letters. So a line in which no gate of a kind matches cannot give a
# finding of that kind: scan_text skips a line that no gate matches, and runs all finders, as before, on every other
# line. Each kind has (case-sensitive gates, case-free gates). A case-free gate is in lower case and is searched in
# the lower-case copy of the text (a plain search there is fast); when the text holds a letter in FOLD_EXTRAS, or its
# lower-case copy has another length, it is searched with (?i) in the text itself. A gate holds only while the kind
# uses the kit's finders alone (scan_text checks that). Proved by the self-test case "gates".
_DIGITS = r"\d{3}(?:\)?[-. ]\d{3}[-.]\d{4}|\) ?\d{3}[-. ]\d{4}|-\d{2}-\d{4}|\d{7})"   # PHONE 0 and 1, SSN, DODID
GATES = {
    "email": (["@"], []),
    "secret": (["-----BEGIN "], []),
    "phone": ([_DIGITS, r"\+\d"], ["phone", "tel", "cell", "mobile", "fax", "call"]),
    "id": ([_DIGITS], ["ssn", "social security"]),
    "dodid": ([_DIGITS], []),
    "milhost": ([], [r"\.mil", r"sharepoint-mil\.us", r"dod\.teams\.microsoft\.us"]),
    "marking": (["CU" "I", "SEC" "RET", "CONFID" "ENTIAL", "UNCLASS" "IFIED", "FO" "UO", "NOF" "ORN"],
                ["controlled", r"top\s+sec" "ret", "official", "secret/" "/", "confidential/" "/", "unclassified/" "/"]),
}
# The letters outside a-z and A-Z that (?i) matches with a letter a-z (dotted and dotless i, long s, Kelvin sign):
# str.lower() does not turn them into that letter, so a text that holds one is searched with (?i). The self-test
# checks this list against the regex engine over every code point.
FOLD_EXTRAS = ("\u0130", "\u0131", "\u017f", "\u212a")

_GATE_CACHE = {}   # (kinds, words, folded) -> the compiled gates of candidate_lines


def _gates(kinds, words, folded):
    """The compiled gates for these kinds and words: a list of (pattern, True when it searches the lower-case copy).

    Args:
        kinds: the finding kinds in use (each uses the kit's finders alone).
        words: the names and terms.
        folded: True when the lower-case copy can be used (candidate_lines); False: case-free gates get (?i).

    Returns:
        The list of (compiled pattern, searches the lower-case copy).
    """
    key = (tuple(kinds), tuple(words), folded)
    if key not in _GATE_CACHE:
        cased = [g for k in kinds for g in GATES[k][0]]
        free = [g for k in kinds for g in GATES[k][1]]
        for w in words:   # each word is one more case-free gate: the word, or its longest ASCII part when it is not ASCII
            part = w if w.isascii() else max(re.findall(r"[ -~]+", w) or [""], key=len)
            if w.isascii() or len(part) >= 3:
                free.append(re.escape(part.lower()))
            else:   # too short a part: the name pattern's own search
                cased.append(r"(?i)(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])")
        gates = [(re.compile(g), False) for g in dict.fromkeys(cased)]
        gates += [(re.compile(g), True) if folded else (re.compile("(?i)" + g), False) for g in dict.fromkeys(free)]
        if len(_GATE_CACHE) > 64:   # many word lists in one process (the self-test): keep the cache small
            _GATE_CACHE.clear()
        _GATE_CACHE[key] = gates
    return _GATE_CACHE[key]


def candidate_lines(text, kinds, words, finders):
    """The lines of scan_text that can give a finding (speed only); every other line cannot.

    Each kind that uses the kit's finders alone has gates (GATES), and each name or term is one
    more gate. Each gate is searched in the whole text (or its lower-case copy, which has the same length, so the same
    places), not line by line: a match in one line is also a match at the same place in the whole text, because the
    gates have no anchors and the look-arounds of a word that is not ASCII see a line break there, which is never a
    letter or digit. After a match, the search goes on at the start of the next line, so every line with a match is
    found. A match that runs over a line break only adds a line: that line is scanned in full, as before.

    Args:
        text: the whole text that scan_text scans.
        kinds: the finding kinds in use.
        words: the names and terms.
        finders: the finders in use ({kind: [finder]}).

    Returns:
        None when a kind has no gate (a project's own finders: every line is scanned); else the sorted indexes
        (from 0, in text.splitlines()) of the lines to scan.
    """
    if any(finders[k] != KIT_FINDERS[k] for k in kinds):
        return None
    low = text.lower()
    folded = len(low) == len(text) and not any(c in text for c in FOLD_EXTRAS)
    hits = [(rx, low if on_low else text) for rx, on_low in _gates(kinds, words, folded)]
    hits = [(rx, hay, m) for rx, hay in hits for m in [rx.search(hay)] if m]
    if not hits:
        return []
    starts = list(itertools.accumulate(map(len, text.splitlines(True)), initial=0))   # start of each line, then the end
    last, rows = len(starts) - 2, set()
    for rx, hay, m in hits:
        while m:
            i = min(bisect.bisect_right(starts, m.start()) - 1, last)
            rows.add(i)
            if i >= last:
                break
            m = rx.search(hay, starts[i + 1])
    return sorted(rows)


# ---------------------------------------------------------------- a project's own finders ---------------------------

LOCAL_NAME = "check_content_local.py"   # a project's own file, next to the scanner; the kit has none


class LocalError(Exception):
    """A project's own finder module exists and cannot be used: every scan fails, and the hook blocks."""


def local_lists(mod, name, need_one):
    """The {kind: [finder]} dict a project's module gives under `name` (REPLACE or ADD), checked.

    Args:
        mod: the loaded module.
        name: "REPLACE" or "ADD".
        need_one: True when each kind must have at least one finder (an empty REPLACE list would switch a kind off).

    Returns:
        The dict ({} when the module has no such name). LocalError when it is not {kind in KINDS: [functions]}.
    """
    got = getattr(mod, name, {})
    shaped = isinstance(got, dict) and all(
        k in KINDS and isinstance(v, (list, tuple)) and all(callable(x) for x in v) and (v or not need_one)
        for k, v in got.items())
    if not shaped:
        raise LocalError(f"{LOCAL_NAME}: {name} must be a dict {{kind: [finder functions]}} with kinds from "
                         f"{', '.join(KINDS)}" + (" and at least one finder for each kind" if need_one else ""))
    return {k: list(v) for k, v in got.items()}


def load_local(path):
    """The finders in use, with a project's own module applied when its file exists.

    Args:
        path: the path of the project's module (a file named LOCAL_NAME next to the scanner).

    Returns:
        (finders, note): finders is {kind: [finder]} for each kind in KINDS; note is "" when there is no such file,
        else a text for the result line that names the kinds the module replaces and adds. LocalError when the file
        cannot be imported, or has neither REPLACE nor ADD in the documented shape: the caller fails every scan.
    """
    path = pathlib.Path(path)
    if not path.is_file():
        return dict(KIT_FINDERS), ""
    try:
        spec = importlib.util.spec_from_file_location("check_content_local", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except BaseException as err:   # noqa: B036 - any error or exit of the project's file (a sys.exit at import too):
        # no scan runs on the kit's default in silence, and the process does not end with the file's exit code
        raise LocalError(f"{LOCAL_NAME} cannot be loaded ({err.__class__.__name__}: {err})") from None
    replace, add = local_lists(mod, "REPLACE", True), local_lists(mod, "ADD", False)
    if not replace and not any(add.values()):
        raise LocalError(f"{LOCAL_NAME} has no finder: it must define REPLACE or ADD (the interface: the header of "
                         "scripts/check_content_scan.py)")
    finders = {k: list(replace.get(k, KIT_FINDERS[k])) + add.get(k, []) for k in KINDS}
    parts = (["replaces " + ", ".join(k for k in KINDS if k in replace)] if replace else []) \
        + (["adds " + ", ".join(k for k in KINDS if add.get(k))] if any(add.values()) else [])
    return finders, f"local module {LOCAL_NAME} active ({'; '.join(parts)})"


# ---------------------------------------------------------------- scanner core --------------------------------------

ZERO = re.compile(r"^0+$")
LOCAL_FILE = pathlib.Path(__file__).resolve().parent / LOCAL_NAME   # a project's own finders (see the header)
FINDERS, LOCAL, LOCAL_ERROR = None, "", None   # the finders in use, the note for the result line, why they cannot be used


def use_local(path=None):
    """Set the finders in use: the kit's, with the project's own module at `path` applied when that file exists
    (None = LOCAL_FILE). A module that cannot be used sets LOCAL_ERROR, and then every scan_text call raises."""
    global FINDERS, LOCAL, LOCAL_ERROR
    try:
        (FINDERS, LOCAL), LOCAL_ERROR = load_local(path or LOCAL_FILE), None
    except LocalError as err:
        FINDERS, LOCAL, LOCAL_ERROR = None, "", f"{err}. Correct or remove that file: no scan runs until then"


use_local()
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".woff", ".woff2", ".ttf")


def mask(kind, s):
    """Show the kind and a length, never enough to rebuild the value (CI logs may be public)."""
    if kind in ("unscanned", "blocked"):
        return s  # a reason, not a value
    if kind in ("name", "term", "secret", "milhost", "marking"):
        return f"<{len(s)} chars>"
    if kind == "email" and "@" in s:
        return "***@" + "*" * len(s.split("@", 1)[1])
    return "*" * (len(s) - 2) + s[-2:] if len(s) > 6 else "*" * len(s)


def _inside(spans):
    """A test for "the span (s, e) lies inside one of these spans", in log time: one sort, then a binary search over
    the starts and a running maximum of the ends (spans may overlap). A plain any() was quadratic on long lines.

    Args:
        spans: the (start, end) spans.

    Returns:
        A function test(s, e) that gives True or False.
    """
    spans = sorted(spans)
    starts = [a for a, _ in spans]
    reach, best = [], -1
    for _, b in spans:
        best = max(best, b)
        reach.append(best)

    def test(s, e):
        """True when the span (s, e) lies inside one of the spans."""
        i = bisect.bisect_right(starts, s) - 1
        return i >= 0 and reach[i] >= e
    return test


def scan_text(text, where, deny, allow, dod=False, terms=()):
    """Return findings (where, line_no, kind, masked) for one text. dod: also run the DoD checks. terms: the Administrator's
    own blocked words, found like the names (whole word, any case) and reported as kind term.

    Args:
        text: the text to scan.
        where: the name of its place, for the findings.
        deny: the names of the denylist.
        allow: the lines of the settings file (load_allow).
        dod: True in the DoD tier: also run the DoD checks.
        terms: the Administrator's own blocked words.

    Returns:
        The findings, each (where, line number, kind, masked value).
    """
    if LOCAL_ERROR:
        raise LocalError(LOCAL_ERROR)
    found = []
    kinds = [k for k in KINDS if dod or k not in DOD_KINDS]
    words = list(deny) + list(terms)
    names_low = {w.lower() for w in deny}
    name_re = re.compile(r"(?i)(?<![A-Za-z0-9])(" + "|".join(re.escape(w) for w in words) + r")(?![A-Za-z0-9])") if words else None
    rows = candidate_lines(text, kinds, words, FINDERS)
    if rows == []:   # no line of this text can give a finding
        return found
    # Compiled once per call, used only on a line with a name hit (one finditer per allow line per line was slow).
    allow_res = [re.compile(re.escape(v), re.IGNORECASE) for v in allow if not v.startswith(("skip:", "block:"))] if name_re else []
    hosts_ok = {v.lower() for v in allow} if dod else set()  # a host name has no case
    lines = text.splitlines()
    for i in range(len(lines)) if rows is None else rows:   # only the lines that can give a finding (candidate_lines)
        n, line = i + 1, lines[i]
        hits = []
        in_mail = _inside(m.span() for m in emails(line)) if dod else None  # the host of a mail address is part of that finding
        for kind in kinds:
            for find in FINDERS[kind]:
                hits += [(kind, val) for s, e, val in find(line) if kind != "milhost" or not in_mail(s, e)]
        names = list(name_re.finditer(line)) if name_re else []
        if names:
            in_allowed = _inside((s.start(), s.end()) for rx in allow_res for s in rx.finditer(line))
            hits += [("name" if m.group(1).lower() in names_low else "term", m.group(1)) for m in names
                     if not in_allowed(m.start(1), m.end(1))]  # inside an allowed string
        seen = set()  # values already reported on this line, of any kind (a set: a list scan was quadratic)
        for kind, val in hits:
            if val in allow or (kind == "milhost" and val.lower() in hosts_ok) or val in seen:
                continue
            seen.add(val)
            found.append((where, n, kind, mask(kind, val)))
    split = [(kind, find) for kind, kit, find in SPLIT_FINDERS if kind in kinds and kit in FINDERS[kind]]
    if split:   # a mark, or a keyword and its number, over two lines: reported at the first
        near = range(len(lines) - 1) if rows is None else sorted({j for i in rows for j in (i - 1, i) if 0 <= j < len(lines) - 1})
        found += [(where, i + 1, kind, mask(kind, val)) for i in near for kind, find in split
                  for _, _, val in find(lines[i], lines[i + 1]) if val not in allow]
    return found


def git(*args, root="."):
    """Run git in root and return its stdout as text; a git error raises CalledProcessError."""
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True,
                          errors="replace").stdout


def scan_files(paths, root, deny, allow, dod=False, named=False, terms=()):
    """dod, or named (the caller named these files: FILE mode, the hook): a file that cannot be scanned is a finding
    (kind unscanned) unless a `skip:` line names it. A path that a `block:` line names is a finding (kind blocked).

    Args:
        paths: the repo-relative paths.
        root: the repo root (a folder path).
        deny: the names of the denylist.
        allow: the lines of the settings file (load_allow).
        dod: True in the DoD tier: also run the DoD checks.
        named: True when the caller named these files.
        terms: the Administrator's own blocked words.

    Returns:
        The findings, each (where, line number, kind, masked value).
    """
    limit = max_bytes_of(allow)   # once per call, not once per file
    job = (root, deny, allow, dod, named, terms, limit)
    parts = _in_parallel(paths, root, job) if not named else None   # named files (FILE mode, the hook): this process
    if parts is None:
        parts = [_scan_path(p, job) for p in paths]
    return [f for part in parts for f in part]


PARALLEL_BYTES = 4_000_000   # a scan of fewer bytes runs in this process: starting a pool costs more than it saves


def usable_cores():
    """The number of cores this process may use (its CPU affinity where the system has one), at least 1."""
    return len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)


def _in_parallel(paths, root, job):
    """The findings of each path, in the order of paths, from a pool of processes (speed only; the same findings as
    the scan in this process). None when the scan is small, the machine has one core, or a pool cannot start.

    Args:
        paths: the repo-relative paths.
        root: the repo root (a folder path).
        job: the arguments of _scan_path after the path.

    Returns:
        A list with the findings of each path, or None.
    """
    try:
        cores = usable_cores()
        size = sum(os.path.getsize(f) for f in (os.path.join(root, p) for p in paths) if os.path.isfile(f))
    except OSError:
        return None
    if cores < 2 or len(paths) < 2 or size < PARALLEL_BYTES:
        return None
    import concurrent.futures
    import functools
    import multiprocessing
    try:
        ctx = multiprocessing.get_context("fork" if sys.platform.startswith("linux") else None)   # fork: no new imports
        with concurrent.futures.ProcessPoolExecutor(min(cores, 8), mp_context=ctx) as pool:
            return list(pool.map(functools.partial(_scan_path, job=job), paths, chunksize=8))
    except (OSError, concurrent.futures.process.BrokenProcessPool):   # no pool here: scan in this process
        return None


def _scan_path(p, job):
    """The findings of one path (scan_files).

    Args:
        p: the repo-relative path.
        job: (root, deny, allow, dod, named, terms, limit), as in scan_files; limit: max_bytes_of(allow).

    Returns:
        The findings, each (where, line number, kind, masked value).
    """
    root, deny, allow, dod, named, terms, limit = job
    f = pathlib.Path(root) / p
    rel = os.path.relpath(f, root).replace(os.sep, "/") if os.path.isabs(str(p)) else str(p)
    if f.is_file() and blocked(rel, allow):
        return [(str(p), 0, "blocked", BLOCKED)]
    if skipped(str(p), allow) or not f.is_file():
        return []
    why = None
    if f.suffix.lower() in SKIP_SUFFIX:
        why = f"file type {f.suffix.lower()} is not scanned"
    elif f.stat().st_size > limit:
        why = f"larger than {limit} bytes"
    else:
        data = f.read_bytes()
        if b"\0" in data[:8192]:
            why = "binary file"
    if why:
        return [(str(p), 0, "unscanned", why)] if dod or named else []
    return scan_text(data.decode("utf-8", "replace"), str(p), deny, allow, dod, terms)


def commit_meta(sha, root, deny, allow, dod, terms):
    """Findings in a commit's author and committer identity and in its message."""
    lines = git("show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%B", sha, root=root).split("\n")
    out = []
    for part, text in (("author/committer", "\n".join(lines[:4])), ("message", "\n".join(lines[4:]))):
        out += [(f"commit {sha[:7]} {part}", n, k, v) for _, n, k, v in scan_text(text, "", deny, allow, dod, terms)]
    return out


def blocked_in_commit(sha, root, allow):
    """Findings (kind blocked) for each file this commit adds or changes (a merge: against its first parent) that a
    `block:` line names."""
    names = git("-c", "core.quotepath=off", "show", "--format=", "--name-only", "-z", "--no-renames", "-m",
                "--first-parent", "--diff-filter=AM", sha, root=root)
    return [(f"commit {sha[:7]} {n}", "+", "blocked", BLOCKED) for n in filter(None, names.split("\0"))
            if blocked(n, allow)]


def unscanned_in_commit(sha, root, allow, unscanned):
    """DoD tier: the files one commit adds or changes that cannot be scanned (too large, a file type that is not
    scanned, binary), unless a `skip:` line names them. numstat marks a binary file with "-"; the patch has no added
    lines for it.

    Args:
        sha: the commit.
        root: the repo root.
        allow: the lines of the settings file (load_allow).
        unscanned: a set that gets the name of each file over the size limit, so its patch lines are not scanned again.

    Returns:
        The findings (where, "+", "unscanned", reason).
    """
    found, short, limit = [], sha[:7], max_bytes_of(allow)   # once per commit, not once per file
    stat = git("-c", "core.quotepath=off", "show", "--format=", "--numstat", "-z", "--no-renames",
               "--diff-filter=AM", sha, root=root)
    sizes = {}
    for rec in filter(None, git("ls-tree", "-r", "-l", "-z", sha, root=root).split("\0")):
        info, _, name = rec.partition("\t")
        size = info.split()[-1]
        if size.isdigit():
            sizes[name] = int(size)
    for rec in filter(None, stat.split("\0")):
        parts = rec.split("\t", 2)
        if len(parts) != 3 or skipped(parts[2], allow):
            continue
        if sizes.get(parts[2], 0) > limit:
            unscanned.add(parts[2])
            found.append((f"commit {short} {parts[2]}", "+", "unscanned", f"larger than {limit} bytes"))
        elif parts[2].lower().endswith(SKIP_SUFFIX):
            found.append((f"commit {short} {parts[2]}", "+", "unscanned", "file type is not scanned"))
        elif parts[0] == "-":
            found.append((f"commit {short} {parts[2]}", "+", "unscanned", "binary file"))
    return found


def _flush_commit_added(found, short, cur, added, deny, allow, dod, terms, unscanned):
    """Scan accumulated added lines for one file in a commit patch and append findings."""
    if added and not cur.endswith(SKIP_SUFFIX) and cur not in unscanned and not skipped(cur, allow):
        found.extend((f"commit {short} {cur}", "+", k, v) for _, _, k, v in scan_text("\n".join(added), "", deny, allow, dod, terms))
    added.clear()


def scan_commits(revs, root, deny, allow, dod=False, terms=()):
    """revs: arguments for git rev-list. Scan each commit's identity, message and added lines.
    dod: an added or changed file that cannot be scanned is a finding unless a `skip:` line names it.
    A file that a commit adds or changes under a `block:` line is a finding (kind blocked).

    Args:
        revs: the arguments for git rev-list.
        root: the repo root (a folder path).
        deny: the names of the denylist.
        allow: the lines of the settings file (load_allow).
        dod: True in the DoD tier: also run the DoD checks.
        terms: the Administrator's own blocked words.

    Returns:
        (findings, the number of commits scanned).
    """
    found = []
    shas = git("rev-list", *revs, root=root).split()
    has_block = any(a.startswith("block:") for a in allow)
    for sha in shas:
        short = sha[:7]
        unscanned = set()  # dod: files already reported as unscanned; their patch lines are not scanned again
        found += commit_meta(sha, root, deny, allow, dod, terms)
        if has_block:
            found += blocked_in_commit(sha, root, allow)
        if dod:
            found += unscanned_in_commit(sha, root, allow, unscanned)
        patch = git("-c", "core.quotepath=off", "show", "--format=", "--unified=0", "--no-color", "--no-ext-diff",
                    "--src-prefix=a/", "--dst-prefix=b/", sha, root=root)
        cur, in_header, added = "?", False, []
        for line in patch.splitlines():
            # A "+++ " line names the file only in a file header (after "diff --git", before the first "@@").
            # In a hunk it is an added line that starts with "++ ", and must be scanned like any other.
            if line.startswith(("diff --git ", "diff --cc ", "diff --combined ")):  # the last two: merge commits
                _flush_commit_added(found, short, cur, added, deny, allow, dod, terms, unscanned)
                in_header = True
            elif line.startswith("@@"):
                in_header = False
            elif in_header and line.startswith("+++ "):
                name = line[4:].split("\t", 1)[0]
                if len(name) > 1 and name[0] == name[-1] == '"':
                    name = name[1:-1].replace('\\"', '"').replace("\\\\", "\\")
                cur = name[2:] if name.startswith("b/") else name
            elif line.startswith("+"):
                added.append(line[1:])
        _flush_commit_added(found, short, cur, added, deny, allow, dod, terms, unscanned)
    return found, len(shas)


def push_revs(stdin_text, root):
    """Turn pre-push stdin lines into rev-list argument lists (one per pushed ref).

    Args:
        stdin_text: the lines git gives a pre-push hook on stdin.
        root: the repo root (a folder path).

    Returns:
        A list of rev-list argument lists.
    """
    out = []
    for line in stdin_text.splitlines():
        parts = line.split()
        if len(parts) != 4 or ZERO.match(parts[1]):
            continue
        lsha, rsha = parts[1], parts[3]
        known = not ZERO.match(rsha) and subprocess.run(
            ["git", "cat-file", "-e", rsha + "^{commit}"], cwd=root, capture_output=True).returncode == 0
        out.append([f"{rsha}..{lsha}"] if known else [lsha, "--not", "--remotes"])
    return out
