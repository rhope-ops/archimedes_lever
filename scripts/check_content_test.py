"""Self-test of scripts/check_content.py (run by `python3 scripts/check_content.py --test`; kept in its own file).

It proves every check on built-at-run-time samples (no real address, token, host, mark or ID is in this file): the
patterns and their speed on long lines, the allow and skip lines, the tiers and the settings-file reader (under both
`.check` and `.pii-guard`), the denylist and terms sources, the `block:` lines, the `code-` and `audit-` option lines,
the speed gates and process pool, the CLI modes (--all, --push, --status, --stdin, files) in temporary git repos,
the commit scan, the PreToolUse hook (Write, Edit, NotebookEdit, Bash, and other tools), and a project's own finders.
Input: none (temporary folders only; the host's git config is switched off). Output: one "ok" or "FAIL" line per
case, then CONTENT CHECK TEST PASS or FAIL; run() returns the exit code 0 or 1. Needs git.
Network: none.
Writes: temporary folders only.
Credentials: none (the sample secrets are built at run time and are not real).
"""
import contextlib
import io
import json
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import check_content
import check_content_scan
from check_content_scan import (MAX_BYTES, OPTION_MAX, blocked, config_name, denylist_source, dod_mode, fingerprint,
                                git, is_option_line, is_tier_line, load_allow, load_denylist, load_terms, mask,
                                max_bytes_of, parse_denylist, profile_of, push_revs, scan_commits, scan_files,
                                scan_text, skipped, warn_mode)

at, dot = "@", "."  # addresses and hosts are joined at run time, so this file does not flag itself
x36 = "A1b2C3d4E5" * 3 + "F6g7H8"  # body of the sample secrets
mil = "portal" + dot + "unit" + dot + "mi" + "l"  # a sample host in the military domain
ME = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_content.py")]  # the guard's CLI
FAILED = []  # labels of the cases that failed


def check(label, good):
    """Print one result line and remember a failure."""
    print(("ok   " if good else "FAIL ") + label)
    if not good:
        FAILED.append(label)


def guard(d, env, *args):
    """Run the guard's CLI in folder d with this environment."""
    return subprocess.run(ME + list(args), cwd=d, env=env, capture_output=True, text=True)


def expect(name, text, kinds_want, deny=(), allow=(), dod=False):
    """Scan one text and check that the finding kinds are exactly these."""
    got = sorted({k for _, _, k, _ in scan_text(text, "t", list(deny), set(allow), dod)})
    check(f"{name}: {got}", got == sorted(kinds_want))


def kinds(text, deny=(), allow=(), terms=()):
    """The sorted finding kinds of one text."""
    return sorted({k for _, _, k, _ in scan_text(text, "t", list(deny), set(allow), False, list(terms))})


def case_speed():
    """Long lines (address chains, host runs, many distinct values) scan in linear time (CPU time of this process,
    so checks that run at the same time do not count)."""
    expect("personal email", "mail jane" + at + "corp" + dot + "io", ["email"])
    t0 = time.process_time()
    chain = len(scan_text(("a" + at + "b" + dot + "cc+") * 20_000, "t", [], set()))  # 200 KB of joined addresses
    secs = time.process_time() - t0  # the first address and the "+" joined one; scan_text drops repeats
    check(f"200 KB chain of joined addresses: linear ({secs:.2f} s)", 1 <= chain <= 2 and secs < 2)
    teams = "api" + dot + "dod" + dot + "teams" + dot + "microsoft" + dot + "us"
    expect("a DoD Teams host with a subdomain", "see https://" + teams + "/x", ["milhost"], dod=True)
    for label, run_s in (("a.", "a." * 100_000), ("a-a.", "a-a." * 50_000), ("a.dod.", "a.dod." * 33_000)):
        t0 = time.process_time()
        scan_text(run_s, "t", [], set(), True)
        secs = time.process_time() - t0
        check(f"200 KB of {label!r}: MILHOST linear ({secs:.2f} s)", secs < 2)
    t0 = time.process_time()
    many = "".join("a" + str(i) + at + "b" + dot + "cc " for i in range(17_600))  # 200 KB of distinct addresses
    many += "".join("h" + str(i) + dot + "mil " for i in range(5_000)) + "Jane Doe" * 18_000  # hosts, allowed names
    scan_text(many, "t", ["jane"], {"Jane Doe"}, True)
    secs = time.process_time() - t0
    check(f"200 KB of distinct addresses, hosts and allowed names: linear ({secs:.2f} s)", secs < 2)


def case_minimum_patterns():
    """Emails, phones, IDs, names, the allow list and skip lines in the minimum tier."""
    expect("third address of a chain of allowed ones",
           "-" + at + "example" + dot + "com+" + at + "example" + dot + "com" + at + "example" + dot + "com" + at + "jane" + dot + "io",
           ["email"])
    expect("address joined to the end of an allowed one", "x" + at + "example" + dot + "com+bob" + at + "corp" + dot + "org", ["email"])
    expect("github noreply allowed", "123+x" + at + "users.noreply.github" + dot + "com", [])
    expect("noreply allowed", "noreply" + at + "anthropic" + dot + "com", [])
    expect("example domain allowed", "a" + at + "example" + dot + "com", [])
    expect("placeholder t@t ignored", "t" + at + "t", [])
    expect("phone dashes", "call 555-123-" + "4567", ["phone"])
    expect("phone parens", "call (555) 123-" + "4567", ["phone"])
    expect("phone intl", "call +44 20 7946 " + "0958", ["phone"])
    expect("SSN shape", "id 123-45-" + "6789", ["id"])
    expect("SSN keyword", "SSN 123 45 " + "6789", ["id"])
    expect("date not a phone", "2026-11-11 10:00", [])
    expect("version not a phone", "v2.1.41 and 1.2.3.4", [])
    expect("unix time not an id", "ts 17312" + "34567", [])
    expect("sha not an id", "commit 0123456789abcdef0123456789abcdef01234567", [])
    expect("denylist name", "ask Alex" + "andra first", ["name"], deny=["Alexandra"])
    expect("denylist any case", "ALEX" + "ANDRA", ["name"], deny=["alexandra"])
    expect("denylist whole word", "Alexandra" + "s", [], deny=["Alexandra"])
    expect("allow list", "mail jane" + at + "corp" + dot + "io", [], allow=["jane" + at + "corp" + dot + "io"])
    expect("allow list is case-exact for findings", "mail jane" + at + "CORP" + dot + "io", ["email"], allow=["jane" + at + "corp" + dot + "io"])
    expect("skip line is not an allowed value", "mail jane" + at + "corp" + dot + "io", ["email"], allow=["skip: ref/x.txt"])
    good = not skipped("a.txt", {"skip: *"}) and not skipped("a/b.txt", {"skip: **"}) \
        and skipped("ref/x.txt", {"skip: ref/x.txt"}) and skipped("ref/a/b.txt", {"skip: ref/"}) \
        and skipped("ref/y.txt", {"skip: ref/*.txt"}) and not skipped("docs/x.txt", {"skip: ref/x.txt"})
    check("skip: exact path, folder, glob; other paths still scanned", good)
    expect("name inside an allowed host is not flagged", "https://acme" + dot + "example" + dot + "org/sites/x", [],
           deny=["ACME"], allow=["acme" + dot + "example" + dot + "org"])
    expect("allowed string matches in any case", "https://ACME" + dot + "EXAMPLE" + dot + "ORG/x", [],
           deny=["ACME"], allow=["acme" + dot + "example" + dot + "org"])
    expect("same name elsewhere on the line is flagged", "ACME team at acme" + dot + "example" + dot + "org", ["name"],
           deny=["ACME"], allow=["acme" + dot + "example" + dot + "org"])


def case_secrets_and_masks():
    """Private-key secret shapes and their look-alikes, more phone and ID forms, and the masks."""
    # Secret test values are built at run time, so this file holds no key header itself.
    for label, val in (("private key", "-----BEGIN OPENSSH " + "PRIVATE KEY-----"),
                       ("RSA private key", "-----BEGIN RSA " + "PRIVATE KEY-----")):
        expect("secret: " + label, "token = " + val, ["secret"])
    expect("not a secret: public key header", "-----BEGIN " + "PUBLIC KEY-----", [])
    check("secrets print as a length only", mask("secret", "-----BEGIN RSA " + "PRIVATE KEY-----") == "<31 chars>")
    expect("allow list is exact", "call 555-123-" + "4567", ["phone"], allow=["call 555-123-" + "4567 now"])
    num = "555-123-" + "4567"
    expect("allowed phone after a keyword and a space", "tel " + num, [], allow=[num])
    expect("allowed phone after a keyword and a dash", "tel-" + num, [], allow=[num])
    expect("an allowed phone does not allow another", "tel " + num + ", cell 555-987-" + "6543", ["phone"], allow=[num])
    expect("URL path not a phone", "github.com/x/pull/123-456-" + "7890", [])
    expect("phone keyword, no separators", "tel: 555123" + "4567", ["phone"])
    expect("+1 packed", "+1555123" + "4567", ["phone"])
    expect("SSN keyword, no dashes", "SSN 123456" + "789", ["id"])
    expect("short name fully masked", "Sam", ["name"], deny=["Sam"])
    good = mask("name", "Sam") == "<3 chars>" and mask("email", "a" + at + "b" + dot + "io") == "***@****"
    check("masking hides names and email users", good)


