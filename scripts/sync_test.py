"""The command line of scripts/sync_baseline.py and scripts/sync_merge.py, tested as a process, plus shared CLI test helpers.

What it proves: a sync into an empty repo brings the kit files and the kit lock, a second sync changes nothing,
--owner swaps the role word, ApplyOwner tests the role swap function itself (by import, no repo), and SyncMergeCli
tests settings, .gitignore, and Arcs table merges (plus invalid settings.json refusal).
Inputs:  none (each CLI case builds a temporary git repo and runs the script by its command line).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'sync_test.py'
Network: none (the baseline is this checkout, a local folder).
Writes: temporary folders only.
Credentials: none.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
TABLE = ("# D\n\n## Decisions\n\nNewest first.\n\n| Date | Decision | By |\n|---|---|---|\n"
         "| 2026-11-22 | Newest row | the Administrator |\n| 2026-11-21 | Older row | the Administrator |\n")
GIT = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid"]


def run(args, cwd):
    """Run a command in cwd; return the finished process (text output, no exception on a non-zero exit)."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def py(script, *args, cwd):
    """Run a kit script by its command line."""
    return run([sys.executable, str(KIT / "scripts" / script), *args], cwd)


def new_repo(path):
    """Make a temporary git repo with one empty commit."""
    run(["git", "init", "-q", "-b", "main"], path)
    run(GIT + ["commit", "-q", "--allow-empty", "-m", "init"], path)


def sync(path, *extra):
    """Sync the kit (this worktree) into the repo at path: starter tier, role owner, with --apply."""
    return py("sync_baseline.py", "--baseline", str(KIT), "--name", "Demo", "--repo", "org/demo", "--purpose", "A demo.",
              "--timezone", "UTC", "--owner", "the administrator", "--tier", "starter", *extra, "--apply", cwd=path)


def commit_all(path):
    """Commit what the test wrote (a sync refuses a project with uncommitted changes)."""
    run(["git", "add", "-A"], path)
    run(GIT + ["commit", "-q", "-m", "project files"], path)


