#!/usr/bin/env python3
"""Self-test of scripts/code_standard.py (run by `python3 scripts/code_standard.py --test` and `python3 -m unittest`).

Builds small sample repos in temporary folders and proves every rule of the check and its built-in strict gate:
- C1 header, C1 prevents (kit FAIL vs project WARN), C1 safety (`on` and `strict`)
- C2 comment and C2 full (Python, PowerShell, JavaScript), --adopt and main comparison
- C3 function and script-block length, C5 duplicate bodies, C6 generated blocks/files, C10 parse
- Python/Shell linter file-selection (`--python-files`, `--shell-files`)
- The ratchet against `.check.state.json` and `origin/main`, `--init`, `--update`, `--adopt`
- Project gate extension point (`scripts/code_standard_gate.py`) and built-in `code-strict-gate: on`
- DEC-LINES: confirms hard 450/600-line file-size gates are retired (long hand-written files do not fail C4).

Input: the check module (or imported via unittest). Output: "code standard self-test: pass" or unittest results.
Network: none.
Writes: temporary folders only.
Credentials: none.
"""

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_settings as settings   # noqa: E402 - scripts/check_settings.py: the reader of .check and .check.state.json
import code_standard as cs_mod      # noqa: E402 - the consolidated check module (scripts/code_standard.py)

PS = bool(shutil.which('pwsh'))   # the PowerShell cases need the real parser
SMALL = 'code-max-function-lines: 5\ncode-max-file-lines: 50\n'   # sample repo caps as .check lines
FULL = 'code-c2: full\n'                                         # opt-in C2 full rule

SAMPLE_GATE = '''"""Sample gate of the code standard self-test (a project's own gate has this shape)."""
RULES = {'line': ('C4 line longer than %d characters', 'max_line_chars')}
OPT_IN = {'line': lambda c: 1 if c['caps'].get('max_line_chars') else 0}


def file_rules(v, path, lines, head, config, skip):
    """The sample per-file rules: the line cap, and for the strict safety form a header that starts with Network:."""
    cap = config['caps'].get('max_line_chars')
    longest = max(len(x) for x in lines)
    if cap and longest > cap:
        v['line'][path] = longest
    if config.get('c1_safety') == 'strict' and not head.startswith('Network:'):
        v['safety'][path] = 1


def decided(root, ref):
    """The sample decision test: the file OWNER-YES exists."""
    return (root / 'OWNER-YES').exists(), ['REFUSED  sample gate: no OWNER-YES file']


def new_debt_refusal(root, ref, kind, key):
    """The sample refusal: no debt for new.py, whatever was decided."""
    return 'FAIL  sample gate: no debt for new.py' if key.startswith('new.py') else None
'''

A45 = 'a' * 45
# Whole files, as ruff 0.17.6 sees them at a cap of 40 (2026-11-25): True = over the cap (check_lines).
RUFF_CASES = (
    ('x = "# noqa %s"' % A45, True),
    ("x = '''\n%s # noqa\n'''" % A45, True),
    ('x = "%s"' % ('\u65e5' * 22), True),
    ('if x:\n\ty = "%s"' % ('a' * 33), True),
    ('x = "%s"' % ('e\u0301' * 20), False),
    ('x = 1  # type: int  # %s' % A45, False),
    ('x = "%s"  # noqa' % A45, False),
    ('x = "%s\u2705\ufe0f"' % ('a' * 32), False),
    ('x = 1  # flake8: %s' % A45, False),
    ('x = 1  # mypy: %s' % A45, True),
    ('x = """\n%s\n"""  # noqa: E501' % ('a b ' * 12), False),
    ('# ruff: noqa\nx = "%s"' % A45, False),
    ('# SPDX-License-Identifier: %s' % ('a b ' * 12), False),
    ("x = ('''\n%s\n''', '''\n%s\n''')  # noqa" % (('w ' * 25,) * 2), False),
    ('# note # ruff: noqa\nx = "%s"' % A45, False),
    (' ' * 60, False),
    ('x = "%s\u3164"' % ('a' * 33), False),
    ('#  SPDX-License-Identifier: %s' % ('a b ' * 12), False),
    ('# ruff : noqa\nx = "%s"' % A45, False),
    ('x = "abc\u0301\t%s"' % ('a' * 28), False),
    ('x = "\t\t%s"' % ('a' * 28), True),
)


# ---------------------------------------------------------------- sample repo helpers ---------------------------------

def write(root, lines, debt=None):
    """Write the sample repo's .check (setting lines) and, when debt is given, its code standard baseline."""
    (root / settings.CHECK).write_text(lines)
    if debt is not None:
        settings.save_part(root, 'code_standard', {'debt': debt})


def config_of(root, lines):
    """Write the sample repo's .check and return the settings the check reads from it."""
    write(root, lines)
    return settings.code_config(root)


def fails(call, *args):
    """Return the message of the ValueError that call(*args) raises, or '' when it raises none."""
    try:
        call(*args)
    except ValueError as err:
        return str(err)
    return ''


def commit(g, message):
    """Commit everything in the sample repo and make that commit origin/main."""
    g('add', '-A')
    g('-c', 'user.email=t@example.invalid', '-c', 'user.name=t', 'commit', '-qm', message)
    g('update-ref', 'refs/remotes/origin/main', 'HEAD')


def main(cs, *args):
    """Run cs.main() with these arguments, its output hidden; return its exit code."""
    saved, sys.argv = sys.argv, ['code_standard.py', *args]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return cs.main()
    finally:
        sys.argv = saved


def row_text(text, by='the Keeper'):
    """Return one DECISIONS table row (four cells) whose decision cell is `text` and names `.check`."""
    return '| 2026-11-17 | %s %s | %s | — |\n' % (text, settings.CHECK, by)


def sample_repo(d):
    """Return a runner of git commands in a new sample repo at folder `d`."""
    def g(*c):
        """Run git in the sample repo directory `d`."""
        return subprocess.run(['git', '-C', d, *c], check=True, capture_output=True)

    g('init', '-q')
    return g


# ---------------------------------------------------------------- core self-test runner -------------------------------

def run(cs):
    """Prove the check on sample repos (core without gate, then built-in strict gate).

    Args:
        cs: the check module (scripts/code_standard.py).

    Returns:
        Exit code 0 on pass.
    """
    real_gate, real_root = cs.GATE_FILE, cs.ROOT
    try:
        with tempfile.TemporaryDirectory() as d:
            cs.GATE_FILE, cs.GATE = Path(d) / 'gate' / 'code_standard_gate.py', None
            run_cases(cs, Path(d) / 'repo')
    finally:
        cs.GATE_FILE, cs.GATE, cs.ROOT = real_gate, None, real_root

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StrictGateTest)
    result = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(suite)
    assert result.wasSuccessful(), 'strict gate self-test failed: %s' % (result.failures + result.errors)
    print('code standard self-test: pass')
    return 0


def no_file_size_gate(cs, root, g, good_py):
    """DEC-LINES: hard 450/600-line file-size caps are retired; long files have no file_size violations.

    Args:
        cs: the check module.
        root: the sample repo Path.
        g: git command runner.
        good_py: text of a valid Python sample file.
    """
    (root / 'p.py').write_text(good_py + '#\n' * 50)
    (root / 'p.sh').write_text('# Sample shell file: long file without a file-size cap.\n' + '#\n' * 650)
    g('add', 'p.py', 'p.sh')
    v = cs.measure(config_of(root, SMALL))['violations']
    assert 'file_size' not in v, 'file_size debt kind is retired: %s' % v
    assert cs.WARN_KINDS == () or 'file_size' not in cs.WARN_KINDS, 'file_size not warned: %s' % (cs.WARN_KINDS,)
    assert cs.compare({'file_size': {'old.sh': 500}}, {'file_size': {'old.sh': 500}}, {'max_function_lines': 60}) == ([], []), \
        'retired file_size keys in legacy state do not trigger failures'
    g('rm', '-qf', 'p.py', 'p.sh')
    python_for_the_linters(cs, root, g, good_py)


