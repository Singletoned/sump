"""Sentry transport configured for local Sump projects."""

from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport


class LocalTransport(Transport):
    """Receive Sentry envelopes for one local project."""

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project

    def capture_envelope(self, envelope: Envelope) -> None:
        """Capture an envelope once registry storage is available."""
        raise RuntimeError("Sump envelope storage is not implemented")
