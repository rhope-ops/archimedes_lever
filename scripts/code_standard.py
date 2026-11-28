#!/usr/bin/env python3
"""Code standard check: measures every source file of this repo against docs/code-standard.md and fails on new debt.

Why: the Administrator, 2026-11-17: all code is lean, modular, commented and human-editable, and stays so as work continues.
A written rule alone is not always obeyed, so this check fails a push or a pull request instead. The kit owns this
file; a project gets it by sync, keeps its own settings in its `.check` file and its own stricter rules in its own
gate file (below) or via `code-strict-gate: on`, never in a copy of this file.

What it measures (the rule numbers are those of docs/code-standard.md; DEC-LINES retired the 450/600-line file caps):
  C1 header      each source file starts with a header comment that says what the file is for
  C1 safety      opt-in (`code-c1-safety: on`): the header also has the labels Network:, Writes: and Credentials:
  C1 prevents    FAIL in the kit, WARN in a project (AUD-1): a check entry point (check.sh or a hook runs it) has `Prevents: <defect>`
  C2 comment     each function has a comment: a docstring, comment-based help, or a comment line directly above it
                 or as the first line of its body (one line is enough)
  C2 full        opt-in (`code-c2: full`): a function longer than 10 lines also documents each
                 parameter and its return value in its language's help form
  C3 length      each function is at most `max_function_lines` lines long
  C5 duplicate   no two functions in hand-written files have the same body (a copy must be generated, with a banner)
  C6 generated   each generated file says GENERATED near its top and names its source
  C10 parse      each PowerShell file parses; each Python file too, when ruff or pylint is not installed
  Python style, complexity (C90), unused/bugbear checks, and line length: ruff (ruff.toml; check.sh) on `--python-files`
  Shell lint: shellcheck (check.sh) on `--shell-files`; PowerShell lint: PSScriptAnalyzer.
A comment that is the file header, or a divider line ("# ----", "# ===="), does not count as a function's comment.
A script block passed as an argument ($b.Add_Click({ ... })) is measured for C3 too, named by the call it is in.
Settings: the `code-` lines of `.check` (caps, scope, opt-in rules; read by scripts/check_settings.py, which lists
the keys; a line that is not valid fails this check).
The ratchet: `.check.state.json` ("code_standard": {"debt": ...}) lists the debt that existed when the standard
started. A violation that is not in that list fails. A listed function that grew fails. A listed item that is fixed
fails too, until the baseline is lowered in the same change (`--update`), so the list can only shrink and always
matches the code. The baseline and the settings are compared with those on the merge base with origin/main: an added
item, a raised value or a changed `code-` setting fails, unless the same change adds a row to docs/DECISIONS.md that
names `.check` (the Administrator's decision). A merge base that still has the old .code-standard.json is compared from it.

A project's own gate (the extension point): when the file scripts/code_standard_gate.py stands next to this one, the
check loads it and calls it. The kit has no gate file. A gate that cannot be imported, or lacks one of the five names
below, fails the check; so do the settings `code-max-line-chars` and `code-c1-safety: strict` with no gate file
(they are a gate's to enforce). The kit's built-in strict gate (strict_gate) is active when a project sets
`code-strict-gate: on` and has no gate file of its own. The self-test runs both core and strict gate cases;
scripts/check.sh also runs `python3 scripts/code_standard_gate.py --test` when a project gate file has one.
  RULES             {debt kind: (label, caps key or None)}: debt kinds the gate adds or relabels. With a caps key the
                    debt value is a size that may only go down, and the label holds one %d for the cap.
  OPT_IN            {debt kind: level(config) -> int}: opt-in kinds the gate adds or replaces (0 = off). A kind whose
                    level is above the one on main may list its debt once with --adopt.
  file_rules(v, path, lines, head, config, skip)   called for each source file after the kit's own per-file rules;
                    it writes its violations into v[kind][path] and may remove one the kit wrote. head is the header
                    text (one header line per text line), skip the (first, last) lines of the generated blocks.
  decided(root, ref) -> (bool, [refusal lines])    replaces the kit's test "docs/DECISIONS.md gained a line that names
                    `.check`"; ref is the merge base with origin/main. The refusal lines are printed with a failure.
  new_debt_refusal(root, ref, kind, key) -> a FAIL line or None   asked for each debt key that main's list lacks; a
                    FAIL line is a problem that no decision lifts (for example debt for a file that is new).

Inputs:  the files git tracks (git ls-files -z): files with a known extension, and files with no extension whose first
         line is a shell or Python shebang (for example scripts/git-hooks/pre-push); filtered by the settings.
Outputs: one line per problem, then `CODE-STANDARD pass` or `CODE-STANDARD fail`; exit 0 or 1.
Usage:   python3 scripts/code_standard.py            check (scripts/check.sh runs it in both lanes)
         python3 scripts/code_standard.py --report   print every measurement (function lengths, comments)
         python3 scripts/code_standard.py --update   lower the baseline to the debt that is left; refuses new debt
         python3 scripts/code_standard.py --init     write the first baseline (only when the repo has none)
         python3 scripts/code_standard.py --adopt    add the debt of a rule the baseline does not list yet (a rule just
                                                     turned on, such as `code-c2: full`); needs a DECISIONS row
         python3 scripts/code_standard.py --python-files all|line   list covered Python files, NUL-separated
         python3 scripts/code_standard.py --shell-files             list covered shell files, NUL-separated
         python3 scripts/code_standard.py --test     prove the check on small sample repos (scripts/code_standard_test.py)
Prevents: code without a header, function comment, size limit or safety label is added, so the code grows hard to read and edit
Network: none (it runs local git read commands, and pwsh to parse PowerShell files).
Writes:  .check.state.json, only with --init, --update or --adopt (and Python's __pycache__ when it imports its modules).
Credentials: none.
Needs:   Python 3.8+, git, and pwsh 7 only when the repo has PowerShell files (the parser gives the function list).
"""

import argparse
import ast
import fnmatch
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tokenize
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_settings as settings   # noqa: E402 - scripts/check_settings.py: the reader of .check and of .check.state.json

ROOT = Path(__file__).resolve().parent.parent
# A project's own gate (the header lists its five names). GATE is the loaded gate or StrictGate, or None: load() sets it.
GATE_FILE = Path(__file__).resolve().parent / 'code_standard_gate.py'
GATE_NAMES = ('RULES', 'OPT_IN', 'file_rules', 'decided', 'new_debt_refusal')
GATE = None

LINTERS = all(shutil.which(t) for t in ('ruff', 'pylint'))   # C10 for Python: external linters when installed, else here

LANGS = {'.py': 'python', '.ps1': 'powershell', '.psm1': 'powershell', '.js': 'js', '.mjs': 'js', '.cjs': 'js', '.sh': 'shell'}
MIN_HEADER_CHARS = 60      # a header shorter than this does not say what the file is for
SAFETY_LABELS = ('Network:', 'Writes:', 'Credentials:')   # C1 safety: what a reviewer must find before a run
# The opt-in rules: the debt kind of each and its level in a config (0 = off). Only these can be adopted later.
OPT_IN = {'docs': lambda c: int(c.get('c2') == 'full'),
          'safety': lambda c: 2 if c.get('c1_safety') == settings.STRICT else int(bool(c.get('c1_safety')))}
# C1: the defect a check stops, 3+ words, no placeholder
PREVENTS = re.compile(r'^[ \t]*Prevents:[ \t]*(?!(?:unclear|unknown|tbd|todo|none|n/?a|see|tba)\b|\?)\S+(?:[ \t]+\S+){2}', re.M | re.I)
ENTRY_FILES = ('scripts/check.sh', '.claude/settings.json')   # plus scripts/git-hooks/* and .github/workflows/*: what runs a check
MIN_DUP_LINES = 4          # a body this short (a one-line wrapper) is not counted as a duplicate
SHORT_FUNCTION = 10        # lines; a function this short needs only the lean C2 comment (the Administrator's 3B, 2026-11-17)
RETURNS_VALUE = re.compile(r'\breturn\s+[^\s;}]')   # `return x`, not a bare `return` or `return;`

DIVIDER = re.compile(r'^\s*(#|//)\s*(-{4,}|={4,})')   # a section line, not a function's comment
BLOCK_BEGIN = re.compile(r'^\s*# >>> ([\w-]+): generated from ')
BLOCK_END = '# <<< '

