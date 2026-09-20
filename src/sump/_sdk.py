"""Application-facing Sentry SDK initialization."""

import re
from collections.abc import Mapping
from contextlib import AbstractContextManager
from typing import Any

import sentry_sdk

from sump._transport import LocalTransport

PROJECT_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,61}[a-z0-9])?$")
MANAGED_SENTRY_OPTIONS = frozenset({"dsn", "transport"})


def validate_project(project: str) -> None:
    """Validate a project identifier for use as a registry directory name."""
    if not isinstance(project, str):
        raise TypeError("project must be a string")
    if PROJECT_PATTERN.fullmatch(project) is None:
        raise ValueError(
            "project must be a lowercase ASCII slug of 1-63 letters, numbers, dots, "
            "underscores, or hyphens, starting and ending with a letter or number"
        )


def init(project: str, **sentry_options: Any) -> AbstractContextManager[Any]:
    """Initialize the Sentry SDK with Sump's local-only transport."""
    validate_project(project)

    conflicting_options = MANAGED_SENTRY_OPTIONS.intersection(sentry_options)
    if conflicting_options:
        names = ", ".join(sorted(conflicting_options))
        raise TypeError(f"sump.init manages these Sentry options: {names}")

    return sentry_sdk.init(
        transport=LocalTransport(project),
        **sentry_options,
    )


def capture_message(project: str, message: str, context: Mapping[str, Any]) -> str:
    """Capture a local error-level message for non-Python SDK callers."""
    if not isinstance(message, str):
        raise TypeError("message must be a string")
    if not message:
        raise ValueError("message must not be empty")

    init(project, default_integrations=False, environment="development")
    with sentry_sdk.isolation_scope() as scope:
        scope.set_context("sump", dict(context))
        event_id = sentry_sdk.capture_message(message, level="error")

    if event_id is None:
        raise RuntimeError("Sentry did not return an event ID")
    return event_id