def case_dod_patterns():
    """DoD tier: military hosts, banner marks and DoD IDs, and what is not one."""
    # DoD tier. Test values are built at run time, so this file holds no host, mark or ID shape itself.
    for label, text in (("host", "see " + mil), ("URL", "https://" + mil + "/sites/x"),
                        ("host, upper case", "see " + mil.upper()), ("host at sentence end", "open " + mil + "."),
                        ("cloud tenant host", "x" + dot + "sharepoint-mi" + "l" + dot + "us/sites/y"),
                        ("cloud meeting host", "dod" + dot + "teams" + dot + "microsoft" + dot + "us")):
        expect("dod milhost: " + label, text, ["milhost"], dod=True)
    for label, text in (("wildcard", "*" + dot + "unit" + dot + "mi" + "l"), ("leading dot", "domain=" + dot + "unit" + dot + "mi" + "l"),
                        ("handle", at + "unit" + dot + "mi" + "l team")):
        expect("dod milhost: " + label, text, ["milhost"], dod=True)
    expect("minimum tier: host not checked", "see " + mil, [])
    expect("dod: mail address is one finding, kind email", "ann" + at + "unit" + dot + "mi" + "l", ["email"], dod=True)
    expect("dod: not a host: other domain after it", "x" + dot + "mi" + "l" + dot + "example" + dot + "org", [], dod=True)
    expect("dod: not a host: the words family and mil alone", "a family of 3 mil units", [], dod=True)
    expect("dod: allowed host", "see " + mil, [], allow=[mil], dod=True)
    expect("dod: allowed host in any case", "see " + mil.upper(), [], allow=[mil], dod=True)
    expect("dod: allowed host does not allow another host", "see other" + dot + "unit" + dot + "mi" + "l", ["milhost"], allow=[mil], dod=True)
    for label, text in (("banner", "CU" + "I//SP-PRVCY"), ("lone line", "  CU" + "I  "), ("long form", "Controlled Unclassified " + "Information"),
                        ("old mark", "UNCLASSIFIED/" + "/FO" + "UO"), ("old mark, long form", "For Official Use " + "Only"),
                        ("dissemination", "NOF" + "ORN"), ("classification banner", "TOP SECRET/" + "/SI")):
        expect("dod marking: " + label, text, ["marking"], dod=True)
    for label, text in (("in brackets", "(CU" + "I)"), ("bold", "**CU" + "I**"), ("heading", "# CU" + "I"),
                        ("bare banner", "TOP SEC" + "RET"), ("bare banner, one word", "  SEC" + "RET  ")):
        expect("dod marking: " + label, text, ["marking"], dod=True)
    for label, text in (("title-case banner with slashes", "Top Sec" + "ret/" + "/SI"), ("lower-case word with slashes", "sec" + "ret/" + "/rel"),
                        ("two-word banner, title case", "Top Sec" + "ret"), ("lowest level alone on a line", "UNCLASS" + "IFIED")):
        expect("dod marking: " + label, text, ["marking"], dod=True)
    expect("dod: a one-word heading in title case is not a mark", "# Sec" + "ret", [], dod=True)
    expect("dod: the word in a sentence, upper case, is not a banner", "THE SEC" + "RET IS OUT", [], dod=True)
    expect("minimum tier: marks not checked", "CU" + "I//SP-PRVCY", [])
    expect("dod: the acronym inside a sentence is not a mark", "the CU" + "I program office", [], dod=True)
    expect("dod: the word secret alone is not a mark", "a secret in the settings", [], dod=True)
    expect("dod id: keyword and 10 digits", "DoD ID: 12345" + "67890", ["dodid"], dod=True)
    expect("dod id: EDIPI", "EDIPI 12345" + "67890", ["dodid"], dod=True)
    expect("dod id: number, then keyword", "12345" + "67890 (DoD ID)", ["dodid"], dod=True)
    for label, text in (("underscore name", "dod_id=12345" + "67890"), ("underscore name, colon", "dod_id: 12345" + "67890"),
                        ("joined to the number", "DODID12345" + "67890"), ("wide space", "DoD   ID 12345" + "67890")):
        expect("dod id: " + label, text, ["dodid"], dod=True)
    expect("dod id: 11 digits are not an ID", "EDIPI 12345" + "678901", [], dod=True)


def case_dod_split_lines():
    """A phrase mark, or a DoD ID keyword and its number, over two lines in a row: found in the DoD tier only, reported
    at the first line, allowed by its text; a blank line between the lines, or a third line, is not joined."""
    for label, text in (("short form, after FOR", "FOR\nOFFICIAL USE ONLY"), ("short form, after OFFICIAL", "FOR OFFICIAL\nUSE ONLY"),
                        ("short form, before ONLY", "for official use\nonly"), ("blanks at the break", "For Official  \n   Use Only"),
                        ("long form", "Controlled Unclassified\nInformation"), ("long form, after the first word", "Controlled\nUnclassified Information")):
        expect("dod marking over two lines: " + label, text, ["marking"], dod=True)
    split = scan_text("x\nFOR OFFICIAL\nUSE ONLY\ny", "t", [], set(), True)
    check(f"dod marking over two lines: one finding, on the first line: {split}", [(n, k) for _, n, k, _ in split] == [(2, "marking")])
    expect("minimum tier: a mark over two lines is not checked", "FOR OFFICIAL\nUSE ONLY", [])
    expect("dod: a mark over two lines, allowed as read", "FOR OFFICIAL\nUSE ONLY", [], allow=["FOR OFFICIAL " + "USE ONLY"], dod=True)
    expect("dod: a mark over three lines is not read", "FOR OFFICIAL\nUSE\nONLY", [], dod=True)
    expect("dod: words that only start a mark are not a mark", "FOR OFFICIAL\nBUSINESS ONLY", [], dod=True)
    expect("dod: a mark over two lines, with words before the break", "the FOR OFFICIAL\nUSE ONLY rule", ["marking"], dod=True)
    expect("dod: a mark inside a word is not a mark", "BEFOR OFFICIAL\nUSE ONLY", [], dod=True)
    expect("dod marking over two lines: a blank line between the lines is a paragraph break, not joined", "FOR OFFICIAL\n\nUSE ONLY", [], dod=True)
    for label, text in (("keyword, then number", "DoD ID:\n12345" + "67890"), ("number, then keyword", "12345" + "67890\n(EDIPI)"),
                        ("blanks at the break", "EDIPI   \n   12345" + "67890")):
        expect("dod id over two lines: " + label, text, ["dodid"], dod=True)
    split = scan_text("x\nDoD ID\n12345" + "67890\ny", "t", [], set(), True)
    check(f"dod id over two lines: one finding, on the first line: {split}", [(n, k) for _, n, k, _ in split] == [(2, "dodid")])
    expect("minimum tier: an ID over two lines is not checked", "EDIPI\n12345" + "67890", [])
    expect("dod id over two lines: the number allowed", "EDIPI\n12345" + "67890", [], allow=["12345" + "67890"], dod=True)
    expect("dod id over two lines: a blank line between the lines is not joined", "EDIPI\n\n12345" + "67890", [], dod=True)
    expect("dod id over two lines: three lines are not read", "EDIPI\nnote\n12345" + "67890", [], dod=True)
    expect("dod id over two lines: 9 digits are not an ID", "EDIPI\n123456789", [], dod=True)
    expect("dod id over two lines: no keyword", "ref\n12345" + "67890", [], dod=True)


def case_profile_lines():
    """The tier line: accepted forms, unknown forms, and no slow match on long or odd lines."""
    good = profile_of({"Profile: DoD"}) == profile_of({"profile:dod"}) == profile_of({"profile :  dod"}) == "dod" \
        and profile_of({"profile: dodd"}) == profile_of({"profile: dod", "profile: min"}) == profile_of({"profile:"}) == "unknown" \
        and profile_of({"profile: d o d"}) == profile_of({"profile = dod"}) == profile_of({"profile dod"}) == "unknown" \
        and profile_of({"profil: dod"}) == profile_of({"tier=dod"}) == profile_of({"profile"}) == "unknown" \
        and all(profile_of({v}) == "unknown" for v in ("profile：dod", "- profile: dod", "* profile: dod", '"profile: dod"',
                                                         "[profile: dod]", "$profile: dod", "profile; dod", "profile - dod",
                                                         "profile dod", "tier; dod", "'profile:dod'")) \
        and profile_of({"denylist: warn", "x", "profile.example.org", "profile-x", "profile/x", "host.dod", "a.dod",
                        "skip: a/dod", "skip: profile dod", "skip: dod", "skip:dod"}) == "minimum"
    check("profile line: any case, spacing around the colon; any other form is unknown", good)
    slow = 0.0  # no line, however long or odd, may make the option-line patterns slow
    hostile = [c * 100_000 + tail for c in "-_a. \t" for tail in ("", " dod", "dod")]
    hostile += ["a" + " " * 100_000, "- " + " " * 100_000 + "x", "a" + " " * 50_000 + "dod" + " " * 50_000 + "x",
                "profile" + " " * 100_000 + ": dod", "a" * 39 + ":" + " " * 100_000 + "dod"]
    hostile += [h[:n] for h in list(hostile) for n in (OPTION_MAX, OPTION_MAX - 1)]  # the longest lines the patterns see
    good = True
    for h in hostile:
        t0 = time.process_time()
        good = profile_of({h}) != "dod" and is_option_line(h) in (True, False) and good
        slow = max(slow, time.process_time() - t0)
    check(f"option lines: {len(hostile)} long or odd lines, the slowest read in {slow:.3f} s", good and slow < 1)
    expect("dod id: a longer word that starts like the keyword is not one", "dodidentifier 12345" + "67890", [], dod=True)


