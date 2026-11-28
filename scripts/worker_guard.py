#!/usr/bin/env python3
"""PreToolUse hook for the worker and reviewer subagents (.claude/agents/): blocks git commands they must never run.

Adapted from an earlier project's worker guard (tested parser).

Usage (wired in the .claude/agents/ frontmatter `hooks:`; runs only while that subagent is active):
  python3 scripts/worker_guard.py            # reads the hook JSON on stdin
  python3 scripts/worker_guard.py --readonly # reviewer: also blocks git verbs that change the repo
  python3 scripts/worker_guard.py --test     # self-test of the block rules and the scan; prints GUARD TEST PASS
  python3 scripts/worker_guard.py --scan TARGET ...  # a worker's branch range or scratch folder: guard workarounds

Blocks Bash commands that push to main or master (also a bare push or HEAD while on one), rebase, git clean, branch deletes, force-push (--force, -f in
grouped flags, +refspec, --force-with-lease), --mirror/--all, reset --hard or delete remote branches. It parses each
simple command into words (quotes respected), so "main" inside a branch name or a commit message is not a match.
Exit 2 with the reason on stderr blocks the call; exit 0 lets the normal permission flow decide. A command string run by
eval or a shell's -c is checked too; other commands built at run time (a script file, stdin, `$(...)` output) are not
seen: it is a seat belt for honest mistakes, not a security boundary.
Prevents: a worker or reviewer subagent that pushes to main, force-pushes, rewrites history or deletes a branch by mistake.
Network: none.
Writes: none.
Credentials: none.
"""
import argparse
import base64
import binascii
import codecs
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

SEPARATORS = {';', '&&', '||', '|', '&', '(', ')'}
GIT_OPTS_WITH_VALUE = {'-C', '-c', '--git-dir', '--work-tree', '--namespace'}
# --readonly (reviewer): also block git verbs that change the repo.
WRITE_VERBS = {'commit', 'add', 'rm', 'mv', 'merge', 'checkout', 'switch', 'restore', 'stash', 'tag', 'apply', 'am',
               'cherry-pick', 'revert', 'reset', 'push', 'pull', 'clean'}

BUILDERS = re.compile(r"chr\(\s*(?:0x[0-9A-Fa-f]+|\d+)\s*\)|\\x[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|\\[0-7]{3}|&#\d+;|"
                      r"b64decode|fromhex|unhexlify|rot_?13|\.join\(")
LITERAL = re.compile(r"(['\"])((?:\\.|(?!\1).)*)\1")
SHELL_SUFFIXES = ('.sh', '.bash')
CODE_SUFFIXES = SHELL_SUFFIXES + ('.py', '.js', '.mjs', '.cjs', '.ps1', '.psm1')


def segments(cmd):
    """Yield the word lists of each simple command (split on newlines and ; && || | &, quotes respected).

    Args:
        cmd: the shell command text.
    """
    for line in cmd.splitlines():
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            words = list(lex)
        except ValueError:          # unbalanced quotes: fall back to a plain split
            words = line.split()
        seg = []
        for w in words:
            if w in SEPARATORS:
                if seg:
                    yield seg
                seg = []
            else:
                seg.append(w)
        if seg:
            yield seg


def current_branch():
    """The checked-out branch name ("HEAD" when detached, "" outside a repo)."""
    r = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True)
    return r.stdout.strip()


BRANCH_OPTS_WITH_VALUE = {'--sort', '--format', '--contains', '--no-contains', '--merged', '--no-merged', '--points-at'}


def branch_delete(rest):
    """True for any delete form of `git branch`: -d/-D alone or grouped (-rd, -df), and --delete or its prefixes
    (git accepts an unambiguous prefix such as --del). A value after --sort and the like is skipped.

    Args:
        rest: the words after `git branch`.

    Returns:
        True or False.
    """
    skip = False
    for w in rest:
        if skip:
            skip = False
            continue
        if w in BRANCH_OPTS_WITH_VALUE:
            skip = True
        elif w.startswith('--'):
            if len(w) >= 3 and '--delete'.startswith(w):
                return True
        elif w.startswith('-') and ('d' in w or 'D' in w):
            return True
    return False


