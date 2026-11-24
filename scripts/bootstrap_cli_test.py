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
import tempfile
import unittest
from pathlib import Path

from sync_baseline_cli_test import GIT, KIT, new_repo, py, run  # the shared CLI test helpers


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
        for gone in ("scripts/bootstrap.sh", "scripts/sync_baseline.py", "scripts/drift.py", "KIT_VERSION", "docs/FILES.md", "docs/tools.md",
                     "scripts/sync_baseline_cli_test.py", "scripts/bootstrap_cli_test.py", "docs/threat-model.md",
                     "scripts/kit_package.py", "pyproject.toml",
                     "SECURITY.md", ".github/dependabot.yml", ".github/workflows/security.yml"):  # DoD group: key off
            self.assertFalse((self.path / gone).exists(), gone)

    def set_dod(self, value):
        """Add a `dod-security:` line to the template's .check and commit it (bootstrap reads the committed tree)."""
        with open(self.path / ".check", "a") as f:
            f.write(f"dod-security: {value}\n")
        run(["git", "add", "-A"], self.path)
        run(GIT + ["commit", "-q", "-m", "dod"], self.path)

    def test_dod_on_keeps_the_dod_group(self):
        """Prove: with `dod-security: on` the DoD group stays; the kit's threat model still goes."""
        self.set_dod("on")
        self.assertEqual(self.starter().returncode, 0)
        for kept in ("SECURITY.md", ".github/dependabot.yml", ".github/workflows/security.yml"):
            self.assertTrue((self.path / kept).is_file(), kept)
        self.assertFalse((self.path / "docs/threat-model.md").exists())

    def test_dod_typo_stops(self):
        """Prove: a `dod-security:` value other than on or off stops bootstrap with a message, before it says Done."""
        self.set_dod("maybe")
        p = self.starter()
        self.assertEqual(p.returncode, 1)
        self.assertIn("dod-security", p.stderr)
        self.assertNotIn("Done.", p.stdout)
        self.assertEqual(run(["git", "status", "--porcelain"], self.path).stdout, "", "the tree is unchanged, so a rerun works")

    def test_role_word_reaches_every_synced_file(self):
        """Prove: with another role, no kit file keeps the baseline word (a sync right after bootstrap changes nothing)."""
        self.assertEqual(self.starter().returncode, 0)
        left = [str(f.relative_to(self.path)) for f in self.path.rglob("*") if f.is_file() and ".git" not in f.parts and f.suffix != ".pyc"
                and f.name not in ("FIRST_USE.md", "first_use_check.py", "DECISIONS.md")
                and "the Maintainer" in f.read_text(errors="replace")]
        self.assertEqual(left, [])

    def test_starter_run_writes_state_and_valid_lock(self):
        """Prove: a starter run writes .check.state.json and a .check.lock that verifies."""
        self.assertEqual(self.starter().returncode, 0)
        state = json.loads((self.path / ".check.state.json").read_text())
        self.assertEqual(state["code_standard"], {"debt": {}})
        v = py("check_lock.py", "--verify", "--project", str(self.path), cwd=self.path)
        self.assertEqual(v.returncode, 0, v.stdout)


if __name__ == "__main__":
    unittest.main()