def case_denylist_and_fingerprint():
    """DoD IDs without a keyword, DoD masks, the fingerprint, and the denylist sources."""
    expect("dod: 10 digits with no keyword", "ts 17312" + "34567", [], dod=True)
    expect("minimum tier: DoD ID not checked", "EDIPI 12345" + "67890", [])
    good = mask("milhost", mil) == f"<{len(mil)} chars>" and mask("dodid", "12345" + "67890") == "********90"
    check("dod: hosts print as a length, IDs as the last 2 digits", good)
    good = fingerprint(parse_denylist("Alex, Sam,River")) == fingerprint(parse_denylist("river\nSAM\nalex\nAlex")) \
        and fingerprint(["Alex"]) != fingerprint(["Sam"]) and re.fullmatch(r"[0-9a-f]{8}", fingerprint(["Alex"]))
    check("fingerprint: same list in any order, case or separator; other list differs", bool(good))
    saved = {k: os.environ.pop(k, None) for k in ("PII_GUARD_DENYLIST", "PII_GUARD_DENYLIST_FILE")}
    try:
        os.environ["PII_GUARD_DENYLIST_FILE"] = os.devnull + ".missing"
        good = load_denylist() == [] and denylist_source()[1] is None
        os.environ["PII_GUARD_DENYLIST"] = "Alex,  Sam\n# note\nRiver"
        good = good and load_denylist() == ["Alex", "Sam", "River"] and "environment" in denylist_source()[1]
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    good = good and parse_denylist("<Alex>, 'Sam' ,\"River\",<>,<a>,--") == ["Alex", "Sam", "River"]
    check("denylist source: none, then environment (comma and newline); <Name> wrappers dropped", good)


def case_cli_denylist(d, env):
    """CLI: the denylist file, --push with no denylist, and `denylist: warn` (minimum and DoD tier).

    Args:
        d: a temporary folder (the sample repo).
        env: the environment for the git and CLI runs.
    """
    f = pathlib.Path(d, "deny.txt")
    f.write_text("Alex\n")
    env["PII_GUARD_DENYLIST_FILE"] = str(f)
    env["PII_GUARD_DENYLIST"] = "# only a comment"
    r = subprocess.run(ME + ["--status"], env=env, capture_output=True, text=True)
    good = r.returncode == 0 and "1 entries from file" in r.stdout and "Alex" not in r.stdout
    check("comment-only env var does not shadow the file; status hides names", good)
    env["PII_GUARD_DENYLIST_FILE"] = str(f) + ".missing"
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d, check=True, capture_output=True)
    z = "0" * 40
    r = subprocess.run(ME + ["--push", "--require-denylist"], cwd=d, env=env, capture_output=True, text=True,
                       input=f"refs/heads/main {'1' * 40} refs/heads/main {z}\n")
    check("push with no denylist: blocked", r.returncode == 1 and "no denylist" in r.stdout)
    r = subprocess.run(ME + ["--push", "--require-denylist"], cwd=d, env=env, capture_output=True, text=True,
                       input=f"(delete) {z} refs/heads/x {'1' * 40}\n")
    check("branch delete with no denylist: passes", r.returncode == 0)
    pathlib.Path(d, ".pii-guard").write_text("# starter\ndenylist: warn\n")
    r = guard(d, env, "--all", "--require-denylist")
    good = r.returncode == 0 and "WARNING" in r.stdout and warn_mode(d)
    pathlib.Path(d, "a.txt").write_text("mail bob" + at + "corp" + dot + "io\n")
    subprocess.run(["git", "add", "a.txt"], cwd=d, check=True, capture_output=True)
    r = guard(d, env, "--all", "--require-denylist")
    check("denylist: warn: no denylist only warns; an email still blocks", good and r.returncode == 1)
    pathlib.Path(d, "a.txt").write_text("clean\n")
    pathlib.Path(d, ".pii-guard").write_text("denylist: warn\nprofile: dod\n")
    r = guard(d, env, "--all", "--require-denylist")
    good = r.returncode == 1 and "no denylist" in r.stdout and dod_mode(d) and not warn_mode(d)
    check("dod: no denylist blocks although the file says denylist: warn", good)


def case_cli_profile(d, env):
    """CLI: an unknown tier line, a byte-order mark, a wrong encoding and a zero-width space in .pii-guard.

    Args:
        d: a temporary folder (the sample repo).
        env: the environment for the git and CLI runs.
    """
    env["PII_GUARD_DENYLIST"] = "Alex"
    pathlib.Path(d, ".pii-guard").write_text("profile: DOD-tier\n")
    r = guard(d, env, "--all")
    r2 = guard(d, env, "--status")
    good = r.returncode == 1 and "CONTENT CHECK FAIL: unknown profile" in r.stdout and r2.returncode == 1 \
        and "UNKNOWN" in r2.stdout and dod_mode(d) and not warn_mode(d)
    check("unknown profile value: the scan and --status fail (no fall back to minimum)", good)
    pathlib.Path(d, ".pii-guard").write_bytes(b"\xef\xbb\xbfprofile: dod\r\n")
    r = guard(d, env, "--status")
    subprocess.run(["git", "add", ".pii-guard"], cwd=d, check=True, capture_output=True)
    staged = load_allow(d, ":0")  # the same file read through git, as --allow-from does
    good = r.returncode == 0 and "profile: dod" in r.stdout and dod_mode(d) and profile_of(staged) == "dod"
    subprocess.run(["git", "rm", "-q", "--cached", ".pii-guard"], cwd=d, check=True, capture_output=True)
    check("tier line after a byte-order mark, with CRLF: DoD tier (file and git read)", good)
    cases = {"UTF-16 with a byte-order mark": "profile: dod\n".encode("utf-16"), "UTF-16, no mark": "profile: dod\n".encode("utf-16-le"),
             "bytes that are not UTF-8": b"# note \xc3(\n", "a NUL byte": b"x\0y\n"}
    for label, raw in cases.items():
        pathlib.Path(d, ".pii-guard").write_bytes(raw)
        r = guard(d, env, "--all")
        subprocess.run(["git", "add", ".pii-guard"], cwd=d, check=True, capture_output=True)
        good = r.returncode == 1 and "CONTENT CHECK FAIL: unknown profile" in r.stdout and "Traceback" not in r.stderr \
            and profile_of(load_allow(d, ":0")) == "unknown"
        subprocess.run(["git", "rm", "-q", "--cached", ".pii-guard"], cwd=d, check=True, capture_output=True)
        check(f".pii-guard with {label}: the scan fails (file and git read)", good)
    pathlib.Path(d, ".pii-guard").write_text("\u200bprofile: dod\n", encoding="utf-8")
    check("tier line after a zero-width space: DoD tier", profile_of(load_allow(d)) == "dod")
    pathlib.Path(d, ".pii-guard").write_text("denylist: warn\nProfile:DoD\n")
    r = guard(d, env, "--status")
    good = r.returncode == 0 and "fingerprint " + fingerprint(["alex"]) in r.stdout and "profile: dod" in r.stdout
    check("status: fingerprint and profile", good)


