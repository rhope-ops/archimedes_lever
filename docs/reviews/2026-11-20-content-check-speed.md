# Content check speed (kit 6.1.2)

Date: 2026-11-20, America/Chicago. Request: the owner, from icf-source (the content check step took about 130 s of the 130-145 s full lane; the pre-push scan about 75 s). Rule: same findings, no skip, no raised limit, no weaker rule.

## Where the time went (profile)

`python3 -m cProfile scripts/check_content.py --all` on icf-source (3,314 tracked files, about 3.2 million scanned lines, DoD tier, 14 denylist names, 4-core cloud runner): 90 s wall, all of it in `scan_text`. Each line ran about 30 regex calls (7 finder kinds, names, and the generator calls around them): 96.8 million `finditer` calls. Reading files, git and the denylist cost under 1 s.

## What changed

1. Gates (`check_content_finders.py`: `GATES`, `candidate_lines`). For each kind, patterns that are parts of that kind's own patterns with look-arounds, anchors and `\b` removed: they can only match more text, so a line with no gate match cannot give a finding. Each gate is searched once in the whole text; its matches name the lines that get the full scan, which is unchanged. Case-free gates search the `str.lower()` copy (same length, so the same places) with plain literals; a text with one of the 4 letters that `(?i)` matches outside a-z (U+0130, U+0131, U+017F, U+212A) or a `lower()` of another length gets `(?i)` search instead. A name that is not ASCII gates on its longest ASCII part. A kind with a project's own finders turns the gates off (every line is scanned).
2. A process pool in `scan_files` for a scan of 4 MB or more (not for named files or the hook): results are kept in file order; a pool that cannot start falls back to the scan in one process.
3. Self-test: the 4 hook runs of the local-finder load-timer case run at the same time (the 3 fall-back cases each wait the 8 s default by design).

## Measurements (icf-source, same runner, nothing else running)

| Run | Before | After |
|---|---|---|
| `check_content.py --all`, 5 runs (s) | 88.73, 88.90, 89.00, 89.17, 90.38 | 6.56, 6.64, 6.68, 6.68, 6.69 |
| Median | 89.00 s | 6.68 s (-92.5 %, 13.3x) |
| Pre-push mode `--all --push --require-denylist`, 1 run | 95.3 s | 9.2 s |
| Kit self-test `check_content.py --test`, 1 run | 31.0 s | 12.5 s |

## Proof of the same result

- icf-source: `--all` and the pre-push mode give byte-identical output and exit codes, old against new.
- Planted corpus (a temporary git repo: 60 docs, 4 large JSON files over the pool limit, an oversize file, a binary, a PNG, a non-UTF-8 file, a blocked file, a skipped file, 6 commits with findings in messages and added lines; every line break that `splitlines` knows; samples split over lines): 7 modes (`--all`, `--range`, `--push`, files, `--stdin`, `--all --require-denylist`, `--status`) in both tiers, 14 of 14 runs byte-identical in stdout, stderr and exit code; all 11 finding kinds present (blocked, dodid, email, id, marking, milhost, name, phone, secret, term, unscanned).
- New self-test cases (`check_content_test_blocks.py`): `FOLD_EXTRAS` equals what the regex engine matches over every code point; 400 seeded random texts from samples of every kind give the same findings with and without the gates in both tiers; the pool gives the same findings in the same order; the gates are off with a project's own finder.
- Mutation test of the gates: 22 of 22 broken gates (one piece removed or changed each) make the random-text case fail.
- `python3 scripts/check_content.py --test`: PASS, 286 cases (the 281 before, all still there, and 5 new). `scripts/check.sh --test`: PASS. `scripts/check.sh` (full lane): CHECK PASS, 24 passed, 1 skipped.

## Limits

- The pool uses fork on Linux and the default start method elsewhere; it was measured on Linux only.
- The time baselines in `.check.state.json` were recorded on a faster machine (check_content self-test 4.1 s); on this runner the old code took 31 s, so the full lane prints WARN lines against them. The baselines were not re-recorded.
