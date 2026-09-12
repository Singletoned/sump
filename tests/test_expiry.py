"""Tests for deterministic active-claim expiry."""

import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from sentry_sdk.envelope import Envelope

from sump._claims import (
    CLAIM_METADATA_FILENAME,
    StaleClaimError,
    acknowledge_claim,
    claim_project,
)
from sump._registry import ProjectRegistry


class ClaimExpiryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_root = Path(self.temporary_directory.name) / "state"
        environment = patch.dict(os.environ, {"SUMP_STATE_DIR": str(self.state_root)})
        environment.start()
        self.addCleanup(environment.stop)
        self.claimed_at = datetime(2026, 2, 3, 4, 5, 6, tzinfo=timezone.utc)

    def store_occurrence(self, message: str, number: int) -> None:
        envelope = Envelope()
        envelope.add_event({"message": message})
        filename = f"20260203T040000.000000Z-{uuid.UUID(int=number + 1).hex}.envelope"
        with patch("sump._registry._occurrence_filename", return_value=filename):
            ProjectRegistry.from_environment("example-app").store(envelope)

    def create_claim(self) -> dict[str, object]:
        with patch("sump._claims._now", return_value=self.claimed_at):
            return claim_project("example-app")

    def test_active_claim_is_unchanged_during_thirty_minute_lease(self) -> None:
        self.store_occurrence("leased event", 1)
        original_claim = self.create_claim()
        before_expiry = self.claimed_at + timedelta(minutes=30) - timedelta(microseconds=1)

        with patch("sump._claims._now", return_value=before_expiry):
            redelivered_claim = claim_project("example-app")

        self.assertEqual(redelivered_claim, original_claim)
        self.assertEqual(redelivered_claim["claimed_at"], "2026-02-03T04:05:06Z")
        self.assertEqual(redelivered_claim["expires_at"], "2026-02-03T04:35:06Z")

        with patch(
            "sump._claims._now",
            return_value=self.claimed_at + timedelta(minutes=30),
        ):
            replacement_claim = claim_project("example-app")

        self.assertNotEqual(replacement_claim["claim_id"], original_claim["claim_id"])
        self.assertEqual(replacement_claim["occurrences"], original_claim["occurrences"])

    def test_expired_claim_is_recovered_and_old_id_is_stale(self) -> None:
        self.store_occurrence("first expired event", 1)
        self.store_occurrence("second expired event", 2)
        original_claim = self.create_claim()
        original_metadata_path = (
            self.state_root
            / "projects"
            / "example-app"
            / "claimed"
            / original_claim["claim_id"]
            / CLAIM_METADATA_FILENAME
        )
        original_metadata = json.loads(original_metadata_path.read_text())
        expiry_time = self.claimed_at + timedelta(minutes=30)

        with (
            patch("sump._claims._now", return_value=expiry_time),
            self.assertRaisesRegex(StaleClaimError, "expired.*eligible again"),
        ):
            acknowledge_claim("example-app", original_claim["claim_id"])

        pending_directory = self.state_root / "projects" / "example-app" / "pending"
        self.assertEqual(len(list(pending_directory.iterdir())), 2)
        expired_metadata_path = (
            self.state_root
            / "projects"
            / "example-app"
            / "expired"
            / original_claim["claim_id"]
            / CLAIM_METADATA_FILENAME
        )
        self.assertEqual(json.loads(expired_metadata_path.read_text()), original_metadata)

        with patch("sump._claims._now", return_value=expiry_time):
            replacement_claim = claim_project("example-app")

        self.assertNotEqual(replacement_claim["claim_id"], original_claim["claim_id"])
        self.assertEqual(
            [item["occurrence_id"] for item in replacement_claim["occurrences"]],
            [item["occurrence_id"] for item in original_claim["occurrences"]],
        )
        self.assertEqual(
            [item["event"] for item in replacement_claim["occurrences"]],
            [item["event"] for item in original_claim["occurrences"]],
        )

        with (
            patch("sump._claims._now", return_value=expiry_time),
            self.assertRaises(StaleClaimError),
        ):
            acknowledge_claim("example-app", original_claim["claim_id"])


if __name__ == "__main__":
    unittest.main()
