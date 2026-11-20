---
name: where-to-save
description: Where the user wants each deliverable saved - copy block, Claude Docs, Artifact, Google Drive folder or the repo. Use this skill before you save, publish or hand over any deliverable (text to paste, a document, a page or tool, a mockup, a binary file such as pptx, png, svg, zip or xlsx), whenever you are not sure which destination is correct, and when the user says a project is done and its old files need a clean-up list.
---

# Where to save

The user wants one correct place for each deliverable, so that nothing is lost when a
session ends and nothing exists in two copies. Choose the destination from this
table before you create the deliverable.

| Deliverable | Destination |
|---|---|
| Short text to paste | A copy block in the reply |
| Long text, or text to review | An editable doc (Claude Docs) |
| Text doc to edit or share | Claude Docs. Use Google Docs only when the user says "Google". |
| Interactive page, tool, mockup, review | An Artifact |
| Binary file outside a repo (pptx, png, svg, zip, xlsx, backup) | Google Drive, in `Claude Projects/<project name>/` |
| Asset for more than one project | Google Drive, in `Claude Projects/Brand assets/` |
| File that a repo uses (code, images, fonts) | The repo |

## Rules

- Save each deliverable as soon as it exists. A cloud session's container does not
  last, so a file that stays only in the session is lost.
- One artifact for each thing. Update it in place. Do not publish a copy, because
  the user then has two links and does not know which is current.
- Do not put files in the Google Drive root. If the project folder does not exist,
  create it.
- If the destination is not available in this session (for example, the Google Drive
  connector is not connected), tell the user, keep the file in the working directory,
  and name the destination where it must go.

## When the user says a project is done

List the project's superseded artifacts and Google Drive files, with links, and
recommend them for deletion. Do not delete them until the user approves the list.