def python_for_the_linters(cs, root, g, good_py):
    """Ruff and pylint get covered Python files: no excluded/generated files; generated-block files skipped for line.

    Args:
        cs: the check module.
        root: the sample repo Path.
        g: git command runner.
        good_py: text of a valid Python sample file.
    """
    (root / 'vendor').mkdir(exist_ok=True)
    (root / 'x').mkdir(exist_ok=True)
    (root / 'vendor/v.py').write_text(good_py)
    (root / 'x/gen.py').write_text('# GENERATED from src/x.py by build.py\nx = 1\n')
    (root / 'x/blk.py').write_text(good_py + '# >>> s: generated from src/s.py by b.py\nx = 1\n# <<< s\n')
    (root / 'x/bad.py').write_text(good_py + 'def (:\n')
    g('add', '-A')
    config = config_of(root, SMALL + FULL + 'code-exclude: vendor/**\ncode-generated: x/gen.py\n')
    everything = cs.python_files(config, 'all').split('\0')[:-1]
    lines = cs.python_files(config, 'line').split('\0')[:-1]
    assert 'vendor/v.py' not in everything and 'x/gen.py' not in everything, 'excluded/generated files: %s' % everything
    assert {'x/blk.py', 'x/bad.py'} <= set(everything), 'block and bad files are in all: %s' % everything
    assert 'x/blk.py' not in lines and 'x/bad.py' in lines, 'generated block excluded from line list: %s' % lines
    (root / 'vendor/v.sh').write_text('echo $1\n')
    (root / 'x/gen.sh').write_text('echo $1\n')
    (root / 'x/ok.sh').write_text('echo $1\n')
    g('add', '-A')
    config = config_of(root, SMALL + FULL + 'code-exclude: vendor/**\ncode-generated: x/gen.sh\n')
    assert cs.shell_files(config).split('\0')[:-1] == ['x/ok.sh'], 'shellcheck gets covered shell files: %r' % cs.shell_files(config)
    kept = cs.LINTERS
    for linters in (True, False):   # a file that does not parse: no traceback with `code-c2: full`
        cs.LINTERS = linters
        assert bool(cs.measure(config)['violations']['parse'].get('x/bad.py')) != linters, 'C10 fallback only without linters'
    cs.LINTERS = kept
    g('rm', '-rqf', 'vendor', 'x')


def run_cases(cs, root):
    """Prove the check on a sample repo across every rule group.

    Args:
        cs: the check module.
        root: the folder for the sample repo (created here).
    """
    good_py = '"""Sample module: it shows a file that meets every rule of the code standard."""\n\n\n' \
              'def add(a, b):\n    """Return a + b."""\n    return a + b\n'
    good_ps = '<#\n  Sample PowerShell file: it shows a file that meets every rule of the code standard.\n#>\n' \
              '# Returns the text in capitals.\nfunction Get-Upper([string]$T) {\n  return $T.ToUpper()\n}\n' \
              '# >>> shared: generated from src/shared.ps1 by build.py (do not edit)\n' \
              'function Get-Copy { return 1 }\n# <<< shared\n'
    root.mkdir()
    cs.ROOT, d = root, str(root)
    g = sample_repo(d)
    (root / 'a.py').write_text(good_py)
    PS and (root / 'b.ps1').write_text(good_ps)
    config = config_of(root, SMALL)
    assert config['caps'] == {'max_function_lines': 5, 'max_file_lines': 50, 'max_file_lines_paste': 600}, \
        'the caps come from .check: %s' % config
    g('add', '.')
    m = cs.measure(config)
    assert not any(m['violations'].values()), 'clean files pass: %s' % m['violations']
    assert not PS or [f['name'] for f in m['files']['b.ps1']['functions']] == ['Get-Upper'], 'generated block skipped'
    no_file_size_gate(cs, root, g, good_py)
    config = config_of(root, SMALL)
    (root / 'a.py').write_text(good_py + '\n\ndef bare(x):\n    return x\n')
    new, fixed = cs.compare(cs.measure(config)['violations'], {}, config['caps'])
    assert len(new) == 1 and 'C2' in new[0] and 'a.py::bare' in new[0], 'a function without a comment fails: %s' % new
    long_fn = '\n\ndef long(x):\n    """Long."""\n' + '    x += 1\n' * 6 + '    return x\n'
    (root / 'a.py').write_text(good_py + long_fn)
    debt = cs.measure(config)['violations']
    assert debt['length'] == {'a.py::long': 9}, 'a long function is debt: %s' % debt['length']
    (root / 'a.py').write_text(good_py + long_fn.replace('    return x', '    x += 1\n    return x'))
    new, fixed = cs.compare(cs.measure(config)['violations'], debt, config['caps'])
    assert len(new) == 1 and 'grew from 9 to 10' in new[0], 'a listed function that grew fails: %s' % new
    (root / 'a.py').write_text(good_py)
    new, fixed = cs.compare(cs.measure(config)['violations'], debt, config['caps'])
    assert not new and len(fixed) == 1, 'a fixed item is reported (and fails until the baseline is lowered)'
    (root / 'c.sh').write_text('echo hi\n')
    g('add', '.')
    new, _ = cs.compare(cs.measure(config)['violations'], {}, config['caps'])
    assert any('C1' in x and 'c.sh' in x for x in new), 'a file without a header fails: %s' % new
    self_test_kinds(cs, root, g, config)
    self_test_forms(cs, root, g, config)
    self_test_main(cs, root, g)
    self_test_init(cs, root)
    self_test_docs(cs, root, g, config)
    self_test_warns(cs, root, g, config)
    self_test_gate(cs, root, g)


def self_test_kinds(cs, root, g, config):
    """Self-test of finding kinds: shell `${#..}`, JS function/method, PowerShell parse, divider, argument block, shebang, C5.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
        config: the settings of the sample repo.
    """
    sh = '#!/usr/bin/env bash\n# Sample shell file: it shows how functions are measured by the check.\n# Counts.\nf() {\n  n=${#a[@]}\n' \
         + '  x=1\n' * 6 + '}\n'
    (root / 'c.sh').write_text(sh)
    js = '// Sample JavaScript file: it shows how functions and methods are found by the check.\n' \
         'function plain(a) {\n  return a;\n}\nclass K {\n  // Adds one.\n  inc(x) {\n    return x + 1;\n  }\n}\n'
    (root / 'd.js').write_text(js)
    PS and (root / 'e.ps1').write_text('<#\n  Sample PowerShell file with a parse error, for the check self-test only.\n#>\n$x = (1 + \n')
    blk = '<#\n  Sample PowerShell file: a long script block passed to a call, for the check self-test only.\n#>\n' \
          '# ---- a divider\nfunction Get-NoDoc { return 1 }\n$b.Add_Click({\n' + '  $y = 1\n' * 6 + '})\n'
    PS and (root / 'f.ps1').write_text(blk)
    (root / 'hook').write_text('#!/bin/sh\necho no header here\n')
    dup = '"""Sample module with two same bodies, for the check self-test only (rule C5)."""\n\n\n' + ''.join(
        'def %s(x):\n    """Same body."""\n    y = x + 1\n    y = y * 2\n    y = y - 3\n    return y\n\n\n' % n for n in ('one', 'two'))
    (root / 'g.py').write_text(dup)
    g('add', '.')
    v = cs.measure(config)['violations']
    assert v['length'].get('c.sh::f') == 9, 'shell ${#..}: the whole function is measured: %s' % v['length']
    assert 'd.js::plain' in v['comment'] and 'd.js::inc' not in v['comment'], 'JS function and method: %s' % v['comment']
    assert not PS or v['parse'].get('e.ps1', 0) >= 1, 'a PowerShell parse error fails: %s' % v['parse']
    assert not PS or 'f.ps1::Get-NoDoc' in v['comment'], 'a divider line is not a comment: %s' % v['comment']
    assert not PS or any(k.startswith('f.ps1::{block in $b.Add_Click') for k in v['length']), 'a long argument block: %s' % v['length']
    assert 'hook' in v['header'], 'a shebang file with no extension is checked: %s' % v['header']
    assert set(v['duplicate']) == {'g.py::one', 'g.py::two'}, 'two same bodies are duplicates: %s' % v['duplicate']
    for f in ('c.sh', 'd.js', 'e.ps1', 'f.ps1', 'hook', 'g.py'):
        (root / f).unlink(missing_ok=True)
    g('add', '-A')


