# Fleet decision hub: step 2 contract (draft for the owner's approval)

Date: 2026-11-19 15:05 America/Chicago. Plan: [2026-11-19-fleet-decision-hub-plan.md](2026-11-19-fleet-decision-hub-plan.md). Survey: [2026-11-19-fleet-survey.md](2026-11-19-fleet-survey.md). State: DRAFT, not approved. Lane C: the owner approves the texts in sections 1 and 2 as written here.

## 1. Opt-in

A project turns the format on with one line in `.check`: `fleet: on`. Without it, the format check and the harvest skip the project, so a kit sync changes nothing for a project the owner has not ported.

## 2. Format texts

### 2a. Handoff file (docs/NEXT_PROMPT.md; in the kit: docs/KIT_HANDOFF.md)

Under the `Updated:` line, one line:

```
Next update: YYYY-MM-DD, <what the next update delivers>
```

A new section after "State":

```
## Timeline

- YYYY-MM-DD · <milestone> · planned
- YYYY-MM-DD · <milestone> · done
```

"Needs the owner" holds one decision or action per line, with an ID:

```
- D<n> · <question or action> · Options: <A> / <B> / <C> · REC: <option>
```

An action with no options (for example a click only the owner can make) writes `Options: done / not done`.

### 2b. docs/DECISIONS.md

A first column `ID`. IDs count up from D1 (oldest row) and never change or get reused. An open item in "Needs the owner" takes the next free ID; when the owner decides it, its row in DECISIONS.md keeps that ID.

```
| ID | Date | Decision | By | Replaces |
```

A row "By" Agent is a recommendation that the owner has not approved. When the owner approves it later, the session that learns it changes "By" to the owner (this closes survey finding 2).

### 2c. Handoff skill text (one added step under "Write a handoff")

"In a project with `fleet: on`: keep the `Next update:` line and the Timeline section current, and give each line in "Needs the owner" an ID (`.claude/skills/handoff/SKILL.md`, format: docs/reviews/2026-11-19-fleet-contract.md)." The final home of the format is the handoff skill itself, not this review file; step 3 moves it there.

## 3. Page database (the fleet page's `db`)

Rules: everyone signed in reads; only the owner (admin) writes. Unchanged from today.

| Path | Fields | Written by |
|---|---|---|
| `repos/<repo>` (existing rows, extended) | today's fields, plus `last_update`, `next_update {date, text}`, `timeline [{date, text, state}]`, `open_count`, `unread_lines`, `not_filed [{text, url, source}]`, `harvested_at`, `source_commit` | the harvest |
| `items/<repo>~<id>` | `repo`, `id`, `kind` (open or resolved), `date`, `summary` (first sentence, at most 140 characters), `by`, `options []`, `rec`, `url` (link to the line on GitHub), `hash` (of the full line) | the harvest |
| `choices/<repo>~<id>` | `repo`, `id`, `item_hash`, `answer` (yes, no, other or modify), `text`, `status` (pending, applied, rejected or stale), `created_at`, `applied_pr` | the page (`answer`, `text`, `status` pending); the applying session (`status`, `applied_pr`) |

One choice document per item (the same key), so two choices on one item cannot exist: a new choice replaces the pending one.

## 4. Failure states

| Case | What the page shows | What the applying session does |
|---|---|---|
| The harvest is older than 36 hours | "as of <time>" in the warning colour | Nothing |
| The item changed after the choice (`item_hash` differs) | The choice shows "stale" | Sets `status: stale`, does not apply it, asks the owner |
| A line the parser cannot read | "N lines not read" on the project, in red | Nothing; the format check blocks the next push |
| An open pull request or a waiting session that no file lists | "Not filed" in the inbox | Nothing; the project's next session files it |
| The harvest cannot read a repo | The project row shows "not reached" and the cause | Nothing |

## 5. Applying session

The owner starts it with "Apply my fleet choices". It reads `choices` with `status: pending`, marks stale ones, then shows every remaining choice in full (project, ID, item summary, answer, text) and waits for the owner's confirmation in their own message (the approved rule). It then makes each change in its repo by the normal delivery lanes, and sets `status: applied` with the pull request link, or `rejected` with the reason.

## 6. Harvest

`scripts/fleet_harvest.py <repo checkout> --state <file>` parses the two files, compares each item's hash with the last run, and prints only the changed documents as JSON for one ArtifactData `batch`. It never prints full decision text. `--test` runs it on fixture files. The cross-check input (open pull requests, waiting sessions) is passed as a JSON file that the scheduled session writes from its tools.