# Each debt kind: its label, and for a kind whose debt value is a size (it may only go down) the cap it is measured
# against (the label then holds one %d). A project's own gate may add kinds (rules()).
RULE = {'header': ('C1 no header comment', None), 'comment': ('C2 function without a comment', None),
        'length': ('C3 function longer than %d lines', 'max_function_lines'),
        'prevents': ('C1 check entry point without a "Prevents: <defect>" header line', None),
        'duplicate': ('C5 same body as another function', None),
        'generated': ('C6 generated file without a GENERATED banner', None),
        'parse': ('C10 PowerShell or Python file that does not parse', None),
        'safety': ('C1 safety: header without the Network:, Writes: and Credentials: lines', None),
        'docs': ('C2 full: function without full docs (--report names the missing parts)', None)}

# Strict-gate constants (formerly code_standard_strict.py): active when `code-strict-gate: on` and no project gate exists.
PRAGMA = re.compile(r'\s*(?:#\s*(?:noqa|type:|pylint:|pyright:|mypy:|nosec|isort:|ruff:|fmt:)[^#]*)+$', re.I)
PRAGMA_START = re.compile(r'#\s*(?:(?i:noqa)|type:|pyright:|pylint:|nosec|isort:|ruff:|flake8:)')
NOQA = re.compile(r'#\s*noqa(?::[^#]*\bE501\b|(?![:\w]))', re.I)
FILE_NOQA = re.compile(r'#\s*(?:ruff|flake8)\s*:\s*(?i:noqa)(?::[^#]*\bE501\b|(?![:\w]))')
SPDX = re.compile(r'\s*#\s+SPDX-(?:License-Identifier|FileCopyrightText):\s')
ZERO_WIDTH = ('Mn', 'Me', 'Cf', 'Cc')   # unicode categories ruff counts as width 0 (combining marks, joiners, controls)
ZERO_CODES = (range(0x1160, 0x1200), range(0xD7B0, 0xD800), (0x3164, 0x302E, 0x302F, 0x16FF0, 0x16FF1))
NOT_OWNER = ('scripts/', '.py', 'agent', 'delegation')
ROW_CELLS = 4              # a DECISIONS row: date, decision, by, last (exactly: a spare cell would move the By cell)
SAFETY_LABEL = 'C1 safety: header without the Network:, Writes: and Credentials: lines, each with a value'
NEW_DEBT_FORMAT = 'FAIL  baseline: debt for a file that is new in this change: %s (%s; new files meet the rules)'

JS_FUNC = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(|'
                     r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?'
                     r'(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)|'
                     r'^\s+(?:static\s+)?(?:async\s+)?(?!(?:if|for|while|switch|catch|function|return)\b)([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{')
SH_FUNC = re.compile(r'^\s*(?:function\s+([A-Za-z_][\w-]*)\s*(?:\(\))?|([A-Za-z_][\w-]*)\s*\(\))\s*(?:\{|$)')

PS_SCRIPT = r'''
$ErrorActionPreference = 'Stop'
$out = @{}
$full = $env:CODE_STANDARD_FULL -eq '1'   # C2 full is on: read the help of each function longer than 10 lines
# Doc facts for the opt-in C2 full rule: the parameter names and what the comment-based help documents.
function Get-DocFacts($node, $help) {
  $ps = @()
  if ($node.Parameters) { $ps = @($node.Parameters) }
  elseif ($node.Body -and $node.Body.ParamBlock) { $ps = @($node.Body.ParamBlock.Parameters) }
  elseif ($node.ParamBlock) { $ps = @($node.ParamBlock.Parameters) }
  $names = @($ps | ForEach-Object { $_.Name.VariablePath.UserPath })
  $documented = @(); if ($help -and $help.Parameters) { $documented = @($help.Parameters.Keys) }
  return @{ params = $names; help = $documented; synopsis = [bool]($help -and ($help.Synopsis -or $help.Description)) }
}
foreach ($path in [Console]::In.ReadToEnd().Split("`n")) {
  if (-not $path.Trim()) { continue }
  $tokens = $null; $errors = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($path.Trim(), [ref]$tokens, [ref]$errors)
  $lines = @([System.IO.File]::ReadAllLines($path.Trim()))
  $help = @()   # comment-based help: <# #> blocks with .SYNOPSIS or .DESCRIPTION, by their first and last line
  foreach ($t in $tokens) {
    if ($t.Kind -eq 'Comment' -and $t.Text.StartsWith('<#') -and $t.Text -match '\.(SYNOPSIS|DESCRIPTION)') {
      $help += ,@($t.Extent.StartLineNumber, $t.Extent.EndLineNumber)
    }
  }
  $list = @(); $blocks = @()
  foreach ($f in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    $s = $f.Extent.StartLineNumber; $e = $f.Extent.EndLineNumber
    $brace = 0; if ($e -gt $s + 1 -and $lines[$s].Trim() -eq '{') { $brace = 1 }   # `{` on its own line after `function`
    $body = $f.Body.Extent; $first = $body.StartLineNumber + 1; $last = $body.EndLineNumber - 1   # the help is first or last in the body
    $inside = @($help | Where-Object {
      $_[0] -ge $body.StartLineNumber -and $_[1] -le $body.EndLineNumber -and ($_[0] -eq $first -or $_[1] -eq $last) }).Count -gt 0
    $inner = $inside -or (($e -gt $s + 1 + $brace) -and $lines[$s + $brace].Trim() -match '^<?#')
    $doc = $(if ($full -and $e - $s -ge 10) { Get-DocFacts $f $f.GetHelpContent() })
    $list += @{ name = $f.Name; start = $s; end = $e; inner = $inner; doc = $doc }
  }
  # A script block kept in a variable or a hashtable key ($ui.Say = { ... }) is a function too: the window code uses
  # them. Any other script block (an argument, such as $b.Add_Click({ ... })) is measured for its length only.
  foreach ($b in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ScriptBlockExpressionAst] }, $true)) {
    $p = $b.Parent; if ($p -is [System.Management.Automation.Language.CommandExpressionAst]) { $p = $p.Parent }
    if ($p -is [System.Management.Automation.Language.PipelineAst]) { $p = $p.Parent }
    $s = $b.Extent.StartLineNumber; $e = $b.Extent.EndLineNumber
    if ($p -is [System.Management.Automation.Language.AssignmentStatementAst]) {
      $doc = $(if ($full -and $e - $s -ge 10) { Get-DocFacts $b.ScriptBlock $b.ScriptBlock.GetHelpContent() })
      $list += @{ name = $p.Left.Extent.Text; start = $s; end = $e; inner = ($e -gt $s + 1) -and $lines[$s].Trim() -match '^<?#'; doc = $doc }
    } elseif ($e - $s -ge 2) {
      $call = ($b.Parent.Extent.Text -split "`n")[0]; $call = $call.Substring(0, [math]::Min(40, $call.Length)).Trim()
      $blocks += @{ name = '{block in ' + $call + '}'; start = $s; end = $e }
    }
  }
  $out[$path.Trim()] = @{ functions = $list; blocks = $blocks; errors = @(
    $errors | ForEach-Object { 'line ' + $_.Extent.StartLineNumber + ': ' + $_.Message }) }
}
$out | ConvertTo-Json -Depth 5 -Compress
'''


def is_kit(root):
    """True in the kit itself: it has kit.config.json and no `.check.lock` (a synced project has the lock)."""
    return (root / 'kit.config.json').is_file() and not (root / '.check.lock').exists()


# Debt kinds that only warn: no FAIL, not in the baseline. C1 Prevents (AUD-1; the Administrator, 2026-11-23):
# a FAIL in the kit, a WARN in a project until its debt is 0.
WARN_KINDS = () if is_kit(ROOT) else ('prevents',)


# ---------------------------------------------------------------- parsing: headers, generated blocks, functions -----

def header_block(lines, lang):
    """Return the comment block at the top of a file (rule C1), one header line per text line, so a project's gate
    can test where a label stands.

    Args:
        lines: the file's lines.
        lang: 'python', 'powershell', 'js' or 'shell'.

    Returns:
        (text, last line number); ('', 0) when there is none.
    """
    i = 0
    while i < len(lines) and (lines[i].startswith('#!') or lines[i].strip() == '' or lines[i].startswith('#Requires')):
        i += 1
    if i >= len(lines):
        return '', 0
    first = lines[i].strip()
    if lang == 'python' and first[:3] in ('"""', "'''"):
        return block_until(lines, i, first[:3], first[:3])
    if lang == 'powershell' and first.startswith('<#'):
        return block_until(lines, i, '<#', '#>')
    if lang == 'js' and first.startswith('/*'):
        return block_until(lines, i, '/*', '*/')
    mark = '//' if lang == 'js' else '#'
    text = []
    while i < len(lines) and lines[i].strip().startswith(mark):
        if not DIVIDER.match(lines[i]):   # a divider line says nothing about the file
            text.append(lines[i].strip().lstrip(mark + '/').strip())
        i += 1
    return '\n'.join(text), i


