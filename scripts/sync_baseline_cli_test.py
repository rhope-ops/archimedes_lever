"""The command line of scripts/sync_baseline.py, tested as a process.

What it proves: a sync into an empty repo brings the kit files and the kit lock, a second sync changes nothing, and
--owner swaps the role word.
Inputs:  none (each case builds a temporary git repo and runs the script by its command line, never by import).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'sync_baseline_cli_test.py'
Network: none (the baseline is this checkout, a local folder).
Writes: temporary folders only.
Credentials: none.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
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
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        new_repo(self.path)

    def test_dry_run_writes_nothing(self):
        p = py("sync_baseline.py", "--baseline", str(KIT), "--name", "Demo", "--repo", "org/demo", "--purpose", "A demo.",
               "--timezone", "UTC", "--owner", "the maintainer", "--tier", "starter", cwd=self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(run(["git", "status", "--short"], self.path).stdout, "")

    def test_apply_brings_kit_files_and_lock(self):
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
        self.assertEqual(sync(self.path).returncode, 0)
        run(["git", "add", "-A"], self.path)
        before = (self.path / ".check.lock").read_text()
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("No changes", p.stdout)
        self.assertEqual((self.path / ".check.lock").read_text(), before)

    def test_owner_role_replaces_the_owner_word(self):
        self.assertEqual(sync(self.path).returncode, 0)
        text = (self.path / ".claude/skills/deliver/SKILL.md").read_text()
        self.assertIn("the maintainer", text)
        self.assertNotIn("the owner", text)

    def test_bad_owner_name_is_refused(self):
        p = sync(self.path, "--owner", "bad;name")
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.path / ".check.lock").exists())


if __name__ == "__main__":
    unittest.main()
