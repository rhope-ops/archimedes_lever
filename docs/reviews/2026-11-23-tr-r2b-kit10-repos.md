# Tool retirement research R2b: the five repos on kit 10.0.0 (2026-11-23)

Step R2 of docs/reviews/2026-11-23-tool-retirement-research-plan.md; coverage row B2-5 of docs/reviews/2026-11-23-tool-retirement-coverage.md. Read-only inventory of five project repos (local clones, history from about 2026-10-24). It lists facts and candidate standard tools with trade-offs. It does not decide retire, shrink or keep.

How the numbers were measured:
- Kit state: `.check.lock` JSON ("files" map, "version", "commit"); sha256 of each locked path in the repo against the same path in the kit checkout (11.0.1).
- Project tool = a script or program the repo owns that is not a kit-locked file: tracked `.py`, `.sh`, `.c`, `.js`, `.cjs`, `.mjs` files under `tools/`, `bench/`, `previews/` (only `.py` there), plus `scripts/check.local.sh`, `.claude/hooks/*.sh` and `tools/git-hooks/*`. Product code (what users run) and data files are not rows.
- Lines = `wc -l` equivalent (newline count). Commits 30d = `git log --since=2026-10-24 --oneline -- <path>` count.
- Callers = text search for the path or file name in every tracked file outside docs/ (so check.sh, check.local.sh, workflows, settings, other scripts, tests). "docs/skills" = named only in .md files or `.claude/skills`. The search is a text match: a name in a comment counts, a dynamic call does not. Treat it as a lead, not proof.
- Test = the tool's own `--test` flag, or a file under tests/ that names the tool. "none found" = neither.
- Candidates are standard tools that do a similar job; fit and cost are not tested here. "none known" = I know no standard tool for the job.

## Summary

| Repo | HEAD | Kit | Locked entries / exist / same / differ / absent in kit | check.local.sh | AGENTS.md lines | Project tools: files / lines | Commits 30d (repo) |
|---|---|---|---|---|---:|---|---:|
| no-more-beyond | aff767b | 10.0.0 | 55 / 54 / 10 / 43 / 1 | yes | 77 | 69 / 12,260 | 761 |
| transcription_assistant | abbc8cc | 10.0.0 | 55 / 54 / 10 / 43 / 1 | yes | 79 | 15 / 2,239 | 53 |
| SPAR | 01ede27 | 10.0.0 | 55 / 54 / 10 / 43 / 1 | no | 74 | 0 / 0 | 43 |
| 36-3003.Z | 253b30b | 10.0.0 | 55 / 54 / 10 / 43 / 1 | no | 73 | 0 / 0 | 38 |
| 65-601.Z | a8e60fd | 10.0.0 | 55 / 54 / 10 / 43 / 1 | no | 73 | 0 / 0 | 33 |

Totals: 84 project tool files, 14,499 lines across the two repos that have any. Not counted above: the test harness in no-more-beyond (tests/, 71 files, 3,868 lines) and in transcription_assistant (none).

## no-more-beyond (HEAD aff767b)

- HEAD: `aff767b` (2026-11-21); commits since 2026-10-24: 761.
- Kit version recorded: `.check.lock` "version": 10.0.0, kit commit f397b52d, overrides: none. No KIT_VERSION, CHANGELOG or kit.config.json in the repo. The kit at /home/user/archimedes_lever is 11.0.1.
- Kit-locked entries in `.check.lock`: 55. One entry is not a file ("AGENTS.md (kit sections)"), so 54 named files exist and 0 named files are missing from disk.
- Compared with the kit by sha256 of the same path (54 existing files): same 10, differ 43, absent in kit 1 (`scripts/fulcrum_tokens.py`, not in kit 11.0.1). Files that differ from the repo's own lock: 0 (the repo matches its recorded 10.0.0 lock; the 43 are kit changes since).
- `scripts/check.local.sh`: yes (13 lines; runs `tools/check.py`, which picks lint, smoke, equiv and bench from the diff). Workflows: `check.yml` (only one). `AGENTS.md`: 77 lines.

Product code: a browser game of about 59 root `.js`/`.mjs` files (8,245 lines, many minified), `.css`/`.html`, `music/*.mjs` (runtime music engine), `data/`, `assets/`, `audio/`, plus `previews/` pages (tuner, proposal book, node previewer). Not rows below.

Project tools (`tools/` has its own table, `tools/README.md`, and `tools/check.py` lints that every `tools/*.py` is in it):

