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
    RegistryCorruptionError,
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


class StaleClaimError(RuntimeError):
    """A claim expired and its occurrences have been made eligible again."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_claim_timestamp(value: Any, field: str, metadata_path: Path) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RegistryCorruptionError(f"claim {field} is not a UTC timestamp: {metadata_path}")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise RegistryCorruptionError(
            f"claim {field} is not a UTC timestamp: {metadata_path}"
        ) from error
    return parsed


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


def _load_claim_metadata(metadata_path: Path) -> dict[str, Any]:
    try:
        serialized_metadata = metadata_path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise RegistryCorruptionError(f"claim metadata is missing: {metadata_path}") from error
    try:
        metadata = json.loads(serialized_metadata)
    except json.JSONDecodeError as error:
        raise RegistryCorruptionError(f"claim metadata is malformed: {metadata_path}") from error
    if not isinstance(metadata, dict):
        raise RegistryCorruptionError(f"claim metadata is not a JSON object: {metadata_path}")
    return metadata


def _read_active_claim(registry: ProjectRegistry, project: str) -> dict[str, Any] | None:
    claimed_directory = registry.paths.claimed
    if not claimed_directory.exists():
        return None

    claim_directories = sorted(claimed_directory.iterdir())
    if any(not path.is_dir() for path in claim_directories):
        raise RegistryCorruptionError(
            f"unexpected entry in active claims directory: {claimed_directory}"
        )
    if len(claim_directories) > 1:
        raise RegistryCorruptionError(f"project {project!r} has multiple active claims")
    if not claim_directories:
        return None

    claim_directory = claim_directories[0]
    metadata_path = claim_directory / CLAIM_METADATA_FILENAME
    metadata = _load_claim_metadata(metadata_path)
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise RegistryCorruptionError(f"unsupported claim metadata schema: {metadata_path}")
    if metadata.get("project") != project:
        raise RegistryCorruptionError(
            f"active claim project does not match {project!r}: {metadata_path}"
        )
    if metadata.get("claim_id") != claim_directory.name:
        raise RegistryCorruptionError(
            f"active claim ID does not match its directory: {metadata_path}"
        )
    claimed_at = _parse_claim_timestamp(metadata.get("claimed_at"), "claimed_at", metadata_path)
    expires_at = _parse_claim_timestamp(metadata.get("expires_at"), "expires_at", metadata_path)
    if expires_at - claimed_at != CLAIM_DURATION:
        raise RegistryCorruptionError(f"claim does not have a 30-minute lease: {metadata_path}")

    occurrence_filenames = metadata.get("occurrence_filenames")
    if not isinstance(occurrence_filenames, list) or not all(
        isinstance(filename, str) for filename in occurrence_filenames
    ):
        raise RegistryCorruptionError(f"invalid occurrence filename list: {metadata_path}")

    stored_filenames = sorted(
        path.name for path in claim_directory.iterdir() if path.name != CLAIM_METADATA_FILENAME
    )
    if sorted(occurrence_filenames) != stored_filenames:
        raise RegistryCorruptionError(
            f"active claim contents do not match metadata: {claim_directory}"
        )

    occurrences = [_read_occurrence(claim_directory / name) for name in occurrence_filenames]
    return _claim_response(project, metadata, occurrences)


def _validate_claim_id(claim_id: str) -> None:
    try:
        parsed_claim_id = uuid.UUID(hex=claim_id)
    except (ValueError, AttributeError) as error:
        raise ValueError("claim ID must be a 32-character lowercase UUID") from error
    if parsed_claim_id.hex != claim_id:
        raise ValueError("claim ID must be a 32-character lowercase UUID")


def _recover_staged_claims(registry: ProjectRegistry) -> None:
    staging_directory = registry.paths.staging
    if not staging_directory.exists():
        return

    staged_claims = sorted(staging_directory.iterdir())
    staged_envelopes: list[tuple[Path, Path]] = []
    metadata_paths: list[Path] = []
    destination_names = (
        {path.name for path in registry.paths.pending.iterdir()}
        if registry.paths.pending.exists()
        else set()
    )

    for staged_claim in staged_claims:
        if not staged_claim.is_dir():
            raise RegistryCorruptionError(f"unexpected staging entry: {staged_claim}")
        try:
            _validate_claim_id(staged_claim.name)
        except ValueError as error:
            raise RegistryCorruptionError(f"invalid staged claim ID: {staged_claim}") from error

        for staged_path in staged_claim.iterdir():
            if staged_path.name == CLAIM_METADATA_FILENAME:
                if not staged_path.is_file():
                    raise RegistryCorruptionError(
                        f"staged claim metadata is not a file: {staged_path}"
                    )
                metadata_paths.append(staged_path)
                continue
            if not staged_path.is_file():
                raise RegistryCorruptionError(f"unexpected staged claim entry: {staged_path}")
            try:
                _parse_occurrence_filename(staged_path)
            except ValueError as error:
                raise RegistryCorruptionError(
                    f"invalid staged occurrence: {staged_path}"
                ) from error
            if staged_path.name in destination_names:
                raise RegistryCorruptionError(
                    f"staged occurrence conflicts with pending: {staged_path.name}"
                )
            destination_names.add(staged_path.name)
            staged_envelopes.append((staged_path, registry.paths.pending / staged_path.name))

    if not staged_claims:
        return

    _ensure_private_directory(registry.paths.pending)
    for staged_path, pending_path in staged_envelopes:
        os.replace(staged_path, pending_path)
    for metadata_path in metadata_paths:
        metadata_path.unlink()
    for staged_claim in staged_claims:
        staged_claim.rmdir()

    _fsync_directory(registry.paths.pending)
    _fsync_directory(staging_directory)


def _record_expired_claim(
    registry: ProjectRegistry,
    claim_id: str,
    metadata: dict[str, Any],
) -> None:
    _ensure_private_directory(registry.paths.expired)
    expired_claim = registry.paths.expired / claim_id
    if expired_claim.exists() and not expired_claim.is_dir():
        raise RegistryCorruptionError(f"expired claim is not a directory: {expired_claim}")
    if expired_claim.exists() and not any(expired_claim.iterdir()):
        expired_claim.rmdir()
    if expired_claim.exists():
        recorded_metadata = _load_claim_metadata(expired_claim / CLAIM_METADATA_FILENAME)
        if recorded_metadata != metadata:
            raise RegistryCorruptionError(
                f"expired claim metadata does not match active claim: {expired_claim}"
            )
        return

    _ensure_private_directory(expired_claim)
    _write_claim_metadata(expired_claim / CLAIM_METADATA_FILENAME, metadata)
    _fsync_directory(expired_claim)
    _fsync_directory(registry.paths.expired)


def _expire_active_claim(
    registry: ProjectRegistry,
    project: str,
    current_time: datetime,
) -> None:
    active_claim = _read_active_claim(registry, project)
    if active_claim is None:
        return

    claim_id = active_claim["claim_id"]
    active_path = registry.paths.claimed / claim_id
    metadata = _load_claim_metadata(active_path / CLAIM_METADATA_FILENAME)
    expires_at = _parse_claim_timestamp(
        metadata.get("expires_at"),
        "expires_at",
        active_path / CLAIM_METADATA_FILENAME,
    )
    if current_time < expires_at:
        return

    _record_expired_claim(registry, claim_id, metadata)
    _ensure_private_directory(registry.paths.staging)
    staged_path = registry.paths.staging / claim_id
    if staged_path.exists():
        raise RegistryCorruptionError(f"expired claim conflicts with staged claim: {staged_path}")
    os.replace(active_path, staged_path)
    _fsync_directory(registry.paths.claimed)
    _fsync_directory(registry.paths.staging)
    _recover_staged_claims(registry)


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
    with registry.claim_lock():
        return _acknowledge_claim_locked(registry, project, claim_id, _now())


def _acknowledge_claim_locked(
    registry: ProjectRegistry,
    project: str,
    claim_id: str,
    current_time: datetime,
) -> dict[str, Any]:
    _recover_staged_claims(registry)
    _expire_active_claim(registry, project, current_time)
    active_path = registry.paths.claimed / claim_id
    acknowledged_path = registry.paths.acknowledged / claim_id

    if active_path.exists() and acknowledged_path.exists():
        raise RegistryCorruptionError(f"claim {claim_id!r} is both active and acknowledged")
    if acknowledged_path.exists():
        if not acknowledged_path.is_dir():
            raise RegistryCorruptionError(
                f"acknowledged claim is not a directory: {acknowledged_path}"
            )
        metadata = _load_claim_metadata(acknowledged_path / CLAIM_METADATA_FILENAME)
        if metadata.get("project") != project or metadata.get("claim_id") != claim_id:
            raise RegistryCorruptionError(
                f"acknowledged claim metadata does not match: {acknowledged_path}"
            )
        return _acknowledgement_response(project, claim_id)

    expired_path = registry.paths.expired / claim_id
    if expired_path.exists():
        if not expired_path.is_dir():
            raise RegistryCorruptionError(f"expired claim is not a directory: {expired_path}")
        metadata = _load_claim_metadata(expired_path / CLAIM_METADATA_FILENAME)
        if metadata.get("project") != project or metadata.get("claim_id") != claim_id:
            raise RegistryCorruptionError(f"expired claim metadata does not match: {expired_path}")
        raise StaleClaimError(f"claim {claim_id!r} expired and its occurrences are eligible again")

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
    with registry.claim_lock():
        return _claim_project_locked(registry, project, _now())


def _claim_project_locked(
    registry: ProjectRegistry,
    project: str,
    current_time: datetime,
) -> dict[str, Any]:
    _recover_staged_claims(registry)
    _expire_active_claim(registry, project, current_time)
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
    claimed_at = current_time
    claim_id = uuid.uuid4().hex
    staging_claim = registry.paths.staging / claim_id
    active_claim_path = registry.paths.claimed / claim_id

    for directory in (registry.paths.staging, registry.paths.claimed, staging_claim):
        _ensure_private_directory(directory)

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "claim_id": claim_id,
        "claimed_at": _format_timestamp(claimed_at),
        "expires_at": _format_timestamp(claimed_at + CLAIM_DURATION),
        "occurrence_filenames": [path.name for path in pending_paths],
    }
    _write_claim_metadata(staging_claim / CLAIM_METADATA_FILENAME, metadata)

    for pending_path in pending_paths:
        os.replace(pending_path, staging_claim / pending_path.name)

    _fsync_directory(pending_directory)
    _fsync_directory(staging_claim)
    os.replace(staging_claim, active_claim_path)
    _fsync_directory(registry.paths.staging)
    _fsync_directory(registry.paths.claimed)

    return _claim_response(project, metadata, occurrences)