def _check_push(rest, branch):
    """Return a reason to block `git push`, or None.

    Args:
        rest: list of command arguments following git push.
        branch: current git branch name or None.

    Returns:
        A string explanation if blocked, or None if permitted.
    """
    pos, cut = [], None
    for w in rest:
        if w and set(w) <= set('<>&|'):  # a redirection such as > or >& (2>&1 splits as 2, >&, 1)
            if cut is None:
                cut = len(pos)
            continue
        if w.startswith('--'):
            if w in ('--force', '--mirror', '--all', '--delete', '--prune') or w.startswith('--force-with-lease'):
                return f'workers may not push with {w} (AGENTS.md "Git history")'
        elif w.startswith('-') and len(w) > 1:
            if 'f' in w[1:] or 'd' in w[1:]:
                return f'workers may not push with {w} (force or delete)'
        else:
            pos.append(w)
    # With a redirection, check two readings and block if either targets main: all words as refspecs (a quoted ">"
    # is a real argument), and only the words before it, minus a file-descriptor digit (`git push 2>&1` on main).
    readings = [pos]
    if cut is not None:
        before = pos[:cut]
        if before and before[-1].isdigit():
            before = before[:-1]
        readings.append(before)
    for words in readings:
        why = push_target(words, branch)
        if why:
            return why
    return None


def check_git(args, branch, readonly=False):
    """args: the words after `git`. Returns a reason to block, or None.

    Args:
        args: the words after `git`.
        branch: the current branch, or None when it is not known.
        readonly: True for the reviewer: also block the git verbs that change the repo.

    Returns:
        A reason to block (a text), or None.
    """
    i = 0
    while i < len(args) and args[i].startswith('-'):
        i += 2 if args[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    if readonly and sub in WRITE_VERBS:
        return f'reviewers are read-only: no git {sub}'
    if sub == 'rebase':
        return 'no rebase; update a branch by merging (AGENTS.md "Git history")'
    if sub == 'reset' and '--hard' in rest:
        return 'no reset --hard; ask the orchestrator'
    if sub == 'clean':
        return 'no git clean; ask the orchestrator'
    if sub == 'branch' and branch_delete(rest):
        return 'no branch deletes; the orchestrator or the Maintainer deletes branches'
    return _check_push(rest, branch) if sub == 'push' else None


def push_target(pos, branch):
    """pos: the push words without options; pos[0] is the remote. Returns a reason to block, or None.

    Args:
        pos: the push words without options; pos[0] is the remote.
        branch: the current branch, or None when it is not known.

    Returns:
        A reason to block (a text), or None.
    """
    refspecs = pos[1:]
    if not refspecs:
        refspecs = ['HEAD']
    for ref in refspecs:
        if ref.startswith('+'):
            return 'no force-push (+refspec)'
        src, sep, dst = ref.partition(':')
        if sep and not src:
            return 'workers do not delete remote branches'
        target = dst or (branch if src == 'HEAD' else src)
        if target in ('main', 'master', 'refs/heads/main', 'refs/heads/master'):
            return 'workers never push main or master; push your own branch'
    return None


SHELLS = {'sh', 'bash', 'zsh', 'dash', 'ksh'}


def _inner_command(seg, k, w, depth):
    """Extract an inner command string from eval or a shell -c call, or None.

    Args:
        seg: command line argument segments list.
        k: integer index of the shell or eval command word.
        w: command word string being inspected.
        depth: current recursion depth integer.

    Returns:
        The extracted inner command string, or None.
    """
    if depth >= 3:
        return None
    if w == 'eval':
        return ' '.join(seg[k + 1:])
    if w.rsplit('/', 1)[-1] in SHELLS:
        # The command string follows the first short-option group with c (-c, -xc, -lc), past long options
        # (--norc, --rcfile x) and an optional "--".
        flags = [j for j in range(k + 1, len(seg)) if re.fullmatch(r'-[A-Za-z]*c[A-Za-z]*', seg[j])]
        if flags:
            j = flags[0] + 1
            if j < len(seg) and seg[j] == '--':
                j += 1
            if j < len(seg):
                return seg[j]
    return None


def reason(cmd, branch=None, readonly=False, depth=0):
    """Why a shell command is blocked, or None; command strings run by a shell or eval are checked too.

    Args:
        cmd: the shell command text.
        branch: the current branch, or None when it is not known.
        readonly: True for the reviewer: also block the git verbs that change the repo.
        depth: how many shell or eval layers are above this text (the check stops at 3).

    Returns:
        A reason to block (a text), or None.
    """
    for seg in segments(cmd):
        for k, w in enumerate(seg):
            # A command string run by a shell (`bash -c "git checkout main"`, `eval "..."`) is checked as a command too.
            inner = _inner_command(seg, k, w, depth)
            if inner is not None:
                why = reason(inner, branch, readonly, depth + 1)
                if why:
                    return why
                break
            if readonly and w.rsplit('/', 1)[-1] in {'rm', 'rmdir', 'unlink', 'shred'}:
                return 'the reviewer is read-only: it never deletes files (a test copy goes in a new mktemp -d folder it leaves)'
            if w == 'git' or w.endswith('/git'):
                why = check_git(seg[k + 1:], branch if branch is not None else current_branch(), readonly)
                if why:
                    return why
                break
    return None


def values(line):
    """The strings a line may build at run time: the chr() characters, the literals with their escapes decoded,
    the literals joined, and each literal decoded as base64, hex and rot13 (a piece that does not decode is left out).

    Args:
        line: one line of text that matched BUILDERS.

    Returns:
        A list of candidate strings.
    """
    lits = [m.group(2) for m in LITERAL.finditer(line)]
    out = [''.join(chr(int(n, 0)) for n in re.findall(r"chr\(\s*(0x[0-9A-Fa-f]+|\d+)\s*\)", line) if int(n, 0) < 0x110000)]
    out.append(re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))) if int(m.group(1)) < 0x110000 else '', line))
    for lit in lits:
        try:
            out.append(codecs.decode(lit, 'unicode_escape'))
        except (UnicodeDecodeError, ValueError):
            pass
        out.append(codecs.decode(lit, 'rot13'))
        for decode in (lambda s: base64.b64decode(s, validate=True), bytes.fromhex):
            try:
                out.append(decode(lit).decode('utf-8'))
            except (binascii.Error, ValueError, UnicodeDecodeError):
                pass
    out.append(''.join(lits))
    return [v for v in out if v]