def self_test_main(cs, root, g):
    """Self-test of the comparison with main, invalid `.check` keys, and migration from `.code-standard.json`.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
    """
    config, debt = settings.code_config(root), {'comment': {'a.py::x': 1}}
    write(root, SMALL, debt)
    (root / 'docs').mkdir()
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n')
    commit(g, 'base')
    assert cs.load() == (config, debt), 'the settings and the debt are read back'
    assert cs.against_main(config, debt)[0] == [], 'the same baseline passes'
    added = {'comment': {'a.py::x': 1, 'a.py::y': 1}}
    assert 'added by hand' in ' '.join(cs.against_main(config, added)[0]), 'an item added by hand fails'
    for lines in (SMALL.replace(': 5', ': 9'), SMALL + 'code-exclude: a.py\n', 'code-max-file-lines: 50\n'):
        raised = config_of(root, lines)
        assert 'setting' in ' '.join(cs.against_main(raised, debt)[0]), 'a setting changed, added or removed fails: ' + lines
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n| cap 9 | .check.state.json |\n')
    assert cs.against_main(raised, debt)[0], 'a row that names another file is no decision'
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n| cap 9 | `.check` |\n')
    assert cs.against_main(raised, debt)[0] == [], 'a setting change with a DECISIONS row passes'
    for bad in ('code-max-function-line: 900\n', 'code-max-function-lines: lots\n'):
        write(root, SMALL + bad)
        assert main(cs) == 1, 'an unknown code- key or a bad value fails the check: ' + bad
    self_test_transition(cs, root, g)


def self_test_transition(cs, root, g):
    """Self-test of the first change after a migration from `.code-standard.json`.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
    """
    old = {'config': {'caps': {'max_function_lines': 5, 'max_file_lines': 50}, 'include': ['*']},
           'debt': {'comment': {'a.py::x': 1}}}
    (root / settings.STATE).unlink()
    (root / settings.CHECK).unlink()
    (root / settings.OLD_CODE).write_text(json.dumps(old))
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n')
    commit(g, 'old layout')
    assert main(cs) == 1, 'the old file in the working tree fails the check (run the migration)'
    (root / settings.OLD_CODE).unlink()
    write(root, SMALL, old['debt'])
    config = settings.code_config(root)
    assert cs.against_main(config, old['debt'])[0] == [], 'after a migration the same settings and debt pass'
    assert cs.against_main(config, {'comment': {'a.py::x': 1, 'a.py::y': 1}})[0], 'debt added in a migration fails'
    assert cs.against_main(config_of(root, SMALL.replace(': 5', ': 9')), old['debt'])[0], 'a cap raised in a migration fails'
    write(root, SMALL)


def self_test_forms(cs, root, g, config):
    """Self-test of function forms and comment places across Python, PowerShell, JavaScript and shell.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
        config: the settings of the sample repo.
    """
    (root / 'h.sh').write_text('#!/bin/sh\n# Sample shell file: two function forms, for the check self-test only.\n'
                               'function longfn {\n  a=1\n}\nnext()\n{\n  b=2\n}\n')
    PS and (root / 'i.ps1').write_text('<#\n.SYNOPSIS\n  Sample PowerShell file: a help header, for the check self-test only.\n#>\n'
                                       'function Get-A { 1 }\n# Returns two.\nfunction Get-B { 2 }\n')
    (root / 'j.py').write_text('"""Sample module: comment places and duplicates, for the check self-test only."""\n\n\n'
                               'def lead(x):\n    # Returns x.\n    return x\n\n\n' + ''.join(
                                   'def %s(x):\n    """%s"""\n    y = x + 1\n    y = y * 2\n    y = y - 3\n    return y\n\n\n'
                                   % (n, doc) for n, doc in (('p', 'One.'), ('q', 'Two.'))))
    (root / 'k.js').write_text('// Sample JavaScript file: an arrow with no braces, for the check self-test only.\n\n'
                               '// Adds one.\nconst inc = x => x + 1;\n// Doubles.\nfunction dbl(x) {\n  return 2 * x;\n}\n')
    (root / 'l.py').write_text('"""Sample module that does not parse, for the check self-test only (rule C10)."""\ndef (:\n')
    g('add', '.')
    v = cs.measure(config)['violations']
    assert {'h.sh::longfn', 'h.sh::next'} <= set(v['comment']), 'shell function forms are found: %s' % v['comment']
    assert not PS or 'i.ps1::Get-A' in v['comment'] and 'i.ps1::Get-B' not in v['comment'], 'comment places: %s' % v['comment']
    assert 'j.py::lead' not in v['comment'], 'a Python lead comment counts: %s' % v['comment']
    assert {'j.py::p', 'j.py::q'} <= set(v['duplicate']), 'docstring-only difference is a duplicate: %s' % v['duplicate']
    assert not any(k.startswith('k.js::') for k in v['comment'].keys() | v['length'].keys()), 'arrow: %s' % v['length']
    assert bool(v['parse'].get('l.py')) != cs.LINTERS, 'a Python parse error: ruff and pylint, or here without them: %s' % v['parse']
    self_test_edges(cs, root, g, config)
    for f in ('h.sh', 'i.ps1', 'j.py', 'k.js', 'l.py'):
        (root / f).unlink(missing_ok=True)
    g('add', '-A')