def case_cli_dod_files(d, env):
    """DoD tier on files and commits: a PDF, a binary file, a host and a file over the size limit block; skip clears.

    Args:
        d: a temporary folder (the sample repo).
        env: the environment for the git and CLI runs.
    """
    pathlib.Path(d, "doc.pdf").write_bytes(b"%PDF-1.4 x")
    pathlib.Path(d, "blob.dat").write_bytes(b"a\0b")
    pathlib.Path(d, "notes.txt").write_text("see " + mil + "\n")
    subprocess.run(["git", "add", "a.txt", "doc.pdf", "blob.dat", "notes.txt"], cwd=d, check=True, capture_output=True)
    r = guard(d, env, "--all")
    good = r.returncode == 1 and r.stdout.count("unscanned") == 2 and "milhost" in r.stdout and "profile dod" in r.stdout \
        and mil not in r.stdout
    check("dod --all: a PDF, a binary file and a host block", good)
    pathlib.Path(d, ".pii-guard").write_text("profile: dod\nskip: doc.pdf\nskip: blob.dat\n" + mil + "\n")
    check("dod --all: skip lines and an allowed host clear them", guard(d, env, "--all").returncode == 0)
    pathlib.Path(d, ".pii-guard").write_text("# minimum\n")
    r = guard(d, env, "--all")
    check("minimum --all: the same files pass", r.returncode == 0 and "profile minimum" in r.stdout)
    idn = ["-c", "user.name=t", "-c", "user.email=1+t" + at + "users.noreply.github" + dot + "com"]
    subprocess.run(["git", *idn, "commit", "-q", "-m", "files"], cwd=d, check=True, capture_output=True)
    found, _ = scan_commits(["HEAD"], d, [], set(), dod=True)
    got = sorted((w.split()[-1], k) for w, _, k, _ in found)
    good = got == [("blob.dat", "unscanned"), ("doc.pdf", "unscanned"), ("notes.txt", "milhost")]
    found, _ = scan_commits(["HEAD"], d, [], {"skip: doc.pdf", "skip: blob.dat", mil}, dod=True)
    good = good and found == [] and scan_commits(["HEAD"], d, [], set())[0] == []
    check(f"dod commits: binary and PDF files block; skip clears; minimum passes: {got}", good)
    pathlib.Path(d, "big.txt").write_text("clean line\n" * (MAX_BYTES // 11 + 10))
    subprocess.run(["git", "add", "big.txt"], cwd=d, check=True, capture_output=True)
    subprocess.run(["git", *idn, "commit", "-q", "-m", "big"], cwd=d, check=True, capture_output=True)
    found, _ = scan_commits(["HEAD~1..HEAD"], d, [], set(), dod=True)
    good = [(w.split()[-1], k) for w, _, k, _ in found] == [("big.txt", "unscanned")] \
        and scan_commits(["HEAD~1..HEAD"], d, [], {"skip: big.txt"}, dod=True)[0] == [] \
        and scan_commits(["HEAD~1..HEAD"], d, [], {f"content-max-bytes: {MAX_BYTES * 2}"}, dod=True)[0] == [] \
        and max_bytes_of({"content-max-bytes: 10"}) == MAX_BYTES and max_bytes_of({"content-max-bytes: x"}) == MAX_BYTES \
        and max_bytes_of({"content-max-bytes: 999999999"}) == MAX_BYTES and not is_tier_line("content-max-bytes: 8000000") \
        and profile_of({"content-x: dod"}) == "unknown"
    check("dod commits: a text file over the size limit blocks; skip or content-max-bytes clears", good)


def case_cli():
    """The CLI cases above, in one temporary repo (each case builds on the state the one before it left)."""
    with tempfile.TemporaryDirectory() as d:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PII_GUARD", "GIT_"))}
        case_cli_denylist(d, env)
        case_cli_profile(d, env)
        case_cli_dod_files(d, env)


def commit_env():
    """Environment for test commits: a noreply identity named Sam, and no host git settings."""
    env = {**os.environ, "GIT_AUTHOR_NAME": "Sam", "GIT_COMMITTER_NAME": "Sam",
           "GIT_AUTHOR_EMAIL": "1+s" + at + "users.noreply.github" + dot + "com",
           "GIT_COMMITTER_EMAIL": "1+s" + at + "users.noreply.github" + dot + "com"}
    for k in [k for k in env if k.startswith("GIT_") and k not in (
            "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL")]:
        env.pop(k)
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def case_commit_range(d, run_git):
    """Commit scan: a range finds the added line and the message; an added '++ ' line is content.

    Args:
        d: a temporary folder (the sample repo).
        run_git: runs one git command in d.

    Returns:
        The commit in the middle of the sample history (a later case scans from it).
    """
    run_git("init", "-q", "-b", "main")
    pathlib.Path(d, "a.txt").write_text("clean\n")
    run_git("add", ".")
    run_git("commit", "-q", "-m", "clean")
    base = git("rev-parse", "HEAD", root=d).strip()
    pathlib.Path(d, "a.txt").write_text("clean\nmail bob" + at + "corp" + dot + "io\n")
    run_git("add", ".")
    run_git("commit", "-q", "-m", "ask Alexandra")
    found, n = scan_commits([f"{base}..HEAD"], d, ["Alexandra"], set())
    kinds_found = sorted(k for _, _, k, _ in found)
    check(f"commit range: {n} commit(s), {kinds_found}", n == 1 and kinds_found == ["email", "name"])
    mid = git("rev-parse", "HEAD", root=d).strip()
    pathlib.Path(d, "a.txt").write_text("clean\nmail bob" + at + "corp" + dot + "io\n++ x\nmail sue" + at + "corp" + dot + "io\n")
    run_git("add", ".")
    run_git("commit", "-q", "-m", "plus lines")
    found, _ = scan_commits([f"{mid}..HEAD"], d, [], {"skip: x"})
    good = [k for _, _, k, _ in found] == ["email"] and all(" a.txt" in w for w, _, _, _ in found)
    check(f"added '++ ' line is content, not a file header: {[k for _, _, k, _ in found]}", good)
    return mid


def case_commit_merge_push(d, run_git, env, mid):
    """Commit scan: a merge commit keeps its file names, the author email is scanned, and pre-push lines parse.

    Args:
        d: a temporary folder (the sample repo).
        run_git: runs one git command in d.
        env: the environment for the git and CLI runs.
        mid: the commit case_commit_range gives.
    """
    run_git("checkout", "-q", "-b", "side", mid)
    pathlib.Path(d, "c.txt").write_text("side\n")
    run_git("add", ".")
    run_git("commit", "-q", "-m", "side")
    run_git("checkout", "-q", "main")
    pathlib.Path(d, "c.txt").write_text("main\n")
    run_git("add", ".")
    run_git("commit", "-q", "-m", "main c")
    subprocess.run(["git", "merge", "-q", "side"], cwd=d, env=env, capture_output=True)
    pathlib.Path(d, "c.txt").write_text("both\nmail ann" + at + "corp" + dot + "io\n")
    run_git("add", ".")
    run_git("commit", "-q", "-m", "merge side")
    found_skip, _ = scan_commits(["HEAD~1..HEAD"], d, [], {"skip: c.txt"})
    found_all, _ = scan_commits(["HEAD~1..HEAD"], d, [], set())
    good = found_skip == [] and [(w.split()[-1], k) for w, _, k, _ in found_all] == [("c.txt", "email")]
    check(f"merge commit (diff --cc): file name kept, skip rule applies: {len(found_skip)}, {len(found_all)}", good)
    env["GIT_AUTHOR_EMAIL"] = "me" + at + "home" + dot + "net"
    run_git("commit", "-q", "--allow-empty", "-m", "x")
    found, _ = scan_commits(["HEAD~1..HEAD"], d, [], set())
    check(f"author email: {[k for _, _, k, _ in found]}", [k for _, _, k, _ in found] == ["email"])
    z = "0" * 40
    head = git("rev-parse", "HEAD", root=d).strip()
    revs = push_revs(f"refs/heads/main {head} refs/heads/main {z}\n(delete) {z} refs/heads/x {head}\n", d)
    check(f"push lines: {revs}", revs == [[head, "--not", "--remotes"]])


def case_commits():
    """The commit-scan cases above, in one temporary repo."""
    with tempfile.TemporaryDirectory() as d:
        env = commit_env()

        def run_git(*a):
            """Run one git command in the temporary test repo."""
            return subprocess.run(["git", *a], cwd=d, env=env, check=True, capture_output=True)

        mid = case_commit_range(d, run_git)
        case_commit_merge_push(d, run_git, env, mid)


def hook_cases(d, mail, key_pem):
    """The sample files and the (name, CLI args, input, wanted exit) cases for --hook, --stdin and named files.

    Args:
        d: a temporary folder (the sample repo).
        mail: a sample address, built at run time.
        key_pem: a sample private key header, built at run time.

    Returns:
        The list of cases.
    """
    pathlib.Path(d, "page.html").write_text("<p>" + mail + "</p>")
    pathlib.Path(d, "clean.html").write_text("<p>hello</p>")
    pathlib.Path(d, "a.pdf").write_bytes(b"%PDF-1.4 fake")
    pathlib.Path(d, "run.html").write_text("a1" * 100_000)  # 200 KB, one line, no "@"
    return [
        ("hook: clean Agent prompt passes", ["--hook"], {"tool_name": "Agent", "cwd": d, "tool_input": {"prompt": "fix the bug"}}, 0),
        ("hook: email in an Agent prompt blocks", ["--hook"], {"tool_name": "Agent", "cwd": d, "tool_input": {"prompt": "mail " + mail}}, 2),
        ("hook: email in a nested list blocks", ["--hook"], {"tool_name": "x", "cwd": d, "tool_input": {"a": [{"b": mail}]}}, 2),
        ("hook: file named by file_path is read", ["--hook"], {"tool_name": "Artifact", "cwd": d, "tool_input": {"file_path": "page.html"}}, 2),
        ("hook: clean file passes", ["--hook"], {"tool_name": "Artifact", "cwd": d, "tool_input": {"file_path": "clean.html"}}, 0),
        ("hook: files map source {from} is read", ["--hook"], {"tool_name": "Artifact", "cwd": d, "tool_input": {
            "file_path": "clean.html", "files": {"p/x.html": {"from": os.path.join(d, "page.html")}}}}, 2),
        ("hook: file_paths list is read", ["--hook"], {"tool_name": "SendUserFile", "cwd": d,
                                                      "tool_input": {"file_paths": ["clean.html", "page.html"]}}, 2),
        ("hook: bad JSON blocks", ["--hook"], "{not json", 2),
        ("hook: the project's DoD tier holds with a cwd outside it", ["--hook"],
         {"tool_name": "Agent", "cwd": "/", "tool_input": {"prompt": "see " + "x" + dot + "af" + dot + "mi" + "l"}}, "dod"),
        ("hook: a crash blocks (deep nesting)", ["--hook"], '{"tool_input": {"prompt": "x", "a": ' + "[" * 3000 + "]" * 3000 + "}}", 2),
        ("hook: a crash blocks (cwd of a wrong type)", ["--hook"], {"tool_name": "Agent", "cwd": 5, "tool_input": {"prompt": "x"}}, 2),
        ("hook: mail recipients are not scanned, the body is", ["--hook"],
         {"tool_name": "mcp__Gmail__send_message", "cwd": d, "tool_input": {"to": [mail], "cc": mail, "subject": "hi", "body": "fix the bug"}}, 0),
        ("hook: a private key in a mail recipient field blocks", ["--hook"],
         {"tool_name": "mcp__Gmail__send_message", "cwd": d, "tool_input": {"to": [mail, key_pem]}}, 2),
        ("hook: a 'to' key in a non-mail tool is scanned", ["--hook"],
         {"tool_name": "mcp__Claude_Docs__batch", "cwd": d, "tool_input": {"blocks": {"to": mail}}}, 2),
        ("hook: a nested 'to' key in a mail call is scanned", ["--hook"],
         {"tool_name": "mcp__Gmail__send_message", "cwd": d, "tool_input": {"body": {"to": mail}}}, 2),
        ("hook: a long run with no @ ends fast and passes", ["--hook"], {"tool_name": "Artifact", "cwd": d, "tool_input": {"file_path": "run.html"}}, 0),
        ("hook: named files over the size cap block", ["--hook"],
         {"tool_name": "SendUserFile", "cwd": d, "tool_input": {"file_paths": ["clean.html", "run.html"]}}, "cap"),
        ("hook: a missing file_path blocks", ["--hook"], {"tool_name": "Artifact", "cwd": d, "tool_input": {"file_path": "no-such.html"}}, 2),
        ("hook: an address in a mail body blocks", ["--hook"],
         {"tool_name": "mcp__Gmail__send_message", "cwd": d, "tool_input": {"to": [mail], "body": "write to " + mail}}, 2),
        ("hook: a named file it cannot scan blocks (minimum tier)", ["--hook"],
         {"tool_name": "SendUserFile", "cwd": d, "tool_input": {"file_paths": ["a.pdf"]}}, 2),
        ("file: a named file it cannot scan fails (minimum tier)", [os.path.join(d, "a.pdf")], "", 1),
        ("stdin: email fails", ["--stdin"], "brief: " + mail, 1),
        ("stdin: clean passes", ["--stdin"], "brief: fix the bug", 0),
        ("file: missing path fails", [os.path.join(d, "no-such.md")], "", 1),
        ("file: /dev/stdin is not a regular file: fails", ["/dev/stdin"], "x " + mail, 1),
    ]


def run_hook_in_process(d, text, want):
    """Run the hook in this process (a new Python per case would double the test time); return (exit, stderr, want).
    want "cap" lowers the size cap for the case; want "dod" makes d a DoD-tier project for the case.

    Args:
        d: a temporary folder (the sample repo).
        text: the hook input.
        want: the wanted exit code, or "cap" or "dod" (see above).

    Returns:
        (exit code, stderr text, the wanted exit code).
    """
    if want == "dod":  # a DoD-tier project folder for this case only
        pathlib.Path(d, ".pii-guard").write_text("profile: dod\n")
        subprocess.run(["git", "init", "-q"], cwd=d, capture_output=True)
    cap = check_content.HOOK_MAX_BYTES
    check_content.HOOK_MAX_BYTES = 150_000 if want == "cap" else cap
    err, t0 = io.StringIO(), time.process_time()  # CPU time of this process, as in case_speed
    try:
        with contextlib.redirect_stderr(err):
            code = check_content.hook(text)
    finally:
        check_content.HOOK_MAX_BYTES = cap
    out = err.getvalue()
    if want == "dod":
        pathlib.Path(d, ".pii-guard").unlink()
    want = 2 if want in ("cap", "dod") else want
    if time.process_time() - t0 > 5:
        out += " too slow"
        code = -1
    return code, out, want


def case_hook():
    """--hook, --stdin and named files (2026-11-16): a wrong path or bad hook input must never pass."""
    with tempfile.TemporaryDirectory() as d:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PII_GUARD_DENYLIST")}
        env["PII_GUARD_DENYLIST_FILE"] = os.path.join(d, "none.txt")
        mail = "jane" + at + "corp" + dot + "io"
        cases = hook_cases(d, mail, "-----BEGIN RSA " + "PRIVATE KEY-----")
        saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("PII_GUARD_DENYLIST") or k == "CLAUDE_PROJECT_DIR"}
        os.environ["PII_GUARD_DENYLIST_FILE"] = env["PII_GUARD_DENYLIST_FILE"]
        os.environ["CLAUDE_PROJECT_DIR"] = d
        try:
            for name, args, data, want in cases:
                text = data if isinstance(data, str) else json.dumps(data)
                if args == ["--hook"]:
                    code, out, want = run_hook_in_process(d, text, want)
                else:
                    r = subprocess.run(ME + args, cwd=d, env=env, input=text, capture_output=True, text=True)
                    code, out = r.returncode, r.stdout + r.stderr
                check(f"{name} (exit {code})", code == want and mail not in out)  # findings stay masked
        finally:
            os.environ.pop("PII_GUARD_DENYLIST_FILE", None)
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            os.environ.update(saved)


# ---------------------------------------------------------------- blocks, terms, gates, pool ------------------------

def case_terms():
    """The Administrator's terms: whole word, any case, masked, kind term; a name stays a name; an allowed string wins."""
    check("term: found as a whole word, any case", kinds("the BLUEBIRD plan", terms=["bluebird"]) == ["term"])
    check("term: not inside another word", kinds("bluebirds fly", terms=["bluebird"]) == [])
    check("term and name in one line keep their kinds", kinds("Alex and Bluebird", ["Alex"], terms=["Bluebird"]) == ["name", "term"])
    check("a word in both lists is a name", kinds("Alex", ["Alex"], terms=["alex"]) == ["name"])
    check("term: inside an allowed string passes", kinds("Bluebird Cafe", allow={"Bluebird Cafe"}, terms=["Bluebird"]) == [])
    found = scan_text("the Bluebird plan", "t", [], set(), False, ["Bluebird"])
    check("term: the finding is masked", found and "Bluebird" not in found[0][3])
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d, "terms.txt")
        f.write_text("# clients\nBluebird\n")
        old = {k: os.environ.get(k) for k in ("CHECK_TERMS", "CHECK_TERMS_FILE")}
        os.environ["CHECK_TERMS_FILE"] = str(f)
        try:
            check("terms: read from the file", load_terms() == ["Bluebird"])
            os.environ["CHECK_TERMS"] = "Osprey, Kestrel"
            check("terms: the environment variable comes first", load_terms() == ["Osprey", "Kestrel"])
            env = {k: v for k, v in os.environ.items() if not k.startswith(("PII_GUARD", "GIT_"))}
            env["PII_GUARD_DENYLIST_FILE"] = str(f) + ".missing"
            r = subprocess.run(ME + ["--stdin"], input="the osprey plan", env=env, capture_output=True, text=True, cwd=d)
            check("terms: the CLI blocks a term and hides it", r.returncode == 1 and "term" in r.stdout
                  and "2 terms checked" in r.stdout and "osprey" not in r.stdout.lower().replace("the osprey plan", ""))
            env["PII_GUARD_DENYLIST"] = "Alex"
            r = subprocess.run(ME + ["--status"], env=env, capture_output=True, text=True, cwd=d)
            check("terms: --status prints the count, never the words", "terms: 2 entries" in r.stdout and "Osprey" not in r.stdout)
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def case_block_lines():
    """`block:` lines: a glob, a file-name glob in any folder, a folder; bare stars are ignored; block wins over skip."""
    allow = {"block: *.xlsx", "block: exports/", "block: data/raw-*.csv", "block: *", "skip: exports/"}
    for path, want in (("a.xlsx", True), ("deep/dir/b.xlsx", True), ("exports/x.txt", True), ("data/raw-1.csv", True),
                       ("data/clean.csv", False), ("notes.md", False), ("xlsx", False), ("Deep/B.XLSX", True),
                       ("EXPORTS/x.txt", True)):
        check(f"block: {path}: {'blocked' if want else 'passes'}", blocked(path, allow) is want)
    with tempfile.TemporaryDirectory() as d:
        pathlib.Path(d, "exports").mkdir()
        pathlib.Path(d, "exports", "x.txt").write_text("clean\n")
        pathlib.Path(d, "ok.txt").write_text("clean\n")
        got = [(p, k) for p, _, k, _ in scan_files(["exports/x.txt", "ok.txt"], d, [], allow)]
        check("block: a blocked file is a finding although a skip line names it", got == [("exports/x.txt", "blocked")])


