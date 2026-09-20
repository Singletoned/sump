"""Record Sentry SDK errors in a machine-local registry."""

from sump._sdk import capture_message, init

__all__ = ["capture_message", "init"]
