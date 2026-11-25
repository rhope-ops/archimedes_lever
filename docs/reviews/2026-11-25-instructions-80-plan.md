# Plan: instructions at "80%" (approved 2026-11-25)

Approved by the Maintainer on 2026-11-25 (question dialog "Approve text and plan", after the request: "i want the 'go on' to stop appearing in every instructions i get. this is across all repos ... i want them to be 80% of the current setup"). Owner: the README session of RADE and 90-161.Z (2026-11-25).

## Approved rule text

In the hard rule "Instructions people follow", this text replaces "Each step holds one action, or the numbered actions that are all on one screen; it names the exact thing on the screen and the exact text to type, says what the person sees next, and says whether to wait, go on or note a value (show the value again where it is needed; never make the person remember it)."

> Write for a competent adult: each step holds one action, or up to three short actions on one screen; it names the exact thing on the screen and the exact text to type; it says what the person sees only when the screen changes in a way they must check, says to wait only when acting early breaks something, and shows again any value the person must use (never make the person remember it). No filler cues ("Go on.") and no reminders the person does not need.

The rest of the rule stays.

## Steps

1. Phase 1, kit (this repo): the rule text above; the `instructions` skill step form to match; `scripts/check_instructions*.py`: no cue needed, "Go on." fails, "You see" not required, up to 3 actions on one screen; tests; session load held under the cap in every repo (the rule text is longer: save the tokens in kit text); fresh review; release (KIT_VERSION, CHANGELOG, tag by the Maintainer).
2. Phase 2: kit sync to RADE and 90-161.Z. In 90-161.Z: README without "How a paste task (round) works"; open tasks with no possessive pronouns ("the computer", not "my computer") unless a pronoun is needed; no "send a line to Claude" or "never send real content" lines; every go.md step in the new style.
3. Phase 3: every other repo on the kit: list them first, then one kit-sync pull request each (one cloud session per repo). Their own texts get the new style in later sessions.

Estimate: 4 to 5 hours, about 15 agents or sessions (Opus for this session and the reviewers, Sonnet for the per-repo syncs).

## State

- [ ] Phase 1  - [ ] Phase 2  - [ ] Phase 3