def git_run(d, *args):
    """Run git in d with a fixed noreply identity and no host settings."""
    env = {**os.environ, "GIT_AUTHOR_NAME": "Sam", "GIT_COMMITTER_NAME": "Sam",
           "GIT_AUTHOR_EMAIL": "sam" + at + "users.noreply.github.com",
           "GIT_COMMITTER_EMAIL": "sam" + at + "users.noreply.github.com"}
    return subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=d, env=env, capture_output=True, text=True, check=True)


def case_check_file():
    """The settings file is `.check`; `.pii-guard` is read only when `.check` is absent; a commit of a blocked file fails."""
    with tempfile.TemporaryDirectory() as d:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PII_GUARD", "GIT_"))}
        env["PII_GUARD_DENYLIST"] = "Alex"
        git_run(d, "init", "-q", "-b", "main")
        check("no settings file: none", config_name(d) is None and load_allow(d) == set())
        pathlib.Path(d, ".pii-guard").write_text("old-allowed\n")
        check("only .pii-guard: it is read", config_name(d) == ".pii-guard" and load_allow(d) == {"old-allowed"})
        pathlib.Path(d, ".check").write_text("# settings\nblock: *.xlsx\nprofile: dod\n")
        check("both files: .check is read, and the scan fails until .pii-guard is gone",
              config_name(d) == ".check" and profile_of(load_allow(d)) == "unknown")
        r = subprocess.run(ME + ["--stdin"], input="clean", env=env, capture_output=True, text=True, cwd=d)
        check("both files: the CLI fails and says what to do", r.returncode == 1 and "delete it" in r.stdout)
        pathlib.Path(d, ".pii-guard").unlink()
        check("only .check: its lines are read", load_allow(d) == {"block: *.xlsx", "profile: dod"})
        r = subprocess.run(ME + ["--status"], env=env, capture_output=True, text=True, cwd=d)
        check(".check: `block:` is no tier line; the tier line is read", "profile: dod" in r.stdout)
        pathlib.Path(d, ".check").write_text("block: *.xlsx\n")
        git_run(d, "add", ".check")
        git_run(d, "commit", "-q", "-m", "settings")
        base = git_run(d, "rev-parse", "HEAD").stdout.strip()
        check(".check at a git ref is read", load_allow(d, base) == {"block: *.xlsx"})
        pathlib.Path(d, "sub").mkdir()
        pathlib.Path(d, "sub", "list.xlsx").write_text("not a real sheet\n")
        git_run(d, "add", "-A")
        git_run(d, "commit", "-q", "-m", "add a sheet")
        r = subprocess.run(ME + ["--range", base + "..HEAD"], env=env, capture_output=True, text=True, cwd=d)
        check("a commit that adds a blocked file fails", r.returncode == 1 and "blocked" in r.stdout)
        r = subprocess.run(ME + ["--all"], env=env, capture_output=True, text=True, cwd=d)
        check("a tracked blocked file fails --all", r.returncode == 1 and "sub/list.xlsx:0: blocked" in r.stdout)
        git_run(d, "rm", "-q", "sub/list.xlsx")
        git_run(d, "commit", "-q", "-m", "remove the sheet")
        r = subprocess.run(ME + ["--all"], env=env, capture_output=True, text=True, cwd=d)
        check("after its removal --all passes", r.returncode == 0)


