"""Tests for durable local envelope storage."""

import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sentry_sdk
from sentry_sdk.envelope import Envelope

import sump
from sump._registry import ProjectRegistry
from sump._transport import LocalTransport


class PartialEnvelope:
    """Write an incomplete payload before simulating serialization failure."""

    def get_event(self) -> dict[str, str]:
        return {"message": "partial"}

    def serialize_into(self, output: object) -> None:
        output.write(b"partial")  # type: ignore[attr-defined]
        raise OSError("serialization failed")


class ProjectRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_root = Path(self.temporary_directory.name) / "state"
        environment = patch.dict("os.environ", {"SUMP_STATE_DIR": str(self.state_root)})
        environment.start()
        self.addCleanup(environment.stop)

    def pending_files(self, project: str = "example-app") -> list[Path]:
        pending = self.state_root / "projects" / project / "pending"
        if not pending.exists():
            return []
        return sorted(pending.iterdir())

    def test_captured_exception_and_message_create_separate_occurrences(self) -> None:
        with sump.init("example-app", default_integrations=False):
            try:
                raise RuntimeError("example exception")
            except RuntimeError:
                sentry_sdk.capture_exception()
            sentry_sdk.capture_message("example message")

        pending_files = self.pending_files()
        self.assertEqual(len(pending_files), 2)
        messages = [Envelope.deserialize(path.read_bytes()).get_event() for path in pending_files]
        self.assertTrue(any(event.get("message") == "example message" for event in messages))
        self.assertTrue(any("exception" in event for event in messages))

    def test_non_event_envelope_is_ignored(self) -> None:
        transport = LocalTransport("example-app")

        transport.capture_envelope(Envelope())

        self.assertEqual(self.pending_files(), [])
        self.assertFalse(self.state_root.exists())

    def test_stored_envelope_preserves_event_and_attachment(self) -> None:
        with (
            sump.init("example-app", default_integrations=False),
            sentry_sdk.isolation_scope() as scope,
        ):
            scope.add_attachment(
                bytes=b"diagnostic contents",
                filename="diagnostic.txt",
                content_type="text/plain",
            )
            sentry_sdk.capture_message("attached message")

        stored = Envelope.deserialize(self.pending_files()[0].read_bytes())
        attachments = [item for item in stored.items if item.type == "attachment"]
        self.assertEqual(stored.get_event()["message"], "attached message")
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].headers["filename"], "diagnostic.txt")
        self.assertEqual(attachments[0].get_bytes(), b"diagnostic contents")

    def test_partial_serialization_never_becomes_pending(self) -> None:
        registry = ProjectRegistry.from_environment("example-app")

        with self.assertRaisesRegex(OSError, "serialization failed"):
            registry.store(PartialEnvelope())  # type: ignore[arg-type]

        self.assertEqual(self.pending_files(), [])
        self.assertEqual(len(list((self.state_root / "tmp").iterdir())), 1)

    def test_registry_permissions_are_private(self) -> None:
        envelope = Envelope()
        envelope.add_event({"message": "private"})

        stored_path = ProjectRegistry.from_environment("example-app").store(envelope)

        self.assertIsNotNone(stored_path)
        directories = (
            self.state_root,
            self.state_root / "tmp",
            self.state_root / "projects",
            self.state_root / "projects" / "example-app",
            self.state_root / "projects" / "example-app" / "pending",
        )
        for directory in directories:
            with self.subTest(directory=directory):
                self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(stored_path.stat().st_mode), 0o600)

    def test_permission_failure_propagates_without_pending_record(self) -> None:
        envelope = Envelope()
        envelope.add_event({"message": "permission failure"})

        with (
            patch("sump._registry.os.open", side_effect=PermissionError("permission denied")),
            self.assertRaisesRegex(PermissionError, "permission denied"),
        ):
            ProjectRegistry.from_environment("example-app").store(envelope)

        self.assertEqual(self.pending_files(), [])

    def test_disk_sync_failure_propagates_without_pending_record(self) -> None:
        envelope = Envelope()
        envelope.add_event({"message": "disk failure"})

        with (
            patch("sump._registry.os.fsync", side_effect=OSError("disk sync failed")),
            self.assertRaisesRegex(OSError, "disk sync failed"),
        ):
            ProjectRegistry.from_environment("example-app").store(envelope)

        self.assertEqual(self.pending_files(), [])

    def test_state_root_that_is_a_file_fails_plainly(self) -> None:
        self.state_root.parent.mkdir(parents=True, exist_ok=True)
        self.state_root.write_text("not a directory")
        envelope = Envelope()
        envelope.add_event({"message": "bad path"})

        with self.assertRaises((FileExistsError, NotADirectoryError)):
            ProjectRegistry.from_environment("example-app").store(envelope)

    def test_relative_state_root_is_rejected(self) -> None:
        with (
            patch.dict("os.environ", {"SUMP_STATE_DIR": "relative/state"}),
            self.assertRaisesRegex(ValueError, "absolute path"),
        ):
            ProjectRegistry.from_environment("example-app")

    def test_empty_state_root_is_rejected(self) -> None:
        with (
            patch.dict("os.environ", {"SUMP_STATE_DIR": ""}),
            self.assertRaisesRegex(ValueError, "must not be empty"),
        ):
            ProjectRegistry.from_environment("example-app")


if __name__ == "__main__":
    unittest.main()
