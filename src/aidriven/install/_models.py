"""Data model: enums and dataclasses for the install subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Scope(StrEnum):
    PROJECT = "project"
    USER = "user"


class InstallMode(StrEnum):
    SYMLINK = "symlink"
    COPY = "copy"


class ArtifactType(StrEnum):
    SKILL = "skill"


class PerTargetAction(StrEnum):
    INSTALL_NEW = "install_new"
    UPDATE = "update"
    SKIP_IDENTICAL = "skip_identical"
    CONFLICT = "conflict"
    INCOMPATIBLE = "incompatible"


# ---------------------------------------------------------------------------
# Value objects (frozen)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AITarget:
    name: str
    project_read_path: str
    user_read_path: str
    autodetect_markers: tuple[str, ...]


@dataclass(frozen=True)
class ManifestEntry:
    name: str
    type: ArtifactType
    path_in_repo: str
    content_hash: str
    compatible_targets: frozenset[str]
    description: str


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    source_commit_sha: str
    entries: Mapping[tuple[ArtifactType, str], ManifestEntry]


@dataclass(frozen=True)
class ProjectContext:
    cwd: Path
    project_root: Path
    user_home: Path
    cache_dir: Path


# ---------------------------------------------------------------------------
# Request / Plan / Result
# ---------------------------------------------------------------------------


@dataclass
class InstallRequest:
    artifact_type: ArtifactType
    name: str
    targets: tuple[str, ...]
    scope: Scope = Scope.PROJECT
    mode: InstallMode = InstallMode.SYMLINK
    force: bool = False
    dry_run: bool = False
    assume_yes: bool = False
    no_cache: bool = False


@dataclass
class PlannedTarget:
    target: AITarget
    canonical_path: Path | None
    read_path: Path
    needs_symlink: bool
    action: PerTargetAction
    existing_hash: str | None
    reason: str | None


@dataclass
class InstallPlan:
    request: InstallRequest
    manifest_entry: ManifestEntry
    source_commit_sha: str
    expected_content_hash: str
    targets: tuple[PlannedTarget, ...]
    overall_status: Literal["ready", "blocked", "noop"]


@dataclass
class PerTargetResult:
    target_name: str
    action_taken: PerTargetAction
    final_mode: InstallMode
    read_path: Path
    canonical_path: Path | None
    error: str | None


@dataclass
class InstallResult:
    request: InstallRequest
    plan: InstallPlan
    target_results: tuple[PerTargetResult, ...]
    lockfile_path: Path
    success: bool
    exit_code: int


# ---------------------------------------------------------------------------
# Lockfile persistence
# ---------------------------------------------------------------------------


@dataclass
class LockfileEntry:
    source: str
    source_commit_sha: str
    computed_hash: str
    targets: tuple[str, ...]
    scope: Scope
    install_mode: InstallMode


@dataclass
class Lockfile:
    version: int = 1
    skills: dict[str, LockfileEntry] = field(default_factory=dict)