def block_until(lines, start, opener, closer):
    """Return a block comment or docstring that opens on line index `start` and ends at the first `closer`.

    Args:
        lines: the file's lines.
        start: the index (0-based) of the line that opens the block.
        opener: the text that opens it (for example `<#`).
        closer: the text that closes it.

    Returns:
        (text, last line number), the lines of the block joined by line feeds.
    """
    text = lines[start].strip()[len(opener):]
    if closer in text:
        return text.split(closer)[0], start + 1
    out, end = [text], len(lines)
    for k, line in enumerate(lines[start + 1:], start + 2):
        if closer in line:
            out.append(line.split(closer)[0])
            end = k
            break
        out.append(line)
    return '\n'.join(x.strip() for x in out), end


def generated_blocks(lines):
    """Return the (first, last) line numbers (1-based) of each marked generated block in a file."""
    blocks, start = [], None
    for i, line in enumerate(lines, 1):
        if start is None and BLOCK_BEGIN.match(line):
            start = i
        elif start is not None and line.strip().startswith(BLOCK_END):
            blocks.append((start, i))
            start = None
    return blocks


def is_generated_ok(lines):
    """C6: a generated file says GENERATED in its first 15 lines and names a source (a path or 'from')."""
    top = '\n'.join(lines[:15])
    return 'GENERATED' in top.upper() and ('from ' in top or '/' in top)


def python_functions(text):
    """Return each def of a Python file. Top is the first decorator line; an inner comment is a docstring or a `#`
    comment on the def line or as the first body line (a comment above the def is checked by measure()).

    Args:
        text: the whole file.

    Returns:
        [(qualified name, top line, first line, last line, has inner comment, body text)].
    """
    lines = text.split('\n')
    tree = ast.parse(text)
    found = []

    def visit(node, prefix):
        """Add each def under `node` to `found`, named `prefix` + name; classes and nested defs add to the prefix.

        Args:
            node: a module, class or function node.
            prefix: the qualified name so far, ending in a dot (or '').
        """
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                top = min([child.lineno] + [d.lineno for d in child.decorator_list])
                first = child.body[0].lineno if child.body else child.lineno + 1
                lead = [x.strip() for x in lines[child.lineno:first - 1]]   # lines before the first statement
                if child.body and isinstance(child.body[0], (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    while lead and lead[-1].startswith(('#', '@')):
                        lead.pop()   # comment lines that touch a nested def are that def's comment
                inner = bool(ast.get_docstring(child)) or any(x.startswith('#') for x in lead) \
                    or lines[child.lineno - 1].split(':', 1)[-1].strip().startswith('#')
                skip = 1 if ast.get_docstring(child) and len(child.body) > 1 else 0   # C5 compares code, not the docstring
                body = '\n'.join(lines[child.body[0].end_lineno if skip else child.lineno:child.end_lineno])
                found.append((name, top, child.lineno, child.end_lineno, inner, body))
                visit(child, name + '.')
            elif isinstance(child, ast.ClassDef):
                visit(child, prefix + child.name + '.')
    visit(tree, '')
    return found


def powershell_functions(root, paths, full=False):
    """Return the functions of PowerShell files, from the real PowerShell parser (pwsh).
    Functions are (name, top, first line, last line, has inner comment, body text, doc facts): each function (nested
    ones too) and each script block assigned to a variable or a hashtable key (named by the left side, for example
    `$ui.Say`). Blocks are (name, first line, last line) of the other script blocks, named by the call they are in.

    Args:
        root: the repo root (a Path).
        paths: the repo-relative paths of the PowerShell files.
        full: True when rule C2 full is on: the parser also reads each function's help.

    Returns:
        {path: (functions, blocks, parse errors)}.
    """
    if not paths:
        return {}
    env = dict(os.environ, CODE_STANDARD_FULL='1' if full else '0')
    run = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-Command', PS_SCRIPT],
                         input='\n'.join(str(root / p) for p in paths), capture_output=True, text=True, env=env)
    if run.returncode != 0:
        raise SystemExit('CODE-STANDARD fail: the PowerShell parser did not run: ' + run.stderr.strip()[:300])
    data = json.loads(run.stdout or '{}')
    result = {}

    def as_list(val):
        """Normalize dict/list/None parser field to a list."""
        return [val] if isinstance(val, dict) else (val or [])

    for p in paths:
        item = data.get(str(root / p), {})
        lines = (root / p).read_text(encoding='utf-8-sig', errors='replace').split('\n')
        funcs = [(f['name'], f['start'], f['start'], f['end'], f['inner'], '\n'.join(lines[f['start']:f['end']]),
                  f.get('doc')) for f in as_list(item.get('functions'))]
        blocks = [(b['name'], b['start'], b['end']) for b in as_list(item.get('blocks'))]
        errors = item.get('errors') or []
        result[p] = (funcs, blocks, [errors] if isinstance(errors, str) else errors)
    return result


def brace_functions(text, pattern, comment_mark):
    """Return the functions of a JavaScript or shell file found by a line pattern; the end of a function is the line
    where the braces opened on its first line close again.

    Args:
        text: the whole file.
        pattern: JS_FUNC or SH_FUNC.
        comment_mark: '//' or '#'.

    Returns:
        [(name, top line, first line, last line, has inner comment, body text)].
    """
    lines = text.split('\n')
    found = []
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if not m:
            continue
        name = next(g for g in m.groups() if g)
        arrow = '=>' in line and m.lastindex == 2   # `const f = (...) =>`: its body must open on this line or the next
        depth, end, opened = 0, i, False
        for j in range(i, len(lines)):
            if not opened and j > i + (1 if arrow else 40 if re.search(r'\bfunction\b', line) else 10):
                break   # no body opens: an arrow's opens on its line or the next, a `function` within 40 lines, others 10
            depth, opened = count_braces(lines[j], depth, opened, comment_mark)
            if opened and depth <= 0:
                end = j
                break
        if not opened:
            if arrow:   # an arrow with no braces (`const f = x => x + 1;`) is a one-line function
                found.append((name, i + 1, i + 1, i + 1, False, line))
            continue
        own = '{' not in line and i + 1 < len(lines) and lines[i + 1].strip() == '{'
        k = i + 2 if own else i + 1   # skip the body's `{` when it stands on its own line
        first = lines[k].strip() if end > k else ''   # a one-line function has no inner first line
        found.append((name, i + 1, i + 1, end + 1, first.startswith(comment_mark), '\n'.join(lines[i + 1:end + 1])))
    return found


def count_braces(line, depth, opened, comment_mark):
    """Add the `{` and `}` of one line (outside quotes and comments) to the running depth. A shell `#` starts a
    comment only at the start of a word, so `${#list[@]}` and `${name#prefix}` count as code.

    Args:
        line: one line of the file.
        depth: the brace depth before this line.
        opened: True when a `{` was seen before this line.
        comment_mark: '//' or '#'.

    Returns:
        (depth, opened) after this line.
    """
    quote = None
    k = 0
    while k < len(line):
        c = line[k]
        if quote:
            if c == '\\' and quote != "'":
                k += 1
            elif c == quote:
                quote = None
        elif line.startswith(comment_mark, k) and (comment_mark != '#' or k == 0 or line[k - 1] in ' \t;'):
            break
        elif c in '"\'`':
            quote = c
        elif c == '{':
            depth += 1
            opened = True
        elif c == '}':
            depth -= 1
        k += 1
    return depth, opened


def has_comment_above(lines, top, header_last):
    """True when the line right above line `top` (1-based) is a comment that is not part of the file header and not a
    divider line. A comment block that ends there counts (its last line is checked)."""
    if top < 2 or top - 1 <= header_last:
        return False
    above = lines[top - 2].strip()
    if DIVIDER.match(above):
        return False
    return above.startswith(('#', '//')) or above.endswith(('*/', '#>'))


# ---------------------------------------------------------------- C2 full documentation -------------------------------

def python_docs(text):
    """Map each def's line number to its doc facts, for a Python file.

    Args:
        text: the whole file.

    Returns:
        {def line: (parameter names, docstring or '', True when it returns a value)}.
    """
    facts = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            names = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs]
            names += [x.arg for x in (a.vararg, a.kwarg) if x]
            names = [n for n in names if n not in ('self', 'cls')]
            own = [n for n in ast.walk(node) if isinstance(n, ast.Return) and n.value is not None
                   and not (isinstance(n.value, ast.Constant) and n.value.value is None)
                   and owner_of(node, n)]
            facts[node.lineno] = (names, ast.get_docstring(node) or '', bool(own))
    return facts