def run_hook_tool(d, tool, tool_input):
    """Run the hook in this process for one tool call in project d; return its exit code."""
    with contextlib.redirect_stderr(io.StringIO()):
        return check_content.hook(json.dumps({"tool_name": tool, "cwd": d, "tool_input": tool_input}))


def _hook_cases(mail, d):
    """Return test cases (name, tool, input, expected_exit) for hook tool testing.

    Args:
        mail: sample email address string.
        d: temporary directory path.

    Returns:
        List of tuples: (name, tool, inp, want_code).
    """
    return [
        ("Write: clean text to a new file passes", "Write", {"file_path": "new.md", "content": "hello"}, 0),
        ("Write: an address in the content blocks", "Write", {"file_path": "new.md", "content": "mail " + mail}, 2),
        ("Write: a blocked path blocks", "Write", {"file_path": os.path.join(d, "out", "a.xlsx"), "content": "x"}, 2),
        ("Edit: an address in the new text blocks", "Edit", {"file_path": "a.md", "old_string": "x", "new_string": mail}, 2),
        ("Edit: an address only in the old text passes (the edit removes it)",
         "Edit", {"file_path": "a.md", "old_string": mail, "new_string": "the Administrator"}, 0),
        ("NotebookEdit: an address in the new source blocks", "NotebookEdit", {"notebook_path": "n.ipynb", "new_source": mail}, 2),
        ("Bash: a local command with an address passes unread", "Bash", {"command": "grep -rn '" + mail + "' ."}, 0),
        ("Bash: curl with an address blocks", "Bash", {"command": "curl -d 'to=" + mail + "' https://example.com"}, 2),
        ("Bash: git commit with an address blocks", "Bash", {"command": "git -C . commit -m 'thanks " + mail + "'"}, 2),
        ("Bash: gh with a clean text passes", "Bash", {"command": "gh pr view 5"}, 0),
        ("Bash: a URL with a clean text passes", "Bash", {"command": "python3 fetch.py https://example.com/x"}, 0),
        ("Bash: a word that only holds 'gh' is local", "Bash", {"command": "echo high " + mail}, 0),
        ("Bash: a command of a wrong type is scanned and passes", "Bash", {"command": 5}, 0),
        ("Write: a path-form block line blocks", "Write", {"file_path": "data/x.csv", "content": "x"}, 2),
        ("Write: new text is scanned also under a skip line", "Write", {"file_path": "ref/a.md", "content": mail}, 2),
        ("Bash: git commit after a line continuation blocks", "Bash", {"command": "git -C /p \\\n commit -m " + mail}, 2),
        ("Bash: a client name split by a line continuation blocks",
         "Bash", {"command": "cu\\\nrl -d " + mail + " h; git com\\\nmit -m x"}, 2),
        ("Bash: /dev/udp blocks", "Bash", {"command": "echo " + mail + " > /dev/udp/h/1"}, 2),
        ("Bash: a comment, then a client name split over two lines, blocks",
         "Bash", {"command": "# x\\\ncu\\\nrl -d " + mail + " h"}, 2),
        ("Bash: a comment, then a git verb split over two lines, blocks",
         "Bash", {"command": "true # x\\\ngit com\\\nmit -m " + mail}, 2),
        ("Bash: a line continuation with clean text passes", "Bash", {"command": "ls \\\n -la"}, 0),
        ("Bash: wget2 and xh block", "Bash", {"command": "wget2 h?" + mail + "; xh post h a=" + mail}, 2),
        ("Bash: lftp blocks", "Bash", {"command": "lftp -e 'put " + mail + "' host"}, 2),
        ("Bash: a git verb split by a line continuation blocks", "Bash", {"command": "git com\\\nmit -m " + mail}, 2),
        ("Bash: a backslash and CR LF do not hide the next command", "Bash", {"command": "x\\\r\ncurl -d " + mail + " h"}, 2),
        ("Bash: a comment line that ends in a backslash does not hide the next command",
         "Bash", {"command": "# x\\\ncurl -d " + mail + " h"}, 2),
        ("Bash: rclone and /dev/tcp block", "Bash", {"command": "rclone copy x r:" + mail + "; echo " + mail + " > /dev/tcp/h/1"}, 2),
        ("Bash: a client named by its full path blocks", "Bash", {"command": "/usr/bin/curl -d " + mail + " example.org"}, 2),
        ("Bash: ./gh and sudo /bin/wget block", "Bash", {"command": "./gh issue create -b " + mail + "; sudo /bin/wget x?" + mail}, 2),
        ("Bash: git with a quoted folder, then commit, blocks", "Bash", {"command": "git -C 'my dir' commit -m '" + mail + "'"}, 2),
        ("Bash: aws with an address blocks", "Bash", {"command": "aws s3 cp - s3://b/" + mail}, 2),
        ("Bash: git status with an address is local", "Bash", {"command": "git status; grep " + mail + " notes.md"}, 0),
    ]


def case_hook_tools():
    """The hook for Write, Edit, NotebookEdit and Bash."""
    mail = "jane" + at + "corp" + dot + "io"
    with tempfile.TemporaryDirectory() as d:
        pathlib.Path(d, ".check").write_text("block: *.xlsx\nblock: data/*.csv\nskip: ref/\n")
        os.symlink(d, d + "-link")  # the same project folder through a symlink
        saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("PII_GUARD_DENYLIST") or k == "CLAUDE_PROJECT_DIR"}
        os.environ["PII_GUARD_DENYLIST_FILE"] = os.path.join(d, "none.txt")
        os.environ["CLAUDE_PROJECT_DIR"] = d
        try:
            for name, tool, inp, want in _hook_cases(mail, d):
                code = run_hook_tool(d, tool, inp)
                check(f"hook: {name} (exit {code})", code == want)
            with contextlib.redirect_stderr(io.StringIO()):
                code = check_content.hook(json.dumps({"tool_name": "Write", "cwd": d + "-link",
                                                      "tool_input": {"file_path": "data/x.csv", "content": "x"}}))
            check(f"hook: Write through a symlinked folder: the block line holds (exit {code})", code == 2)
            t0 = time.process_time()
            slow = check_content.outgoing("git -a " * 16_000) or check_content.outgoing("x /" * 40_000)
            check("hook: a long Bash command is classified in linear time", not slow and time.process_time() - t0 < 1)
        finally:
            os.environ.pop("PII_GUARD_DENYLIST_FILE", None)
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            os.environ.update(saved)
            os.unlink(d + "-link")


def case_setting_lines():
    """The `code-` and `audit-` lines of `.check` (scripts/check_settings.py reads them): option lines, never allowed
    values and never tier lines; every other line keeps its meaning, and the tier line still fails closed."""
    settings = ["code-max-file-lines: 600", "code-exclude: Alex/*", "audit-ignore: ref/**", "audit-budget-file_kb: 100",
                "Code-C2: full", "code-c2 : dod", "audit-x: dod"]
    check("setting lines are option lines", all(is_option_line(v) for v in settings))
    check("setting lines are never tier lines", not any(is_tier_line(v) for v in settings))
    check("a setting line does not change the tier", profile_of(set(settings)) == "minimum"
          and profile_of(set(settings) | {"profile: dod"}) == "dod")
    check("a wrong tier line next to setting lines still fails closed",
          profile_of(set(settings) | {"profil: dod"}) == "unknown" and profile_of(set(settings) | {"profile: dodd"}) == "unknown")
    plain = ["code-review", "audit-trail", "codes: x", "code: dod", "the code-max: 1", "code-: 1"]
    check("a line that only looks like a setting is no setting line",
          [v for v in plain if is_option_line(v) and not is_tier_line(v)] == [])
    check("`code: dod` is still an unknown tier line", is_tier_line("code: dod") and profile_of({"code: dod"}) == "unknown")
    with tempfile.TemporaryDirectory() as d:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PII_GUARD", "GIT_"))}
        env["PII_GUARD_DENYLIST"] = "Alex"
        pathlib.Path(d, ".check").write_text("code-exclude: Alex/*\naudit-ignore: ref/**\nAlex Example\n")
        r = subprocess.run(ME + ["--stdin"], input="see code-exclude: Alex/* here", env=env, capture_output=True, text=True, cwd=d)
        check("a setting line is not an allowed value: a name in it is still found", r.returncode == 1 and "name" in r.stdout)
        r = subprocess.run(ME + ["--stdin"], input="by Alex Example", env=env, capture_output=True, text=True, cwd=d)
        check("an allowed string next to setting lines still passes", r.returncode == 0)