def rebuilt(line, deny, terms):
    """True when a line builds a string at run time whose value holds the at sign or a word the content check blocks.

    Args:
        line: one line of text.
        deny: the names of the denylist.
        terms: the Maintainer's own blocked words.

    Returns:
        True or False.
    """
    if not BUILDERS.search(line):
        return False
    import check_content_scan as scan   # scripts/check_content_scan.py: scan_text and the word lists
    return any('@' in v or scan.scan_text(v, 'built', deny, [], terms=terms) for v in values(line))


def wrapped(path, line):
    """True when a line of a shell script holds a git command that the worker guard blocks.

    Args:
        path: the file's path (a Path or text).
        line: one line of the file.

    Returns:
        True or False.
    """
    return bool(reason(line.strip())) if line.strip() and not line.lstrip().startswith('#') else False


def listed(line):
    """True when a line of code holds a git command, as a list of literals (for example a subprocess call), that the
    worker guard blocks.

    Args:
        line: one line of code.

    Returns:
        True or False.
    """
    lits = [m.group(2) for m in LITERAL.finditer(line)]
    return 'git' in lits and bool(reason(' '.join(lits)))


def git(args, check=True):
    """The output of one git command as text (bytes that are not UTF-8 are replaced).

    Args:
        args: the git arguments.
        check: True: a failing command raises CalledProcessError.

    Returns:
        The standard output.
    """
    return subprocess.run(['git', '--literal-pathspecs', *args], capture_output=True, check=check).stdout.decode('utf-8', 'replace')


def lines_of(target):
    """Yield (path, line number, line, is shell, is code) for a folder (every line of every text file, not the
    worktrees of .claude/worktrees) or a git range (added lines).

    Args:
        target: a folder path, or a git range such as origin/main...BRANCH.
    """
    root = Path(target)
    if root.is_dir():
        for p in sorted(x for x in root.rglob('*') if x.is_file() and '.git' not in x.parts and '.claude/worktrees/' not in x.relative_to(root).as_posix()):
            try:
                text = p.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            shell = p.suffix in SHELL_SUFFIXES or text.startswith('#!')
            for no, line in enumerate(text.split('\n'), 1):
                yield str(p), no, line, shell, shell or p.suffix in CODE_SUFFIXES
        return
    head = re.split(r"\.\.\.?", target)[-1] or 'HEAD'
    names = git(['diff', '--name-only', '-z', '--diff-filter=d', target]).split('\0')
    for path in filter(None, names):   # one diff per file: no header parsing, any file name
        shell = path.endswith(SHELL_SUFFIXES) or git(['show', f'{head}:{path}'], check=False).startswith('#!')
        no, body = 0, False
        for line in git(['diff', '-U0', '--no-color', target, '--', path]).split('\n'):
            if line.startswith('@@'):
                no, body = int(re.search(r"\+(\d+)", line).group(1)), True
            elif body and line.startswith('+'):
                yield path, no, line[1:], shell, shell or path.endswith(CODE_SUFFIXES)
                no += 1