class SyncBaselineCli(unittest.TestCase):
    def setUp(self):
        """Make an empty temporary git repo."""
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        new_repo(self.path)

    def test_dry_run_writes_nothing(self):
        """Prove: dry run writes nothing."""
        p = py("sync_baseline.py", "--baseline", str(KIT), "--name", "Demo", "--repo", "org/demo", "--purpose", "A demo.",
               "--timezone", "UTC", "--owner", "the administrator", "--tier", "starter", cwd=self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(run(["git", "status", "--short"], self.path).stdout, "")

    def test_apply_brings_kit_files_and_lock(self):
        """Prove: apply brings kit files and lock."""
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        for rel in ("AGENTS.md", "CLAUDE.md", "scripts/check.sh", "scripts/check_lock.py", ".claude/settings.json",
                    ".claude/skills/deliver/SKILL.md", ".gitignore", ".check.lock"):
            self.assertTrue((self.path / rel).is_file(), rel)
        lock = json.loads((self.path / ".check.lock").read_text())
        self.assertIn("scripts/check.sh", lock["files"])
        self.assertIn("version", lock)
        self.assertIn("- Owner: the administrator", (self.path / "AGENTS.md").read_text())

    def test_second_run_changes_nothing(self):
        """Prove: second run changes nothing."""
        self.assertEqual(sync(self.path).returncode, 0)
        run(["git", "add", "-A"], self.path)
        before = (self.path / ".check.lock").read_text()
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("No changes", p.stdout)
        self.assertEqual((self.path / ".check.lock").read_text(), before)

    def tree_hashes(self):
        """Map each file of the project (not .git) to its hash."""
        return {str(f.relative_to(self.path)): hashlib.sha256(f.read_bytes()).hexdigest()
                for f in sorted(self.path.rglob("*")) if f.is_file() and ".git" not in f.relative_to(self.path).parts}

    def test_edited_kit_file_stops_the_sync(self):
        """Prove: one edited kit file stops the sync with exit 2, names the file, and writes nothing."""
        self.assertEqual(sync(self.path).returncode, 0)
        (self.path / "scripts/check_lock.py").write_text("# local edit\n")
        run(["git", "add", "-A"], self.path)
        run(GIT + ["commit", "-q", "-m", "edit"], self.path)
        before = self.tree_hashes()
        p = sync(self.path)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("scripts/check_lock.py", p.stdout)
        self.assertIn("scripts/check.local.sh", p.stdout)
        self.assertEqual(self.tree_hashes(), before)

    def synced_and_committed(self, *extra):
        """Sync the kit into the repo and commit the result."""
        self.assertEqual(sync(self.path, *extra).returncode, 0)
        self.commit_all("sync")

    def commit_all(self, msg):
        """Commit every change of the repo."""
        run(["git", "add", "-A"], self.path)
        run(GIT + ["commit", "-q", "-m", msg], self.path)

    def test_relocked_override_stops_the_sync(self):
        """Prove: a file the Administrator relocked (an override) stops the sync (exit 2): nothing written, lock unchanged."""
        self.synced_and_committed()
        with (self.path / "scripts/check.sh").open("a") as f:
            f.write("# local\n")
        p = py("check_lock.py", "--relock", "scripts/check.sh", "--project", str(self.path), cwd=self.path)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.commit_all("relock")
        before = self.tree_hashes()
        p = sync(self.path)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("scripts/check.sh", p.stdout)
        self.assertEqual(self.tree_hashes(), before)

    def test_unreadable_lock_is_said(self):
        """Prove: a lock that cannot be read does not stop the sync, and one line says the edits were not checked."""
        self.synced_and_committed()
        (self.path / ".check.lock").write_text("[]")
        self.commit_all("break the lock")
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("could not be read", p.stdout)

    def test_edit_of_a_file_this_sync_does_not_write_is_no_stop(self):
        """Prove: an edited advanced file (full tier) does not stop a --tier starter sync that never writes it."""
        self.synced_and_committed("--tier", "full")
        (self.path / ".claude/agents/scout.md").write_text("# local\n")
        self.commit_all("edit scout")
        p = sync(self.path, "--tier", "starter")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual((self.path / ".claude/agents/scout.md").read_text(), "# local\n")

    def test_edit_of_the_kit_part_of_agents_md_says_project_rules(self):
        """Prove: an edit in the kit part of AGENTS.md stops the sync and points to "Project rules", not to a PROJECT.md."""
        self.synced_and_committed()
        text = (self.path / "AGENTS.md").read_text()
        (self.path / "AGENTS.md").write_text(text.replace("## Defaults\n", "## Defaults\n\n- A local rule.\n", 1))
        self.commit_all("edit AGENTS.md")
        p = sync(self.path)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("AGENTS.md (kit sections)", p.stdout)
        self.assertIn('AGENTS.md "Project rules"', p.stdout)
        self.assertNotIn("PROJECT.md", p.stdout)

    def advice_line(self, out, rel):
        """The line of the sync output that names this file."""
        return next(line for line in out.splitlines() if line.strip().startswith(rel))

    def test_each_file_gets_its_own_way_forward(self):
        """Prove: an edited kit part of AGENTS.md, kit skill and kit script each get their own way forward."""
        self.synced_and_committed()
        text = (self.path / "AGENTS.md").read_text()
        (self.path / "AGENTS.md").write_text(text.replace("## Defaults\n", "## Defaults\n\n- A local rule.\n", 1))
        with (self.path / ".claude/skills/deliver/SKILL.md").open("a") as f:
            f.write("# local\n")
        with (self.path / "scripts/check.sh").open("a") as f:
            f.write("# local\n")
        self.commit_all("edit three")
        p = sync(self.path)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        rules = self.advice_line(p.stdout, "AGENTS.md (kit sections)")
        skill = self.advice_line(p.stdout, ".claude/skills/deliver/SKILL.md")
        script = self.advice_line(p.stdout, "scripts/check.sh")
        self.assertIn('AGENTS.md "Project rules"', rules)
        self.assertNotIn("PROJECT.md", rules)
        self.assertIn("PROJECT.md", skill)
        self.assertIn("scripts/check.local.sh", script)
        self.assertIn(".check", script)
        self.assertNotIn("PROJECT.md", script)

    def test_null_overrides_is_an_unreadable_lock(self):
        """Prove: a lock with "overrides": null is said as unreadable and does not crash the sync."""
        self.synced_and_committed()
        lock = json.loads((self.path / ".check.lock").read_text())
        lock["overrides"] = None
        (self.path / ".check.lock").write_text(json.dumps(lock))
        self.commit_all("null overrides")
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("could not be read", p.stdout)

    def test_unlocked_kit_file_that_differs_stops_the_sync(self):
        """Prove: a kit file that is not in the lock, exists with other text, and will be written stops the sync (exit 2, nothing written)."""
        self.synced_and_committed()
        lock = json.loads((self.path / ".check.lock").read_text())
        del lock["files"]["scripts/stop_check.py"]
        (self.path / ".check.lock").write_text(json.dumps(lock))
        (self.path / "scripts/stop_check.py").write_text("# mine\n")
        self.commit_all("unlocked and different")
        before = self.tree_hashes()
        p = sync(self.path)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("scripts/stop_check.py", p.stdout)
        self.assertEqual(self.tree_hashes(), before)

    def test_unlocked_kit_file_that_matches_is_no_stop(self):
        """Prove: a kit file that is not in the lock but has the kit's text is no stop."""
        self.synced_and_committed()
        lock = json.loads((self.path / ".check.lock").read_text())
        del lock["files"]["scripts/stop_check.py"]
        (self.path / ".check.lock").write_text(json.dumps(lock))
        self.commit_all("unlocked and equal")
        self.assertEqual(sync(self.path).returncode, 0)

    def unlock(self, rel):
        """Drop one file from the lock of the project, and commit."""
        lock = json.loads((self.path / ".check.lock").read_text())
        del lock["files"][rel]
        (self.path / ".check.lock").write_text(json.dumps(lock))
        self.commit_all("unlock " + rel)

    def test_unchanged_older_kit_copy_is_no_stop(self):
        """Prove: a file that is an earlier kit version, with no project change, is replaced and does not stop the sync."""
        old = {".claude/skills/audit/SKILL.md": "8ad5448", "scripts/bloat_check.py": "239cdfd"}
        for rel, sha in old.items():
            if run(["git", "cat-file", "-e", f"{sha}:{rel}"], KIT).returncode != 0:
                self.skipTest("the kit history has no " + sha)
        self.synced_and_committed("--tier", "full")
        self.synced_and_committed("--tier", "starter")
        for rel, sha in old.items():
            shown = subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=KIT, capture_output=True, check=True)
            (self.path / rel).write_bytes(shown.stdout)
        self.commit_all("older kit copies")
        p = sync(self.path, "--tier", "full")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for rel, sha in old.items():
            shown = subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=KIT, capture_output=True, check=True)
            self.assertNotEqual((self.path / rel).read_bytes(), shown.stdout, rel + " is updated")
        self.commit_all("synced")
        self.assertIn("No changes", sync(self.path, "--tier", "full").stdout)

    def test_unlocked_file_with_other_line_ends_is_no_stop(self):
        """Prove: an unlocked kit file that differs from the kit's only by CRLF line ends is no stop, as with a locked file."""
        self.synced_and_committed()
        path = self.path / "scripts/stop_check.py"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.unlock("scripts/stop_check.py")
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_unlocked_file_and_a_baseline_with_no_history_stops_with_advice(self):
        """Prove: with no git history in the baseline, a differing unlocked file stops, and the advice names the delete."""
        self.synced_and_committed()
        self.unlock("scripts/stop_check.py")
        (self.path / "scripts/stop_check.py").write_text("# mine\n")
        self.commit_all("edit")
        with tempfile.TemporaryDirectory() as plain:
            copy = Path(plain) / "kit"
            shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"))
            p = py("sync_baseline.py", "--baseline", str(copy), "--name", "Demo", "--repo", "org/demo", "--purpose", "A demo.",
                   "--timezone", "UTC", "--owner", "the administrator", "--tier", "starter", "--apply", cwd=self.path)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        line = self.advice_line(p.stdout, "scripts/stop_check.py")
        self.assertIn("delete", line)
        self.assertIn("scripts/check.local.sh", line)
        self.assertNotIn("PROJECT.md", line)

    def test_relock_with_null_overrides_is_an_unreadable_lock(self):
        """Prove: --relock on a lock with "overrides": null says the lock is not readable and exits 1, with no traceback."""
        self.synced_and_committed()
        lock = json.loads((self.path / ".check.lock").read_text())
        lock["overrides"] = None
        (self.path / ".check.lock").write_text(json.dumps(lock))
        p = py("check_lock.py", "--relock", "scripts/check.sh", "--project", str(self.path), cwd=self.path)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("not readable", p.stdout)
        self.assertNotIn("Traceback", p.stderr)

    def test_project_without_a_lock_is_synced_as_before(self):
        """Prove: a project with no .check.lock is not stopped (nothing to compare with): the first sync writes the lock."""
        self.assertFalse((self.path / ".check.lock").exists())
        self.assertEqual(sync(self.path).returncode, 0)
        self.assertTrue((self.path / ".check.lock").is_file())

    def test_owner_role_replaces_the_owner_word(self):
        """Prove: owner role replaces the Administrator word."""
        self.assertEqual(sync(self.path).returncode, 0)
        text = (self.path / ".claude/skills/deliver/SKILL.md").read_text()
        self.assertIn("the administrator", text)
        self.assertNotIn("the Administrator", text)

    def test_bad_owner_name_is_refused(self):
        """Prove: bad owner name is refused."""
        p = sync(self.path, "--owner", "bad;name")
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.path / ".check.lock").exists())

    def commit_file(self, rel, text):
        """Write one file into the temporary repo and commit it (the sync needs a clean tree)."""
        (self.path / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.path / rel).write_text(text)
        run(["git", "add", "-A"], self.path)
        run(GIT + ["commit", "-q", "-m", "setup"], self.path)

    def test_sync_full_tier_adds_the_decisions_marker(self):
        """Prove: a full-tier sync writes the marker into docs/DECISIONS.md, and a second sync changes nothing."""
        self.commit_file("docs/DECISIONS.md", TABLE)
        p = sync(self.path, "--tier", "full")
        self.assertEqual(p.returncode, 0, p.stderr)
        text = (self.path / "docs/DECISIONS.md").read_text()
        self.assertIn("<!-- approval-quote-exempt-from: Newest row -->", text)
        run(["git", "add", "-A"], self.path)
        self.assertIn("No changes", sync(self.path, "--tier", "full").stdout)

    def test_sync_starter_tier_leaves_decisions_alone(self):
        """Prove: a starter project has no T6 check, so its docs/DECISIONS.md is not changed."""
        self.commit_file("docs/DECISIONS.md", TABLE)
        self.assertEqual(sync(self.path).returncode, 0)
        self.assertEqual((self.path / "docs/DECISIONS.md").read_text(), TABLE)

    def test_dod_group_off_by_default(self):
        """Prove: with no `dod-security: on` line, the sync adds no DoD file (fleet v2 DEC 4: ICF-Source)."""
        self.assertEqual(sync(self.path).returncode, 0)
        for rel in ("SECURITY.md", ".github/dependabot.yml", ".github/workflows/security.yml"):
            self.assertFalse((self.path / rel).exists(), rel)

    def test_dod_group_on_adds_missing_files_only(self):
        """Prove: `dod-security: on` adds the missing DoD files, keeps a project's own copy, and locks none."""
        self.commit_file(".check", "dod-security: on\n")
        self.commit_file(".github/workflows/security.yml", "name: own scan\n")
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((self.path / "SECURITY.md").is_file())
        self.assertTrue((self.path / ".github/dependabot.yml").is_file())
        self.assertEqual((self.path / ".github/workflows/security.yml").read_text(), "name: own scan\n")
        lock = json.loads((self.path / ".check.lock").read_text())
        for rel in ("SECURITY.md", ".github/dependabot.yml", ".github/workflows/security.yml"):
            self.assertNotIn(rel, lock["files"])
        self.assertIn(".github/workflows/security.yml: kept; it differs from the kit's file", p.stdout)

    def test_dod_copy_of_an_earlier_kit_version_is_replaced(self):
        """Prove: a DoD copy equal to an earlier kit version is replaced; an edited copy is kept with a note."""
        sys.path.insert(0, str(KIT / "scripts"))
        from sync_baseline import dod_files
        base = self.path / "kit"
        base.mkdir()
        new_repo(base)
        for text in ("v1\n", "v2\n"):
            (base / "a.yml").write_text(text)
            (base / "b.yml").write_text(text)
            run(["git", "add", "-A"], base)
            run(GIT + ["commit", "-q", "-m", text], base)
        root = self.path / "proj"
        root.mkdir()
        (root / ".check").write_text("dod-security: on\n")
        (root / "a.yml").write_text("v1\n")
        (root / "b.yml").write_text("v1 tuned\n")
        new, notes = dod_files(base, root, ["a.yml", "b.yml", "c.yml"])
        self.assertEqual(new, {"a.yml": "v2\n"})
        self.assertEqual(len(notes), 2, notes)
        self.assertIn("a.yml: the project's copy is an earlier kit version", notes[0])
        self.assertIn("b.yml: kept; it differs from the kit's file (this project changed it)", notes[1])
        (root / "a.yml").write_text("v2\n")
        self.assertEqual(dod_files(base, root, ["a.yml"]), ({}, []), "the kit's own text: no change, no note")
        (root / ".check").write_text("dod-security: off\n")
        self.assertEqual(dod_files(base, root, ["a.yml", "c.yml"]), ({}, []), "the key off: nothing")


