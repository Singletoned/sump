"""Tests for the transactional release command."""

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_SCRIPT = PROJECT_ROOT / "scripts" / "release.sh"


class ReleaseCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.repository = self.root / "repository"
        self.remote = self.root / "remote.git"
        self.bin_directory = self.root / "bin"
        self.command_log = self.root / "commands.log"

        self._run(["git", "init", "--bare", "--initial-branch=main", self.remote])
        self._run(["git", "init", "--initial-branch=main", self.repository])
        self._git("config", "user.name", "Release Test")
        self._git("config", "user.email", "release@example.com")
        self._git("remote", "add", "origin", str(self.remote))
        (self.repository / "pyproject.toml").write_text(
            '[project]\nname = "sump"\nversion = "0.1.0"\n'
        )
        (self.repository / "uv.lock").write_text('version = "0.1.0"\n')
        self._git("add", "pyproject.toml", "uv.lock")
        self._git("commit", "-m", "Initial release state")
        self._git("push", "-u", "origin", "main")
        self.initial_commit = self._git_output("rev-parse", "HEAD")
        self._create_fake_commands()

    def test_release_versions_commits_tags_verifies_and_atomically_pushes(self) -> None:
        completed = self._release("0.2.0")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('version = "0.2.0"', (self.repository / "pyproject.toml").read_text())
        self.assertEqual(self._git_output("log", "-1", "--format=%s"), "Release v0.2.0")
        self.assertEqual(self._git_output("tag", "--list", "v0.2.0"), "v0.2.0")
        release_commit = self._git_output("rev-parse", "HEAD")
        self.assertEqual(self._remote_output("rev-parse", "refs/heads/main"), release_commit)
        self.assertEqual(self._remote_output("rev-parse", "refs/tags/v0.2.0^{}"), release_commit)
        self.assertEqual(self.command_log.read_text().splitlines(), ["compatibility", "smoke"])
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def test_release_accepts_prerelease_versions(self) -> None:
        for version in ("0.2.0a1", "0.2.0b2", "0.2.0rc3"):
            with self.subTest(version=version), self._fresh_repository():
                completed = self._release(version)
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_release_rejects_invalid_or_unchanged_versions_before_mutation(self) -> None:
        for version in ("next", "0.2", "0.2.0.post1", "0.1.0"):
            with self.subTest(version=version):
                completed = self._release(version)
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(self._git_output("rev-parse", "HEAD"), self.initial_commit)
                self.assertEqual(self._git_output("status", "--porcelain"), "")
        self.assertFalse(self.command_log.exists())

    def test_failed_verification_rolls_back_version_commit_and_tag(self) -> None:
        completed = self._release("0.2.0", fail_target="smoke")

        self.assertNotEqual(completed.returncode, 0)
        self._assert_release_was_rolled_back()
        self.assertIn('version = "0.1.0"', (self.repository / "pyproject.toml").read_text())

    def test_failed_atomic_push_rolls_back_the_local_release(self) -> None:
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        completed = self._release("0.2.0")

        self.assertNotEqual(completed.returncode, 0)
        self._assert_release_was_rolled_back()

    def test_release_rejects_a_tag_that_already_exists_on_origin(self) -> None:
        self._git("tag", "--annotate", "v0.2.0", "--message", "Existing tag")
        self._git("push", "origin", "v0.2.0")
        self._git("tag", "--delete", "v0.2.0")

        completed = self._release("0.2.0")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("tag v0.2.0 already exists on origin", completed.stderr)
        self.assertEqual(self._git_output("rev-parse", "HEAD"), self.initial_commit)
        self.assertEqual(self._git_output("tag", "--list", "v0.2.0"), "")
        self.assertFalse(self.command_log.exists())

    def test_release_rejects_a_dirty_or_unsynchronized_main_branch(self) -> None:
        (self.repository / "pyproject.toml").write_text('version = "dirty"\n')
        dirty = self._release("0.2.0")
        self.assertNotEqual(dirty.returncode, 0)
        self.assertIn("working tree must be clean", dirty.stderr)

        self._git("restore", "pyproject.toml")
        (self.repository / "local-change.txt").write_text("ahead\n")
        self._git("add", "local-change.txt")
        self._git("commit", "-m", "Local change")
        ahead = self._release("0.2.0")
        self.assertNotEqual(ahead.returncode, 0)
        self.assertIn("must match origin/main", ahead.stderr)

    def _fresh_repository(self):
        test_case = self

        class FreshRepository:
            def __enter__(self) -> None:
                return None

            def __exit__(self, *args: object) -> None:
                test_case._git("reset", "--hard", test_case.initial_commit)
                for tag in test_case._git_output("tag", "--list", "v*").splitlines():
                    test_case._git("tag", "--delete", tag)
                test_case._run(
                    [
                        "git",
                        "--git-dir",
                        str(test_case.remote),
                        "update-ref",
                        "refs/heads/main",
                        test_case.initial_commit,
                    ]
                )
                for reference in test_case._remote_output(
                    "for-each-ref", "--format=%(refname)", "refs/tags"
                ).splitlines():
                    test_case._run(
                        ["git", "--git-dir", str(test_case.remote), "update-ref", "-d", reference]
                    )
                test_case.command_log.unlink(missing_ok=True)

        return FreshRepository()

    def _assert_release_was_rolled_back(self) -> None:
        self.assertEqual(self._git_output("rev-parse", "HEAD"), self.initial_commit)
        self.assertEqual(self._git_output("tag", "--list", "v0.2.0"), "")
        self.assertEqual(self._remote_output("rev-parse", "refs/heads/main"), self.initial_commit)
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def _create_fake_commands(self) -> None:
        self.bin_directory.mkdir()
        uv = self.bin_directory / "uv"
        uv.write_text(
            """#!/bin/sh
set -eu
if [ "$1" != "version" ]; then
    echo "unexpected uv command: $*" >&2
    exit 2
fi
if [ "${2:-}" = "--short" ]; then
    python3 <<'PY'
import pathlib
import re
text = pathlib.Path("pyproject.toml").read_text()
print(re.search(r'version = "([^"]+)', text).group(1))
PY
    exit 0
fi
python3 - "$2" <<'PY'
import pathlib
import re
import sys
version = sys.argv[1]
for filename in ("pyproject.toml", "uv.lock"):
    path = pathlib.Path(filename)
    path.write_text(re.sub(r'version = "[^"]+"', f'version = "{version}"', path.read_text()))
PY
"""
        )
        make = self.bin_directory / "make"
        make.write_text(
            """#!/bin/sh
set -eu
printf '%s\n' "$1" >> "$RELEASE_TEST_LOG"
if [ "${RELEASE_TEST_FAIL_TARGET:-}" = "$1" ]; then
    echo "injected $1 failure" >&2
    exit 42
fi
"""
        )
        executable = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        uv.chmod(executable)
        make.chmod(executable)

    def _release(
        self, version: str, fail_target: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin_directory}{os.pathsep}{environment['PATH']}"
        environment["RELEASE_TEST_LOG"] = str(self.command_log)
        if fail_target is not None:
            environment["RELEASE_TEST_FAIL_TARGET"] = fail_target
        return subprocess.run(
            [RELEASE_SCRIPT, version],
            cwd=self.repository,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def _git(self, *arguments: str) -> None:
        self._run(["git", *arguments], cwd=self.repository)

    def _git_output(self, *arguments: str) -> str:
        return self._output(["git", *arguments], cwd=self.repository)

    def _remote_output(self, *arguments: str) -> str:
        return self._output(["git", "--git-dir", str(self.remote), *arguments])

    def _run(self, command: list[object], cwd: Path | None = None) -> None:
        subprocess.run([str(part) for part in command], cwd=cwd, check=True, capture_output=True)

    def _output(self, command: list[object], cwd: Path | None = None) -> str:
        return subprocess.check_output([str(part) for part in command], cwd=cwd, text=True).strip()


if __name__ == "__main__":
    unittest.main()