| Path | Job | Lines | Callers | Test | Commits 30d | Candidates |
|---|---|---:|---|---|---:|---|
| `.claude/hooks/session-start.sh` | Cloud sessions: make tools/smoke.py and the other browser checks runnable even when the session did not | 32 | .claude/settings.json, tools/cloud-setup.sh, tools/git-hooks/pre-push; docs/skills | none found | 7 | kit session_checkin.sh / first_use_check.py (hooks path); husky or lefthook for hooks path |
| `bench/capacity/run.py` | Native GPU capacity sweep. Explicit --software is a diagnostic fallback, not device FPS | 39 | docs/skills | none found | 1 | Lighthouse CI; Playwright tracing; none known for the GPU capacity sweep |
| `bench/capacity/validate.py` | Validate a completed capacity run without assuming a particular performance result | 16 | docs/skills | none found | 1 | none known (validates its own run output) |
| `bench/capacity/workload.js` | Benchmark only. Loaded before the game inside capacity.html's isolated iframe | 75 | bench/capacity.html, bench/results/capacity-rtx3080-hit-accurate.json | none found | 1 | none known (in-page workload for capacity.html) |
| `bench/profile.py` | Seeded CPU profiles of max-path weapons using the existing #bench fixture | 180 | tests/hardening/projectile_profile.py | tests/hardening/projectile_profile.py | 2 | node --cpu-prof; Playwright/CDP profiler |
| `previews/assets/opening-claude/build_artifact.py` | Builds the self-contained artifact copy of previews/opening-claude.html | 43 | none found | none found | 1 | vite/esbuild single-file plugin; make |
| `previews/assets/opening-claude/render_art.py` | Renders the new opening-cutscene art for previews/opening-claude.html | 418 | none found | none found | 1 | none known (one-off art render) |
| `previews/proposal-book/build.py` | Build previews/proposal-book/index.html from its parts, then check the contract rules that data can show | 153 | none found | none found | 2 | esbuild/vite; make |
| `previews/proposal-book/measure.py` | Headless frame-time check for the proposal book: console errors and per-stage draw cost | 70 | none found | none found | 4 | Playwright Test (@playwright/test) with webServer; Lighthouse CI |
| `scripts/check.local.sh` | No More Beyond project checks, run last by the kit's scripts/check.sh. Pass = exit 0 | 13 | scripts/check.sh (kit, by name); docs/skills | none found | 1 | kit-defined hook (check.sh runs it last); not a free-standing tool |
| `tools/alias.py` | Collapse install-time aliases `NAME=OTHER;` (or chains `A=B=OTHER;`) into one declaration | 60 | docs/skills | none found | 2 | jscodeshift; ESLint no-multi-assign + fix |
| `tools/audit_cards.py` | Audit editor records against actual takeOffer transitions. Exit 1 on discrepancies | 160 | tests/conformance/prove_card_rows.py, tests/conformance/prove_checks.py, tools/card_rows.py; docs/skills | tests/conformance/prove_card_rows.py, tests/conformance/prove_checks.py | 5 | none known (project rule audit) |
| `tools/balance_sim.py` | Earned-run diagnostics using the existing rebuild driver (no duplicate simulator) | 15 | tests/rebuild/earned.py, tools/echo_income.py; docs/skills | tests/rebuild/earned.py | 2 | none known (game-specific model) |
| `tools/bench.py` | Run the in-game benchmark headlessly and save the results | 87 | .claude/settings.json, tests/cleanup/bench_pairs.py, tools/bench_pairs.py; docs/skills | tests/cleanup/bench_pairs.py | 8 | tinybench / benchmark.js; Lighthouse CI; Chrome DevTools Protocol tracing |
| `tools/bench_pairs.py` | Canonical benchmarks, alternating reference/current, exactly one browser job | 82 | .claude/settings.json, tests/perf/bench_pairs_summary.py, tools/check.py; docs/skills | tests/perf/bench_pairs_summary.py | 5 | hyperfine (CLI, not browser); tinybench; none known for matched browser A/B pairs |
| `tools/branches.py` | Branch and session state against origin/main: what is not merged yet | 300 | .check.state.json, .claude/settings.json; docs/skills | own --test | 9 | `gh` CLI (gh pr list, gh api); `git branch -r --merged origin/main`; git-delete-merged-branches |
| `tools/browser.py` | Shared headless Chromium launch for every tool | 17 | previews/proposal-book/measure.py, tools/build_tuner.py, tools/check.py, tools/equiv.py (+5); docs/skills | none found | 2 | Playwright config (use.launchOptions in playwright.config) |
| `tools/build_tuner.py` | Build the NMB Omniversal Tuner page and its publish folder | 258 | previews/omniversal-tuner.html, previews/tuner/d2-omni-items.js, previews/tuner/omni-hook.js; docs/skills | own --test | 4 | vite/esbuild bundling; make; none known for the tuner publish folder |
| `tools/card_rows.py` | Measure active Card Editor rows without changing the game or source catalog | 197 | tests/conformance/prove_card_rows.py; docs/skills | tests/conformance/prove_card_rows.py | 1 | none known |
| `tools/chains.py` | Inspect live wrapper chains (layers that call the previous version) | 71 | tools/flatten.py, tools/merge_helpers.py, tools/staticchain.py; docs/skills | none found | 1 | jscodeshift / recast for AST inspection |
| `tools/check.py` | Run the checks a change needs, chosen from the files it touches (AGENTS.md "Checks") | 172 | .check.state.json, .claude/settings.json, scripts/check.local.sh, tools/browser.py (+1); docs/skills | none found | 9 | make or just (task runner); pre-commit (per-file selection); nx/turbo "affected" (needs a package.json workspace) |
| `tools/cloud-setup.sh` | Setup script for the "NMB" Claude Code cloud environment (claude.ai/code -> environment selector -> settings i | 31 | .claude/hooks/session-start.sh; docs/skills | none found | 6 | devcontainer.json / Dockerfile; a Claude Code SessionStart hook |
| `tools/codemap.py` | Regenerate the generated tables in docs/load-order.md (linked from CODEMAP.md) from the source | 125 | .claude/settings.json, tests/cleanup/test_inline_scripts.py, tools/check.py; docs/skills | tests/cleanup/test_inline_scripts.py | 5 | madge; dependency-cruiser (module graph); none known for the wrapper-chain tables |
| `tools/deadcode.py` | Remove dead layered code from the minified legacy files | 154 | tests/cleanup/test_inline_scripts.py, tools/chains.py, tools/extract.py, tools/flatten.py (+2); docs/skills | tests/cleanup/test_inline_scripts.py | 3 | knip; ts-prune; ESLint no-unused-vars; terser dead-code removal |
| `tools/decisions.py` | Check which decision-ledger bullets are reflected in docs/design.md | 86 | .claude/settings.json; docs/skills | none found | 3 | none known (project ledger vs design.md) |
| `tools/drawprof.py` | Where does a bench frame go? Per-function draw cost, sim/draw totals, population mix and terrain bake state | 147 | .claude/settings.json; docs/skills | none found | 3 | Chrome DevTools Protocol profiler / Playwright tracing; Chrome performance panel |
| `tools/echo_income.py` | Echo income per run from a balance_sim curve report (T26) | 98 | catalog.js, previews/omniversal-tuner.html; docs/skills | none found | 2 | none known (game-specific model) |
| `tools/equiv.py` | Deterministic behavior digest, for checking that a refactor changes nothing | 134 | .claude/settings.json, bench/profile.py, tests/cleanup/bake_visuals.py, tests/hardening/digest_causality.py (+7); docs/skills | tests/cleanup/bake_visuals.py, tests/hardening/digest_causality.py (+4) | 6 | Playwright Test (@playwright/test) with webServer with golden-file (snapshot) compare; none known for "behavior equal to another commit" |
| `tools/equiv_scenarios.py` | Deterministic consolidation coverage, reusing equiv.py's seeded clock and RNG setup | 193 | .claude/settings.json, bench/profile.py, tests/cleanup/bake_visuals.py, tests/cleanup/draw_profile.py (+29); docs/skills | tests/cleanup/bake_visuals.py, tests/cleanup/draw_profile.py (+22) | 6 | Playwright Test (@playwright/test) with webServer snapshot compare; none known for the scenario matrix |
| `tools/extract.py` | Move the live definition of global functions into one owning file | 190 | tools/alias.py, tools/merge_helpers.py, tools/staticchain.py; docs/skills | none found | 4 | jscodeshift; ts-morph "move to file"; IDE refactor |
| `tools/flatten.py` | Flatten a wrapper chain into one orchestrating function plus named per-module steps | 196 | docs/skills | none found | 3 | jscodeshift; ts-morph; recast |
| `tools/fractal/jdz.c` | Julia deep-zoom loop renderer for the NMB title fractal (assets/menu-fractal.mp4) | 101 | start-fractal.js | none found | 1 | none known (project renderer; generic fractal renderers exist but not for this asset) |
| `tools/game_docs.py` | Map every GAME leaf to the source comment that explains it (catalog.js), for the Omniversal Tuner | 106 | tools/build_tuner.py; docs/skills | none found | 1 | JSDoc / typedoc (comment extraction); none known for GAME-leaf mapping |
| `tools/git-hooks/pre-push` | Hand-off only: the old project pre-push hook, kept so a clone whose core.hooksPath still names tools/git-hooks | 30 | .check; docs/skills | none found | 10 | kit scripts/git-hooks/pre-push (kit-locked, active hooks path); husky; lefthook; pre-commit |
| `tools/htmlscripts.py` | Locate inline JavaScript without confusing the loader with the gameplay core | 20 | tests/cleanup/test_inline_scripts.py, tools/alias.py, tools/codemap.py, tools/deadcode.py (+4); docs/skills | tests/cleanup/test_inline_scripts.py | 1 | html parser (BeautifulSoup / parse5); cheerio |
| `tools/jsedit.py` | Small helpers for editing the minified legacy files safely (used during consolidation) | 40 | docs/skills | none found | 1 | recast; jscodeshift |
| `tools/layers.py` | Find (and optionally delete) layers that a later install overwrites without keeping | 248 | tests/cleanup/test_inline_scripts.py, tools/chains.py, tools/extract.py, tools/flatten.py (+2); docs/skills | tests/cleanup/test_inline_scripts.py | 2 | knip; ESLint no-unused-vars / no-shadow; jscodeshift |
| `tools/live_fn.py` | Print which definition of each global function is live after all layers install | 47 | docs/skills | none found | 2 | ESLint no-redeclare; none known for load-order liveness |
| `tools/merge_helpers.py` | Helpers for hand-merging a wrapper chain into one declaration (used during consolidation) | 49 | tools/staticchain.py; docs/skills | none found | 3 | recast; jscodeshift |
| `tools/music/audit_assets.py` | Verify the runtime pack without trusting names or decoder exit status alone | 26 | tools/music/preflight.py; docs/skills | none found | 3 | ffprobe (ffmpeg) for decode check; none known for the manifest check |
| `tools/music/build_desk.py` | Build the Music Studio previewer (artifact "NMB Music Studio", formerly the Music Desk) and a compact publish  | 173 | docs/skills | none found | 18 | vite/esbuild; make |
| `tools/music/claude_fusion.py` | Claude's Nov 8 batch: ten drum-and-bass x synthwave run tracks (two with a massed choir lead, one with a choir | 1487 | tools/music/claude_pro.py; docs/skills | none found | 4 | same as claude_tracks.py |
| `tools/music/claude_pro.py` | Usage: python3 tools/music/claude_pro.py SONG [--revision claude-pro1] [--only LAYER] [--no-encode] | 309 | tools/music/pro_sampler.py; docs/skills | none found | 5 | surgepy direct + sfizz/FluidSynth; none known for the project song pipeline |
| `tools/music/claude_runs.py` | Claude's run tracks after Perihelion (generic builder in claude_song.run_track) and the start-screen theme | 680 | tools/music/claude_fusion.py; docs/skills | none found | 7 | same as claude_tracks.py (renderers only; composition: none known) |
| `tools/music/claude_sfx.py` | Rendered sample layers for hybrid SFX (sample + live synth). Original synthesis only | 755 | previews/omniversal-tuner.html, system-sfx.js, tools/cloud-setup.sh; docs/skills | none found | 7 | sfxr/jsfxr-style generators; sox; ffmpeg lavfi synth |
| `tools/music/claude_song.py` | Shared layer builders for Claude's tracks after Perihelion, plus the track definitions themselves | 636 | tools/music/claude_fusion.py, tools/music/claude_runs.py, tools/music/claude_tracks.py; docs/skills | none found | 8 | same as claude_tracks.py |
| `tools/music/claude_synth.py` | Claude's offline synthesis toolkit for No More Beyond stems (numpy + numba) | 575 | tools/music/claude_fusion.py, tools/music/claude_runs.py, tools/music/claude_sfx.py, tools/music/claude_song.py (+1); docs/skills | none found | 6 | SuperCollider; Csound; pyo; numpy+scipy stay as the base |
| `tools/music/claude_tracks.py` | Claude's layered run tracks for No More Beyond: composition, rendering, sectioning, Opus encoding, manifests | 594 | tools/music/claude_fusion.py, tools/music/claude_pro.py, tools/music/claude_runs.py, tools/music/claude_song.py (+1); docs/skills | none found | 9 | FluidSynth / sox / SuperCollider / Csound as renderers; composition itself: none known |
| `tools/music/compress_assets.py` | Encode music section FLACs to Ogg Opus and update every manifest that points at them | 35 | .gitignore | none found | 1 | ffmpeg + libopus or opusenc in a Makefile/shell loop |
| `tools/music/mixcheck.py` | Mix check: decode a manifest's Opus sections, apply its layer curves at given game states, report loudness, | 121 | tools/cloud-setup.sh, tools/music/claude_pro.py | none found | 2 | ffmpeg ebur128 filter; pyloudnorm; loudness-scanner |
| `tools/music/mixlive.py` | Measure the in-game mix: music bus vs SFX bus loudness (RMS dBFS), idle and while BMR fires | 73 | none found | none found | 2 | ffmpeg ebur128 filter; pyloudnorm (live capture part: none known) |
| `tools/music/originality.py` | Originality check: compare our hook/answer lines against a reference melody line, in any key | 115 | tools/music/claude_fusion.py, tools/music/claude_tracks.py; docs/skills | none found | 3 | none known (melody similarity; music21 is a toolkit, not a checker) |
| `tools/music/preflight.py` | One command to check the modular music handoff on a fresh checkout | 22 | docs/skills | own --test | 2 | make target / shell wrapper over audit_assets.py |
| `tools/music/pro_fx.py` | Mix effects for the pro renders: zita_rev1 hall reverb (Faust, through DawDreamer) and pedalboard EQ, compress | 27 | docs/skills | none found | 1 | Faust / sox / ffmpeg reverb filters |
| `tools/music/pro_kit.py` | Drum one-shots (CC0) for the pro renders, trimmed and peak-normalized in tools/music/kit/ (sources: kit/SOURCE | 51 | docs/skills | none found | 1 | sox; ffmpeg (trim/normalize) |
| `tools/music/pro_sampler.py` | Multisample playback for the pro renders: nearest recorded note, repitched by resampling; long notes extend by | 72 | docs/skills | none found | 1 | sfizz; FluidSynth; sox |
| `tools/music/serve.py` | Serve the local workshop with correct ES-module MIME types on Windows | 13 | tests/response/boss_diagnostics.py, tests/response/integration.py, tests/response/stress.py; docs/skills | tests/response/boss_diagnostics.py, tests/response/integration.py (+1) | 1 | `python3 -m http.server` with mimetypes fix; `npx serve`; vite dev server |
| `tools/music/setup_pro.sh` | Install the pro music toolchain (Surge XT synthesizer as a Python module, DawDreamer, pedalboard) and the CC0  | 29 | tools/music/pro_sampler.py, tools/music/surge_render.py; docs/skills | none found | 4 | pip + requirements.txt; devcontainer/Dockerfile |
| `tools/music/surge_render.py` | Render note events through the Surge XT synthesizer (surgepy, the Python build of Surge XT) with no audio devi | 51 | tools/music/claude_pro.py; docs/skills | none found | 1 | surgepy direct; FluidSynth / sox / SuperCollider for rendering |
| `tools/node_field.py` | Build the in-game Node Field page (node-field.html) from the Node Previewer | 56 | .claude/settings.json, tools/check.py; docs/skills | none found | 3 | esbuild/vite build step; make; none known for this single-file inline build |
| `tools/screens.py` | Screenshot the menus: the game's start screen and every sub-screen, or a preview page's screens | 82 | .claude/settings.json; docs/skills | none found | 2 | Playwright Test (@playwright/test) with webServer screenshots; Puppeteer; shot-scraper |
| `tools/simprof.py` | Fixed-step mixed simulation diagnostic, independent of live RAF/GPU scheduling | 58 | docs/skills | none found | 2 | node --cpu-prof; clinic.js; 0x |
| `tools/sky_check.py` | Node Previewer backdrop check: red hue, arena contrast, cost per frame, seed determinism, screenshots | 272 | docs/skills | none found | 4 | Playwright Test (@playwright/test) with webServer + axe-core (contrast part); none known for the hue/bake checks |
| `tools/smoke.py` | Smoke test: the game loads, a run starts, every weapon fires and deals damage | 323 | .check.state.json, .claude/hooks/session-start.sh, .claude/settings.json, tests/response/boss_diagnostics.py (+5); docs/skills | tests/response/boss_diagnostics.py, tests/response/integration.py (+1) | 21 | Playwright Test (@playwright/test) with webServer; Cypress |
| `tools/staticchain.py` | Turn an install-time wrapper chain into plain named functions in one file | 152 | docs/skills | none found | 6 | jscodeshift; ts-morph |
| `tools/sync_cards.py` | Sync card data from the Card Editor into the game | 249 | editor-copy.js, tests/card-faces/check.py; docs/skills | tests/card-faces/check.py | 6 | none known (project card-editor sync) |
| `tools/sync_tuner.py` | Write approved Omniversal Tuner values back into the game's source files | 400 | previews/omniversal-tuner.html, previews/tuner/d2-omni-items.js, tools/game_docs.py; docs/skills | none found | 1 | none known (writes edited values back into minified source) |
| `tools/ui_audit.py` | Measure phone/desktop readability and touch-target rules on a static HTML page (previews, tools, studio pages) | 97 | previews/claude-audio/desk.template.html, previews/claude-audio/index.html; docs/skills | none found | 2 | axe-core / @axe-core/playwright; Lighthouse; pa11y |
| `tools/worker_guard.py` | PreToolUse hook for the nmb-worker and nmb-reviewer subagents: blocks git commands they must never run | 274 | docs/skills | own --test | 5 | kit scripts/worker_guard.py (same name, kit-locked, different file: 275 vs kit copy); Claude Code permission deny rules |

Totals: 69 files, 12260 lines, 269 commit-touches in 30 days (a commit that touches two files counts twice).

Subtotals (lines): `tools/` non-music 39 files, 5,377 lines; `tools/music/` 20 files, 5,844 lines (the seven `claude_*` synthesis files are 5,036 of them); `bench/` 4 files, 310 lines; `previews/` 4 files, 684 lines; `scripts/check.local.sh` 13; `.claude/hooks/session-start.sh` 32. `tools/` as a whole (py, sh, c): 59 files, 11,221 lines.

Test harness (not rows; one line each, 71 files, 3,868 lines, python and node scripts run by hand or by `tools/check.py`/skills): tests/card-faces 1 file 188 lines; tests/cleanup 6 / 323; tests/conformance 6 / 491; tests/hardening 22 / 847; tests/music 2 / 504 (`runtime.test.mjs` is a node test; `build_fixture.py` builds audio fixtures); tests/perf 8 / 255; tests/rebuild 7 / 376; tests/response 5 / 241; tests/scenarios 9 / 301; tests/startup 1 / 32. Candidate for the runner part: Playwright Test, pytest, `node --test`; none known for the game-specific oracles.

Observations (facts): `tools/check.py` is the repo's own check selector behind `check.local.sh`. `tools/worker_guard.py` (275 lines) has the same name as the kit-locked `scripts/worker_guard.py` but differs from it; `tools/git-hooks/pre-push` is described in its header as hand-off only, the kit hook is the active one. Settings call `tools/branches.py --stop-hook` next to the kit `scripts/stop_check.py`. Most-touched tools in 30 days: `tools/smoke.py` 21, `tools/music/build_desk.py` 18, `tools/branches.py` 9, `tools/check.py` 9, `tools/bench.py` 8.

## transcription_assistant (HEAD abbc8cc)

- HEAD: `abbc8cc` (2026-11-21); commits since 2026-10-24: 53.
- Kit version recorded: `.check.lock` "version": 10.0.0, kit commit f397b52d, overrides: none. No KIT_VERSION, CHANGELOG or kit.config.json in the repo. The kit at /home/user/archimedes_lever is 11.0.1.
- Kit-locked entries in `.check.lock`: 55. One entry is not a file ("AGENTS.md (kit sections)"), so 54 named files exist and 0 named files are missing from disk.
- Compared with the kit by sha256 of the same path (54 existing files): same 10, differ 43, absent in kit 1 (`scripts/fulcrum_tokens.py`, not in kit 11.0.1). Files that differ from the repo's own lock: 0 (the repo matches its recorded 10.0.0 lock; the 43 are kit changes since).
- `scripts/check.local.sh`: yes (33 lines; runs contrast, regress, scroll, ui_audit; fast lane skips when no checked file changed). Workflows: `check.yml` (only one). `AGENTS.md`: 79 lines.

Product code: one static page `index.html` plus `design/cta.css`, `design/style-sample.html` and self-hosted fonts (about 1,400 lines with design/); no build step, no runtime dependencies. `package.json` has one devDependency (Playwright 1.63.0) and one script (`check`). Not rows below.

Project tools:

| Path | Job | Lines | Callers | Test | Commits 30d | Candidates |
|---|---|---:|---|---|---:|---|
| `.claude/hooks/session-start.sh` | Git hooks for every agent: the kit's scripts/git-hooks/pre-push (blocks force-pushes and runs the fast lane an | 12 | .claude/settings.json, tools/git-hooks/pre-push | none found | 4 | kit hooks setup (scripts/session_checkin.sh); husky/lefthook |
| `scripts/check.local.sh` | Transcription Assistant project checks, run last by the kit's scripts/check.sh. Pass = exit 0 and "LOCAL PASS" | 32 | scripts/check.sh (kit, by name); docs/skills | none found | 1 | kit-defined hook (check.sh runs it last); not a free-standing tool |
| `tools/bloat_check.py` | Cheap bloat and drift metrics for a project repo, and the bloat-audit due date. Report only, unless --record | 272 | tools/check.sh | own --test | 4 | kit scripts/bloat_check.py (kit-locked, same name, repo has both) |
| `tools/check.sh` | Run every check. Usage: bash tools/check.sh   (needs node, python3, Playwright + Chromium) | 17 | package.json; docs/skills | none found | 7 | kit scripts/check.sh + scripts/check.local.sh (already run in the repo); `npm run check` wrapper |
| `tools/contrast.py` | Contrast check of the color tokens in index.html | 42 | scripts/check.local.sh, tools/check.sh, tools/ui_audit.js; docs/skills | none found | 1 | axe-core (color-contrast rule); pa11y; Lighthouse accessibility audit |
| `tools/git-hooks/pre-push` | Git pre-push hook for Claude, any git client, and people | 97 | .check, tools/pii_guard.py | none found | 5 | kit scripts/git-hooks/pre-push (kit-locked; active hooks path); husky; lefthook |
| `tools/lib.js` | Shared helpers for the check tools. Not run directly | 15 | scripts/check.local.sh, tools/regress.js, tools/scroll_check.js, tools/ui_audit.js | none found | 1 | Playwright `webServer` config; `python3 -m http.server`; `npx serve` |
| `tools/log_check.py` | Check a project log (docs/LOG.md) against the AGENTS.md "Project log" rules | 247 | tools/check.sh, tools/timeline.py | own --test | 2 | kit scripts/log_check.py (kit-locked, same name, repo has both) |
| `tools/make_fixtures.py` | Write the synthetic test files to tests/fixtures/ | 36 | .check; docs/skills | none found | 1 | none known (builds invented xlsx/csv; Faker + openpyxl are libraries, not a replacement) |
| `tools/pii_guard.py` | Block personal data and secrets before they reach the remote: emails, phone numbers, ID-number shapes, API tok | 779 | tools/check.sh, tools/git-hooks/pre-push | own --test | 1 | kit scripts/check_content*.py (`scripts/check.sh --content`); gitleaks / detect-secrets (secrets part only) |
| `tools/regress.js` | Behavior regression for index.html. Usage: node tools/regress.js | 55 | scripts/check.local.sh, tools/check.sh; docs/skills | none found | 2 | @playwright/test (test runner, built-in reporters, retries) with webServer |
| `tools/scroll_check.js` | Scroll-position check on a phone (iPhone 13 emulation). Usage: node tools/scroll_check.js | 49 | scripts/check.local.sh, tools/check.sh | none found | 2 | @playwright/test (page.evaluate assertions on scrollY) |
| `tools/stop_check.py` | Claude Code Stop hook: block the end of a turn while work is not on GitHub | 203 | .claude/settings.json | own --test | 2 | kit scripts/stop_check.py (kit-locked; settings.json runs both) |
| `tools/timeline.py` | Render one or more project logs (docs/LOG.md) as one self-contained HTML timeline page | 309 | tools/check.sh | own --test | 2 | kit scripts/timeline.py (kit-locked, same name, repo has both) |
| `tools/ui_audit.js` | Look and accessibility audit for index.html. Usage: node tools/ui_audit.js [--shots DIR] | 74 | scripts/check.local.sh, tools/check.sh; docs/skills | none found | 3 | @axe-core/playwright for a11y part; @playwright/test; Lighthouse; pa11y |

Totals: 15 files, 2239 lines, 38 commit-touches in 30 days (a commit that touches two files counts twice).

Facts: `tools/bloat_check.py`, `log_check.py`, `stop_check.py`, `timeline.py`, `pii_guard.py`, `check.sh` and `git-hooks/pre-push` are the project's pre-kit copies; `docs/tools.md` calls them "old" and "kept until the owner retires it". Each differs from the kit file of the same name in `scripts/` (bloat_check 272 vs 467 lines, log_check 247 vs 320, stop_check 203 vs 317, timeline 309 vs 372). `tools/check.sh` still runs them, and `package.json` "check" runs `tools/check.sh`; `.claude/settings.json` runs both `scripts/stop_check.py` and `tools/stop_check.py` as Stop hooks. `tools/pii_guard.py` is off ("no `.pii-guard` file": its scan is SKIP in `tools/check.sh`). Active tools (run by `scripts/check.local.sh`): contrast.py, regress.js, scroll_check.js, ui_audit.js, lib.js (helper). Test column "own --test" for the old tools = their `--test` self-test, run only by `tools/check.sh`.

## SPAR (HEAD 01ede27)

- HEAD: `01ede27` (2026-11-21); commits since 2026-10-24: 43.
- Kit version recorded: `.check.lock` "version": 10.0.0, kit commit f397b52d, overrides: none. No KIT_VERSION, CHANGELOG or kit.config.json in the repo. The kit at /home/user/archimedes_lever is 11.0.1.
- Kit-locked entries in `.check.lock`: 55. One entry is not a file ("AGENTS.md (kit sections)"), so 54 named files exist and 0 named files are missing from disk.
- Compared with the kit by sha256 of the same path (54 existing files): same 10, differ 43, absent in kit 1 (`scripts/fulcrum_tokens.py`, not in kit 11.0.1). Files that differ from the repo's own lock: 0 (the repo matches its recorded 10.0.0 lock; the 43 are kit changes since).
- `scripts/check.local.sh`: no. Workflows: `check.yml` (only one). `AGENTS.md`: 74 lines.

Product code: none in the repo (only docs and the kit files); `scripts/` holds only kit-locked files.

Project tools: none. Tracked files that are not kit-locked and not under docs/: `.check`, `.check.lock`, `.claude/settings.json`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md`. Totals: 0 files, 0 lines.

## 36-3003.Z (HEAD 253b30b)

- HEAD: `253b30b` (2026-11-21); commits since 2026-10-24: 38.
- Kit version recorded: `.check.lock` "version": 10.0.0, kit commit f397b52d, overrides: none. No KIT_VERSION, CHANGELOG or kit.config.json in the repo. The kit at /home/user/archimedes_lever is 11.0.1.
- Kit-locked entries in `.check.lock`: 55. One entry is not a file ("AGENTS.md (kit sections)"), so 54 named files exist and 0 named files are missing from disk.
- Compared with the kit by sha256 of the same path (54 existing files): same 10, differ 43, absent in kit 1 (`scripts/fulcrum_tokens.py`, not in kit 11.0.1). Files that differ from the repo's own lock: 0 (the repo matches its recorded 10.0.0 lock; the 43 are kit changes since).
- `scripts/check.local.sh`: no. Workflows: `check.yml` (only one). `AGENTS.md`: 73 lines.

Product code: none in the repo (same file list as SPAR outside docs/).

Project tools: none (same file list as SPAR). Totals: 0 files, 0 lines.

## 65-601.Z (HEAD a8e60fd)

- HEAD: `a8e60fd` (2026-11-21); commits since 2026-10-24: 33.
- Kit version recorded: `.check.lock` "version": 10.0.0, kit commit f397b52d, overrides: none. No KIT_VERSION, CHANGELOG or kit.config.json in the repo. The kit at /home/user/archimedes_lever is 11.0.1.
- Kit-locked entries in `.check.lock`: 55. One entry is not a file ("AGENTS.md (kit sections)"), so 54 named files exist and 0 named files are missing from disk.
- Compared with the kit by sha256 of the same path (54 existing files): same 10, differ 43, absent in kit 1 (`scripts/fulcrum_tokens.py`, not in kit 11.0.1). Files that differ from the repo's own lock: 0 (the repo matches its recorded 10.0.0 lock; the 43 are kit changes since).
- `scripts/check.local.sh`: no. Workflows: `check.yml` (only one). `AGENTS.md`: 73 lines.

Product code: none in the repo (same file list as SPAR outside docs/).

Project tools: none (same file list as SPAR). Totals: 0 files, 0 lines.

## Limits of this inventory

- The kit-state counts were computed per repo; the five repos give the same numbers (same lock commit f397b52d, 10.0.0).
- `docs/` files were excluded from callers and from tools (a script under docs/ would be missed; none seen in the file lists of the three rhope-ops repos).
- `.claude/skills/*/PROJECT.md` and `.claude/skills` text was treated as docs, not read for per-tool use; a tool named only there shows "docs/skills".
- Candidate lists are from general knowledge, not tested against these repos; no fit judgment is made.
- Lines of the `tests/` harness in no-more-beyond are summarized per folder, not as rows.