def owner_of(func, ret):
    """True when the return statement `ret` belongs to `func` itself, not to a function nested in it.

    Args:
        func: the function node.
        ret: a Return node somewhere inside it.

    Returns:
        True or False.
    """
    for node in ast.walk(func):
        if node is not func and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if any(x is ret for x in ast.walk(node)):
                return False
    return True


def python_missing(facts, def_line):
    """Return the missing parts of one Python function's docs, as short labels (an empty list when complete).

    Args:
        facts: the result of python_docs() for the file.
        def_line: the line of the `def`.

    Returns:
        A list such as ['docstring'], ['Args: x'] or ['Returns:'].
    """
    names, doc, returns = facts.get(def_line, ([], '', False))
    if not doc:
        return ['docstring']
    miss = []
    if names:
        args = re.split(r'^\s*Args:\s*$', doc, maxsplit=1, flags=re.M)
        listed = args[1] if len(args) == 2 else ''
        listed = re.split(r'^\s*(?:Returns?|Raises|Yields|Examples?|Notes?):', listed, maxsplit=1, flags=re.M)[0]
        miss += ['Args: ' + n for n in names
                 if not re.search(r'^\s*\*{0,2}%s\s*(\(.*\))?:' % re.escape(n), listed, re.M)]   # `name:` or `name (type):`
    if returns and not re.search(r'^\s*Returns?:', doc, re.M):
        miss.append('Returns:')
    return miss


def powershell_missing(doc):
    """Return the missing parts of one PowerShell function's help, from what the parser reported.

    Args:
        doc: {"params": [names], "help": [.PARAMETER names, upper case], "synopsis": bool}, or None when the parser
             gave nothing.

    Returns:
        A list such as ['help'] or ['.PARAMETER Path'].
    """
    if not doc or not doc.get('synopsis'):
        return ['help']
    known = {str(n).upper() for n in (doc.get('help') or [])}
    return ['.PARAMETER ' + p for p in (doc.get('params') or []) if p.upper() not in known]


def js_params(lines, start):
    """Return the parameter names of the JavaScript function that starts on line `start` (1-based).

    Args:
        lines: the file's lines.
        start: the line of the function's signature.

    Returns:
        Names in order; a destructured parameter ({a, b} or [a]) is returned as '' (any @param name covers it).
    """
    text = ' '.join(lines[start - 1:start + 9])
    sig = re.split(r'=>|\{', text, maxsplit=1)[0] if '(' not in text.split('=>')[0] else text
    open_at = sig.find('(')
    if open_at < 0:
        m = re.search(r'=\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*=>', text)   # `const f = x => ...`, `= async x =>`
        return [m.group(1)] if m else []
    depth, out, cur, quote = 0, [], '', None
    for c in text[open_at + 1:]:   # the text after the `(` of the parameter list
        if quote or c in '"\'`':
            quote = None if c == quote else (quote or c)
            cur += c
            continue
        if depth == 0 and c == ')':
            break
        if depth == 0 and c == ',':
            out.append(cur)
            cur = ''
            continue
        depth += (c in '([{') - (c in ')]}')
        cur += c
    out.append(cur)
    names = []
    for raw in out:
        p = raw.split('=')[0].strip().lstrip('.')
        if p:
            names.append('' if p[0] in '{[' else p)
    return names


def js_missing(lines, top, start, body):
    """Return the missing parts of one JavaScript function's JSDoc.

    Args:
        lines: the file's lines.
        top: the first line of the function (1-based).
        start: the line of its signature.
        body: the function's text.

    Returns:
        A list such as ['JSDoc'], ['@param a'] or ['@returns'].
    """
    k = top - 2
    if k < 0 or not lines[k].strip().endswith('*/'):
        return ['JSDoc']
    while k >= 0 and '/*' not in lines[k]:
        k -= 1   # the start of the comment block that ends right above the function
    if k < 0 or '/**' not in lines[k]:
        return ['JSDoc']   # a plain /* */ comment is not JSDoc
    doc = '\n'.join(lines[k:top - 1])
    tags = re.findall(r'@param\s+(?:\{(?:[^{}]|\{[^{}]*\})*\}\s*)?\[?([\w$.]+)', doc)   # a type may hold one {} level
    miss = []
    for i, name in enumerate(js_params(lines, start)):
        if (name and name not in tags) or (not name and len([t for t in tags if '.' not in t]) <= i):
            miss.append('@param ' + (name or '#%d' % (i + 1)))
    if js_returns_value(body) and not re.search(r'@returns?\b', doc):
        miss.append('@returns')
    return miss


def js_returns_value(body):
    """True when the function body returns a value itself (a `return x` at its own brace level, not in a nested callback).

    Args:
        body: the function's lines after its signature line, up to its closing brace.

    Returns:
        True or False.
    """
    lines = body.split('\n')
    depth = -1 if lines and lines[0].strip() == '{' else 0   # the body's `{` on its own line opens level 0
    quote = None
    for line in lines:
        code = line.split('//')[0]
        for k, c in enumerate(code):
            if quote:
                quote = None if c == quote else quote
            elif c in '"\'`':
                quote = c
            elif c in '{}':
                depth += 1 if c == '{' else -1
            elif depth == 0 and RETURNS_VALUE.match(code, k) and (k == 0 or not code[k - 1].isalnum()):
                return True
    return False


def docs_missing(lang, lines, func, extra, py_facts):
    """Return the missing parts of one function's full docs, or [] when they are complete or not required.

    Args:
        lang: 'python', 'powershell', 'js' or 'shell'.
        lines: the file's lines.
        func: (name, top, first line, last line, has inner comment, body), as found by file_functions().
        extra: the PowerShell parser's doc facts for this function, or None.
        py_facts: python_docs() of the file, or None for other languages.

    Returns:
        A list of short labels.
    """
    _, top, start, end, _, body = func
    if end - start + 1 <= SHORT_FUNCTION:
        return []
    if lang == 'python':
        return python_missing(py_facts or {}, start)
    if lang == 'powershell':
        return powershell_missing(extra)
    if lang == 'js':
        return js_missing(lines, top, start, body)
    return []


# ---------------------------------------------------------------- built-in strict gate -------------------------------

def safety_ok(head):
    """C1 safety: each label starts a line of the header (after comment characters and spaces) and has a value.

    Args:
        head: the header text, one header line per text line.

    Returns:
        True when Network:, Writes: and Credentials: each start a line and are followed by a value on it.
    """
    lines = head.split('\n')
    return all(any(re.match(r'^[\s#/*]*' + re.escape(x) + r'\s*\S', line) for line in lines) for x in SAFETY_LABELS)


def longest_line(lines, skip, cap=0):
    """Return the width of the longest line outside the generated blocks; for a Python file, as ruff's E501 counts it.

    Args:
        lines: the lines of the file.
        skip: the (first, last) line numbers of the generated blocks (1-based).
        cap: 0 for a non-Python file (the length in characters); else the cap: the width as ruff counts it, and a
            line that ruff's E501 also lets pass does not count (ruff_ok).

    Returns:
        The width of the longest counted line, 0 for none.
    """
    info = python_comments(lines) if cap else None
    if info and info[2]:
        return 0   # a file-level ruff or flake8 noqa directive, blanket or for E501
    keep, seen = [], {}
    for i, x in enumerate(lines, 1):
        x = x.rstrip('\r')
        if any(a <= i <= b for a, b in skip):
            continue
        if not cap:
            keep.append(len(x))
        elif info is None:
            keep += [] if ruff_ok(x, cap) else [width(x)]
        else:
            cols, owner = info[0], info[1].get(i, i)   # the noqa of a multi-line string or continuation: on its end line
            if owner not in seen:   # each end line's comment is read once (no N lines x L comment work)
                seen[owner] = '# noqa' if owner in cols and NOQA.search(lines[owner - 1], cols[owner]) else ''
            keep += [] if ruff_ok(x, cap, cols.get(i, -1), seen[owner]) else [width(x)]
    return max(keep or [0])


