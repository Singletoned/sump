"""Claim pending Sentry occurrences for coding-agent collection."""

import base64
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sentry_sdk.envelope import Envelope

from sump._registry import (
    FILE_MODE,
    ProjectRegistry,
    _ensure_private_directory,
    _fsync_directory,
)
from sump._sdk import validate_project

SCHEMA_VERSION = 1
CLAIM_LIMIT = 100
CLAIM_DURATION = timedelta(minutes=30)
CLAIM_METADATA_FILENAME = "claim.json"
OCCURRENCE_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S.%fZ"
OCCURRENCE_SUFFIX = ".envelope"


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_occurrence_filename(path: Path) -> tuple[str, str]:
    if not path.name.endswith(OCCURRENCE_SUFFIX):
        raise ValueError(f"invalid pending occurrence filename: {path.name}")

    stem = path.name.removesuffix(OCCURRENCE_SUFFIX)
    try:
        captured_at_text, occurrence_id = stem.rsplit("-", 1)
        captured_at = datetime.strptime(captured_at_text, OCCURRENCE_TIMESTAMP_FORMAT).replace(
            tzinfo=timezone.utc
        )
        parsed_id = uuid.UUID(hex=occurrence_id)
    except ValueError as error:
        raise ValueError(f"invalid pending occurrence filename: {path.name}") from error

    return _format_timestamp(captured_at), parsed_id.hex


def _attachment_record(item: Any) -> dict[str, Any]:
    return {
        "filename": item.headers.get("filename"),
        "content_type": item.headers.get("content_type"),
        "content_base64": base64.b64encode(item.get_bytes()).decode("ascii"),
    }


def _read_occurrence(path: Path) -> dict[str, Any]:
    captured_at, occurrence_id = _parse_occurrence_filename(path)
    envelope = Envelope.deserialize(path.read_bytes())
    event = envelope.get_event()
    if event is None:
        raise ValueError(f"pending occurrence has no event item: {path}")

    return {
        "occurrence_id": occurrence_id,
        "captured_at": captured_at,
        "envelope_headers": envelope.headers,
        "event": event,
        "attachments": [
            _attachment_record(item) for item in envelope.items if item.type == "attachment"
        ],
    }


def _empty_claim(project: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "claim_id": None,
        "claimed_at": None,
        "expires_at": None,
        "occurrences": [],
    }


def _write_claim_metadata(path: Path, metadata: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, FILE_MODE)
    with os.fdopen(descriptor, "w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, sort_keys=True, separators=(",", ":"))
        metadata_file.write("\n")
        metadata_file.flush()
        os.fsync(metadata_file.fileno())


def claim_project(project: str) -> dict[str, Any]:
    """Claim up to the oldest 100 pending occurrences for a project."""
    validate_project(project)
    registry = ProjectRegistry.from_environment(project)
    pending_directory = registry.paths.pending
    if not pending_directory.exists():
        return _empty_claim(project)

    pending_paths = sorted(pending_directory.iterdir())[:CLAIM_LIMIT]
    if not pending_paths:
        return _empty_claim(project)

    occurrences = [_read_occurrence(path) for path in pending_paths]
    claimed_at = datetime.now(timezone.utc)
    claim_id = uuid.uuid4().hex
    claim_directory = registry.paths.claimed / claim_id

    for directory in (registry.paths.claimed, claim_directory):
        _ensure_private_directory(directory)

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "claim_id": claim_id,
        "claimed_at": _format_timestamp(claimed_at),
        "expires_at": _format_timestamp(claimed_at + CLAIM_DURATION),
        "occurrence_filenames": [path.name for path in pending_paths],
    }
    _write_claim_metadata(claim_directory / CLAIM_METADATA_FILENAME, metadata)

    for pending_path in pending_paths:
        os.replace(pending_path, claim_directory / pending_path.name)

    _fsync_directory(pending_directory)
    _fsync_directory(claim_directory)
    _fsync_directory(registry.paths.claimed)

    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "claim_id": claim_id,
        "claimed_at": metadata["claimed_at"],
        "expires_at": metadata["expires_at"],
        "occurrences": occurrences,
    }
