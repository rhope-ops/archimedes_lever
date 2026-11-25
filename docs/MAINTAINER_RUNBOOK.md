# Maintainer runbook

This page is for the Maintainer of the kit. The Maintainer decides. The Content Approver approves content changes. The
Release Manager makes tags and releases. One person can hold all three roles.

Each task below has numbered steps. Run each command in a terminal, in the folder of the kit, unless the step names
another folder.

## Run the checks

The kit has two check lanes. The fast lane runs the self-tests of the scripts that changed. The full lane runs everything.

1. In the terminal, run `scripts/check.sh --fast`. You see one line for each check: PASS, FAIL or SKIP. Wait until the last line shows.
2. If the last line is `CHECK FAIL`, read the output of the failed check. You see the cause of the failure.
3. Before a merge, in the terminal, run `scripts/check.sh`. You see the full lane run. Wait until the last line shows.
4. Make sure the last line is `CHECK PASS`. You see the words `CHECK PASS`. The task is complete.

To run the command-line tests of the sync, drift, lock and bootstrap scripts, run
`python3 -m unittest discover -s scripts -p '*_cli_test.py' -v`. The last lines are `Ran N tests` and `OK`.

## Cut a kit release

The file `KIT_VERSION` holds the version. The version has the form MAJOR.MINOR.PATCH.

- Use MAJOR when a project must do more than run the sync, or when a kit rule text changes.
- Use MINOR for new behavior that the sync alone brings.
- Use PATCH for a fix.

The Maintainer prepares the release. The Release Manager makes the tag.

1. In the file `KIT_VERSION`, write the new version. You see the version and one new line.
2. In the file `docs/CHANGELOG.md`, add one row at the top of the table. The row has the version, the change and the project step. You see the new row.
3. In the terminal, run `scripts/check.sh`. You see the full lane run. Wait until the last line shows `CHECK PASS`.
4. On GitHub, open a pull request with the change. You see the page of the pull request. Wait until the checks are green and the review finds no MAJOR finding.
5. On GitHub, merge the pull request. You see the status Merged.
6. The Release Manager opens the page **Releases** of the repository. You see the list of releases.
7. Click **Draft a new release**. You see the box **Choose a tag**.
8. In the box **Choose a tag**, type `v` and the new version, for example `v11.0.0`. You see the tag in the box.
9. Select the merge commit as the target. You see the commit in the box **Target**.
10. Click **Publish release**. You see the new tag on the page **Releases**. The task is complete.

## Sync a project

A sync brings the kit files to a project. A sync never changes the project rules, the Commands section or the project files. The project folder must have no uncommitted changes.

1. In the kit folder, run `git checkout v<version>` with the release version. You see the message that the folder is at the release.
2. In the project folder, run `python3 <kit folder>/scripts/sync_baseline.py --baseline <kit folder>`. This is a dry run. You see the list of changes, and the command writes no file.
3. If the project is a public repository, add `--owner "the maintainer"` to both sync commands. You see the role word in the list of changes, and no real name.
4. If the list of changes is right, run the same command with `--apply` at the end. You see the line `Written, with the kit lock .check.lock`. Wait until the line shows.
5. In the project folder, commit the files. You see the new commit.
6. Open a pull request on GitHub. You see the page of the pull request. The task is complete.

A second run of the same command writes nothing. You see `No changes`.

## Read the drift report

The drift report shows how a project differs from the kit. It never writes a file.

1. In the kit folder, run `python3 scripts/drift.py --project <project folder> --baseline <kit folder>`. You see one line for each item. Wait until the last line shows.
2. Read the last line. You see `DRIFT: N of M item(s) not the same as the baseline`.
3. If N is 0, the project has no drift. You see `DRIFT: 0`. The task is complete.
4. If N is more than 0, find the lines that do not start with `same`. You see the name of a file or of a rule part on each line.
5. For a line `differs` or `changed`, choose a sync or keep the project text on purpose. You see the choice in the pull request text.

To make the command exit with code 1 when anything differs, add `--strict`.

## Read the kit lock

The file `.check.lock` records the kit version, the kit commit and a hash of each kit file.

1. In the project folder, run `python3 scripts/check_lock.py --status`. You see the pinned version, the commit and the number of locked files.
2. Run `python3 scripts/check_lock.py --verify`. You see one line for each difference. Wait until the last line shows.
3. If the last line starts with `LOCK PASS`, no kit file changed. The task is complete.
4. If you see `FAIL  kit file changed in this project: <file>`, restore the file from the kit or run a sync. You see no FAIL line at the next `--verify`.
5. Only when the Maintainer asks for a project override, run `python3 scripts/check_lock.py --relock <file>`. You see the message `relocked`.

Each later `--verify` shows a `WARN` line for a relocked file.

## Change the settings of the checks

The settings are in the file `.check`. The file `docs/check-config-schema.md` lists the keys. A change of `.check` needs the written request of the Maintainer.

1. Open the file `.check`. You see the lines of the settings.
2. Add or change one line. You see the new line in the file.
3. If the line starts with `code-`, add a row to `docs/DECISIONS.md` that names `.check`. You see the new row.
4. In the terminal, run `python3 scripts/check_settings.py`. You see the settings as JSON, or an error message for a wrong line.
5. Run `scripts/check.sh`. You see the full lane run. Wait until the last line shows `CHECK PASS`. The task is complete.

## Change config values (after kit 11.0.0)

This task is valid after kit 11.0.0, and only in the kit clone. Before that version, the file `kit.config.json` does not exist. A project has no `kit.config.json`.

From kit 11.0.0, the file `kit.config.json` holds the organization and repository URL of the kit. No script or page holds the URL in its own text. A change needs the written request of the Maintainer.

1. Open the file `kit.config.json`. You see the keys and values.
2. In the file `kit.config.json`, change the value of the key that the request names. You see the new value.
3. In the terminal, run `scripts/check.sh`. You see the full lane run. Wait until the last line shows `CHECK PASS`.
4. Add a row to `docs/CHANGELOG.md`. A new URL is a MAJOR change when a project must act on it. You see the new row.
5. On GitHub, open a pull request with the change. You see the page of the pull request.
6. Cut a kit release with the steps of the task "Cut a kit release". You see the release on the page **Releases**. The task is complete.