def python_comments(lines):
    """Read the comments of a Python text with tokenize, so that `# noqa` in a string is no comment, as for ruff.

    Args:
        lines: the lines of the file.

    Returns:
        ({line: column of its comment}, {line: the line whose comment can hold its noqa}, True for a file-level noqa),
        or None when the text does not tokenize (then each line is read whole). A multi-line string and a backslash
        continuation take the noqa of the line where they end, as in ruff.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO('\n'.join(lines)).readline))
    except (tokenize.TokenError, SyntaxError):
        return None
    cols = {t.start[0]: t.start[1] for t in tokens if t.type == tokenize.COMMENT}
    owner = {r: t.end[0] for t in tokens if t.end[0] > t.start[0] and t.type != tokenize.COMMENT
             for r in range(t.start[0], t.end[0])}
    for i in range(len(lines) - 1, 0, -1):   # a backslash at the end of a code line joins it to the next line
        if i not in owner and i not in cols and lines[i - 1].rstrip('\r').endswith('\\'):
            owner[i] = owner.get(i + 1, i + 1)
    for r in sorted(owner, reverse=True):   # chains: a string that ends on a line where another one or a continuation starts
        owner[r] = owner.get(owner[r], owner[r])
    whole = any(FILE_NOQA.search(lines[r - 1], c) and not lines[r - 1][:c].strip() for r, c in cols.items())
    return cols, owner, whole


def width(text):
    """The width of a line as ruff counts it: a wide or full-width character counts 2, a combining mark, joiner or
    control character 0, Hangul vowel and final jamo 0, and a tab adds the step to the next tab stop of 4 (ruff's default
    indent-width) of a column that counts characters.

    Args:
        text: the line, without its line end.

    Returns:
        The width in columns.
    """
    n = col = 0   # ruff: the column counts characters and goes to the next tab stop at a tab; the width adds that step
    for ch in text:
        if ch == '\t':
            n, col = n + 4 - col % 4, col + 4 - col % 4
        else:
            n += 0 if unicodedata.category(ch) in ZERO_WIDTH or any(ord(ch) in z for z in ZERO_CODES) else (
                2 if unicodedata.east_asian_width(ch) in 'WF' else 1)
            col += 1
    return n


def ruff_ok(line, cap, comment=None, noqa=None):
    """True for a long Python line that ruff's E501 lets pass: a `# noqa` for all codes or for E501 (any case); a line
    that is long only by a comment that starts with one of ruff's pragmas (`# noqa: ...`, `# type:`, `# pylint:`,
    `# nosec` and the like); a `# SPDX-` comment line; one word with no space; or a last word that holds :// and starts
    at or before the cap (the line ends with a URL).

    Args:
        line: the line, without its line end.
        cap: the line cap.
        comment: the column of the line's real comment (python_comments), -1 for none; None reads the whole line,
            with a trailing run of pragma comments as the pragma.
        noqa: the comment that can hold the line's noqa (the end line of a multi-line string or a continuation);
            None: the line's own comment.

    Returns:
        True when ruff's E501 does not fail the line.
    """
    tail = line if comment is None else line[comment:] if comment >= 0 else ''
    if NOQA.search(tail if noqa is None else noqa) or SPDX.match(line):
        return True
    body = PRAGMA.sub('', line) if comment is None else line[:comment].rstrip() if PRAGMA_START.match(tail) else line
    if width(body) <= cap:
        return True
    words = body.split()
    return len(words) <= 1 or ('://' in words[-1] and width(body) - width(words[-1]) <= cap)


def owner_role_in(text):
    """Return the Administrator role from the "- Owner:" line of an AGENTS.md text, lower case, without a leading "the "
    ('' if the text has no such line)."""
    m = re.search(r'^- Owner:\s*(.+?)\s*$', text, re.M)
    return re.sub(r'^the\s+', '', m.group(1).rstrip('.').lower()) if m else ''


def owner_role(root):
    """Return the Administrator role from the AGENTS.md file under `root` (owner_role_in; '' when there is no file)."""
    try:
        return owner_role_in((Path(root) / 'AGENTS.md').read_text(encoding='utf-8'))
    except OSError:
        return ''


def squeeze(text):
    """Return `text` with all white space removed, so two rows that differ only in spacing are equal."""
    return re.sub(r'\s+', '', text)


def row_refusal(text, name, owner, names=None):
    """Return why a DECISIONS line is not a new owner's row for file `name`, or None when it is one.

    Args:
        text: a line of docs/DECISIONS.md that main does not have.
        name: the settings file name the decision cell must name.
        owner: the Administrator role (owner_role), lower case.
        names: a test that says whether a text names the file (None: the text holds `name`).

    Returns:
        The refusal (which rule refused it) or None.
    """
    row = text.strip()
    if not row.startswith('|'):
        return 'rule 1: not a table row (a line that starts with |)'
    cells = [c.replace('\0', '|').strip() for c in row.replace('\\|', '\0').strip('|').split('|')]
    if len(cells) != ROW_CELLS:
        return 'rule 1: a decision row has %d cells: date, decision, by, last (write \\| for a | inside a cell)' % ROW_CELLS
    if not (names(cells[1]) if names else name in cells[1]):
        return 'rule 2: the decision cell does not name ' + name
    by = cells[2].lower()
    bad = [x for x in NOT_OWNER if x in by]
    if bad:
        return 'rule 3: the By cell names a script or an agent (%s)' % bad[0]
    if not owner:
        return 'rule 4: AGENTS.md has no "- Owner:" line to name the Administrator'
    if not re.fullmatch(r'(the\s+)?' + re.escape(owner) + r'(\s*\([^()]*\))?', by):
        return 'rule 4: the By cell is not the Administrator alone (%s; one note in brackets may follow)' % owner
    return None


def owner_row(new_text, name, owner, old_text='', names=None):
    """Compare docs/DECISIONS.md with its text on the merge base and look for the Administrator's new row that opens the
    ratchet gate. The gate opens only in a change that adds rows and leaves every older row as it was.

    Args:
        new_text: docs/DECISIONS.md as it is in this change.
        name: the settings file name.
        owner: the Administrator role (owner_role_in).
        old_text: docs/DECISIONS.md at the merge base ('' when there is none).
        names: a test that says whether a text names the file (None: the text holds `name`).

    Returns:
        (True, []) when a new table row names `name` and has the Administrator alone in its By cell, and no older row was
        edited or removed; else (False, the refusal lines, each with the rule that refused).
    """
    def table(text):
        """Return squeezed table lines of `text`."""
        return {squeeze(x) for x in text.split('\n') if x.strip().startswith('|')}
    old_lines = {squeeze(x) for x in old_text.split('\n')}
    refusals, found = [], False
    for line in new_text.split('\n'):
        if not (names(line) if names else name in line) or squeeze(line) in old_lines:
            continue
        why = row_refusal(line, name, owner, names)
        found = found or why is None
        if why:
            refusals.append('REFUSED  docs/DECISIONS.md line (%s): %s' % (why, line.strip()[:60]))
    touched = sorted(table(old_text) - table(new_text))
    if found and touched:
        return False, ['REFUSED  docs/DECISIONS.md (rule 5: this change also edits or removes %d older row(s), first: %s; '
                       'record the decision in a change that only adds its row)' % (len(touched), touched[0][:40])]
    return found, ([] if found else refusals)


def exists_at(root, ref, path):
    """True when `path` exists in the commit `ref` (git cat-file -e); a file that does not is new in this change."""
    return subprocess.run(['git', '-C', str(root), 'cat-file', '-e', '%s:%s' % (ref, path)],
                          capture_output=True).returncode == 0


def at_ref(root, ref, path):
    """Return the text of `path` in the commit `ref` ('' when it has none); bytes are read, so a lone CR stays in its line."""
    out = subprocess.run(['git', '-C', str(root), 'show', '%s:%s' % (ref, path)], capture_output=True)
    return out.stdout.decode('utf-8', 'replace') if out.returncode == 0 else ''


class StrictGate:
    """Built-in strict code-standard rules (`code-strict-gate: on` in `.check`)."""

    __file__ = __file__
    RULES = {'safety': (SAFETY_LABEL, None), 'line': ('C4 line longer than %d characters', 'max_line_chars')}
    OPT_IN = {'line': lambda c: 1 if c.get('caps', {}).get('max_line_chars') else 0}

    @staticmethod
    def file_rules(v, p, lines, head, config, skip):
        """Write strict C1 safety and line-length violations into `v`."""
        if config.get('c1_safety') and not safety_ok(head):
            v['safety'][p] = 1
        cap = config['caps'].get('max_line_chars')
        py = p.endswith('.py') and not skip   # without ruff and pylint, measured here as ruff's E501 would
        longest = longest_line(lines, skip, cap if py else 0) if cap else 0
        if cap and longest > cap and not (py and LINTERS):
            v['line'][p] = longest

    @staticmethod
    def decided(root, ref):
        """Return whether this change records the Administrator's decision on `.check` (owner_row)."""
        here = Path(root) / 'docs' / 'DECISIONS.md'
        text = here.read_bytes().decode('utf-8', 'replace') if here.is_file() else ''
        return owner_row(text, settings.CHECK, owner_role_in(at_ref(root, ref, 'AGENTS.md')),
                         at_ref(root, ref, 'docs/DECISIONS.md'), settings.NAMES_CHECK.search)

    @staticmethod
    def new_debt_refusal(root, ref, kind, key):
        """Refuse debt for a file that is new in this change."""
        if exists_at(root, ref, key.split('::')[0]):
            return None
        return NEW_DEBT_FORMAT % (key, kind)