def self_test_edges(cs, root, g, config):
    """Self-test of edge forms: multi-line JS signatures, nested Python defs, PowerShell body help, shell braces.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
        config: the settings of the sample repo.
    """
    (root / 'm.js').write_text('// Sample JavaScript file: edge forms, for the check self-test only.\n'
                               'function longParams(\n  alpha,\n  beta\n) {\n  return alpha + beta;\n}\nconst bare = x => x * 3;\n')
    (root / 'n.py').write_text('"""Sample module: a nested def, for the check self-test only."""\n\n\n'
                               'def outer(x):\n    # Helper.\n    def inner(y):\n        return y\n    return inner(x)\n')
    PS and (root / 'o.ps1').write_text('<#\n  Sample PowerShell file: help in the body, for the check self-test only.\n#>\n\n'
                                       'function Get-X\n{\n  <#\n  .SYNOPSIS\n  Returns one.\n  #>\n  1\n}\n\n'
                                       'function Get-Y {\n  2\n  <#\n  .SYNOPSIS\n  Returns two.\n  #>\n}\n')
    (root / 'p.sh').write_text('#!/bin/sh\n# Sample shell file: a brace on its own line, for the check self-test only.\n\n'
                               'next()\n{\n  # Does b.\n  b=2\n}\n')
    g('add', '.')
    v = cs.measure(config)['violations']
    assert 'm.js::longParams' in v['comment'] and 'm.js::bare' in v['comment'], 'JS edge forms: %s' % v['comment']
    assert 'n.py::outer' in v['comment'] and 'n.py::outer.inner' not in v['comment'], 'nested def: %s' % v['comment']
    assert not PS or not {'o.ps1::Get-X', 'o.ps1::Get-Y'} & set(v['comment']), 'help in the body counts: %s' % v['comment']
    assert 'p.sh::next' not in v['comment'], 'a shell comment after `{` counts: %s' % v['comment']
    PS and (root / 'q.ps1').write_text('<#\n  Sample PowerShell file: help that is not the function own, for the self-test only.\n#>\n\n'
                                       'function Outer {\n  function Inner {\n    <#\n    .SYNOPSIS\n    Inner.\n    #>\n'
                                       '    1\n  }\n  Inner\n}\n\n'
                                       'function Plain {\n  $x = 1  # see .DESCRIPTION of Foo\n  $x\n}\n')
    (root / 'r.py').write_text('"""Sample module: an outer comment and a nested def, for the self-test only."""\n\n\n'
                               'def outer2():\n    # Outer does X.\n\n    def inner2():\n        return 1\n    return inner2()\n')
    g('add', '.')
    v = cs.measure(config)['violations']
    assert not PS or {'q.ps1::Outer', 'q.ps1::Plain'} <= set(v['comment']), 'help must be the function own: %s' % v['comment']
    assert 'r.py::outer2' not in v['comment'], 'an outer comment before a blank line counts: %s' % v['comment']
    (root / 's.js').write_text('// Sample JavaScript file: a long signature, for the self-test only.\n\n'
                               'function k(\n' + '  a,\n' * 12 + ') {\n  return 1;\n}\n')
    PS and (root / 't.ps1').write_text('<#\n  Sample PowerShell file: a block comment first in the body, for the self-test only.\n#>\n\n'
                                       'function Blk {\n  <# Does a thing. #>\n  1\n}\n')
    (root / 'u.py').write_text('"""Sample module: a decorated nested def, for the self-test only."""\n\n\n'
                               'def deco(f):\n    # Wraps f.\n    @staticmethod\n    def w():\n        return f\n    return w\n')
    g('add', '.')
    v = cs.measure(config)['violations']
    assert 's.js::k' in v['comment'], 'a long JS signature is still a function: %s' % v['comment']
    assert not PS or 't.ps1::Blk' not in v['comment'], 'a first-line block comment counts: %s' % v['comment']
    assert 'u.py::deco' in v['comment'], 'a comment above a nested decorator is not the outer one: %s' % v['comment']
    for f in ('m.js', 'n.py', 'o.ps1', 'p.sh', 'q.ps1', 'r.py', 's.js', 't.ps1', 'u.py'):
        (root / f).unlink(missing_ok=True)


def self_test_init(cs, root):
    """Self-test of --init and --report without an existing baseline."""
    state = root / settings.STATE
    state.unlink()
    settings.save_part(root, 'timings', {'check': {'seconds': 1.0}})
    assert main(cs) == 1, 'no baseline: the check fails'
    assert main(cs, '--init', '--report') == 0 and cs.load()[1] is None, '--report writes no baseline'
    assert main(cs, '--init') == 0 and cs.load()[1] is not None, '--init writes the first baseline'
    assert settings.load_state(root)['timings'], '--init keeps the other parts of the state file'
    assert main(cs, '--init') == 1, 'a second --init is refused'


# ---------------------------------------------------------------- C2 full docs and WARN kinds -------------------------

def self_test_docs(cs, root, g, config):
    """Self-test of the opt-in C2 full rule (`code-c2: full`) and C1 safety.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
        config: the settings of the sample repo.
    """
    full = config_of(root, FULL)
    body = '    y = x\n' * 9
    (root / 'f.py').write_text('"""Sample module for the C2 full self-test: two long functions and a short one."""\n\n\n'
                               'def bare(x, *rest):\n    """Adds."""\n' + body + '    return y\n\n\n'
                               'def full(x):\n    """Adds.\n\n    Args:\n        x: a number.\n\n    Returns:\n        y.\n    """\n'
                               + body + '    return y\n\n\ndef short(x):\n    """Adds."""\n    return x\n')
    js = '// Sample JavaScript file for the C2 full self-test.\n/**\n * Adds.\n * @param {number} a first\n * @returns {number}\n */\n' \
         'function good(a) {\n' + '  let y = a;\n' * 9 + '  return y;\n}\n// Adds.\nfunction bad(a, {b}) {\n' \
         + '  let y = a;\n' * 9 + '  return y;\n}\n'
    (root / 'g.js').write_text(js)
    if PS:
        lines = '  $y = 1\n' * 9
        (root / 'h.ps1').write_text('<#\n  Sample PowerShell file for the C2 full self-test: one complete and one incomplete.\n#>\n\n'
                                    '<#\n.SYNOPSIS\n  Adds.\n.PARAMETER Path\n  A path.\n#>\nfunction Get-Good([string]$Path) {\n'
                                    + lines + '}\n# Adds.\nfunction Get-Bad([string]$Path) {\n' + lines + '}\n')
    g('add', '.')
    m = cs.measure(full)
    docs = m['violations']['docs']
    want = {'f.py::bare', 'g.js::bad'} | ({'h.ps1::Get-Bad'} if PS else set())
    assert want <= set(docs) and not {'f.py::full', 'f.py::short', 'g.js::good', 'h.ps1::Get-Good'} & set(docs), \
        'C2 full finds the long functions without full docs: %s' % docs
    gaps = {f['name']: f.get('docs_missing') for f in m['files']['f.py']['functions']}
    assert gaps['bare'] == ['Args: x', 'Args: rest', 'Returns:'], 'the report names the missing parts: %s' % gaps
    jgaps = {f['name']: f.get('docs_missing') for f in m['files']['g.js']['functions']}
    assert jgaps['bad'] == ['JSDoc'], 'a plain comment is not JSDoc: %s' % jgaps
    self_test_docs_forms(cs)
    if PS:
        g('rm', '-q', '--cached', '--', '*.ps1')
    assert not cs.measure(config)['violations']['docs'], 'without `code-c2: full` the rule is off'
    safe = config_of(root, FULL + 'code-c1-safety: on\n')
    safety = cs.measure(safe)['violations']['safety']
    assert 'f.py' in safety and 'g.js' in safety, 'C1 safety: a header without the three lines fails: %s' % safety
    text = (root / 'f.py').read_text().replace('a short one."""', 'a short one.\n\nNetwork: none. Writes: none. Credentials: none.\n"""', 1)
    (root / 'f.py').write_text(text)
    assert 'f.py' not in cs.measure(safe)['violations']['safety'], 'C1 safety: the three lines pass'
    write(root, FULL, {})
    assert main(cs, '--adopt') == 0, '--adopt lists a rule that was just turned on'
    assert set(cs.load()[1]['docs']) == want - {'h.ps1::Get-Bad'}, '--adopt writes its debt'
    assert main(cs, '--adopt') == 1, 'a second --adopt is refused (the kind is listed now)'
    self_test_adopt_ratchet(cs, root, g, full)


