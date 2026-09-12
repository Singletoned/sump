"""Subprocess coverage for lock-free concurrent transport writers."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sentry_sdk.envelope import Envelope

from sump._claims import acknowledge_claim, claim_project
from sump._registry import ProjectRegistry

WRITER_COUNT = 6
EVENTS_PER_WRITER = 20
WRITER_SCRIPT = """
import os
import sentry_sdk
import sump

worker = os.environ["SUMP_TEST_WORKER"]
count = int(os.environ["SUMP_TEST_EVENT_COUNT"])
with sump.init("concurrent-app", default_integrations=False):
    for sequence in range(count):
        sentry_sdk.capture_message(f"{worker}:{sequence}")
print(count)
"""


class ConcurrentWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_root = Path(self.temporary_directory.name) / "state"
        environment = patch.dict(os.environ, {"SUMP_STATE_DIR": str(self.state_root)})
        environment.start()
        self.addCleanup(environment.stop)

    def run_writer(self, worker: str, event_count: int) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["SUMP_TEST_WORKER"] = worker
        environment["SUMP_TEST_EVENT_COUNT"] = str(event_count)
        return subprocess.run(
            [sys.executable, "-c", WRITER_SCRIPT],
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    def test_concurrent_writers_are_complete_unique_and_all_collectible(self) -> None:
        processes: list[subprocess.Popen[str]] = []
        for worker_number in range(WRITER_COUNT):
            environment = os.environ.copy()
            environment["SUMP_TEST_WORKER"] = str(worker_number)
            environment["SUMP_TEST_EVENT_COUNT"] = str(EVENTS_PER_WRITER)
            processes.append(
                subprocess.Popen(
                    [sys.executable, "-c", WRITER_SCRIPT],
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            )

        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(stdout.strip(), str(EVENTS_PER_WRITER))

        expected_messages = {
            f"{worker}:{sequence}"
            for worker in range(WRITER_COUNT)
            for sequence in range(EVENTS_PER_WRITER)
        }
        pending_directory = self.state_root / "projects" / "concurrent-app" / "pending"
        pending_paths = list(pending_directory.iterdir())
        self.assertEqual(len(pending_paths), len(expected_messages))
        self.assertEqual(len({path.name for path in pending_paths}), len(expected_messages))

        stored_messages = set()
        for path in pending_paths:
            with self.subTest(path=path.name):
                envelope = Envelope.deserialize(path.read_bytes())
                event = envelope.get_event()
                self.assertIsNotNone(event)
                stored_messages.add(event["message"])
        self.assertEqual(stored_messages, expected_messages)

        collected_messages = []
        batch_sizes = []
        while True:
            claim = claim_project("concurrent-app")
            if claim["claim_id"] is None:
                break
            batch_sizes.append(len(claim["occurrences"]))
            collected_messages.extend(
                occurrence["event"]["message"] for occurrence in claim["occurrences"]
            )
            acknowledge_claim("concurrent-app", claim["claim_id"])

        self.assertEqual(batch_sizes, [100, 20])
        self.assertEqual(set(collected_messages), expected_messages)
        self.assertEqual(len(collected_messages), len(expected_messages))

    def test_transport_write_does_not_wait_for_project_claim_lock(self) -> None:
        registry = ProjectRegistry.from_environment("concurrent-app")

        with registry.claim_lock():
            completed = self.run_writer("lock-held", 1)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "1")
        pending_directory = self.state_root / "projects" / "concurrent-app" / "pending"
        pending_paths = list(pending_directory.iterdir())
        self.assertEqual(len(pending_paths), 1)
        event = Envelope.deserialize(pending_paths[0].read_bytes()).get_event()
        self.assertEqual(event["message"], "lock-held:0")


if __name__ == "__main__":
    unittest.main()
