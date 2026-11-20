---
name: spec
description: Writes a specification for a piece of work before it is built. Reads the context, interviews the user with multiple-choice questions until no decision that changes the result is open, then writes one spec file with requirements, out-of-scope items and pass/fail acceptance checks, and stops for approval. Run this skill only when the user asks for it ("spec", "spec this", "write a spec", "build a spec", "help me spec", "/spec"). Do not run it on your own judgment. If a task looks large, or needs more than about 5 constraints to state, ask the user whether to spec it first.
---

# Spec

A spec is the written definition of done for one piece of work. The build starts from it and the review checks against it. This skill makes the spec; it does not build.

The subject of the spec is the text the user gives with the request (after "/spec" or the trigger phrase). If there is none, ask for it first.

A repo's own rules (AGENTS.md, CLAUDE.md, its decisions file) win over this skill where they differ.

## 1. Check the size

- If the work is small (a bug fix, a one-file change, fewer than about 5 constraints), say so and give the short form in the reply: Goal, Done (pass/fail checks), Out of scope. Write no file unless the user wants one.
- All other work: do steps 2 to 6.

## 2. Read before you ask

- Read the request, the repo's instruction files, its decisions file, its specs and the code or documents the work touches.
- Never ask what you can verify. Keep each fact with its source (file and line, command, URL).
- Search for a spec on the same topic. If one exists, update it. Do not write a second one.
- Make no change to code or data in steps 2 to 5.

## 3. Interview

Ask only what the user alone knows and what changes the result.

- Use the question dialog where it exists (the `AskUserQuestion` tool, or the host's tool of that type): at most 4 questions for each round, 2 to 4 options for each question, the recommended option first with its reason. Each question must be clear without the others. With no dialog tool, number the questions in the reply.
- Ask first the questions whose answers change the later questions.
- Do not ask obvious questions. Ask about the parts that are not decided, and name a risk or a simpler alternative when you see one.
- Areas to cover; skip an area that does not apply:
  - Goal: the problem, who has it, what is better when the work is done.
  - Scope: what is in, what is out.
  - Behavior: inputs, outputs, states, errors, edge cases, limits.
  - Interface: screens, text, flows, accessibility (only for work with a user interface).
  - Approach: the technical choices the user wants to make (stack, architecture, data model, interfaces to other systems) and the concerns the user has about them.
  - Data: sources, writes, personal data, retention.
  - Constraints: platform, compatibility, performance, security, cost, dates.
  - Tradeoffs: where two goals conflict, which one wins.
  - Proof: the test, command, source data or standard that shows each requirement is met.
  - Delivery: the target (live, preview, repo), rollout, undo, irreversible steps.
- Continue the rounds until you can write each acceptance check as pass or fail and no open decision changes the build.
- If the user stops the interview, write the remaining items under "Open questions" and "Assumptions". Do not invent the answers.

## 4. Write the spec

Location:

- In a repo: where the repo keeps its specs. If it has no such place, `docs/specs/<short-name>.md`.
- Outside a repo: use the `where-to-save` skill if the user has it; otherwise an editable document.

Sections, in this order. Omit a section that has no content.

```markdown
# Spec: <name>

Status: Draft | Approved <date> · Owner: <role> · Updated: <date>

## Goal
<1 to 3 sentences: the problem, for whom, the result>

## Done
<the outside proof that the work is complete, in one or two lines>

## Requirements
- R1. <one behavior or constraint, testable>
- R2. ...

## Out of scope
- <what this work does not do>

## Edge cases and errors
- E1. <condition> -> <required behavior>

## Constraints
- <platform, compatibility, performance, security, data, cost, dates>

## Decisions
| ID | Decision | By | Date | Alternatives rejected, and why |

## Acceptance checks
| ID | Covers | Check (command or observation) | Pass when |
| A1 | R1, E1 | ... | ... |

## Assumptions
- <assumption> · source · confidence (high / medium / low)

## Open questions
- <question> · who answers · what it blocks

## Risks
- <risk> · REC: <what to do>
```

Rules for the text:

- Write what the work must do, not how to build it. Give an implementation detail only when the user decided it or a constraint needs it.
- Each requirement is one testable statement. Each requirement and each edge case has at least one acceptance check.
- An acceptance check gives pass or fail from outside the author: a test, a command, source data, a measurement, a standard. If no such check exists, propose the smallest one and mark it "REC".
- Record a decision only when the user made it. Mark your own proposals "REC"; they are not decisions.
- The spec must be sufficient alone: a new session that has only this file and the repo can build the work. Give full paths and full URLs.
- No personal data and no secrets. Use invented data in examples.
- Be as short as the content permits. One fact in one place; link to existing documents, do not copy them.

## 5. Check, then stop

- Compare the spec with the user's answers, one by one. Each answer is in the spec. The spec contains nothing that the user did not say or approve, except items marked "Assumption" or "REC".
- Make sure each R and E has an A, and each A names its R or E.
- Give the user: the link to the spec, a summary of 5 lines or fewer, and the open questions.
- Ask for approval. On approval, set "Status: Approved" with the date.
- Do not start the build in this turn unless the user tells you to.

## 6. After approval

Offer these two texts with the real path filled in; do not run them unasked.

Build, in a new session, so that the build starts with a clean context:

```text
Read <path to the spec>. Build what it specifies and nothing more. Then run each acceptance check and report its command and output. If the spec is wrong or incomplete, stop and tell me; do not guess.
```

Review, after the build:

```text
Use a subagent to review the diff against <path to the spec>. Check that each requirement is implemented and each listed edge case has a test. Report gaps that affect correctness. Skip style.
```

If the required behavior changes during the build, change the spec first, get approval, then change the code.