def self_test_docs_forms(cs):
    """Self-test of the parsing edge cases of C2 full docs in Python and JavaScript.

    Args:
        cs: the check module.
    """
    assert cs.js_params(['const f = x => {', '  foo(q);', '};'], 1) == ['x'], 'arrow parameter from the signature'
    assert cs.js_params(['function f(a = ",", b) {', '}'], 1) == ['a', 'b'], 'a quoted comma is not a separator'
    assert not cs.js_returns_value('  a.forEach(v => {\n    return v;\n  });\n}'), 'a nested return is not counted'
    assert cs.js_returns_value('{\n  return 1;\n}'), 'a return under a `{` on its own line is counted'
    assert cs.js_params(['const h = async x => {', '};'], 1) == ['x'], 'an async arrow parameter is read'
    assert cs.js_missing(['/** K.', ' * @param {{a: number}} o', ' */', 'function k(o) {', '}'], 4, 4, '}') == [], \
        'a JSDoc type with nested braces is read'
    lead = cs.python_docs(
        'def g(a, b):\n    """Do.\n\n    Args:\n        b: the value of\n'
        '            a value.\n    """\n    return None\n')
    assert cs.python_missing(lead, 1) == ['Args: a'], 'a word in a continuation line is not an Args entry; return None is no value'
    facts = cs.python_docs('def f(x, value):\n    """Do.\n\n    Args:\n        x: a.\n\n    Returns:\n        value: b.\n    """\n')
    assert cs.python_missing(facts, 1) == ['Args: value'], 'Args: ends at Returns:'
    lines = ['/** Other. */', 'function a() {', '}', '/* plain */', 'function b(z) {', '  return z;', '}']
    assert cs.js_missing(lines, 5, 5, '  return z;\n}') == ['JSDoc'], 'a plain /* */ comment is not JSDoc'


def self_test_adopt_ratchet(cs, root, g, full):
    """Self-test of the ratchet around --adopt: core rules cannot be adopted; opt-in rules require a DECISIONS row.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
        full: the settings with `code-c2: full`.
    """
    write(root, 'code-c2: lean\n', {})
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n')
    commit(g, 'baseline')
    lean = settings.code_config(root)
    (root / 'docs' / 'DECISIONS.md').write_text('| row | names %s |\n' % settings.CHECK)
    assert cs.against_main(lean, {'length': {'x.py::f': 99}})[0], 'a core rule debt added by hand fails, even with a DECISIONS row'
    on = {'docs': {'f.py::bare': 1}}
    assert not cs.against_main(full, on)[0], 'an opt-in rule turned on now: its first list passes with a DECISIONS row'
    (root / 'docs' / 'DECISIONS.md').unlink()
    assert cs.against_main(full, on)[0], 'the same list fails with no DECISIONS row'


def self_test_warns(cs, root, g, config):
    """Self-test of WARN kinds: C1 Prevents warns in a project and fails in the kit (AUD-1).

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
        config: the settings of the sample repo.
    """
    for name in [p.name for p in root.iterdir() if p.name != '.git']:
        g('rm', '-rqf', '--ignore-unmatch', name)
    saved = cs.WARN_KINDS
    cs.WARN_KINDS = ('prevents',)   # a project
    head = '"""Sample check script for the WARN self-test: it names no defect and is long enough for C1."""\n\n\n'
    (root / 'scripts').mkdir(exist_ok=True)
    (root / 'scripts/check.sh').write_text(
        '# Sample runner: it runs the sample check scripts of the WARN self-test.\npython3 scripts/chk.py\npython3 scripts/chk_test.py\n')
    (root / 'scripts/chk.py').write_text(head + '#\n' * 50)
    (root / 'scripts/chk_test.py').write_text(head)
    (root / 'scripts/other.py').write_text(head)
    g('add', '-A')
    assert cs.entry_points(root) == {'scripts/chk.py'}, 'named by check.sh, no test file: %s' % cs.entry_points(root)
    now = cs.measure(config)['violations']
    assert now['prevents'] == {'scripts/chk.py': 1}, 'prevents measured: %s' % now
    assert cs.compare(now, {}, config['caps']) == ([], []), 'a warning is no new debt and is never "fixed"'
    warns = cs.warn_lines(now, config['caps'])
    assert [w for w in warns if 'Prevents' in w and 'scripts/chk.py' in w], 'the missing line shows: %s' % warns
    cs.WARN_KINDS = ()   # the kit: AUD-1 fails
    new, _ = cs.compare(now, {}, config['caps'])
    assert [n for n in new if n.startswith('FAIL') and 'Prevents' in n and 'scripts/chk.py' in n], 'the kit fails it: %s' % new
    assert not [w for w in cs.warn_lines(now, config['caps']) if 'Prevents' in w], 'the kit has no Prevents warning'
    cs.WARN_KINDS = ('prevents',)
    for text in ('unclear (see report)', 'TBD', 'see the report', 'two words', 'a check that runs with no stated defect to stop.'):
        (root / 'scripts/chk.py').write_text('"""Sample check script.\n\nPrevents: %s\n"""\n' % text)
        assert bool(cs.measure(config)['violations']['prevents']) == (not text.startswith('a check')), 'only a defect clears it: %s' % text
    g('add', '-A')
    cs.save(now)
    assert 'prevents' not in settings.load_state(root)['code_standard']['debt'], 'never in the baseline'
    cs.WARN_KINDS = saved
    assert not cs.is_kit(root), 'no kit.config.json: not the kit'
    (root / 'kit.config.json').write_text('{}')
    assert cs.is_kit(root), 'kit.config.json and no lock: the kit'
    (root / '.check.lock').write_text('{}')
    assert not cs.is_kit(root), 'a lock: a project'
    (root / 'kit.config.json').unlink()
    (root / '.check.lock').unlink()
    g('rm', '-rqf', 'scripts')


# ---------------------------------------------------------------- project gate extension point ------------------------

def self_test_gate(cs, root, g):
    """Self-test of the extension point (`scripts/code_standard_gate.py`).

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
    """
    for name in [p.name for p in root.iterdir() if p.name != '.git']:
        g('rm', '-rqf', '--ignore-unmatch', name)
    (root / 'docs').mkdir(exist_ok=True)
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n')
    (root / 'a.py').write_text('"""Sample module of the gate self-test: one long line and nothing else."""\nX = "' + 'x' * 120 + '"\n')
    write(root, '', {})
    commit(g, 'gate base')
    assert main(cs) == 0 and cs.GATE is None, 'no gate file and no gate setting: the kit check runs alone'
    for line in ('code-max-line-chars: 100\n', 'code-c1-safety: strict\n'):
        write(root, line)
        assert 'own gate' in fails(cs.load), 'a setting a gate enforces fails with no gate file: ' + line
        assert main(cs) == 1, 'and the check fails: ' + line
    cs.GATE_FILE.parent.mkdir()
    for bad, why in (
        ('import no_such_module_anywhere\n', 'cannot be loaded'),
        ('def f(:\n', 'cannot be loaded'),
        ('import sys\nsys.exit(0)\n', 'cannot be loaded'),
        ('raise SystemExit(1)\n', 'cannot be loaded'),
        (SAMPLE_GATE.replace('def decided', 'def undecided'), 'lacks decided'),
        (SAMPLE_GATE.replace("OPT_IN = {'line': lambda c: 1 if c['caps'].get('max_line_chars') else 0}", 'OPT_IN = []'), 'wrong shape'),
        (SAMPLE_GATE.replace("('C4 line longer than %d characters', 'max_line_chars')", "'C4 line'"), 'wrong shape'),
    ):
        cs.GATE_FILE.write_text(bad)
        write(root, '')
        assert why in fails(cs.load), 'a gate that is broken or incomplete fails the load (%s)' % why
        assert main(cs) == 1 and main(cs, '--update') == 1, 'and every run of the check (%s)' % why
    cs.GATE_FILE.write_text(SAMPLE_GATE)
    config = config_of(root, 'code-max-line-chars: 100\n')
    assert cs.load()[0] == config and cs.GATE is not None, 'a good gate loads'
    now = cs.measure(config)['violations']
    assert now['line'] == {'a.py': 126}, "the gate's per-file rule writes its own debt kind: %s" % now
    new, _ = cs.compare(now, {}, config['caps'])
    assert new == ['FAIL  C4 line longer than 100 characters: a.py (126)'], "the gate's label and cap are used: %s" % new
    assert cs.compare(now, {'line': {'a.py': 120}}, config['caps'])[0] == [
        'FAIL  C4 line longer than 100 characters: a.py grew from 120 to 126']
    assert cs.compare({'line': {'a.py': 110}}, {'line': {'a.py': 126}}, config['caps'])[1], \
        'a gate kind with a cap is a size: smaller is fixed'
    self_test_gate_ratchet(cs, root, config, now)
    strict = config_of(root, 'code-c1-safety: strict\n')
    assert cs.measure(strict)['violations']['safety'] == {'a.py': 1}, 'the gate enforces the strict safety form'
    assert cs.level('safety', strict) == 2 and cs.level('safety', config_of(root, 'code-c1-safety: on\n')) == 1, \
        'strict is a higher level'
    cs.GATE_FILE.unlink()
    write(root, '', {})
    assert main(cs) == 0 and cs.GATE is None, 'the gate file removed: the kit check runs alone again'


