"""Tests for acknowledging and retaining error claims."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from sentry_sdk.envelope import Envelope

from sump._claims import CLAIM_METADATA_FILENAME, claim_project
from sump._registry import ProjectRegistry
from sump.cli import main


class AcknowledgementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_root = Path(self.temporary_directory.name) / "state"
        environment = patch.dict(os.environ, {"SUMP_STATE_DIR": str(self.state_root)})
        environment.start()
        self.addCleanup(environment.stop)

    def store_occurrence(self, message: str, captured_at: datetime, number: int) -> Path:
        envelope = Envelope()
        envelope.add_event({"message": message})
        filename = (
            f"{captured_at.strftime('%Y%m%dT%H%M%S.%fZ')}-{uuid.UUID(int=number + 1).hex}.envelope"
        )
        with patch("sump._registry._occurrence_filename", return_value=filename):
            path = ProjectRegistry.from_environment("example-app").store(envelope)
        self.assertIsNotNone(path)
        return path

    def test_acknowledgement_retains_claim_and_excludes_it_from_later_claims(self) -> None:
        first_capture = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.store_occurrence("acknowledged event", first_capture, 1)
        claim = claim_project("example-app")
        active_path = self.state_root / "projects" / "example-app" / "claimed" / claim["claim_id"]
        original_files = {
            path.name: path.read_bytes() for path in active_path.iterdir() if path.is_file()
        }
        self.store_occurrence("later event", first_capture + timedelta(seconds=1), 2)
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["acknowledge", "example-app", claim["claim_id"]])

        expected_response = {
            "schema_version": 1,
            "project": "example-app",
            "claim_id": claim["claim_id"],
            "acknowledged": True,
        }
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue()), expected_response)
        self.assertFalse(active_path.exists())

        acknowledged_path = (
            self.state_root / "projects" / "example-app" / "acknowledged" / claim["claim_id"]
        )
        self.assertTrue((acknowledged_path / CLAIM_METADATA_FILENAME).is_file())
        retained_files = {
            path.name: path.read_bytes() for path in acknowledged_path.iterdir() if path.is_file()
        }
        self.assertEqual(retained_files, original_files)

        next_claim = claim_project("example-app")
        self.assertEqual(len(next_claim["occurrences"]), 1)
        self.assertEqual(next_claim["occurrences"][0]["event"]["message"], "later event")

    def test_repeated_acknowledgement_returns_same_success(self) -> None:
        self.store_occurrence(
            "repeat acknowledgement", datetime(2026, 1, 1, tzinfo=timezone.utc), 1
        )
        claim = claim_project("example-app")
        first_output = StringIO()
        second_output = StringIO()

        with redirect_stdout(first_output):
            main(["acknowledge", "example-app", claim["claim_id"]])
        with redirect_stdout(second_output):
            main(["acknowledge", "example-app", claim["claim_id"]])

        self.assertEqual(json.loads(first_output.getvalue()), json.loads(second_output.getvalue()))

    def test_unknown_project_and_claim_fail_commands_with_tracebacks(self) -> None:
        self.store_occurrence("active event", datetime(2026, 1, 1, tzinfo=timezone.utc), 1)
        known_claim = claim_project("example-app")
        command = Path(sys.executable).parent / "sump"
        cases = (
            ("unknown-project", uuid.uuid4().hex),
            ("example-app", uuid.uuid4().hex),
        )

        for project, claim_id in cases:
            with self.subTest(project=project, claim_id=claim_id):
                completed = subprocess.run(
                    [command, "acknowledge", project, claim_id],
                    env=os.environ.copy(),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(completed.stdout, "")
                self.assertIn("Traceback", completed.stderr)
                self.assertIn("FileNotFoundError", completed.stderr)

        self.assertEqual(claim_project("example-app")["claim_id"], known_claim["claim_id"])


if __name__ == "__main__":
    unittest.main()
