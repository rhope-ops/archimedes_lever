"""The merges of scripts/sync_merge.py, tested through the command line of scripts/sync_baseline.py (sync_merge.py has
no command line of its own: it is imported by sync_baseline.py and drift.py).

What it proves: a sync keeps the project own deny rule and setting, adds the kit .gitignore lines at the top, and adds
the story columns to an old Arcs table (success); a sync refuses a settings.json that is not valid JSON and writes nothing
(refusal).
Inputs:  none (each case builds a temporary git repo and runs the script by its command line, never by import).
Outputs: unittest results.
Run:     python3 -m unittest discover -s scripts -p 'sync_merge_cli_test.py'
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




def commit_all(path):
    """Commit what the test wrote (a sync refuses a project with uncommitted changes)."""
    run(["git", "add", "-A"], path)
    run(GIT + ["commit", "-q", "-m", "project files"], path)


class SyncMergeCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name)
        new_repo(self.path)

    def test_merge_keeps_project_parts_and_adds_kit_parts(self):
        (self.path / ".claude").mkdir()
        (self.path / ".claude/settings.json").write_text(json.dumps(
            {"permissions": {"deny": ["Bash(rm -rf demo:*)"]}, "model": "demo-model"}))
        (self.path / ".gitignore").write_text("build/\n")
        (self.path / "docs").mkdir()
        (self.path / "docs/LOG.md").write_text("# Log\n\n| Arc | Span | Summary | Outcome |\n|---|---|---|---|\n"
                                                "| A1 | May | Did it | Done |\n")
        commit_all(self.path)
        p = sync(self.path)
        self.assertEqual(p.returncode, 0, p.stderr)
        settings = json.loads((self.path / ".claude/settings.json").read_text())
        self.assertIn("Bash(rm -rf demo:*)", settings["permissions"]["deny"])
        self.assertGreater(len(settings["permissions"]["deny"]), 1)
        self.assertEqual(settings["model"], "demo-model")
        self.assertIn("hooks", settings)
        ignore = (self.path / ".gitignore").read_text().splitlines()
        self.assertIn("build/", ignore)
        self.assertIn(".env", ignore)
        self.assertLess(ignore.index(".env"), ignore.index("build/"))
        log = (self.path / "docs/LOG.md").read_text()
        self.assertIn("Problem", log)
        self.assertIn("| A1 | May | Did it | - | - | Done | - |", log)

    def test_invalid_settings_json_is_refused(self):
        (self.path / ".claude").mkdir()
        (self.path / ".claude/settings.json").write_text("{not json")
        commit_all(self.path)
        p = sync(self.path)
        self.assertEqual(p.returncode, 1)
        self.assertIn("settings.json is not valid JSON", p.stderr)
        self.assertEqual((self.path / ".claude/settings.json").read_text(), "{not json")
        self.assertFalse((self.path / ".check.lock").exists())


if __name__ == "__main__":
    unittest.main()
