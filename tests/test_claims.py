"""Tests for claiming pending Sentry occurrences."""

import base64
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

from sentry_sdk.envelope import Envelope, Item

from sump._claims import CLAIM_METADATA_FILENAME, claim_project
from sump._registry import ProjectRegistry
from sump.cli import main


class ClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_root = Path(self.temporary_directory.name) / "state"
        environment = patch.dict(os.environ, {"SUMP_STATE_DIR": str(self.state_root)})
        environment.start()
        self.addCleanup(environment.stop)

    def store_occurrence(
        self,
        project: str,
        message: str,
        captured_at: datetime,
        occurrence_number: int,
        attachment: bytes | None = None,
    ) -> Path:
        envelope = Envelope(headers={"event_id": f"event-{occurrence_number}"})
        envelope.add_event({"message": message, "sequence": occurrence_number})
        if attachment is not None:
            envelope.add_item(
                Item(
                    payload=attachment,
                    type="attachment",
                    filename="diagnostic.bin",
                    content_type="application/octet-stream",
                )
            )
        filename = (
            f"{captured_at.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-"
            f"{uuid.UUID(int=occurrence_number + 1).hex}.envelope"
        )
        with patch("sump._registry._occurrence_filename", return_value=filename):
            stored_path = ProjectRegistry.from_environment(project).store(envelope)
        self.assertIsNotNone(stored_path)
        return stored_path

    def test_claim_command_returns_versioned_event_and_attachment_json(self) -> None:
        captured_at = datetime(2026, 1, 2, 3, 4, 5, 6000, tzinfo=timezone.utc)
        self.store_occurrence(
            "example-app",
            "attached event",
            captured_at,
            occurrence_number=7,
            attachment=b"binary contents",
        )
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["claim", "example-app"])

        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["project"], "example-app")
        self.assertIsInstance(result["claim_id"], str)
        self.assertIsInstance(result["claimed_at"], str)
        self.assertIsInstance(result["expires_at"], str)
        self.assertEqual(len(result["occurrences"]), 1)

        occurrence = result["occurrences"][0]
        self.assertEqual(occurrence["occurrence_id"], uuid.UUID(int=8).hex)
        self.assertEqual(occurrence["captured_at"], "2026-01-02T03:04:05.006000Z")
        self.assertEqual(occurrence["envelope_headers"], {"event_id": "event-7"})
        self.assertEqual(occurrence["event"]["message"], "attached event")
        self.assertEqual(len(occurrence["attachments"]), 1)
        attachment = occurrence["attachments"][0]
        self.assertEqual(attachment["filename"], "diagnostic.bin")
        self.assertEqual(attachment["content_type"], "application/octet-stream")
        self.assertEqual(base64.b64decode(attachment["content_base64"]), b"binary contents")

        claim_directory = (
            self.state_root / "projects" / "example-app" / "claimed" / result["claim_id"]
        )
        metadata = json.loads((claim_directory / CLAIM_METADATA_FILENAME).read_text())
        self.assertEqual(metadata["claim_id"], result["claim_id"])
        self.assertEqual(metadata["project"], "example-app")

    def test_claim_contains_only_oldest_hundred_for_requested_project(self) -> None:
        first_capture = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for sequence in range(101):
            self.store_occurrence(
                "example-app",
                f"event-{sequence}",
                first_capture + timedelta(seconds=sequence),
                occurrence_number=sequence,
            )
        self.store_occurrence(
            "other-app",
            "other project event",
            first_capture,
            occurrence_number=500,
        )

        result = claim_project("example-app")

        self.assertEqual(len(result["occurrences"]), 100)
        self.assertEqual(
            [occurrence["event"]["sequence"] for occurrence in result["occurrences"]],
            list(range(100)),
        )
        example_pending = self.state_root / "projects" / "example-app" / "pending"
        other_pending = self.state_root / "projects" / "other-app" / "pending"
        self.assertEqual(len(list(example_pending.iterdir())), 1)
        self.assertEqual(len(list(other_pending.iterdir())), 1)

    def test_empty_project_returns_versioned_empty_claim(self) -> None:
        self.assertEqual(
            claim_project("empty-project"),
            {
                "schema_version": 1,
                "project": "empty-project",
                "claim_id": None,
                "claimed_at": None,
                "expires_at": None,
                "occurrences": [],
            },
        )

    def test_malformed_envelope_command_fails_with_traceback(self) -> None:
        stored_path = self.store_occurrence(
            "example-app",
            "will be malformed",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            occurrence_number=1,
        )
        stored_path.write_bytes(b"not a Sentry envelope")
        command = Path(sys.executable).parent / "sump"

        completed = subprocess.run(
            [command, "claim", "example-app"],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("Traceback", completed.stderr)
        self.assertIn("JSONDecodeError", completed.stderr)


if __name__ == "__main__":
    unittest.main()
