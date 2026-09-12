"""Compatibility contract for supported Sentry SDK 2.x releases."""

import socket
import unittest
from unittest.mock import patch

import sentry_sdk
from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport


class RecordingTransport(Transport):
    """Keep captured envelopes in memory for contract assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.envelopes: list[Envelope] = []

    def capture_envelope(self, envelope: Envelope) -> None:
        self.envelopes.append(envelope)


class FailingTransport(Transport):
    """Represent a local storage transport that cannot write."""

    def __init__(self) -> None:
        super().__init__()

    def capture_envelope(self, envelope: Envelope) -> None:
        raise OSError("local registry write failed")


class SentryTransportContractTests(unittest.TestCase):
    def test_custom_transport_receives_event_without_dsn_or_network(self) -> None:
        transport = RecordingTransport()

        with (
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network access attempted"),
            ),
            sentry_sdk.init(transport=transport, default_integrations=False),
        ):
            sentry_sdk.capture_message("contract event")

        self.assertIsNone(transport.parsed_dsn)
        self.assertEqual(len(transport.envelopes), 1)
        self.assertEqual(transport.envelopes[0].get_event()["message"], "contract event")

    def test_event_and_attachment_survive_envelope_serialization(self) -> None:
        transport = RecordingTransport()

        with (
            sentry_sdk.init(transport=transport, default_integrations=False),
            sentry_sdk.isolation_scope() as scope,
        ):
            scope.add_attachment(
                bytes=b"attachment contents",
                filename="diagnostic.txt",
                content_type="text/plain",
            )
            sentry_sdk.capture_message("event with attachment")

        restored = Envelope.deserialize(transport.envelopes[0].serialize())
        event = restored.get_event()
        attachments = [item for item in restored.items if item.type == "attachment"]

        self.assertIsNotNone(event)
        self.assertEqual(event["message"], "event with attachment")
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].headers["filename"], "diagnostic.txt")
        self.assertEqual(attachments[0].headers["content_type"], "text/plain")
        self.assertEqual(attachments[0].get_bytes(), b"attachment contents")

    def test_transport_write_error_propagates_to_capture_caller(self) -> None:
        with (
            sentry_sdk.init(transport=FailingTransport(), default_integrations=False),
            self.assertRaisesRegex(OSError, "local registry write failed"),
        ):
            sentry_sdk.capture_message("event that cannot be stored")


if __name__ == "__main__":
    unittest.main()