class ApplyOwner(unittest.TestCase):
    """apply_owner follows BASELINE_OWNER (fleet v2 DEC 2): the baseline word is swapped, other words stay."""

    def test_decisions_marker_added_above_the_table(self):
        """Prove: a Decisions table with no marker gets the line with the newest row's Decision cell, above the header row."""
        sys.path.insert(0, str(KIT / "scripts"))
        import sync_baseline as sb
        got = sb.decisions_marker(TABLE)
        self.assertIn("\n<!-- approval-quote-exempt-from: Newest row -->\n\n| Date | Decision | By |\n", got)
        self.assertEqual(sb.decisions_marker(got), got, "a second run changes nothing")
        self.assertEqual(sb.decisions_marker("# D\n\n## Decisions\n\n| Date | Decision | By |\n|---|---|---|\n"),
                         "# D\n\n## Decisions\n\n| Date | Decision | By |\n|---|---|---|\n", "no row: no marker")
        self.assertEqual(sb.decisions_marker("# No table\n"), "# No table\n")
        untitled = TABLE.replace("## Decisions", "Text under the title.")
        self.assertIn("\n<!-- approval-quote-exempt-from: Newest row -->\n\n| Date | Decision | By |\n",
                      sb.decisions_marker(untitled), "no '## Decisions': the Date | Decision | By table gets the marker")
        self.assertEqual(sb.decisions_marker("# D\n\n| Name | Value |\n|---|---|\n| a | b |\n"),
                         "# D\n\n| Name | Value |\n|---|---|\n| a | b |\n", "another table: no marker")
        scope = "# D\n\n| Date | Scope | Decision | Replaces |\n|---|---|---|---|\n| 2026-11-25 | Kit sync | By: the Administrator. New text. | - |\n"
        self.assertIn("\n<!-- approval-quote-exempt-from: By: the Administrator. New text. -->\n\n| Date | Scope |",
                      sb.decisions_marker(scope), "a Date | Scope | Decision table: the marker names the Decision cell")
        empty = "# D\n\n| Date | Decision | By |\n|---|---|---|\n\n| Name | Value |\n|---|---|\n| a | b |\n"
        self.assertEqual(sb.decisions_marker(empty), empty, "an empty Decisions table: no marker from a later table")

    def swap(self, base, text, owner):
        """apply_owner(text, owner) with BASELINE_OWNER set to base for this call."""
        sys.path.insert(0, str(KIT / "scripts"))
        import sync_baseline as sb
        saved, sb.BASELINE_OWNER = sb.BASELINE_OWNER, base
        try:
            return sb.apply_owner(text, owner)
        finally:
            sb.BASELINE_OWNER = saved

    def test_each_baseline_and_role(self):
        """Prove: for the old and the new baseline word, each role word replaces it; near words stay."""
        for base in ("the Administrator", "the Administrator"):
            word = base.split(" ", 1)[1]
            text = f"The {word} decides. Ask the {word}'s OK. The {word}ship and a running {word.lower()}s stay."
            for owner in ("the Administrator", "the Administrator", "the Administrator"):
                got = self.swap(base, text, owner)
                cap = owner[:1].upper() + owner[1:]
                self.assertTrue(got.startswith(f"{cap} decides. Ask {owner}'s OK."), (base, owner, got))
                self.assertIn(f"The {word}ship", got)