def self_test_gate_ratchet(cs, root, config, now):
    """Self-test of a gate in the comparison with main and in --adopt.

    Args:
        cs: the check module.
        root: the sample repo folder.
        config: the settings with the line cap of the sample gate.
        now: the measured violations dict.
    """
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n| cap | `.check` |\n')
    problems = cs.against_main(config, {})[0]
    assert len(problems) == 2 and 'setting' in problems[0] and problems[1] == 'REFUSED  sample gate: no OWNER-YES file', \
        "the gate's decision test replaces the kit's: %s" % problems
    assert 'added by hand' in ' '.join(cs.against_main(config, now)[0]), 'not decided: the new list is refused'
    (root / 'OWNER-YES').write_text('')
    assert cs.against_main(config, {})[0] == [], 'decided by the gate: the setting change passes'
    assert cs.against_main(config, now)[0] == [], "decided, and the gate's opt-in kind is turned on now: its first list passes"
    refused = cs.against_main(config, {'line': {'a.py': 126, 'new.py': 300}})[0]
    assert refused == ['FAIL  sample gate: no debt for new.py'], 'a refused debt key fails whatever was decided: %s' % refused
    assert main(cs, '--adopt') == 0 and cs.load()[1]['line'] == {'a.py': 126}, "--adopt lists the gate's opt-in kind"
    assert main(cs, '--adopt') == 1, 'a second --adopt is refused'
    assert main(cs) == 0, 'the check passes with the adopted list and the decision'
    (root / 'OWNER-YES').unlink()
    real_base, gate, decisions = cs.settings.code_base, cs.GATE, (root / 'docs' / 'DECISIONS.md')
    kept = decisions.read_text()
    cs.settings.code_base, cs.GATE = (lambda r, ref: ({}, {'line': {'a.py': 126}, 'length': {}})), None
    try:
        decisions.write_text('# Decisions\n')
        gone = cs.against_main({}, {})[0]
        assert len(gone) == 1 and 'main holds line debt, but no rule here knows that kind' in gone[0], \
            'a debt kind of main that no rule knows fails (the gate is gone): %s' % gone
        decisions.write_text('# Decisions\n| the gate is retired | `.check` |\n')
        assert cs.against_main({}, {})[0] == [], "with the Maintainer's row, removing the gate's rule passes"
    finally:
        cs.settings.code_base, cs.GATE = real_base, gate
        decisions.write_text(kept)


# ---------------------------------------------------------------- strict gate self-tests ------------------------------

def check_safety(cs):
    """Self-test of strict C1 safety: a label inside prose, mid-line or with no value fails; line-start + value passes.

    Args:
        cs: the check module.
    """
    lab = ['Network: none.', 'Writes: none.', 'Credentials: none.']
    what = 'Sample file: what it is for, long enough to be a header of the sample.'
    prose = 'Sample file. It has Network: none, Writes: none and Credentials: none, all in one sentence of prose.'
    assert not cs.safety_ok(prose), 'a label inside prose does not pass'
    assert not cs.safety_ok('\n'.join([what, 'Network:', lab[1], lab[2]])), 'a label with no value does not pass'
    assert not cs.safety_ok('\n'.join([what, 'Network: none. Writes: none. Credentials: none.'])), \
        'a label in the middle of a line does not pass'
    forms = {'powershell': ['<#', what] + lab + ['#>'],
             'python': ['"""' + what] + lab + ['"""', ''],
             'js': ['// ' + what] + ['// ' + x for x in lab],
             'shell': ['#!/bin/sh', '# ' + what] + ['# ' + x for x in lab],
             'powershell#': ['# ' + what] + ['#   ' + x for x in lab],
             'js*': ['/*', ' * ' + what] + [' * ' + x for x in lab] + [' */']}
    for name, lines in forms.items():
        head = cs.header_block(lines, name.rstrip('#*'))[0]
        assert cs.safety_ok(head), 'a label at the start of a header line passes (%s): %r' % (name, head)


def check_rows(cs):
    """Self-test of the Maintainer-row gate on diff text.

    Args:
        cs: the check module.
    """
    name = settings.CHECK

    def plus(by):
        """Format a DECISIONS row with `by` in the By cell."""
        return row_text('cap', by).rstrip('\n')

    ok, why = cs.owner_row('The decision names %s in prose.' % name, name, 'keeper')
    assert not ok and 'rule 1' in why[0], 'a plain non-table line is refused: %s' % why
    ok, why = cs.owner_row(plus('scripts/bump_lock.py'), name, 'keeper')
    assert not ok and 'rule 3' in why[0], 'a row by a script is refused: %s' % why
    ok, why = cs.owner_row(plus("agent, under the Keeper's delegation"), name, 'keeper')
    assert not ok and 'rule 3' in why[0], 'a row by an agent is refused: %s' % why
    ok, why = cs.owner_row(plus('someone else'), name, 'keeper')
    assert not ok and 'rule 4' in why[0], 'a row by another person is refused: %s' % why
    assert cs.owner_row('| 2026-11-17 | other | the Keeper | - |', name, 'keeper') == (False, []), \
        'a row that does not name the file is not a decision for it'
    assert not cs.owner_row('| 2026-11-17 | names %s | the Keeper |' % name, name, 'keeper')[0], \
        'a row with fewer than four cells is refused'
    assert cs.owner_row(plus('the Keeper'), name, 'keeper') == (True, []), 'the Keeper row passes'
    exact = settings.NAMES_CHECK.search
    assert cs.owner_row(plus('the Keeper'), name, 'keeper', '', exact) == (True, []), 'it passes the exact test'
    assert cs.owner_row(plus('the Keeper').replace(name, settings.STATE), name, 'keeper', '', exact) == (False, []), \
        'a row that names only the state file is not a decision for the settings'
    check_row_tricks(cs, name)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / 'AGENTS.md').write_text('# Rules\n- Owner: the Keeper\n')
        assert cs.owner_role(d) == 'keeper', 'the Keeper role is read from AGENTS.md, without "the "'
        assert cs.owner_role(Path(d) / 'none') == '', 'no AGENTS.md: no owner'