def scan_targets(targets, deny=None, terms=None):
    """The findings in the targets, each (path, line number, kind).

    Args:
        targets: folders or git ranges.
        deny: the names of the denylist (None: the content check's own list).
        terms: the Maintainer's own blocked words (None: the content check's own list).

    Returns:
        A list of (path, line number, kind).
    """
    import check_content_scan as scan   # scripts/check_content_scan.py: scan_text and the word lists
    deny = scan.load_denylist() if deny is None else deny
    terms = scan.load_terms() if terms is None else terms
    found = []
    for target in targets:
        for path, no, line, shell, code in lines_of(target):
            if shell and wrapped(path, line) or code and listed(line):
                found.append((path, no, 'wrapped'))
            elif code and rebuilt(line, deny, terms):
                found.append((path, no, 'rebuilt'))
    return found


def scan_main(targets):
    """Print one line per finding and a summary line.

    Args:
        targets: folders or git ranges.

    Returns:
        The exit code: 0 no finding, 1 a finding (a MAJOR finding for the review: the delegate skill, S8), 2 an error.
    """
    try:
        found = scan_targets(targets)
    except (subprocess.CalledProcessError, OSError) as err:
        print(f'GUARD SCAN ERROR: {err}')
        return 2
    for path, no, kind in found:
        print(f'{kind:8}  {path}:{no}')
    print(f'GUARD SCAN {"FAIL" if found else "PASS"}: {len(found)} finding(s) in {len(targets)} target(s)')
    return 1 if found else 0


def scan_selftest():
    """Prove the scan on the sample files of scripts/worker_guard_scan_samples.json (in a temporary folder), and the
    range mode on a temporary git repo (an added line that starts with "++", a file name with a space, a byte that is
    not UTF-8). The blocked word is invented.

    Returns:
        A list of the failed cases (empty when all pass).
    """
    data = json.loads((Path(__file__).parent / 'worker_guard_scan_samples.json').read_text(encoding='utf-8'))
    word, cases, bad = data['word'], data['samples'], []
    with tempfile.TemporaryDirectory() as tmp:
        for name, (text, _) in cases.items():
            (Path(tmp) / name).write_text(text)
        kinds = {Path(p).name: k for p, _, k in scan_targets([tmp], deny=[word], terms=[])}
        bad += [f'{n}: want {w}, got {kinds.get(n)}' for n, (_, w) in cases.items() if kinds.get(n) != w]
        inner = Path(tmp) / '.claude' / 'worktrees' / 'agent-x'   # a worker's scratch folder, given as the target
        inner.mkdir(parents=True)
        (inner / 'a.py').write_text(cases['a.py'][0])
        if not scan_targets([str(inner)], deny=[word], terms=[]):
            bad.append('a target inside .claude/worktrees is scanned')
        repo = Path(tmp) / 'repo'

        def run(*a):
            """Run git in the temporary test repository."""
            return subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c', 'user.email=t@t.invalid', *a],
                                  capture_output=True, check=True)
        repo.mkdir()
        run('init', '-q')
        (repo / 's p.py').write_text('x = 1\n')
        run('add', '-A')
        run('commit', '-qm', 'base')
        (repo / 's p.py').write_bytes(data['range'].encode('latin-1'))   # a byte that is not UTF-8 (0xff)
        run('commit', '-qam', 'change')
        old = Path.cwd()
        try:
            os.chdir(repo)
            found = scan_targets(['HEAD~1...HEAD'], deny=[word], terms=[])
        finally:
            os.chdir(old)
        if found != [('s p.py', 4, 'rebuilt')]:
            bad.append(f'range mode: want [s p.py:4 rebuilt], got {found}')
    return bad