STRICT_GATE = StrictGate()


# ---------------------------------------------------------------- rules, gates and file list --------------------------

def gate_settings(config):
    """Return the `code-` lines in a config that only a gate enforces (the check fails when one is set with no gate)."""
    lines = ['code-' + settings.dash(c) for c in settings.OPT_IN_CAPS if c in config['caps']]
    return lines + (['code-c1-safety: ' + settings.STRICT] if config.get('c1_safety') == settings.STRICT else [])


def matches(rel, patterns):
    """True when the path matches one of the glob patterns (fnmatch; `*` also matches `/`)."""
    return any(fnmatch.fnmatch(rel, p) for p in patterns)


def load_gate(path=None):
    """Load a project's own gate module when its file exists.

    Args:
        path: the gate file; None = GATE_FILE (next to this file).

    Returns:
        The module, or None when there is no such file. ValueError when the file cannot be imported or lacks one of
        GATE_NAMES in the documented shape (the check then fails: a broken gate is never skipped).
    """
    path = Path(path or GATE_FILE)
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location('code_standard_gate', str(path))
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
    except BaseException as err:   # noqa: B036 - any error or exit of the project's file: the check fails with its name
        raise ValueError('the gate %s cannot be loaded (%s: %s)' % (path.name, err.__class__.__name__, err)) from None
    lacks = [n for n in GATE_NAMES if not hasattr(gate, n)]
    if lacks:
        raise ValueError('the gate %s lacks %s (the entry points: the header of scripts/code_standard.py)'
                         % (path.name, ', '.join(lacks)))
    shaped = isinstance(gate.RULES, dict) and isinstance(gate.OPT_IN, dict) \
        and all(isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], str) for r in gate.RULES.values()) \
        and all(callable(x) for x in list(gate.OPT_IN.values()) + [gate.file_rules, gate.decided, gate.new_debt_refusal])
    if not shaped:
        raise ValueError('the gate %s has a wrong shape: RULES is {kind: (label, caps key or None)}, OPT_IN is '
                         '{kind: function}, the three other names are functions' % path.name)
    return gate


def rules():
    """Return {debt kind: (label, caps key or None)}: the kit's rules (RULE), with those a gate adds or relabels."""
    return dict(RULE, **(GATE.RULES if GATE else {}))


def level(kind, config):
    """Return how far the opt-in rule of debt kind `kind` is adopted in `config` (0 = off or not an opt-in kind)."""
    known = dict(OPT_IN, **(GATE.OPT_IN if GATE else {}))
    return int(known[kind](config)) if kind in known else 0


def tracked_files(config):
    """Return the repo-relative paths that the standard covers: tracked files with a known extension that match
    `include` and no `exclude` pattern. Paths that match `generated` are returned too (they get check C6 only).

    Args:
        config: the code standard settings.

    Returns:
        The sorted list of paths.
    """
    out = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, text=True, check=True).stdout
    keep = []
    for rel in out.split('\0'):
        if not rel or (lang_of(rel) is None and not matches(rel, config.get('generated', []))):
            continue
        if not matches(rel, config.get('include', ['*'])) or matches(rel, config.get('exclude', [])):
            continue
        if (ROOT / rel).is_file():
            keep.append(rel)
    return sorted(keep)


def lang_of(rel):
    """Return the language of a file: by its extension, or for a file with no extension by its shebang line
    (sh or bash: shell; python: python); None for any other file.

    Args:
        rel: the repo-relative path.

    Returns:
        'python', 'powershell', 'js', 'shell' or None.
    """
    suffix = Path(rel).suffix
    if suffix:
        return LANGS.get(suffix)
    try:
        first = (ROOT / rel).read_bytes()[:80].split(b'\n')[0].decode('ascii', 'replace')
    except OSError:
        return None
    if first.startswith('#!') and re.search(r'\b(ba)?sh\b', first):
        return 'shell'
    if first.startswith('#!') and 'python' in first:
        return 'python'
    return None


def file_functions(p, text, lang, ps):
    """Return the functions of one source file, in the shapes powershell_functions() gives.

    Args:
        p: the repo-relative path.
        text: the whole file.
        lang: its language (lang_of).
        ps: the result of powershell_functions() for the repo's PowerShell files.

    Returns:
        (functions, blocks, parse errors).
    """
    if lang == 'powershell':
        return ps[p]
    if lang == 'python':
        try:
            return python_functions(text), [], []
        except SyntaxError as err:   # C10 for Python: ruff and pylint in scripts/check.sh; this check only without them
            return [], [], [] if LINTERS else ['line %s: %s' % (err.lineno, err.msg)]
    pattern, mark = (JS_FUNC, '//') if lang == 'js' else (SH_FUNC, '#')
    return brace_functions(text, pattern, mark), [], []


def unique_key(p, name, seen):
    """Return the debt key of a function: "<path>::<name>", with "#2", "#3" for the next ones of the same name."""
    seen[name] = seen.get(name, 0) + 1
    return '%s::%s' % (p, name if seen[name] == 1 else '%s#%d' % (name, seen[name]))


def function_rules(v, entry, p, lines, func, extra, ctx):
    """Write the violations of one function into `v` (C2 comment, C2 full, C3 length) and note its body for C5.

    Args:
        v: the violations dict, changed in place.
        entry: the report entry of the file; its "functions" list gets this function.
        p: the repo-relative path.
        lines: the file's lines.
        func: (name, top, first line, last line, has inner comment, body text).
        extra: the PowerShell parser's doc facts for this function, or None.
        ctx: per-file facts: lang, head_last, seen, full, py, cap and bodies.
    """
    name, top, start, end, inner, body = func
    key = unique_key(p, name, ctx['seen'])
    size, commented = end - start + 1, inner or has_comment_above(lines, top, ctx['head_last'])
    entry['functions'].append({'name': name, 'start': start, 'lines': size, 'comment': commented})
    if not commented:
        v['comment'][key] = 1
    gaps = docs_missing(ctx['lang'], lines, func, extra, ctx['py']) if ctx['full'] else []
    if gaps:
        v['docs'][key] = 1
        entry['functions'][-1]['docs_missing'] = gaps
    if size > ctx['cap']:
        v['length'][key] = size
    norm = '\n'.join(x.strip() for x in body.split('\n') if x.strip() and not x.strip().startswith(('#', '//')))
    if norm.count('\n') + 1 >= MIN_DUP_LINES:
        ctx['bodies'].setdefault(hashlib.sha256(norm.encode()).hexdigest()[:12], []).append(key)


def entry_points(root):
    """Return the check entry points of a repo: the non-test scripts (scripts/*.py and scripts/*.sh) that a file that
    runs checks names (scripts/check.sh, a git hook, a Claude Code hook setting or a workflow). A *_test file never counts.

    Args:
        root: the repo root (a Path).

    Returns:
        A set of repo-relative paths of scripts that exist.
    """
    files = [root / f for f in ENTRY_FILES] + sorted((root / 'scripts/git-hooks').glob('*')) \
        + sorted((root / '.github/workflows').glob('*.y*ml'))
    text = '\n'.join(f.read_text(encoding='utf-8', errors='replace') for f in files if f.is_file())
    named = set(re.findall(r'scripts/[\w.-]+?\.(?:py|sh)\b', text))
    return {n for n in named if (root / n).is_file() and not re.search(r'_test|^test_', n.split('/')[-1])}