class SyncMergeCli(unittest.TestCase):
    def setUp(self):
        """Make an empty temporary git repo with a .claude folder."""
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        new_repo(self.path)
        (self.path / ".claude").mkdir()

    def merged(self):
        """Write a project with its own settings, .gitignore and old Arcs table, commit it, sync, return the process."""
        (self.path / ".claude/settings.json").write_text(json.dumps(
            {"permissions": {"deny": ["Bash(rm -rf demo:*)"]}, "model": "demo-model"}))
        (self.path / ".gitignore").write_text("build/\n")
        (self.path / "docs").mkdir()
        (self.path / "docs/LOG.md").write_text("# Log\n\n| Arc | Span | Summary | Outcome |\n|---|---|---|---|\n"
                                                "| A1 | May | Did it | Done |\n")
        commit_all(self.path)
        return sync(self.path)

    def test_merge_settings_keeps_project_parts(self):
        """Prove: the settings keep the project deny rule and setting, and gain the kit deny rules and hooks."""
        self.assertEqual(self.merged().returncode, 0)
        settings = json.loads((self.path / ".claude/settings.json").read_text())
        self.assertIn("Bash(rm -rf demo:*)", settings["permissions"]["deny"])
        self.assertGreater(len(settings["permissions"]["deny"]), 1)
        self.assertEqual(settings["model"], "demo-model")
        self.assertIn("hooks", settings)

    def test_merge_gitignore_puts_kit_lines_first(self):
        """Prove: the kit .gitignore lines go above the project lines, which stay."""
        self.assertEqual(self.merged().returncode, 0)
        ignore = (self.path / ".gitignore").read_text().splitlines()
        self.assertIn("build/", ignore)
        self.assertLess(ignore.index(".env"), ignore.index("build/"))

    def test_merge_arcs_adds_story_columns(self):
        """Prove: an old 4-column Arcs table gets the story columns and keeps its rows."""
        self.assertEqual(self.merged().returncode, 0)
        log = (self.path / "docs/LOG.md").read_text()
        self.assertIn("Problem", log)
        self.assertIn("| A1 | May | Did it | - | - | Done | - |", log)

    def test_invalid_settings_json_is_refused(self):
        """Prove: invalid settings json is refused."""
        (self.path / ".claude/settings.json").write_text("{not json")
        commit_all(self.path)
        p = sync(self.path)
        self.assertEqual(p.returncode, 1)
        self.assertIn("settings.json is not valid JSON", p.stderr)
        self.assertEqual((self.path / ".claude/settings.json").read_text(), "{not json")
        self.assertFalse((self.path / ".check.lock").exists())


if __name__ == "__main__":
    unittest.main()
