"""Sentry transport configured for local Sump projects."""

from typing import Any

from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport

from sump._registry import ProjectRegistry


class LocalTransport(Transport):
    """Store Sentry event envelopes for one local project."""

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project
        self.registry = ProjectRegistry.from_environment(project)

    def capture_envelope(self, envelope: Envelope) -> None:
        """Store an event envelope synchronously."""
        self.registry.store(envelope)

    def flush(self, timeout: float, callback: Any | None = None) -> None:
        """Return immediately because captures are synchronous."""

    def kill(self) -> None:
        """Return immediately because the transport has no worker."""
