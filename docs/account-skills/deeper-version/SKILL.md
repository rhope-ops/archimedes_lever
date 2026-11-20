---
name: deeper-version
description: Rewrites a task prompt into a deeper version of the same task (what a top professional would do, the rawest source material, the specific methods and tools, and the outside proof that the result is right). Run this skill only when the user asks for it by name ("deeper version", "run deeper version", "/deeper-version") or answers yes when asked if they want it. Do not run it on your own judgment, even for a big feature or a new project; for those, ask the user first.
---

# Deeper version

Turn the user's task into a deeper version of the same task, not a bigger one.

## Why this is opt-in

This prompt raises the quality bar of a task. On small or routine tasks it causes
over-engineering: more sources, more tools and more checks than the result is worth.
The user wants it for big features and new projects, and wants to make that choice
each time. Thus, if the user did not ask for it in this turn, do not apply it. You
may ask one time if they want it.

## The prompt

Apply this prompt to the task the user gave (the task in their message, or the most
recent task in the conversation if they only say "run deeper version"):

> I want a deeper version of this task, not a bigger one. Before rewriting it:
> (1) say what a top professional in this field would do here that I'm not asking for;
> (2) name the rawest material they would start from instead of what has already been digested for me;
> (3) name the specific methods and tools they would use;
> (4) say what, other than you or me, would show the result is right.
> Then rewrite my prompt to ask for exactly that.

## How to do it

1. Identify the field of the task and the level of person who does this work best.
   Be specific ("a staff data engineer who owns billing pipelines"), because a
   generic "expert" gives generic answers.
2. Answer the four points, in order, in a few lines each. Be concrete:
   - (1) Name the actions, not the attitudes. "Checks the migration against a copy
     of production data" is useful. "Is careful" is not.
   - (2) Name the primary sources: the source code, the raw data, the logs, the
     specification, the original paper, the users. Not a summary, a blog post about
     it, or the user's own description of it.
   - (3) Name methods and tools that exist and that are available here. If a tool
     is not available in this session, say so and name the nearest one that is.
   - (4) Name proof that does not depend on your judgment or the user's: tests, CI,
     the source data, a standard, a benchmark, the output of a tool, a third party.
3. Write the rewritten prompt in one code block, complete, with no placeholders, so
   the user can run it or edit it.
4. Stop and show the result. Do not start the rewritten task until the user approves
   it. The rewrite changes what the user asked for, so the decision is theirs.

## Deeper, not bigger

Keep the goal and the deliverable of the original task. Add depth in how the work
starts (sources), how it is done (methods) and how it is proved (evidence). Do not
add features, deliverables or scope. If a point from step 2 would add scope, list it
below the rewritten prompt as an option, with its cost, and leave it out of the
rewrite.

If the task is too small for this to help, say so in one line and give the reason.
That answer is more useful than a rewrite that makes a small task heavy.

## Output format

```
Field and professional: <one line>

1. What a top professional would do: <lines>
2. Rawest material: <lines>
3. Methods and tools: <lines>
4. Outside proof: <lines>

Rewritten prompt:
<one code block>

Left out (adds scope): <options with cost, or omit this line>
```

## Source

The prompt is from "How to be more ambitious: A tutorial for humans with models" by
Felix Rieseberg:
https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/
