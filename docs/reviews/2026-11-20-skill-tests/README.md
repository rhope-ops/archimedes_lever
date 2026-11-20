# Skill tests: pages-and-tools, deliver, handoff (new against old)

Date: 2026-11-20 (America/Chicago). Plan: [2026-11-20-skill-use-plan.md](../2026-11-20-skill-use-plan.md), step 3. Method: the skill-creator test loop. 9 cases, each run one time with the new skill text and one time with the old text (18 runs, `worker` agents, Sonnet). The case folders here hold the prompt, the expected outcome and one file per assertion, in the layout `claude plugin eval` reads.

Grading: deliver and handoff by a script from the repo state and the final message (git state, file content, regular expressions); pages-and-tools from a browser probe (Playwright), the kit's `verify/measure.mjs` and the final message. One assertion (the measure script passes) was added to the 3 page cases after the runs and applied to both versions.

## Result

| Skill | New: assertions passed | Old: assertions passed | Time per run (new / old) | Tokens per run (new / old) |
|---|---|---|---|---|
| pages-and-tools | 26 of 26 | 20 of 26 | 55 s / 41 s | 45,801 / 43,144 |
| deliver | 18 of 18 | 18 of 18 | 32 s / 32 s | 47,713 / 47,508 |
| handoff | 17 of 18 | 18 of 18 | 40 s / 36 s | 49,237 / 48,462 |

## Per case

