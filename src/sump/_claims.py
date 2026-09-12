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
        raise ValueError(f"invalid occurrence filename: {path.name}")

    stem = path.name.removesuffix(OCCURRENCE_SUFFIX)
    try:
        captured_at_text, occurrence_id = stem.rsplit("-", 1)
        captured_at = datetime.strptime(captured_at_text, OCCURRENCE_TIMESTAMP_FORMAT).replace(
            tzinfo=timezone.utc
        )
        parsed_id = uuid.UUID(hex=occurrence_id)
    except ValueError as error:
        raise ValueError(f"invalid occurrence filename: {path.name}") from error

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


def _claim_response(
    project: str,
    metadata: dict[str, Any],
    occurrences: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "claim_id": metadata["claim_id"],
        "claimed_at": metadata["claimed_at"],
        "expires_at": metadata["expires_at"],
        "occurrences": occurrences,
    }


def _read_active_claim(registry: ProjectRegistry, project: str) -> dict[str, Any] | None:
    claimed_directory = registry.paths.claimed
    if not claimed_directory.exists():
        return None

    claim_directories = sorted(claimed_directory.iterdir())
    if any(not path.is_dir() for path in claim_directories):
        raise ValueError(f"unexpected entry in active claims directory: {claimed_directory}")
    if len(claim_directories) > 1:
        raise ValueError(f"project {project!r} has multiple active claims")
    if not claim_directories:
        return None

    claim_directory = claim_directories[0]
    metadata_path = claim_directory / CLAIM_METADATA_FILENAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported claim metadata schema: {metadata_path}")
    if metadata.get("project") != project:
        raise ValueError(f"active claim project does not match {project!r}: {metadata_path}")
    if metadata.get("claim_id") != claim_directory.name:
        raise ValueError(f"active claim ID does not match its directory: {metadata_path}")

    occurrence_filenames = metadata.get("occurrence_filenames")
    if not isinstance(occurrence_filenames, list) or not all(
        isinstance(filename, str) for filename in occurrence_filenames
    ):
        raise ValueError(f"invalid occurrence filename list: {metadata_path}")

    stored_filenames = sorted(
        path.name for path in claim_directory.iterdir() if path.name != CLAIM_METADATA_FILENAME
    )
    if sorted(occurrence_filenames) != stored_filenames:
        raise ValueError(f"active claim contents do not match metadata: {claim_directory}")

    occurrences = [_read_occurrence(claim_directory / name) for name in occurrence_filenames]
    return _claim_response(project, metadata, occurrences)


def _validate_claim_id(claim_id: str) -> None:
    try:
        parsed_claim_id = uuid.UUID(hex=claim_id)
    except (ValueError, AttributeError) as error:
        raise ValueError("claim ID must be a 32-character lowercase UUID") from error
    if parsed_claim_id.hex != claim_id:
        raise ValueError("claim ID must be a 32-character lowercase UUID")


def _acknowledgement_response(project: str, claim_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "claim_id": claim_id,
        "acknowledged": True,
    }


def acknowledge_claim(project: str, claim_id: str) -> dict[str, Any]:
    """Retain an active claim under acknowledged storage."""
    validate_project(project)
    _validate_claim_id(claim_id)
    registry = ProjectRegistry.from_environment(project)
    active_path = registry.paths.claimed / claim_id
    acknowledged_path = registry.paths.acknowledged / claim_id

    if active_path.exists() and acknowledged_path.exists():
        raise ValueError(f"claim {claim_id!r} is both active and acknowledged")
    if acknowledged_path.exists():
        if not acknowledged_path.is_dir():
            raise ValueError(f"acknowledged claim is not a directory: {acknowledged_path}")
        metadata = json.loads(
            (acknowledged_path / CLAIM_METADATA_FILENAME).read_text(encoding="utf-8")
        )
        if metadata.get("project") != project or metadata.get("claim_id") != claim_id:
            raise ValueError(f"acknowledged claim metadata does not match: {acknowledged_path}")
        return _acknowledgement_response(project, claim_id)

    active_claim = _read_active_claim(registry, project)
    if active_claim is None or active_claim["claim_id"] != claim_id:
        raise FileNotFoundError(f"claim {claim_id!r} not found for project {project!r}")

    _ensure_private_directory(registry.paths.acknowledged)
    os.replace(active_path, acknowledged_path)
    _fsync_directory(registry.paths.claimed)
    _fsync_directory(registry.paths.acknowledged)
    return _acknowledgement_response(project, claim_id)


def claim_project(project: str) -> dict[str, Any]:
    """Return an active claim or claim up to the oldest 100 pending occurrences."""
    validate_project(project)
    registry = ProjectRegistry.from_environment(project)
    active_claim = _read_active_claim(registry, project)
    if active_claim is not None:
        return active_claim

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

    return _claim_response(project, metadata, occurrences)