def warn_lines(now, caps, limit=10):
    """Return the WARN lines of the kinds in WARN_KINDS (e.g. `prevents` in a project)."""
    out = []
    for kind in WARN_KINDS:
        items = sorted(now.get(kind, {}).items(), key=lambda kv: (-kv[1], kv[0]))
        label = RULE[kind][0] % caps.get(RULE[kind][1], 0) if RULE[kind][1] else RULE[kind][0]
        out += ['WARN  %s: %s%s' % (label, k, '' if v == 1 else ' (%d)' % v) for k, v in items[:limit]]
        if len(items) > limit:
            out.append('WARN  %s: and %d more (--report lists every file)' % (label, len(items) - limit))
    return out


def summary(v):
    """One line: the count of each kind of debt."""
    return ', '.join('%s %d' % (k, len(items)) for k, items in v.items())


# ---------------------------------------------------------------- measure ---------------------------------------------

def file_rules(v, p, lines, head, config, skip):
    """Write the per-file violations of one source file into `v`: C1 header and C1 safety;
    then a project's own gate (or built-in strict gate) adds its per-file rules.

    Args:
        v: the violations dict {kind: {key: value}}, changed in place.
        p: the repo-relative path.
        lines: the file's lines.
        head: the header text (header_block).
        config: the code standard settings.
        skip: the (first, last) line numbers of the generated blocks.
    """
    if len(head) < MIN_HEADER_CHARS:
        v['header'][p] = 1
    if config.get('c1_safety') and not all(x in head for x in SAFETY_LABELS):
        v['safety'][p] = 1
    if GATE:
        GATE.file_rules(v, p, lines, head, config, skip)


def measure_file(v, p, config, ps, bodies, entries=()):
    """Measure one hand-written source file: its per-file rules, its functions and its script blocks.

    Args:
        v: the violations dict, changed in place.
        p: the repo-relative path.
        config: the code standard settings.
        ps: the result of powershell_functions() for the repo's PowerShell files.
        bodies: {body hash: [keys]} of the functions seen so far (rule C5), changed in place.
        entries: the check entry points (entry_points): one of them needs a "Prevents:" header line (C1).

    Returns:
        The report entry of the file.
    """
    text = (ROOT / p).read_text(encoding='utf-8-sig', errors='replace')
    lines, lang = text.split('\n'), lang_of(p)
    funcs, blocks, errors = file_functions(p, text, lang, ps)
    head, head_last = header_block(lines, lang)
    entry = {'lines': len(lines), 'header': len(head), 'functions': [], 'blocks': [], 'errors': errors}
    if errors:
        v['parse'][p] = len(errors)
    skip = generated_blocks(lines)
    file_rules(v, p, lines, head, config, skip)
    if p in entries and not PREVENTS.search(head):
        v['prevents'][p] = 1
    full, py = config.get('c2') == 'full' and not errors, None
    if full and lang == 'python':
        try:
            py = python_docs(text)
        except SyntaxError:   # the parse error is C10 (here, or ruff and pylint); no docs check on a file that does not parse
            full = False
    ctx = {'lang': lang, 'head_last': head_last, 'seen': {}, 'full': full, 'bodies': bodies, 'py': py,
           'cap': config['caps']['max_function_lines']}
    for name, top, start, end, inner, body, *extra in funcs:
        if not any(a <= start <= b for a, b in skip):
            function_rules(v, entry, p, lines, (name, top, start, end, inner, body), extra[0] if extra else None, ctx)
    for name, start, end in blocks:
        if any(a <= start <= b for a, b in skip):
            continue
        key = unique_key(p, name, ctx['seen'])
        entry['blocks'].append({'name': name, 'start': start, 'lines': end - start + 1})
        if end - start + 1 > ctx['cap']:
            v['length'][key] = end - start + 1
    return entry


def python_files(config, kind):
    """The Python files that scripts/check.sh gives to ruff and pylint: the hand-written files this check covers
    (include, exclude and generated as for every rule). A file with a generated block is left out of the `line` list,
    because linters cannot skip the lines of a block (the strict gate measures its hand-written lines); its parse
    and other checks stay in the `all` list.

    Args:
        config: the code standard settings.
        kind: 'all' or 'line'.

    Returns:
        The paths, each followed by a NUL character.
    """
    out = ''
    for p in tracked_files(config):
        if lang_of(p) != 'python' or matches(p, config.get('generated', [])):
            continue
        if kind == 'line' and generated_blocks((ROOT / p).read_text(encoding='utf-8-sig', errors='replace').split('\n')):
            continue
        out += p + '\0'
    return out


def shell_files(config):
    """The shell files that scripts/check.sh gives to shellcheck: the hand-written shell files this check covers.

    Args:
        config: the code standard settings.

    Returns:
        The paths, each followed by a NUL character.
    """
    return ''.join(p + '\0' for p in tracked_files(config) if lang_of(p) == 'shell' and not matches(p, config.get('generated', [])))


def measure(config):
    """Measure every covered file.

    Args:
        config: the code standard settings.

    Returns:
        {"files": {path: {...}}, "violations": {kind: {key: value}}}.
    """
    files = tracked_files(config)
    generated = [p for p in files if matches(p, config.get('generated', []))]
    source = [p for p in files if p not in generated]
    ps = powershell_functions(ROOT, [p for p in source if lang_of(p) == 'powershell'], config.get('c2') == 'full')
    report, v = {}, {k: {} for k in rules()}
    bodies, entries = {}, entry_points(ROOT)
    for p in generated:
        if not is_generated_ok((ROOT / p).read_text(encoding='utf-8-sig', errors='replace').split('\n')):
            v['generated'][p] = 1
    for p in source:
        report[p] = measure_file(v, p, config, ps, bodies, entries)
    for keys in bodies.values():
        if len(keys) > 1:
            for k in keys:
                v['duplicate'][k] = len(keys)
    return {'files': report, 'violations': v}


# ---------------------------------------------------------------- ratchet and main ------------------------------------

def git(*args):
    """Run git in the repo root; return the finished process (text output)."""
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)


def decided_at(ref):
    """Return (True when this change records the Administrator's decision on `.check`, refusal lines)."""
    if GATE:
        return GATE.decided(ROOT, ref)
    return any(x.startswith('+') and settings.NAMES_CHECK.search(x)
               for x in git('diff', ref, '--', 'docs/DECISIONS.md').stdout.split('\n')), []


def compare_debt_items(debt, old_debt, config, old_config, ref, decided):
    """Compare baseline debt entries against main's debt list and gate refusals.

    Args:
        debt: the debt dict of the working tree.
        old_debt: the debt dict on the merge base.
        config: the working tree's code standard settings.
        old_config: the merge base's code standard settings.
        ref: the merge base commit SHA.
        decided: True when the Administrator's decision row is recorded.

    Returns:
        List of FAIL problem strings.
    """
    problems = []
    for kind, items in debt.items():
        adopting = level(kind, config) > level(kind, old_config)
        was = old_debt.get(kind, {})
        for key, value in sorted(items.items()):
            refused = GATE.new_debt_refusal(ROOT, ref, kind, key) if GATE and key not in was else None
            if refused:
                problems.append(refused)
            elif adopting and decided:
                continue   # an opt-in rule turned on or raised now (--adopt): its list is the Administrator's decision
            elif key not in was:
                problems.append('FAIL  baseline: %s item added by hand: %s' % (kind, key))
            elif value > was[key]:
                problems.append('FAIL  baseline: %s value raised: %s (%d to %d)' % (kind, key, was[key], value))
    return problems


