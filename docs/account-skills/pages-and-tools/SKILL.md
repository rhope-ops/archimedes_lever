---
name: pages-and-tools
description: The user's quality rules for any page or tool that Claude builds or changes for them. Use this skill each time you build, change, publish or republish something a person will open and use - an artifact, HTML page, web app, dashboard, status or fleet page, form, calculator, tracker, quiz or study page, mockup, prototype, preview, comparison or review page, or internal tool - even if the request is only "make me a page for X", "add a button", "fix the layout" or "show me the options", and before you report such work as done. Do not use it for plain text documents, slide decks, or code with no user interface.
---

# Pages and tools

These are the user's own rules for pages and tools. They are the same for each
build, so apply all of them and do not add rules of your own. If a rule gives an
absurd result for a specific page, follow its intent and tell the user.

The common purpose: the user counts each click and each typed character. A page
that needs setup, loses their choices, or stops at an unfinished state costs
them work each time they open it.

## Before you build

- A visual or design question (look, layout, colours, a logo, a new identity):
  load the `ui-design` skill if this session has it, else the design skills it
  has (`frontend-design`, `artifact-design`, `design:design-critique`). This
  skill holds the user's rules; those hold the design method.
- A choice of direction is the user's. Show 2 to 4 options side by side on one
  page, each with a short label, and let the user pick. Do not pick for them
  and build on it.
- A change to the look, the text or the behaviour of a page the user already
  uses: show a preview first, and change the live page only after their yes.
- Change the page that exists (the same artifact, the same URL). A new page for
  each version leaves the user with old links.

## Rules

### 1. Use with no effort
- Work with no setup.
- Good defaults.
- Remember the user's last choices.
- One-click copy and one-click download.
- Keyboard support: focus in the first field, Enter submits, visible focus.
- Undo or autosave instead of confirm dialogs. Confirm only destructive actions.

### 2. Finish every state
- Empty.
- Loading.
- Error: say what happened and what to do.
- Success.
- Show units, thousands separators, and the last-updated time.

### 3. Accessibility beyond contrast
- Targets at least 24x24 px; 44 px for touch-first tools.
- Labelled inputs.
- Respect reduced motion.

### 4. One meaning per color or label
- Each color and each label has one meaning, applied everywhere on the page
  and across the pages of the same tool.

## Before you report the work as done

Check the built page against each line above, on the real page and not from the
source code alone: open it, use the keyboard only, cause an error, load it with
no data, look at it at phone width and in dark mode.

- Measure, do not judge by eye. In a repository that has
  `.claude/skills/verify/SKILL.md`, follow its section for a visual change (its
  script gives the contrast, target-size and scroll numbers). Elsewhere, use a
  browser tool if the session has one and read the sizes from the page.
- After you publish or republish, read the live page back and confirm it is the
  version you built. A preview that changed is not the live page.
- In your report, give one line per rule group: checked and how, or not met and
  the reason. Do not report a rule as met if you did not check it. Keep "built",
  "published" and "checked" apart.
