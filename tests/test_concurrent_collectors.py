"""Subprocess and interruption coverage for serialized collectors."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from sentry_sdk.envelope import Envelope

from sump._claims import acknowledge_claim, claim_project
from sump._registry import ProjectRegistry

COLLECTOR_COUNT = 6
OCCURRENCE_COUNT = 10


class ConcurrentCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_root = Path(self.temporary_directory.name) / "state"
        environment = patch.dict(os.environ, {"SUMP_STATE_DIR": str(self.state_root)})
        environment.start()
        self.addCleanup(environment.stop)
        self.command = Path(sys.executable).parent / "sump"

    def store_occurrences(self, project: str, count: int) -> None:
        registry = ProjectRegistry.from_environment(project)
        for sequence in range(count):
            envelope = Envelope()
            envelope.add_event({"message": f"event-{sequence}", "sequence": sequence})
            registry.store(envelope)

    def run_while_lock_is_held(
        self,
        project: str,
        arguments: list[str],
    ) -> list[subprocess.CompletedProcess[str]]:
        registry = ProjectRegistry.from_environment(project)
        processes = []
        with registry.claim_lock():
            for _ in range(COLLECTOR_COUNT):
                processes.append(
                    subprocess.Popen(
                        [self.command, *arguments],
                        env=os.environ.copy(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )
            time.sleep(0.2)

        completed = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            completed.append(
                subprocess.CompletedProcess(
                    process.args,
                    process.returncode,
                    stdout,
                    stderr,
                )
            )
        return completed

    def assert_successful_json(
        self,
        completed_processes: list[subprocess.CompletedProcess[str]],
    ) -> list[dict[str, object]]:
        results = []
        for completed in completed_processes:
            self.assertEqual(completed.returncode, 0, completed.stderr)
            results.append(json.loads(completed.stdout))
        return results

    def test_concurrent_claims_and_acknowledgements_share_one_state_transition(self) -> None:
        project = "collector-app"
        self.store_occurrences(project, OCCURRENCE_COUNT)

        claim_processes = self.run_while_lock_is_held(project, ["claim", project])
        claim_results = self.assert_successful_json(claim_processes)

        self.assertTrue(all(result == claim_results[0] for result in claim_results))
        claim_id = claim_results[0]["claim_id"]
        self.assertIsInstance(claim_id, str)
        self.assertEqual(len(claim_results[0]["occurrences"]), OCCURRENCE_COUNT)
        occurrence_orders = [
            [occurrence["occurrence_id"] for occurrence in result["occurrences"]]
            for result in claim_results
        ]
        self.assertTrue(all(order == occurrence_orders[0] for order in occurrence_orders))
        claimed_directory = self.state_root / "projects" / project / "claimed"
        self.assertEqual([path.name for path in claimed_directory.iterdir()], [claim_id])

        acknowledge_processes = self.run_while_lock_is_held(
            project,
            ["acknowledge", project, claim_id],
        )
        acknowledgement_results = self.assert_successful_json(acknowledge_processes)

        self.assertTrue(
            all(result == acknowledgement_results[0] for result in acknowledgement_results)
        )
        self.assertEqual(list(claimed_directory.iterdir()), [])
        acknowledged_directory = self.state_root / "projects" / project / "acknowledged"
        self.assertEqual(
            [path.name for path in acknowledged_directory.iterdir()],
            [claim_id],
        )

    def test_acknowledgement_retries_before_and_after_atomic_rename(self) -> None:
        for failure_point in ("before", "after"):
            with self.subTest(failure_point=failure_point):
                self.assert_acknowledgement_retry(failure_point)

    def assert_acknowledgement_retry(self, failure_point: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_root = Path(directory) / "state"
            with patch.dict(os.environ, {"SUMP_STATE_DIR": str(state_root)}):
                project = "interrupted-ack"
                self.store_occurrences(project, 1)
                claim = claim_project(project)
                claim_id = claim["claim_id"]
                registry = ProjectRegistry.from_environment(project)
                active_path = registry.paths.claimed / claim_id

                if failure_point == "before":
                    real_replace = os.replace

                    def interrupt_replace(
                        source: str | os.PathLike[str],
                        destination: str | os.PathLike[str],
                    ) -> None:
                        if Path(source) == active_path:
                            raise OSError("interrupted before acknowledgement rename")
                        real_replace(source, destination)

                    interruption = patch(
                        "sump._claims.os.replace",
                        side_effect=interrupt_replace,
                    )
                else:

                    def interrupt_sync(path: Path) -> None:
                        if path == registry.paths.claimed:
                            raise OSError("interrupted after acknowledgement rename")

                    interruption = patch(
                        "sump._claims._fsync_directory",
                        side_effect=interrupt_sync,
                    )

                with interruption, self.assertRaisesRegex(OSError, f"interrupted {failure_point}"):
                    acknowledge_claim(project, claim_id)

                result = acknowledge_claim(project, claim_id)
                self.assertTrue(result["acknowledged"])
                self.assertFalse(active_path.exists())
                self.assertEqual(
                    [path.name for path in registry.paths.acknowledged.iterdir()],
                    [claim_id],
                )


if __name__ == "__main__":
    unittest.main()
