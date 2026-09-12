"""Durable filesystem storage for captured Sentry envelopes."""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from platformdirs import user_state_path
from sentry_sdk.envelope import Envelope

STATE_DIRECTORY_ENVIRONMENT_VARIABLE = "SUMP_STATE_DIR"
DIRECTORY_MODE = 0o700
FILE_MODE = 0o600


@dataclass(frozen=True)
class ProjectPaths:
    """Filesystem locations used by one project registry."""

    root: Path
    temporary: Path
    projects: Path
    project: Path
    pending: Path
    claimed: Path


def resolve_state_root() -> Path:
    """Resolve the central state root without creating it."""
    configured_root = os.environ.get(STATE_DIRECTORY_ENVIRONMENT_VARIABLE)
    if configured_root is None:
        return user_state_path("sump", appauthor=False)
    if configured_root == "":
        raise ValueError(f"{STATE_DIRECTORY_ENVIRONMENT_VARIABLE} must not be empty")

    root = Path(configured_root).expanduser()
    if not root.is_absolute():
        raise ValueError(f"{STATE_DIRECTORY_ENVIRONMENT_VARIABLE} must be an absolute path")
    return root


def project_paths(root: Path, project: str) -> ProjectPaths:
    """Return all storage paths used to capture events for a project."""
    projects_directory = root / "projects"
    project_directory = projects_directory / project
    return ProjectPaths(
        root=root,
        temporary=root / "tmp",
        projects=projects_directory,
        project=project_directory,
        pending=project_directory / "pending",
        claimed=project_directory / "claimed",
    )


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=DIRECTORY_MODE, parents=True, exist_ok=True)
    path.chmod(DIRECTORY_MODE)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _occurrence_filename() -> str:
    captured_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return f"{captured_at}-{uuid.uuid4().hex}.envelope"


class ProjectRegistry:
    """Store complete event envelopes for one project."""

    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    @classmethod
    def from_environment(cls, project: str) -> "ProjectRegistry":
        """Create a project registry from the central state configuration."""
        return cls(project_paths(resolve_state_root(), project))

    def store(self, envelope: Envelope) -> Path | None:
        """Store an event envelope durably, or ignore a non-event envelope."""
        if envelope.get_event() is None:
            return None

        self._ensure_directories()
        filename = _occurrence_filename()
        temporary_path = self.paths.temporary / f"{filename}.tmp"
        pending_path = self.paths.pending / filename

        descriptor = os.open(
            temporary_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            FILE_MODE,
        )
        with os.fdopen(descriptor, "wb") as temporary_file:
            envelope.serialize_into(temporary_file)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, pending_path)
        _fsync_directory(self.paths.pending)
        return pending_path

    def _ensure_directories(self) -> None:
        for directory in (
            self.paths.root,
            self.paths.temporary,
            self.paths.projects,
            self.paths.project,
            self.paths.pending,
        ):
            _ensure_private_directory(directory)
