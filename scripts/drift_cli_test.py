"""The command line of scripts/drift.py, tested as a process.

What it proves: after a sync drift.py reports no drift; after one synced file changes it names that file; --strict exits 1.
Inputs:  none (each case builds a temporary git repo and runs the script by its command line, never by import).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'drift_cli_test.py'
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


class DriftCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        new_repo(self.path)
        self.assertEqual(sync(self.path).returncode, 0)

    def drift(self, *extra):
        return py("drift.py", "--project", str(self.path), "--baseline", str(KIT), "--owner", "the maintainer", *extra,
                  cwd=self.path)

    def test_no_drift_after_sync(self):
        p = self.drift("--strict")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("DRIFT: 0 of", p.stdout)

    def test_edited_file_is_reported(self):
        with open(self.path / "scripts/session_checkin.sh", "a") as f:
            f.write("# local edit\n")
        p = self.drift()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("DRIFT: 0 of", p.stdout)
        line = [l for l in p.stdout.splitlines() if "scripts/session_checkin.sh" in l]
        self.assertEqual(len(line), 1, p.stdout)
        self.assertIn("differs", line[0])

    def test_strict_exits_1_on_drift(self):
        (self.path / "scripts/session_checkin.sh").write_text("changed\n")
        self.assertEqual(self.drift("--strict").returncode, 1)

    def test_drift_never_writes(self):
        (self.path / "scripts/session_checkin.sh").write_text("changed\n")
        run(["git", "add", "-A"], self.path)
        before = (run(["git", "status", "--short"], self.path).stdout, (self.path / ".check.lock").read_text())
        self.drift()
        after = (run(["git", "status", "--short"], self.path).stdout, (self.path / ".check.lock").read_text())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