| Skill | Case | New | Old | Failed assertions |
|---|---|---|---|---|
| pages-and-tools | add-clear-button | 8 of 8 | 7 of 8 | old: The kit's page measure script (verify/measure.mjs: text contrast, targ (measure.mjs: UI MEASURE FAIL, exit 1: contrast 2:1 (need 4.5:1) on button#clear 'Clear history') |
| pages-and-tools | header-look-options | 8 of 8 | 5 of 8 | old: The output page shows at least 2 and at most 4 different header option (probe: one 'Next round' button, no choice control; the run's own summary: 'Only one header look shown'); old: Each option has a visible label or name (for example A, B, C) (one option only, no labels); old: The final message asks the user to pick a direction and does not prese (report line 1: 'Here is the new header look for Demo Quiz': one design presented as the result) |
| pages-and-tools | tester-round-tracker | 10 of 10 | 8 of 10 | old: The page handles dark mode or was checked in it, and has no horizontal (probe: horizontal scroll of 11 px at 375 px width; CSS has no prefers-color-scheme; report does not name dark ); old: The kit's page measure script (verify/measure.mjs: text contrast, targ (measure.mjs: UI MEASURE FAIL, exit 1) |
| deliver | end-of-turn-lane-c | 6 of 6 | 6 of 6 | - |
| deliver | live-copy-stale | 5 of 5 | 5 of 5 | - |
| deliver | uncommitted-code-fix | 7 of 7 | 7 of 7 | - |
| handoff | fleet-format | 6 of 6 | 6 of 6 | - |
| handoff | start-from-stale-handoff | 4 of 5 | 5 of 5 | new: The session did not present step 2 as built on a main that has step 1 (The run built step 2 and first committed it to local main by mistake (65a3f09, not pushed), then moved the wor) |
| handoff | write-handoff-open-work | 7 of 7 | 7 of 7 | - |

## Reading

**pages-and-tools**
- New version 26 of 26 assertions, old version 20 of 26; one run per configuration, so no variance estimate.
- The difference comes from 3 things the new text adds: show 2 to 4 options and let the user pick (old run built one header and presented it as the result), look at phone width and dark mode (old tracker had 11 px of horizontal scroll at 375 px and no dark mode), and measure instead of judging by eye (old clear button had a 2:1 text contrast).
- 20 of the 26 assertions pass in both versions: the rule list itself (no setup, states, labels, undo) already worked in the old version.
- The assertion on the kit's measure script was added after the runs, from an outside tool, and applied to both versions in the same way.
- Cost: the new version took about 14 s and 2,700 tokens more per run (more checks run).

**deliver**
- No measured difference: 18 of 18 assertions pass in both versions. These 3 cases do not discriminate.
- Both versions already compared the live copy with main in the live-copy case; the old run said 'identical', the new run gave a SHA-256 of 3 copies. The new step 7 made the proof stronger, not different in pass or fail.
- The stop-check block (16 in the session sample) cannot be reproduced in this sandbox: it needs the real stop hook. The new step 0 is not proven by these tests.
- Both versions left an untracked scripts/__pycache__/ from the check; a .gitignore line in the fixture, not a skill problem.
- Time and tokens are equal within 1%.

**handoff**
- No measured difference that is caused by the skill: new 17 of 18, old 18 of 18.
- The one fail (new version, stale-handoff case): the run committed step 2 to local main by mistake, then moved it to a branch and reported it. Nothing in the changed text relates to this; with one run per configuration it reads as run-to-run variance. Both versions found the stale claim and called it drift.
- The fleet-format case passes in both versions: moving the 600-character line into its own section changed readability, not the result.
- The new resume-prompt bullets did not change the result: both versions wrote a prompt of at most 100 words with a 'DEMO · <task>' first line.

## Limits

- One run per configuration: no variance estimate. A difference of one assertion can be run-to-run noise.
- The sandbox had no pull request tool, no stop hook and no session tools, so the pull request, stop-check and session-name steps were not tested.
- The description (trigger) texts were not tested here. The kit descriptions were shortened after these runs to hold the 5,000-token session load; the bodies tested are the bodies merged.
- 3 of 18 runs could not write their report file (the Write tool refused it in a subagent); their final message was saved from the hand-back text.

## Fixture builder

The git fixtures (a small demo repo with a bare `origin`, a `live` and a `preview` folder) were built by this script, one fixture per run:

```bash
#!/usr/bin/env bash
# Build one test fixture. Usage: mkfix.sh <case> <dest-dir> <skill-name> <skill-dir-to-install>
set -eu
CASE=$1; DEST=$2; SKILL=$3; SKILLDIR=$4
K=/home/user/archimedes_lever
rm -rf "$DEST"; mkdir -p "$DEST"; cd "$DEST"
g() { git -c user.name="demo-bot" -c user.email="demo-bot@users.noreply.github.com" "$@"; }
base_repo() {
  git init -q --bare origin.git
  git init -q -b main repo; cd repo
  git config user.name "demo-bot"; git config user.email "demo-bot@users.noreply.github.com"
  git remote add origin ../origin.git
  mkdir -p .claude/skills scripts docs/reviews site
  for s in deliver handoff verify rule-change project-log personal-data; do cp -r $K/.claude/skills/$s .claude/skills/; done
  rm -rf .claude/skills/$SKILL; cp -r "$SKILLDIR" .claude/skills/$SKILL; rm -rf .claude/skills/$SKILL/evals
  sed -e 's/{{PROJECT_NAME}}/Demo Quiz/' -e 's#{{REPO}}#demo-org/demo-quiz#' -e 's/{{PURPOSE}}/A small quiz page for new staff (test fixture)./' \
      -e 's/{{OWNER}}/the owner/' -e 's#{{TIMEZONE}}#America/Chicago#' -e 's/{{TIER}}/full/' -e 's/{{SHORT_NAME}}/DEMO/' $K/AGENTS.md > AGENTS.md
  python3 - <<'P'
t=open('AGENTS.md').read()
i=t.index('## Project rules')
t=t[:i]+'## Project rules\n\n- Content (the owner, 2026-11-10): quiz questions are original; never copy questions from another source.\n'
open('AGENTS.md','w').write(t)
P
  echo '@AGENTS.md' > CLAUDE.md
  printf '#!/usr/bin/env bash\n# Test fixture check: full lane and fast lane are the same here.\npython3 -m py_compile scripts/*.py && echo "CHECK PASS: 3 passed, 0 skipped, of 3"\n' > scripts/check.sh; chmod +x scripts/check.sh
  printf 'def score(right, total):\n    """Return the score in percent."""\n    return round(100 * right / total)\n' > scripts/tool.py
  printf '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Demo Quiz</title></head>\n<body><h1>Demo Quiz</h1><p id="version">Version 2.0</p></body></html>\n' > site/index.html
  printf '#!/usr/bin/env bash\n# Publish: copy the built site to the live folder (the test stand-in for the live site).\nset -eu\ncp site/index.html ../live/index.html\necho "published site/index.html to ../live/index.html"\n' > scripts/publish.sh; chmod +x scripts/publish.sh
  printf '# Decisions\n\n| ID | Date | Decision | Scope | Replaces |\n|---|---|---|---|---|\n| D1 | 2026-11-10 | Quiz questions are original. | project | nothing |\n| D2 | 2026-11-12 | One HTML page, no build step. | project | nothing |\n| D3 | 2026-11-14 | Rounds are numbered R1, R2, ... | project | nothing |\n' > docs/DECISIONS.md
  printf '# Project log\n\n| when | type | topic | evidence |\n|---|---|---|---|\n| 2026-11-10 | milestone | repo created | first commit |\n' > docs/LOG.md
  cat > docs/NEXT_PROMPT.md <<'N'
# Next prompt: Demo Quiz

Updated: 2026-11-18 16:10 by the session "DEMO · Build round R30 · 2026-11-18". Keep this file at 40 lines or fewer. The current request overrides it.

## State

- main: round R30 merged (version 2.0 of site/index.html is live in ../live).
- No open branches or pull requests.

## Approved plan

- Round R31 (the owner, 2026-11-18): step 1 score rounding fix in scripts/tool.py; step 2 show the score on the page; step 3 release 2.1.
- [ ] 1. [ ] 2. [ ] 3.

## Open (in order)

1. R31 step 1: done when scripts/check.sh passes and the fix is merged.

## Needs the owner

- None.

## Do not

- Do not hand-edit ../live: publish with scripts/publish.sh.
N
  mkdir -p ../live ../preview; cp site/index.html ../live/index.html
  git add -A; git commit -q -m "Demo Quiz: base"; git push -q -u origin main
}
base_repo
case "$CASE" in
 uncommitted-code-fix)
  printf 'def score(right, total):\n    """Return the score in percent (0 when there are no questions)."""\n    if total == 0:\n        return 0\n    return round(100 * right / total)\n' > scripts/tool.py ;;
 live-copy-stale)
  sed -i 's/Version 2.0/Version 2.1/' site/index.html
  git checkout -q -b claude/release-2-1; git commit -qam "Release 2.1: version text"; git push -q -u origin claude/release-2-1
  git checkout -q main; git merge -q --no-ff claude/release-2-1 -m "Merge pull request #14 from demo-org/claude/release-2-1"; git push -q origin main
  git push -q origin --delete claude/release-2-1; git branch -q -d claude/release-2-1
  cp site/index.html ../preview/index.html
  sed -i 's/- main: round R30 merged (version 2.0 of site\/index.html is live in ..\/live)./- main: release 2.1 merged (pull request 14). The preview in ..\/preview shows 2.1./' docs/NEXT_PROMPT.md
  git commit -qam "Handoff: 2.1 merged"; git push -q origin main ;;
 end-of-turn-lane-c)
  git checkout -q -b claude/r31-notes
  printf '# R31 notes\n\nTesters asked for the score on the page.\n' > docs/reviews/2026-11-20-r31-notes.md; git add -A; git commit -q -m "R31 notes"
  printf '\n- 2026-11-20: three testers, all on phones.\n' >> docs/reviews/2026-11-20-r31-notes.md; git commit -qam "R31 notes: testers"
  printf -- '- Rounds (the owner, 2026-11-20): a round is closed only after every tester result is recorded in docs/reviews/.\n' >> AGENTS.md
  printf '# R31 tester list\n\nTester A, Tester B, Tester C (invented).\n' > docs/reviews/2026-11-20-r31-testers.md ;;
 write-handoff-open-work)
  git checkout -q -b claude/r31
  printf 'def score(right, total):\n    """Return the score in percent (0 when there are no questions)."""\n    if total == 0:\n        return 0\n    return round(100 * right / total)\n' > scripts/tool.py
  git commit -qam "R31 step 1: score is 0 when there are no questions"; git push -q -u origin claude/r31 ;;
 start-from-stale-handoff)
  git checkout -q -b claude/r31
  printf 'def score(right, total):\n    """Return the score in percent (0 when there are no questions)."""\n    if total == 0:\n        return 0\n    return round(100 * right / total)\n' > scripts/tool.py
  git commit -qam "R31 step 1: score is 0 when there are no questions"; git push -q -u origin claude/r31
  git checkout -q main
  python3 - <<'P'
p='docs/NEXT_PROMPT.md'; t=open(p).read()
t=t.replace('Updated: 2026-11-18 16:10 by the session "DEMO · Build round R30 · 2026-11-18".','Updated: 2026-11-19 17:02 by the session "DEMO · Build round R31 · 2026-11-19".')
t=t.replace('- main: round R30 merged (version 2.0 of site/index.html is live in ../live).\n- No open branches or pull requests.','- main: R31 step 1 merged (commit 4f2a9c1, pull request 15). Version 2.0 is live in ../live.\n- No open branches or pull requests.')
t=t.replace('- [ ] 1. [ ] 2. [ ] 3.','- [x] 1. [ ] 2. [ ] 3.')
t=t.replace('1. R31 step 1: done when scripts/check.sh passes and the fix is merged.','1. R31 step 2: show the score on the page (site/index.html), done when scripts/check.sh passes and it is merged.')
open(p,'w').write(t)
P
  git commit -qam "Handoff: R31 step 1 merged"; git push -q origin main ;;
 fleet-format)
  printf 'profile: minimum\nfleet: on\n' > .check
  cp $K/scripts/fleet_harvest.py scripts/ 2>/dev/null || true
  git add -A; git commit -q -m "Fleet format on"; git push -q origin main
  git checkout -q -b claude/r31
  printf 'def score(right, total):\n    """Return the score in percent (0 when there are no questions)."""\n    if total == 0:\n        return 0\n    return round(100 * right / total)\n' > scripts/tool.py
  git commit -qam "R31 step 1: score is 0 when there are no questions"; git push -q -u origin claude/r31 ;;
 *) echo "unknown case $CASE"; exit 2 ;;
esac
git rev-parse origin/main > ../BASE_MAIN_SHA
echo "fixture $CASE ready in $DEST/repo"
```
