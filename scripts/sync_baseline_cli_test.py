"""The command line of scripts/sync_baseline.py, tested as a process.

What it proves: a sync into an empty repo brings the kit files and the kit lock, a second sync changes nothing, and
--owner swaps the role word; ApplyOwner tests the role swap function itself (by import, no repo).
Inputs:  none (each CLI case builds a temporary git repo and runs the script by its command line).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'sync_baseline_cli_test.py'
Network: none (the baseline is this checkout, a local folder).
Writes: temporary folders only.
Credentials: none.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
TABLE = "# D\n\n## Decisions\n\nNewest first.\n\n| Date | Decision | By |\n|---|---|---|\n| 2026-11-22 | Newest row | the owner |\n| 2026-11-21 | Older row | the owner |\n"
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
              "--timezone", "UTC", "--owner", "the maintainer", "--tier", "starter", *extra, "--apply", cwd=path)


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
               "--timezone", "UTC", "--owner", "the maintainer", "--tier", "starter", cwd=self.path)
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
        self.assertIn("- Owner: the maintainer", (self.path / "AGENTS.md").read_text())

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

    def test_clean_project_syncs_again(self):
        """Prove: a project whose kit files match its lock is synced (exit 0)."""
        self.assertEqual(sync(self.path).returncode, 0)
        run(["git", "add", "-A"], self.path)
        run(GIT + ["commit", "-q", "-m", "sync"], self.path)
        self.assertEqual(sync(self.path).returncode, 0)

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
        self.assertIn("PROJECT.md", p.stdout)
        self.assertEqual(self.tree_hashes(), before)

    def test_project_without_a_lock_is_synced_as_before(self):
        """Prove: a project with no .check.lock is not stopped (nothing to compare with): the first sync writes the lock."""
        self.assertFalse((self.path / ".check.lock").exists())
        self.assertEqual(sync(self.path).returncode, 0)
        self.assertTrue((self.path / ".check.lock").is_file())

    def test_owner_role_replaces_the_owner_word(self):
        """Prove: owner role replaces the owner word."""
        self.assertEqual(sync(self.path).returncode, 0)
        text = (self.path / ".claude/skills/deliver/SKILL.md").read_text()
        self.assertIn("the maintainer", text)
        self.assertNotIn("the owner", text)

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


class ApplyOwner(unittest.TestCase):
    """apply_owner follows BASELINE_OWNER (fleet v2 DEC 2): the baseline word is swapped, other words stay."""


    def test_decisions_marker_added_above_the_table(self):
        """Prove: a Decisions table with no marker gets the line with the newest row's Decision cell, above the header row."""
        sys.path.insert(0, str(KIT / "scripts"))
        import sync_baseline as sb
        got = sb.decisions_marker(TABLE)
        self.assertIn("\n<!-- approval-quote-exempt-from: Newest row -->\n\n| Date | Decision | By |\n", got)
        self.assertEqual(sb.decisions_marker(got), got, "a second run changes nothing")
        self.assertEqual(sb.decisions_marker("# D\n\n## Decisions\n\n| Date | Decision | By |\n|---|---|---|\n"), "# D\n\n## Decisions\n\n| Date | Decision | By |\n|---|---|---|\n", "no row: no marker")
        self.assertEqual(sb.decisions_marker("# No table\n"), "# No table\n")

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
        for base in ("the owner", "the Maintainer"):
            word = base.split(" ", 1)[1]
            text = f"The {word} decides. Ask the {word}'s OK. The {word}ship and a running {word.lower()}s stay."
            for owner in ("the owner", "the PFM", "the Maintainer"):
                got = self.swap(base, text, owner)
                cap = owner[:1].upper() + owner[1:]
                self.assertTrue(got.startswith(f"{cap} decides. Ask {owner}'s OK."), (base, owner, got))
                self.assertIn(f"The {word}ship", got)

if __name__ == "__main__":
    unittest.main()
