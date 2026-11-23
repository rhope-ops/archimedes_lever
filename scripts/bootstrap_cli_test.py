"""The command line of scripts/bootstrap.sh, tested as a process.

What it proves: in a copy of the kit (tracked files only) in a temporary git repo, bootstrap fills the placeholders,
renames the owner word, writes README.md, .check.state.json and .check.lock, deletes the kit-only files and itself, and
leaves a repo whose lock verifies; it refuses a wrong argument count, a bad tier and a bad owner name, and changes nothing
then. It needs perl and bash, and no network.
Inputs:  none (each case builds a temporary git repo and runs the script by its command line, never by import).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'sync_baseline_cli_test.py'
Network: none (the baseline is this checkout, a local folder).
Writes: temporary folders only.
Credentials: none.
"""
import json
import shutil
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




def kit_copy(path):
    """Copy the tracked files of the kit into path and commit them, as a new project made from the template."""
    names = run(["git", "ls-files", "-z"], KIT).stdout.split("\0")
    for rel in filter(None, names):
        if (KIT / rel).is_file():
            (path / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(KIT / rel, path / rel, follow_symlinks=False)
    new_repo(path)
    run(["git", "add", "-A"], path)
    run(GIT + ["commit", "-q", "-m", "template"], path)


class BootstrapCli(unittest.TestCase):
    def setUp(self):
        """Make a temporary git repo that holds a copy of the kit."""
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        kit_copy(self.path)

    def boot(self, *args):
        """Run scripts/bootstrap.sh in the project with these arguments."""
        return run(["bash", "scripts/bootstrap.sh", *args], self.path)

    def test_wrong_argument_count_is_refused(self):
        """Prove: wrong argument count is refused."""
        p = self.boot("Only One")
        self.assertEqual(p.returncode, 1)
        self.assertIn("usage:", p.stderr)
        self.assertTrue((self.path / "scripts/bootstrap.sh").exists())

    def test_bad_tier_and_bad_owner_are_refused(self):
        """Prove: bad tier and bad owner are refused."""
        p = self.boot("Demo App", "org/demo", "A demo.", "the maintainer", "UTC", "middle")
        self.assertEqual(p.returncode, 1)
        self.assertIn("use starter or full", p.stderr)
        p = self.boot("Demo App", "org/demo", "A demo.", "bad;name")
        self.assertEqual(p.returncode, 1)
        self.assertIn("owner name", p.stderr)
        self.assertTrue((self.path / "scripts/bootstrap.sh").exists())

    def test_bad_time_zone_is_refused(self):
        """Prove: bad time zone is refused."""
        p = self.boot("Demo App", "org/demo", "A demo.", "the maintainer", "Mars/Base")
        self.assertEqual(p.returncode, 1)
        self.assertIn("not a known IANA name", p.stderr)

    def starter(self):
        """Run a starter bootstrap with the role owner and return the finished process."""
        return self.boot("Demo App", "org/demo", "A demo.", "the maintainer", "UTC", "starter")

    def test_starter_run_fills_template(self):
        """Prove: a starter run fills the placeholders, renames the owner word and writes README.md."""
        p = self.starter()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("Done.", p.stdout)
        agents = (self.path / "AGENTS.md").read_text()
        for want in ("# Demo App: agent instructions", "- Repo: org/demo", "- Owner: the maintainer"):
            self.assertIn(want, agents)
        self.assertNotIn("{{", agents)
        self.assertIn("the maintainer", (self.path / ".claude/skills/deliver/SKILL.md").read_text())
        self.assertTrue((self.path / "README.md").read_text().startswith("# Demo App\n\nA demo."))

    def test_starter_run_removes_kit_files(self):
        """Prove: a starter run deletes the kit-only files and the script itself."""
        self.assertEqual(self.starter().returncode, 0)
        for gone in ("scripts/bootstrap.sh", "scripts/sync_baseline.py", "scripts/drift.py", "KIT_VERSION", "docs/FILES.md"):
            self.assertFalse((self.path / gone).exists(), gone)

    def test_starter_run_writes_state_and_valid_lock(self):
        """Prove: a starter run writes .check.state.json and a .check.lock that verifies."""
        self.assertEqual(self.starter().returncode, 0)
        state = json.loads((self.path / ".check.state.json").read_text())
        self.assertEqual(state["code_standard"], {"debt": {}})
        v = py("check_lock.py", "--verify", "--project", str(self.path), cwd=self.path)
        self.assertEqual(v.returncode, 0, v.stdout)


if __name__ == "__main__":
    unittest.main()
