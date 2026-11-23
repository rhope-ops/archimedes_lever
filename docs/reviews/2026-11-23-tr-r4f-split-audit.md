# Tool retirement R4f: sample audit of check-driven splits (AUD-4)

Fresh read-only review, 2026-11-23 ~16:55 America/Chicago, by a reviewer on a model other than the split authors'
(coverage row AUD-4). The reviewer got the code and the design goal ("is the code easier to change and understand?"),
not the authors' conclusions. Saved by the main session; 2 claims re-checked (marked "checked").

Rule used: a part that receives its parent module (`cs`, `sb`, `core`) or the parent's `read`/`write`/callbacks, where
the code before the split did not, counts as coupling made by the split. PowerShell: shared dot-source scope is normal;
the test there is "one job you can name".

## Totals

| Source | Judged | COHESIVE | MIXED | ARBITRARY |
|---|---|---|---|---|
| ICF-Source (merge 03d407a1, 11 of 21) | 11 | 7 | 3 | 1 |
| Kit | 7 | 2 | 4 | 1 |
| 90-161.Z (5 splits found, not 6) | 4 | 2 | 2 | 0 |
| **Overall** | **22** | **11** | **9** | **2** |

Pattern: splits by subject mostly hold. The weak ones are test files that mix fixtures with cases, parts named by kind
(`_steps`, `_helpers`, `_plan`, `_rules`, `_run`), and parts that get the parent module handed back to them. Four ICF
parents sit at 437-445 lines, so the next edit reopens the cap question.

## Three worst

1. **Kit `scripts/sync_baseline_run.py`**: `main()` moved out with the parent module as its argument; 14 `sb.` names;
   `main` is now one line (`scripts/sync_baseline.py:441`, checked); parent at 445. Seam: plan (`planned_files`,
   `build_agents`, `new_log`) against write (`write_files`, `write_lock`), `main` in the entry file.
2. **ICF `scripts/quality_points_plan.py`** (63 lines): three unrelated items from two places; the parent imports a
   private name (`quality_points.py:27`); parent at 442 (checked). Seam: plan reading and shape checks as one part.
3. **ICF `scripts/question_language_forms.py`**: a cut at the tail of the file with a two-way import at the end of both
   files (`question_language.py:436`, `question_language_forms.py:133`, checked). Seam: tables and
   `acronym_profile`/`expansions`/`full_form` in a base module both import.

Close behind: kit `code_standard_ratchet.py` (parent module as argument, 7 attributes, 3 wrappers left behind) and ICF
`validate_questions_rules.py` (a grab-bag of constants, a cache and helpers).

## All judged splits

| # | Source | Split | Lines | Verdict | Evidence / better seam |
|---|---|---|---|---|---|
| 1 | ICF | apply_revision -> _edits | 528 -> 133 + 408 | COHESIVE | CLI stays, Revision engine moves; one import line |
| 2 | ICF | question_language -> _forms | 547 -> 437 + 133 | MIXED | import cycle (worst 3) |
| 3 | ICF | quality_points -> _plan | 490 -> 442 + 63 | ARBITRARY | worst 2 |
| 4 | ICF | new_bank_apply -> _steps | 591 -> 437 + 188 | MIXED | split added `read, write` to 4 signatures; revision rows in both files. Seam: approvals and revision rows; Standard/Exam run; Hard run |
| 5 | ICF | mutant_gates -> _spec | 575 -> 375 + 220 | COHESIVE | item gates vs spec gates; header line 9 is wrong (says the parent imports every name; it imports none) |
| 6 | ICF | test_mutation_gates -> _gates | 512 -> 382 + 149 | COHESIVE | data and gates vs mutations and tests |
| 7 | ICF | validate_questions -> _rules, _exports | 578 -> 443 + 72 + 134 | MIXED | grab-bag rules; exports cut from function bodies with `read`/`check` passed in |
| 8 | ICF | blind_check -> _judge, _selftest | 588 -> 445 + 56 + 127 | COHESIVE (weak) | self-test got 3 callback arguments; parent at 445 |
| 9 | ICF | test_new_bank_tools -> _expand, _points | 586 -> 382 + 151 + 96 | COHESIVE | split by tool under test |
| 10 | ICF | test_build_glossary -> _matcher | 513 -> 415 + 133 | COHESIVE | matcher rules vs build output |
| 11 | ICF | screen_walk_scholar_passes -> _b3 | 536 -> 223 + 327 | COHESIVE | one walk per file |
| 12 | Kit | token_log -> _rows, _report (c79a917) | 599 -> 361 + 162 + 153 | COHESIVE | lazy report load for an install reason; cost: parent injected as `core`, module `__getattr__` |
| 13 | Kit | token_log_test -> _test_report (d75c483) | 591 -> 368 + 255 | MIXED | "report" file holds agent, self-update, URL cases and all fixtures. Seam: fixtures file, then cases by subject |
| 14 | Kit | code_standard -> _rules, _ratchet (9254c92) | 597 -> 431 + 117 + 111 | MIXED | `_ratchet` takes the parent module. Seam: a base with `git`, `level`, `rules`, `save` |
| 15 | Kit | code_standard_test -> _test_gate, _test_docs (9254c92) | 571 -> 317 + 190 + 115 | MIXED | gate cases mixed with shared helpers. Seam: fixtures file, cases by rule |
| 16 | Kit | sync_baseline -> _repo, _run (d98c106) | 587 -> 436 + 133 + 74 | ARBITRARY (`_run`); `_repo` COHESIVE | worst 1 |
| 17 | Kit | check_settings -> _read (46c0247) | 586 -> 292 + 321 | COHESIVE | readers vs migration and CLI; cost: a 34-name re-export |
| 18 | Kit | check_content_scan -> _scan_settings (8cd7414) | 599 -> 374 + 251 | MIXED | "settings" also loads the denylist and fingerprint. Seam: word-list sources vs `.check` parsing |
| 19 | 90-161.Z | T26 endorse -> T26-restore-r1 (bce3231) | 558 -> 430 + 145 | COHESIVE | one test's parts and fixtures move together |
| 20 | 90-161.Z | New-Publication -> Publication.Word (13ce43d) | 500 -> 444; part 226 -> 306 | MIXED | run steps appended to a format-helper file, reading caller scope; the commit also changes behaviour (not a pure split). Seam: a third file for post-render checks |
| 21 | 90-161.Z | T20 provision -> T20-helpers-r4 (de90dcc) | 553 -> 444 + 125 | MIXED | pure planning mixed with 10 SharePoint calls. Seam: plan part, SharePoint part |
| 22 | 90-161.Z | logo_svg -> _path (2f91342) | 458 -> 330 + 145 | COHESIVE | pure SVG path parser, 3-name interface |

Outside the sample: kit `build_site_html.py` mixes the Markdown builders, the page shell and the `dod-security`
settings reader that `check_settings.py:65` imports.

## Not verified

No code was run (the import cycle is read from source and re-checked by reading). ICF items 9-11 and 90-161.Z
`build_flow_solution` -> `_xml` were judged from headers, definitions and imports only. 10 of the 21 ICF splits were not
sampled.
