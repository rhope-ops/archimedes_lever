"""The command line of scripts/check_lock.py, tested as a process.

What it proves: --verify passes after a sync and fails after a synced file changes, and --status names the pinned version
and the file count; --relock records an override.
Inputs:  none (each case builds a temporary git repo and runs the script by its command line, never by import).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'check_lock_cli_test.py'
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


class CheckLockCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        new_repo(self.path)
        self.assertEqual(sync(self.path).returncode, 0)

    def lock(self, *args):
        return py("check_lock.py", *args, "--project", str(self.path), cwd=self.path)

    def test_verify_passes_after_sync(self):
        p = self.lock("--verify")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("LOCK PASS", p.stdout)

    def test_verify_fails_after_change_and_names_file(self):
        with open(self.path / "scripts/stop_check.py", "a") as f:
            f.write("# local edit\n")
        p = self.lock("--verify")
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAIL  kit file changed in this project: scripts/stop_check.py", p.stdout)
        self.assertIn("LOCK FAIL", p.stdout)

    def test_verify_fails_when_file_is_missing(self):
        (self.path / "scripts/stop_check.py").unlink()
        p = self.lock("--verify")
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAIL  kit file missing: scripts/stop_check.py", p.stdout)

    def test_status_names_version_and_count(self):
        p = self.lock("--status")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads((self.path / ".check.lock").read_text())
        self.assertIn(f"version {data['version']}", p.stdout)
        self.assertIn(f"{len(data['files'])} locked files", p.stdout)

    def test_relock_lists_override(self):
        with open(self.path / "scripts/stop_check.py", "a") as f:
            f.write("# accepted edit\n")
        self.assertEqual(self.lock("--relock", "scripts/stop_check.py").returncode, 0)
        p = self.lock("--verify")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("WARN  kit file with a project override", p.stdout)
        self.assertIn("scripts/stop_check.py", p.stdout)

    def test_no_lock_file_is_refused_or_reported(self):
        empty = tempfile.TemporaryDirectory()
        self.addCleanup(empty.cleanup)
        p = py("check_lock.py", "--status", "--project", empty.name, cwd=Path(empty.name))
        self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