def selftest():
    """Check sample commands that must block and must pass; print the wrong ones and the result.

    Returns:
        The exit code: 0 pass, 1 fail.
    """
    block = ['git push origin main', 'git push -u origin HEAD:main', 'git push origin claude/x:main', 'git push --force origin claude/x',
             'git push -f', 'git push -fu origin claude/x', 'git push origin "+claude/x"', 'git push origin +claude/x',
             'git rebase origin/main', 'cd x && git rebase -i HEAD~2', 'git -C sub rebase main', 'git reset --hard origin/main',
             'git push origin --delete claude/x', 'git push origin :claude/x', 'git push --mirror origin', 'git push --all',
             'git push --force-with-lease origin claude/x', 'git status; git push origin main',
             'git push origin master', 'git clean -fd', 'git branch -D x', '(git push origin main)', 'git --no-pager -C r push --force',
             'git push --prune origin', 'git push origin ">" main', 'git push origin claude/x > /dev/null; git push origin main',
             'git branch -df x', 'git branch -rd origin/x', 'git branch --dele x', 'git branch --del x']
    allow = ['git push -u origin claude/t40-slc', 'git push -u origin claude/main-menu', 'git push origin claude/fix-main',
             'git merge origin/main', 'git status', 'python3 tools/check.py --no-perf', 'git log --oneline main..HEAD',
             'git fetch origin main', 'git commit -m "push main menu fix"', 'git commit -m "fix rebase of main"',
             'git push', 'git push origin HEAD', 'git commit -m "note; git rebase later"', 'git branch -a', 'git branch -vv',
             'git push origin claude/x 2>&1', 'git push -u origin claude/x > /dev/null', 'git branch --sort -committerdate', 'git branch --sort=-committerdate',
             'git branch -m old new', 'git branch --list']
    bad = [c for c in block if not reason(c, 'claude/x')] + [c for c in allow if reason(c, 'claude/x')]
    for c in ['git push', 'git push origin HEAD', 'git push 2>&1', 'git push > /dev/null', 'git push 2> err.txt',
              'git push origin 2>&1']:     # on main these must block
        if not reason(c, 'main'):
            bad.append(c + ' (on main)')
    for c in ['git commit -m x', 'git checkout -b y', 'git add .', 'cd a && git merge origin/main',
              'bash -c "git checkout main"', 'sh -lc \'git switch main\'', 'eval "git checkout main"', '/bin/bash -c "cd x; git commit -m y"',
              'bash --norc -c "git checkout main"', 'bash --rcfile x -c "git checkout main"', 'bash -c -- "git checkout main"',
              'ksh -c "git checkout main"', 'rm -rf x', 'cd /tmp/a && /bin/rm -r b', 'bash -c "rmdir x"']:
        if not reason(c, 'claude/x', readonly=True):
            bad.append(c + ' (readonly)')
    for c in ['git diff origin/main...HEAD', 'git log -p', 'git show HEAD:x', 'git status', 'git fetch origin',
              'bash -c "git log --oneline -3"', 'bash scripts/check.sh']:
        if reason(c, 'claude/x', readonly=True):
            bad.append(c + ' (readonly allow)')
    bad += scan_selftest()
    for c in bad:
        print('WRONG:', c)
    print('GUARD TEST PASS' if not bad else 'GUARD TEST FAIL')
    return 1 if bad else 0


def main():
    """PreToolUse hook: exit 2 with the reason when a Bash command is blocked; or run --test.

    Returns:
        The exit code: 0 lets the command run, 2 blocks it.
    """
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--test', action='store_true', help='run the self-test')
    ap.add_argument('--readonly', action='store_true', help='also block git verbs that change the repo (reviewer)')
    ap.add_argument('--scan', nargs='+', metavar='TARGET', help='scan folders or git ranges for guard workarounds')
    opts = ap.parse_args()
    if opts.test:
        return selftest()
    if opts.scan:
        return scan_main(opts.scan)
    try:
        hook = json.load(sys.stdin)
    except ValueError:
        return 0
    if hook.get('tool_name') != 'Bash':
        return 0
    why = reason(hook.get('tool_input', {}).get('command', ''), readonly=opts.readonly)
    if why:
        print(f'Blocked by scripts/worker_guard.py: {why}. Report the need to the orchestrator instead.', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