def check_row_tricks(cs, name):
    """Self-test of the ways an edited or moved row must not open the Maintainer-row gate.

    Args:
        cs: the check module.
        name: the settings file name.
    """
    row = row_text('the cap of the function length goes from sixty to seventy lines, see').rstrip('\n')
    short = '| 2026-11-10 | The Keeper is not a tenant admin. | the Keeper | archive |'
    head = '# Decisions\n| Date | Decision | By | Replaces |\n|---|---|---|---|\n'
    old = head + short + '\n' + row + '\n'

    def check(line, old_text='', gone=''):
        """Run owner_row with `line` prepended and optional `gone` removed."""
        return cs.owner_row(line + '\n' + (old_text.replace(gone + '\n', '') if gone else old_text), name, 'keeper', old_text)

    for what, line in (('moved', row), ('re-spaced', row.replace('| the cap', '|   the cap'))):
        assert check(line, old, row) == (False, []), 'an old row %s is not a decision' % what
    edits = (
        ('with a full stop added', row, row.replace(', see', '., see')),
        ('with a word changed', row, row.replace('sixty', 'fifty')),
        ('with its date changed', row, row.replace('2026-11-17', '2031-01-01')),
        ('in capital letters', row, row.upper().replace(name.upper(), name)),
        ('with only the file name added', short, short.replace('admin.', 'admin. ' + name)),
        ('with an unseen character added', row, row.replace('cap', 'ca\u200bp')),
        ('cut short', row, row.replace(' goes from sixty to seventy lines', '')),
    )
    for what, was, now in edits:
        ok, why = check(now, old, was)
        assert not ok and 'rule 5' in why[0], 'an old row %s is refused: %s' % (what, why)
    assert check(row.replace('sixty to seventy', 'seventy to eighty').replace('2026-11-17', '2026-12-01'), old)[0], \
        'a new row in the words of an old one passes when the old row stays'
    ok, why = check(row_text('new opt-in rule for line length, cap 200, adopted in').rstrip('\n'), old, short)
    assert not ok and 'rule 5' in why[0], 'a new owner row beside a removed old row is refused: %s' % why
    assert check(row_text('new opt-in rule for line length, cap 200, adopted in').rstrip('\n'), old)[0], 'a new row passes'
    forged = row.replace('sixty', 'fifty') + '\n' + short + '\r' + row
    ok, why = cs.owner_row(head + forged + '\n', name, 'keeper', old)
    assert not ok and 'rule 5' in why[0], 'an old row edited in place with a carriage-return trick is refused: %s' % why
    assert cs.owner_role_in('- Owner: Claude\n') == 'claude', 'odd input'
    for line in ('| 2026-11-17 | raise the cap in %s (`a | b`) | agent, for the Keeper | - |' % name,
                 '| 2026-11-17 | raise the cap in %s | Agent | the Keeper | - |' % name,
                 '| 2026-11-17 | raise the cap in %s | the Keeper | - | x |' % name):
        ok, why = check(line)
        assert not ok and 'rule 1' in why[0], 'a row with a spare cell is refused: %s' % why
    for by in ('Claude, for the Keeper', 'not the Keeper', 'the Keeper (2A); Claude (drafted it)',
               'the Keeper (not asked; written by Claude) and others'):
        ok, why = check(row_text('cap', by).rstrip('\n'))
        assert not ok and 'rule 4' in why[0], 'the Keeper beside another writer is refused (%s): %s' % (by, why)
    assert check('  ' + row)[0], 'an indented owner row passes'
    assert check('| 2026-11-17 | a \\| b in %s | the Keeper (answer 2A) | - |' % name)[0], 'an escaped | and a note pass'


def check_lines(cs, root, g):
    """Self-test of the line cap (caps.max_line_chars) under the built-in strict gate.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
    """
    head = '"""Sample module for the line-cap self-test: it shows how the longest line is measured."""\n'
    caps = {'max_function_lines': 60, 'max_file_lines': 600, 'max_line_chars': 200}
    config = {'caps': caps, 'include': ['*'], 'exclude': [], 'generated': ['gen.py']}
    (root / 'long.py').write_text(head + 'x = "%s"\n' % ('a' * 250))
    (root / 'long.sh').write_text('# Sample shell file for the line-cap self-test.\nx = "%s"\n' % ('a' * 250))
    (root / 'short.py').write_text(head + 'x = 1\n')
    (root / 'gen.py').write_text('# GENERATED from src/x.py by build.py\nx = "%s"\n' % ('a' * 250))
    (root / 'blk.py').write_text(head + '# >>> s: generated from src/s.py by b.py\nx = "%s"\n# <<< s\n' % ('a' * 250))
    (root / 'blk2.py').write_text(head + '# >>> s: generated from src/s.py by b.py\nx = 1\n# <<< s\nx = "%s"\n' % ('a' * 250))
    g('add', '.')
    linters = cs.LINTERS
    try:
        cs.LINTERS = True
        now = cs.measure(config)['violations']['line']
        assert now == {'long.sh': 256, 'blk2.py': 256}, \
            'a non-Python file, and a .py with a generated block, fail on hand-written lines: %s' % now
        cs.LINTERS = False
        now = cs.measure(config)['violations']['line']
        assert now == {'long.py': 256, 'long.sh': 256, 'blk2.py': 256}, \
            'without ruff and pylint a long .py line is measured here: %s' % now
        ok = [('x = "%s"  # noqa: E501' % ('a b ' * 70), True), ('x = "%s"  # noqa: F401' % ('a b ' * 70), False),
              ('# see https://x.org/' + 'a' * 240, True), ('# ' + 'word ' * 45 + 'https://x.org/' + 'a' * 30, False),
              ('#' + 'a' * 250, True), ('x = "%s"' % ('a b ' * 85), False),
              ('x = "%s"  # type: ignore' % ('a b ' * 48), True), ('x = "%s"  # NOQA' % ('a b ' * 70), True),
              ('x = "%s"  # type: ignore  # noqa: F401' % ('a b ' * 48), True)]
        for line, want in ok:
            assert cs.ruff_ok(line, 200) == want, 'ruff_ok(%r...) should be %s' % (line[:30], want)
        start = time.monotonic()
        cs.ruff_ok('x = 1  ' + '# type: a ' * 1000 + '# end', 200)
        assert time.monotonic() - start < 10, 'ruff_ok is slow on a run of pragma comments'
        start = time.monotonic()
        cs.longest_line(('x = """\n' + 'a b\n' * 20000 + '"""  # ' + 'x' * 20000 + ' noqa').split('\n'), [], 40)
        assert time.monotonic() - start < 10, 'longest_line is slow on a long multi-line string with a long noqa comment'
        for text, want in RUFF_CASES:
            assert (cs.longest_line(text.split('\n'), [], 40) > 40) == want, 'longest_line(%r...) over the cap: %s' % (text[:20], want)
    finally:
        cs.LINTERS = linters
    off = dict(config, caps={k: v for k, v in caps.items() if k != 'max_line_chars'})
    assert cs.measure(off)['violations']['line'] == {}, 'a config with no cap measures nothing'
    assert config_of(root, 'code-max-line-chars: 200\n')['caps'] == dict(settings.CODE_DEFAULTS['caps'], max_line_chars=200), \
        'the cap is read from its .check line'
    assert 'max_line_chars' not in config_of(root, '')['caps'], 'no line: the rule is off'
    (root / settings.CHECK).unlink()
    new, fixed = cs.compare({'line': {'long.py': 256}}, {'line': {'long.py': 256}}, caps)
    assert not new and not fixed, 'a debt value that is the same passes'
    new, _ = cs.compare({'line': {'long.py': 300}}, {'line': {'long.py': 256}}, caps)
    assert len(new) == 1 and 'grew from 256 to 300' in new[0], 'a debt value may not go up: %s' % new
    new, fixed = cs.compare({'line': {'long.py': 210}}, {'line': {'long.py': 256}}, caps)
    assert not new and len(fixed) == 1, 'a debt value that went down is reported as fixed: %s' % fixed