def against_main(config, debt):
    """Return (problem lines, note): compare settings and debt with the merge base against origin/main.

    Args:
        config: the code standard settings of the working tree.
        debt: the debt list of the working tree.

    Returns:
        (problem lines, note).
    """
    mb = git('merge-base', 'HEAD', 'origin/main')
    if mb.returncode != 0:
        if os.environ.get('CI'):
            return ['FAIL  baseline: no merge base with origin/main, so the baseline cannot be compared'], ''
        return [], 'WARN  baseline not compared with main (no origin/main here)'
    ref = mb.stdout.strip()
    try:
        old = settings.code_base(ROOT, ref)
    except ValueError as err:
        return ['FAIL  baseline: the settings or the baseline on the merge base cannot be read (%s)' % err], ''
    if old is None:
        return [], 'NOTE  no baseline on main yet: this change starts it'
    old_config, old_debt = old
    decided, refusals = decided_at(ref)
    orphans = sorted(k for k, items in old_debt.items() if items and k not in rules())
    problems = ['FAIL  baseline: main holds %s debt, but no rule here knows that kind (is %s missing?); removing a '
                'rule needs a docs/DECISIONS.md row that names %s' % (k, GATE_FILE.name, settings.CHECK)
                for k in orphans if not decided]
    problems += compare_debt_items(debt, old_debt, config, old_config, ref, decided)
    if config != old_config and not decided:
        problems.append('FAIL  baseline: a `code-` setting of %s (caps, scope or an opt-in rule) changed with no '
                        'docs/DECISIONS.md row that names %s (a cap or scope change is the Administrator\'s decision)'
                        % (settings.CHECK, settings.CHECK))
    return problems + (list(refusals) if problems and not decided else []), ''


def compare(now, debt, caps):
    """Compare the measured violations with the debt list.

    Args:
        now: the violations measured now {kind: {key: value}}.
        debt: the baseline's debt list, in the same shape.
        caps: the caps of the settings.

    Returns:
        (new problems, fixed items). New: a violation not in the debt, or a debt value that grew. Fixed: a debt item
        that is gone or smaller (the baseline must be lowered in the same change).
    """
    new, fixed = [], []
    table = rules()
    for kind, items in now.items():
        if kind in WARN_KINDS or kind not in table:   # warning-only or retired rule kind
            continue
        text, cap = table[kind]
        label = text % caps.get(cap, 0) if cap else text
        old = debt.get(kind, {})
        for key, value in sorted(items.items()):
            if key not in old:
                new.append('FAIL  %s: %s%s' % (label, key, '' if value == 1 else ' (%d)' % value))
            elif value > old[key] and cap:
                new.append('FAIL  %s: %s grew from %d to %d' % (label, key, old[key], value))
        for key, value in sorted(old.items()):
            if key not in items or (cap and items[key] < value):
                fixed.append('FIXED %s: %s' % (label, key))
    return new, fixed


def adopt(config, debt, now):
    """--adopt: list the debt of an opt-in rule just turned on or raised above main's level.

    Args:
        config: the code standard settings.
        debt: the baseline's debt list.
        now: the violations measured now.

    Returns:
        The exit code: 0 written, 1 refused.
    """
    mb = git('merge-base', 'HEAD', 'origin/main')
    try:
        old = settings.code_base(ROOT, mb.stdout.strip()) if mb.returncode == 0 else None
    except ValueError:
        old = None
    main_config = old[0] if old else None   # the settings on the merge base, or None when there are none to read

    def raised(k):
        """True when opt-in kind `k` was already on at main and is now stricter."""
        return main_config is not None and level(k, config) > level(k, main_config) >= 1

    kinds = [k for k in rules() if level(k, config) and now.get(k) and (not debt.get(k) or raised(k))]
    if not kinds:
        print('CODE-STANDARD fail: no opt-in rule to adopt; use --update (it can only lower the baseline)')
        return 1
    save(dict(debt, **{k: now[k] for k in kinds}))
    print('CODE-STANDARD adopted: %s (add a docs/DECISIONS.md row that names %s)' % (
        ', '.join('%s %d' % (k, len(now[k])) for k in kinds), settings.CHECK))
    return 0


def check_run(args, config, debt, m):
    """Compare the measurement with the baseline and with main, print each problem and the result line; with
    --update, lower the baseline when there is no new debt.

    Args:
        args: the parsed command line arguments.
        config: the code standard settings.
        debt: the baseline's debt list.
        m: the result of measure().

    Returns:
        The exit code: 0 pass, 1 fail.
    """
    new, fixed = compare(m['violations'], debt, config['caps'])
    hand, note = against_main(config, debt)
    new += hand
    for line in warn_lines(m['violations'], config['caps']) + new + fixed + ([note] if note else []):
        print(line)
    if args.update:
        if new:
            print('CODE-STANDARD fail: new debt cannot go into the baseline; fix it (docs/code-standard.md)')
            return 1
        save(m['violations'])
        print('CODE-STANDARD baseline lowered: %s' % summary(m['violations']))
        return 0
    if fixed and not new:
        print('Debt was fixed: run python3 scripts/code_standard.py --update and commit the lower baseline.')
    gate = ', gate %s active' % ('strict' if GATE is STRICT_GATE else os.path.basename(GATE.__file__)) if GATE else ''
    print('CODE-STANDARD %s (files=%d, debt: %s%s)' % ('fail' if new or fixed else 'pass', len(m['files']),
                                                      summary(m['violations']), gate))
    return 1 if new or fixed else 0


def load():
    """Return (settings, debt) of this repo; debt is None when the repo has no baseline yet. It also loads a project's
    own gate (or STRICT_GATE when `code-strict-gate: on`) into GATE.

    Returns:
        (settings dict, debt dict or None).
    """
    global GATE
    GATE = load_gate()
    config = settings.code_config(ROOT)
    if GATE is None and config.get('strict_gate'):   # a project's own gate file wins; the kit's strict rules are the fallback
        GATE = STRICT_GATE
    needs = gate_settings(config)
    if needs and GATE is None:
        raise ValueError('`%s` in %s is enforced by a project\'s own gate, and there is no %s: add the gate or remove '
                         'the line (docs/code-standard.md "A project\'s own gate")'
                         % ('`, `'.join(needs), settings.CHECK, GATE_FILE.name))
    part = settings.load_state(ROOT).get('code_standard')
    return config, None if part is None else part.get('debt', {})


def save(debt):
    """Write the debt list into .check.state.json (the parts of the other tools stay as they are)."""
    settings.save_part(ROOT, 'code_standard', {'debt': {k: x for k, x in debt.items() if k not in WARN_KINDS}})


def parse_args():
    """Parse the command line (the usage: the header of this file).

    Returns:
        The parsed arguments.
    """
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--report', action='store_true', help='print every measurement as JSON')
    ap.add_argument('--update', action='store_true', help='lower the baseline to the debt that is left')
    ap.add_argument('--init', action='store_true', help='write the first baseline (only when the repo has none)')
    ap.add_argument('--adopt', action='store_true', help='add the debt of a rule the baseline does not list yet')
    ap.add_argument('--python-files', choices=('all', 'line'), help='list the Python files that ruff and pylint check, NUL-separated '
                    '(all: parse and lint; line: also the line cap, so no file with a generated block)')
    ap.add_argument('--shell-files', action='store_true', help='list the shell files that shellcheck checks, NUL-separated')
    ap.add_argument('--test', action='store_true', help='prove the check on small sample repos')
    return ap.parse_args()


def main():
    """Parse the arguments, measure, and check against (or lower) the baseline.

    Returns:
        The exit code: 0 pass, 1 fail.
    """
    args = parse_args()
    if args.test:
        sys.modules.setdefault('code_standard', sys.modules[__name__])
        import code_standard_test
        return code_standard_test.run(sys.modules[__name__])
    try:
        config, debt = load()
    except ValueError as err:
        print('CODE-STANDARD fail: %s' % err)
        return 1
    if args.python_files:
        print(python_files(config, args.python_files), end='')
        return 0
    if args.shell_files:
        print(shell_files(config), end='')
        return 0
    existed = debt is not None
    if not existed and not args.init:
        print('CODE-STANDARD fail: no code standard baseline in %s; adopt the standard with --init '
              '(docs/code-standard.md)' % settings.STATE)
        return 1
    m = measure(config)
    if args.report:
        print(json.dumps(m, indent=1))
        return 0
    if args.init:
        if existed:   # a second --init could write new debt into the list; the baseline only shrinks
            print('CODE-STANDARD fail: a baseline exists; use --update (it can only lower it)')
            return 1
        save(m['violations'])
        print('CODE-STANDARD baseline written: %s' % summary(m['violations']))
        return 0
    if args.adopt:
        return adopt(config, debt, m['violations'])
    return check_run(args, config, debt, m)


if __name__ == '__main__':
    sys.exit(main())