def gate_samples():
    """Sample lines of every finding kind, built at run time (no real value is in this file), with the letters that
    (?i) matches outside a-z (Kelvin sign, long s, dotted I), digits outside 0-9, and words that are not ASCII.

    Returns:
        The list of sample lines (case_gates, case_pool).
    """
    arabic = "".join(chr(0x660 + int(c)) if c.isdigit() else c for c in "555-123-" + "4567")
    return [
        "mail ann" + at + "corp" + dot + "io", "x" + at + "users.noreply.github" + dot + "com",
        "-----BEGIN RSA " + "PRIVATE KEY-----",
        "call 555-123-" + "4567", "(555) 123-" + "4567", "+44 20 7946 " + "0958", "TEL: 555123" + "4567", "tel 555 123 " + "4567",
        "+1555123" + "4567", "phone " + arabic, "\uff15\uff15\uff15-123-" + "4567".replace("4", "\uff14"),
        "123-45-" + "6789", "SSN 123456" + "789", "Social Security: 123 45 " + "6789", "\u017f\u017fn 123456" + "789",
        "EDIPI 12345" + "67890", "12345" + "67890 (DoD ID)", "see " + mil, mil.upper(), "unit" + dot + "m\u0130" + "l",
        "x" + dot + "sharepoint-mi" + "l" + dot + "us", "dod" + dot + "teams" + dot + "microsoft" + dot + "us",
        "CU" + "I//SP", "  CU" + "I  ", "Controlled Unclassified " + "Information", "UNCLASSIFIED/" + "/FO" + "UO",
        "for official use " + "only", "NOF" + "ORN", "Top\u00a0Sec" + "ret", "TOP\tSEC" + "RET", "sec" + "ret/" + "/rel",
        "by JANE DOE", "\u212aim said", "o\u2019brien", "ZO\u00cb", "yu", "the BlueBird plan",
    ] + [w + " 555 123 " + "4567" for w in ("Phone", "tel", "CELL", "mobile", "fax", "call")]


def case_gates():
    """The gates skip only lines that cannot give a finding: FOLD_EXTRAS matches the regex engine, and random texts
    built from samples of every kind give the same findings with and without the gates, in both tiers."""
    any_letter = re.compile("(?i)[a-z]")
    cased = [chr(c) for c in range(0x110000) if chr(c).lower() != chr(c) or chr(c).upper() != chr(c)]
    extra = {c for c in cased if not c.isascii() and (any_letter.fullmatch(c) or any(
        re.fullmatch("(?i)" + letter, c) for letter in "abcdefghijklmnopqrstuvwxyz"))}
    check(f"gates: FOLD_EXTRAS are the letters outside a-z that (?i) matches with a-z ({len(extra)})",
          extra == set(check_content_scan.FOLD_EXTRAS))
    samples = gate_samples()
    breaks = ["\n", "\r\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029", " ", ""]
    filler = ["plain words 12 34", "", '{"id": 123, "x": "2026-11-20"}', "caf\u00e9 top call", "a" * 300]
    rnd, deny, terms = random.Random(7), ["Jane Doe", "Kim", "O\u2019Brien", "Zo\u00eb", "Yu"], ["bluebird"]
    texts = []
    for _ in range(400):
        parts = []
        for _ in range(rnd.randint(1, 12)):
            piece = rnd.choice(samples + filler)
            if piece and rnd.random() < 0.2:   # a sample split by a line break
                cut = rnd.randrange(len(piece))
                piece = piece[:cut] + rnd.choice(breaks) + piece[cut:]
            parts.append(piece)
        texts.append("".join(p + rnd.choice(breaks) for p in parts))
    allow = {"Jane Doe Example", "call 555-123-" + "4567"}
    gated = [scan_text(t, "t", deny, allow, dod, terms) for t in texts for dod in (False, True)]
    keep = check_content_scan.candidate_lines
    check_content_scan.candidate_lines = lambda *a: None   # every line: the scan without gates
    try:
        plain = [scan_text(t, "t", deny, allow, dod, terms) for t in texts for dod in (False, True)]
    finally:
        check_content_scan.candidate_lines = keep
    check(f"gates: 400 random texts, both tiers: the same findings with and without gates ({sum(map(len, plain))})",
          gated == plain and sum(map(len, plain)) > 400)
    kind_list = list(check_content_scan.KINDS)
    check("gates: a line with no gate match is skipped",
          keep("plain words\nmail ann" + at + "corp" + dot + "io\nmore", kind_list, [], check_content_scan.FINDERS) == [1])
    own = dict(check_content_scan.FINDERS, phone=[lambda line: iter(())])
    check("gates: off when a kind has a project's own finders", keep("x", kind_list, [], own) is None)


def case_pool():
    """The scan of many files in a pool of processes gives the same findings, in the same order, as in this process."""
    samples = gate_samples()
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for i in range(40):
            paths.append(f"f{i:02}.txt")
            pathlib.Path(d, paths[-1]).write_text("\n".join(samples[i:] + samples[:i]) + "\nfiller\n" * i, encoding="utf-8")
        pathlib.Path(d, "bin.dat").write_bytes(b"\0" * 10)
        paths.append("bin.dat")
        keep = check_content_scan.PARALLEL_BYTES
        check_content_scan.PARALLEL_BYTES = 1
        try:
            pooled = scan_files(paths, d, ["Jane Doe"], set(), True)
            job = (d, ["Jane Doe"], set(), True, False, (), check_content_scan.max_bytes_of(set()))
            ran = check_content_scan._in_parallel(paths, d, job) is not None
        finally:
            check_content_scan.PARALLEL_BYTES = keep
        serial = scan_files(paths, d, ["Jane Doe"], set(), True)
    check(f"pool: the same findings in the same order as one process ({len(serial)}; pool ran: {ran})",
          pooled == serial and len(serial) > 40 and (ran or check_content_scan.usable_cores() < 2))   # 2 or more usable cores: the pool must run


# ---------------------------------------------------------------- local finders and missing parts -------------------

SAMPLE_LOCAL = '''"""Sample of a project's own finders for the self-test of the content check."""
import re

OWN_HOST = re.compile(r"x-[a-z]+\\.mil\\b")
OWN_SECRET = re.compile(r"LOCALKEY-[0-9]{6}")


def own_hosts(line):
    """Yield (start, end, host) for each host of the sample pattern."""
    return ((m.start(), m.end(), m.group()) for m in OWN_HOST.finditer(line))


def own_secrets(line):
    """Yield (start, end, key) for each key of the sample pattern."""
    return ((m.start(), m.end(), m.group()) for m in OWN_SECRET.finditer(line))


REPLACE = {"milhost": [own_hosts]}
ADD = {"secret": [own_secrets]}
'''

BROKEN_LOCAL = (
    ("an import that fails", "import no_such_module_anywhere\n", "cannot be loaded"),
    ("a syntax error", "def f(:\n", "cannot be loaded"),
    ("an error when it is loaded", "REPLACE = {}\nraise RuntimeError('boom')\n", "cannot be loaded"),
    ("neither REPLACE nor ADD", "X = 1\n", "has no finder"),
    ("empty REPLACE and ADD", "REPLACE = {}\nADD = {'secret': []}\n", "has no finder"),
    ("a kind the scanner does not have", "REPLACE = {'hostname': [len]}\n", "REPLACE must be"),
    ("a REPLACE list with no finder", "REPLACE = {'milhost': []}\n", "at least one finder"),
    ("a finder that is not a function", "ADD = {'secret': ['pattern']}\n", "ADD must be"),
    ("REPLACE that is not a dict", "REPLACE = [len]\n", "REPLACE must be"),
)


def local_kinds_of(text, dod=True):
    """The finding kinds of one text with the finders now in use (DoD tier unless dod is False)."""
    return [k for _, _, k, _ in check_content_scan.scan_text(text, "t", [], set(), dod)]


def case_local_in_process(d):
    """The loader and scan_text in this process: a good module, each broken module, and no module.

    Args:
        d: path to a temporary testing directory.
    """
    path = os.path.join(d, check_content_scan.LOCAL_NAME)
    key = "LOCALKEY-" + "123456"
    pem = "-----BEGIN RSA " + "PRIVATE KEY-----"
    try:
        with open(path, "w") as f:
            f.write(SAMPLE_LOCAL)
        check_content_scan.use_local(path)
        check("local module: it loads, and the note names what it replaces and adds",
              check_content_scan.LOCAL_ERROR is None and check_content_scan.LOCAL.endswith("active (replaces milhost; adds secret)"))
        check("local module: its finder replaces the kit's for that kind", local_kinds_of("see x-base" + dot + "mil") == ["milhost"]
              and local_kinds_of("see " + mil) == [])
        check("local module: an added finder runs next to the kit's", local_kinds_of(key + " and " + pem, False) == ["secret", "secret"])
        check("local module: a replaced DoD kind still runs only in the DoD tier", local_kinds_of("see x-base" + dot + "mil", False) == [])
        check("local module: every line is scanned, and the kit's two-line finders still run on the kit's kinds",
              local_kinds_of("FOR OFFICIAL\nUSE ONLY") == ["marking"] and local_kinds_of("EDIPI\n" + "12345" + "67890") == ["dodid"])
        with open(path, "w") as f:
            f.write("REPLACE = {'marking': [lambda line: iter(())], 'dodid': [lambda line: iter(())]}\n")
        check_content_scan.use_local(path)
        check("local module: a replaced kind has no two-line finder (the kit's one-line finder is not in use)",
              local_kinds_of("FOR OFFICIAL\nUSE ONLY") == [] and local_kinds_of("EDIPI\n" + "12345" + "67890") == [])
        with open(path, "w") as f:
            f.write(SAMPLE_LOCAL)
        check_content_scan.use_local(path)
        for label, text, why in BROKEN_LOCAL:
            with open(path, "w") as f:
                f.write(text)
            check_content_scan.use_local(path)
            try:
                local_kinds_of("clean text")
                raised = ""
            except check_content_scan.LocalError as err:
                raised = str(err)
            check(f"broken local module ({label}): every scan raises, and the message says why",
                  why in raised and why in (check_content_scan.LOCAL_ERROR or "") and check_content_scan.FINDERS is None)
        os.remove(path)
        check_content_scan.use_local(path)
        check("no local module: the kit's patterns are in use", check_content_scan.LOCAL == "" and local_kinds_of("see " + mil) == ["milhost"]
              and local_kinds_of(key, False) == [])
    finally:
        check_content_scan.use_local(os.path.join(d, "none", check_content_scan.LOCAL_NAME))