def check_strict_main(cs, root, g):
    """Self-test of the strict ratchet gate against main.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
    """
    (root / 'AGENTS.md').write_text('- Owner: the Keeper\n')
    (root / 'docs').mkdir()
    old_row = '| 2026-11-01 | The Keeper is not a tenant admin. | the Keeper | - |\n'
    (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n' + old_row)
    for f in ('a.py', 'b.py'):
        (root / f).write_text('x = 1\n')
    write(root, 'code-c1-safety: on\n', {'safety': {'a.py': 1}})
    cfg = settings.code_config(root)
    commit(g, 'base')
    strict = dict(cfg, c1_safety=settings.STRICT)
    both = {'safety': {'a.py': 1, 'b.py': 1}}

    def problems(config, debt, decisions, keep=old_row):
        """Evaluate against_main with updated DECISIONS.md content."""
        (root / 'docs' / 'DECISIONS.md').write_text('# Decisions\n' + decisions + keep)
        return ' | '.join(cs.against_main(config, debt)[0])

    strict_text = 'the stricter form of the safety lines is adopted now and files that newly fail are listed once in'
    assert not problems(strict, both, row_text(strict_text)), 'an owner row opens the gate for a raised level'
    assert 'added by hand' in problems(strict, both, 'no row\n'), 'no row: new debt fails'
    edited = old_row.replace('admin.', 'admin. ' + settings.CHECK)
    assert 'rule 5' in problems(strict, both, '', edited), 'main\'s old row with the file name added does not open the gate'
    assert 'rule 5' in problems(strict, both, row_text(strict_text), ''), 'a new row beside a removed old row does not either'
    for by, rule in (('scripts/x.py', 'rule 3'), ("agent, under the Keeper's delegation", 'rule 3'),
                     ('someone else', 'rule 4')):
        assert rule in problems(strict, both, row_text(strict_text, by)), 'a row by %r is refused by %s' % (by, rule)
    assert 'rule 1' in problems(strict, both, 'Level changes %s.\n' % settings.CHECK), 'a plain line is refused'
    (root / 'AGENTS.md').write_text('- Owner: Claude\n')
    assert 'rule 4' in problems(strict, both, row_text(strict_text, 'Claude')), 'a new owner named in this change cannot decide'
    (root / 'AGENTS.md').write_text('- Owner: the Keeper\n')
    assert 'setting' in problems(strict, both, '| 2026-11-17 | other | the Keeper | - |\n'), 'a row for another thing'
    new_file = {'safety': {'a.py': 1, 'new.py': 1}}
    assert 'new files meet the rules' in problems(strict, new_file, row_text(strict_text)), 'debt for a new file is refused'
    on = dict(cfg, caps=dict(cfg['caps'], max_line_chars=200))
    debt = {'safety': {'a.py': 1}, 'line': {'a.py': 300}}
    assert not problems(on, debt, row_text(
        'a new opt-in rule, the longest line of a file, is turned on with a cap of 200 characters in')), \
        'the line cap adopts with an owner row'
    assert problems(on, debt, 'no row\n'), 'the line cap needs a row'
    with contextlib.redirect_stdout(io.StringIO()):
        assert cs.adopt(strict, {'safety': {'a.py': 1}}, both) == 0, '--adopt lists debt of a raised level'
        assert set(cs.load()[1]['safety']) == {'a.py', 'b.py'}, '--adopt writes it'
        write(root, 'code-c1-safety: on\n', {'safety': {'a.py': 1}})
        assert cs.adopt(cfg, {'safety': {'a.py': 1}}, both) == 1, 'the same level as main: --adopt is refused'


def check_key(cs, root, g):
    """Prove that `code-strict-gate: on` loads STRICT_GATE into cs.load() and a project gate file wins.

    Args:
        cs: the check module.
        root: the sample repo folder.
        g: git command runner.
    """
    own = cs.GATE_FILE
    cs.GATE_FILE = root / 'scripts' / 'own_gate.py'
    try:
        write(root, 'code-strict-gate: on\ncode-max-line-chars: 200\ncode-c1-safety: strict\n')
        cfg, _ = cs.load()
        assert cs.GATE is cs.STRICT_GATE, 'the key loads the built-in strict gate'
        assert cfg['strict_gate'] is True, 'the setting is read'
        write(root, 'code-strict-gate: off\n')
        cs.load()
        assert cs.GATE is None, 'off loads nothing'
        write(root, 'code-max-line-chars: 200\n')
        try:
            cs.load()
            raise AssertionError('a line cap with no gate and no key fails')
        except ValueError as err:
            assert 'gate' in str(err), err
        write(root, 'code-strict-gate: maybe\n')
        try:
            cs.load()
            raise AssertionError('an invalid value fails')
        except ValueError:
            pass
        (root / 'scripts').mkdir()
        cs.GATE_FILE.write_text(SAMPLE_GATE)
        write(root, 'code-strict-gate: on\n')
        cs.load()
        assert cs.GATE.__file__ == str(cs.GATE_FILE), 'a project gate file wins over the key'
    finally:
        cs.GATE_FILE = own


# ---------------------------------------------------------------- unittest Entry Points -------------------------------

class StrictGateTest(unittest.TestCase):
    """The cases of the built-in strict rules; each sets cs.GATE to STRICT_GATE and restores state."""

    def setUp(self):
        """Load STRICT_GATE and save cs state."""
        self.saved = cs_mod.ROOT, cs_mod.GATE
        self.gate = cs_mod.GATE = cs_mod.STRICT_GATE
        self.addCleanup(self.restore)

    def restore(self):
        """Restore cs.ROOT and cs.GATE."""
        cs_mod.ROOT, cs_mod.GATE = self.saved

    def in_repo(self, case):
        """Run `case(cs_mod, root, g)` in a fresh sample repo."""
        with tempfile.TemporaryDirectory() as d:
            cs_mod.ROOT = Path(d)
            case(cs_mod, cs_mod.ROOT, sample_repo(d))
            cs_mod.GATE = self.gate

    def test_safety_form(self):
        """A label inside prose, mid-line or with no value fails; a label at a header line start passes."""
        check_safety(cs_mod)

    def test_owner_rows(self):
        """Only a new row with the Maintainer alone in its By cell passes; the refusals name their rule."""
        check_rows(cs_mod)

    def test_line_cap(self):
        """The line cap measures hand-written lines; the debt value may go down, not up."""
        self.in_repo(check_lines)

    def test_against_main(self):
        """The ratchet against main: an owner row opens it, new-file debt is refused, --adopt of a raised level."""
        self.in_repo(check_strict_main)

    def test_key_loads_the_rules(self):
        """`code-strict-gate: on` loads STRICT_GATE when the project has no gate file; a project gate file wins."""
        self.in_repo(check_key)


class CodeStandardTest(unittest.TestCase):
    """Unittest entry point for core code_standard cases."""

    def test_self_test(self):
        """Every case passes on the check module; its repo root is put back after the run."""
        root = cs_mod.ROOT
        self.addCleanup(setattr, cs_mod, 'ROOT', root)
        self.assertEqual(run(cs_mod), 0)


if __name__ == '__main__':
    unittest.main()