def local_cli(scripts, d, args, text, extra_env=None):
    """Run the copied check_content.py with these arguments and this stdin; return (exit code, output)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PII_GUARD_DENYLIST", "CLAUDE_PROJECT_DIR"))}
    env["PII_GUARD_DENYLIST_FILE"] = os.path.join(d, "none.txt")
    env.update(extra_env or {})
    r = subprocess.run([sys.executable, os.path.join(scripts, "check_content.py"), *args], cwd=d, env=env, input=text,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def case_load_ends(scripts, d, path, write):
    """A local module that ends or stalls the process while it loads: the scan fails and the hook blocks.

    Args:
        scripts: directory path containing check_content scripts.
        d: path to temporary testing directory.
        path: path to the local module file.
        write: JSON string payload for hook Write tool invocation.
    """
    for label, text in (("exit 0", "import sys\nsys.exit(0)\n"), ("exit 1", "import sys\nsys.exit(1)\n"),
                        ("a self-test with no main guard", "ADD = {}\nprint('LOCAL TEST PASS')\nraise SystemExit(0)\n")):
        with open(path, "w") as f:   # a file that ends the process while it loads must not end the scan with its code
            f.write(text)
        code, out = local_cli(scripts, d, ["--stdin"], "clean text")
        check(f"local module that exits at load ({label}): a scan fails", code == 1 and "CONTENT CHECK FAIL" in out)
        check(f"local module that exits at load ({label}): the hook blocks (exit 2)", local_cli(scripts, d, ["--hook"], write)[0] == 2)
    with open(path, "w") as f:   # a load that hangs: the hook's own time budget ends it with a block
        f.write("import time\ntime.sleep(20)\n")
    import concurrent.futures

    def timed(value):
        """Run the hook once with this timer value."""
        t0 = time.monotonic()
        code = local_cli(scripts, d, ["--hook"], write, {"CHECK_HOOK_LOAD_S": value})[0]
        return code, time.monotonic() - t0
    cases = (("1", "the timer ends it"), ("abc", "a bad timer value still blocks"),
             ("\u00b2", "a superscript digit still blocks"), ("9" * 5000, "a very long number still blocks"))
    with concurrent.futures.ThreadPoolExecutor(len(cases)) as pool:   # the runs wait at the same time, not in turn
        results = list(pool.map(timed, [value for value, _ in cases]))
    for (value, label), (code, took) in zip(cases, results, strict=False):
        # with "1" the load timer must end the process long before the 20 s sleep does; with a bad value it is 8 s
        check(f"local module that hangs at load: the hook blocks, {label} (exit {code}, under {5 if value == '1' else 15} s)",
              code == 2 and took < (5 if value == "1" else 15))


def case_local_cli(d, kit_scripts):
    """The command line and the hook with a copy of the scripts and a sample module next to them.

    Args:
        d: path to temporary testing directory.
        kit_scripts: directory path containing original kit scripts.
    """
    scripts = os.path.join(d, "scripts")
    shutil.copytree(kit_scripts, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    path = os.path.join(scripts, check_content_scan.LOCAL_NAME)
    write = json.dumps({"tool_name": "Write", "cwd": d, "tool_input": {"file_path": "a.txt", "content": "clean text"}})
    local_bash = json.dumps({"tool_name": "Bash", "cwd": d, "tool_input": {"command": "ls"}})
    code, out = local_cli(scripts, d, ["--stdin"], "clean text")
    check("no local module: the result line does not name one", code == 0 and "CONTENT CHECK PASS" in out and "local module" not in out)
    with open(path, "w") as f:
        f.write(SAMPLE_LOCAL)
    code, out = local_cli(scripts, d, ["--stdin"], "clean text")
    check("local module: the result line says it is active", code == 0 and out.rstrip().endswith(
        "; local module " + check_content_scan.LOCAL_NAME + " active (replaces milhost; adds secret)"))
    code, out = local_cli(scripts, d, ["--stdin"], "the key LOCALKEY-" + "123456")
    check("local module: its finding fails the scan, masked", code == 1 and "secret: <15 chars>" in out)
    code, out = local_cli(scripts, d, ["--status"], "")
    check("local module: --status names it", "finders: local module " + check_content_scan.LOCAL_NAME + " active" in out)
    check("local module: the hook lets a clean call run", local_cli(scripts, d, ["--hook"], write)[0] == 0)
    for label, text, why in BROKEN_LOCAL[:2] + BROKEN_LOCAL[3:4] + BROKEN_LOCAL[5:6]:
        with open(path, "w") as f:
            f.write(text)
        code, out = local_cli(scripts, d, ["--stdin"], "clean text")
        check(f"broken local module ({label}): a scan of clean text fails", code == 1 and "CONTENT CHECK FAIL" in out
              and why in out and "PASS" not in out)
        code, out = local_cli(scripts, d, ["--hook"], write)
        check(f"broken local module ({label}): the hook blocks a clean call (exit 2)", code == 2 and why in out)
        code, out = local_cli(scripts, d, ["--status"], "")
        check(f"broken local module ({label}): --status fails and says why", code == 1 and "finders: FAIL" in out and why in out)
    check("broken local module: a local Bash command is not scanned, so it can repair the file", local_cli(scripts, d, ["--hook"], local_bash)[0] == 0)
    case_load_ends(scripts, d, path, write)
    with open(path, "w") as f:   # the shape is right, but the finder fails when it runs
        f.write("def bad(line):\n    raise RuntimeError('boom')\n\n\nADD = {'email': [bad]}\n")
    code, out = local_cli(scripts, d, ["--stdin"], "clean text")
    check("a finder that fails during a scan: the scan fails", code not in (0, 2) and "PASS" not in out)
    check("a finder that fails during a scan: the hook blocks (exit 2)", local_cli(scripts, d, ["--hook"], write)[0] == 2)
    with open(path, "w") as f:   # a finder that gives a wrong shape
        f.write("ADD = {'email': [lambda line: ['x']]}\n")
    check("a finder that gives a wrong shape: the scan fails", local_cli(scripts, d, ["--stdin"], "clean text")[0] not in (0, 2))
    check("a finder that gives a wrong shape: the hook blocks (exit 2)", local_cli(scripts, d, ["--hook"], write)[0] == 2)


def case_missing_parts(kit_scripts):
    """A copy of check_content.py without check_content_scan.py blocks when run (exit 2, also in the hook) but only raises on import.

    Args:
        kit_scripts: directory path containing original kit scripts.
    """
    with tempfile.TemporaryDirectory() as d:
        alone = os.path.join(d, "check_content.py")
        with open(os.path.join(kit_scripts, "check_content.py")) as src, open(alone, "w") as dst:
            dst.write(src.read())
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}   # only the lone copy is importable
        hook_res = subprocess.run([sys.executable, alone, "--hook"], input="{}", capture_output=True, text=True, cwd=d,
                                  env=env)
        check("missing parts: the hook blocks (exit 2)", hook_res.returncode == 2)
        imp = subprocess.run([sys.executable, "-c", "try:\n import check_content\nexcept ImportError:\n print('raised')"],
                             capture_output=True, text=True, cwd=d, env=env)
        check("missing parts: an importer gets ImportError, not an exit", imp.stdout.strip() == "raised")


def case_local(kit_scripts):
    """Run all local finder and missing-part cases."""
    with tempfile.TemporaryDirectory() as d:
        case_local_in_process(d)
        case_local_cli(d, kit_scripts)
    case_missing_parts(kit_scripts)


def without_local(kit):
    """Make the cases prove the kit's own patterns, also in a project that has its own finders: copy the scripts of
    the content check, without the project's module, into `kit`, point the command line of the cases at that copy, and
    set the finders of this process to the kit's. (The project's module proves itself: its own --test.)

    Args:
        kit: an empty temporary folder.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    for name in os.listdir(here):
        if name.startswith("check_content") and name.endswith(".py") and name != check_content_scan.LOCAL_FILE.name:
            shutil.copy(os.path.join(here, name), kit)
    ME[1] = os.path.join(kit, "check_content.py")
    check_content_scan.use_local(os.path.join(kit, check_content_scan.LOCAL_FILE.name))   # no such file: the kit's finders


def run():
    """Run every case in order; print CONTENT CHECK TEST PASS or FAIL and return the exit code.

    Returns:
        The exit code: 0 pass, 1 fail.
    """
    # The host's git config (forced signing, -c on the command line) must not change the cases.
    for k in ("GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"):
        os.environ.pop(k, None)
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    os.environ.pop("CHECK_TERMS", None)  # the host's terms list must not change the cases
    os.environ["CHECK_TERMS_FILE"] = os.path.join(tempfile.gettempdir(), "no-such-terms-file.txt")
    FAILED.clear()
    with tempfile.TemporaryDirectory() as kit:
        without_local(kit)
        for case in (case_speed, case_minimum_patterns, case_secrets_and_masks, case_dod_patterns, case_dod_split_lines,
                     case_profile_lines, case_denylist_and_fingerprint, case_cli, case_commits, case_hook,
                     case_terms, case_block_lines, case_check_file, case_setting_lines, case_hook_tools,
                     case_gates, case_pool):
            case()
        case_local(kit)
    print("CONTENT CHECK TEST " + ("FAIL" if FAILED else "PASS"))
    return 1 if FAILED else 0


class CheckContentTest(unittest.TestCase):
    """The cases of `python3 scripts/check_content.py --test`, for `python3 -m unittest` and pytest. They run in order
    in one test: they share the copy of the kit and the finders of this process."""

    def test_self_test(self):
        """Every case passes; the environment and the finders that run() changes are put back after it."""
        saved, me = dict(os.environ), list(ME)
        self.addCleanup(check_content_scan.use_local)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(saved), ME.__setitem__(slice(None), me)))
        self.assertEqual(run(), 0, "failed cases: %s" % FAILED)
