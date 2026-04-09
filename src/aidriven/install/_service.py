"""Orchestrated install service — library entrypoint for the install operation."""

from __future__ import annotations

import logging
import re
import shutil
import sys
from typing import TYPE_CHECKING

from aidriven.install._archive import IntegrityError, extract_skill, fetch_tarball

if TYPE_CHECKING:
    from pathlib import Path
from aidriven.install._github import resolve_head_sha
from aidriven.install._hashing import hash_directory
from aidriven.install._installer import execute_plan
from aidriven.install._lockfile import read_lockfile, write_lockfile
from aidriven.install._manifest import (
    ArtifactNotFoundError,
    ManifestVersionError,
    fetch_manifest,
    lookup_skill,
)
from aidriven.install._models import (
    ArtifactType,
    InstallPlan,
    InstallRequest,
    InstallResult,
    LockfileEntry,
    PerTargetAction,
    Scope,
)
from aidriven.install._paths import (
    resolve_project_root,
    user_lockfile_path,
)
from aidriven.install._planner import build_install_plan
from aidriven.install._targets import TARGETS

logger = logging.getLogger(__name__)

# Artifact name validation regex (FR-003)
_NAME_REGEX = re.compile(r"^[a-z][a-z0-9-]{0,63}$")

# Exit codes (from CLI contract)
EXIT_SUCCESS = 0
EXIT_GENERIC_FAILURE = 1
EXIT_USAGE_ERROR = 2
EXIT_NETWORK_ERROR = 3
EXIT_INTEGRITY_ERROR = 4
EXIT_CONFLICT = 5
EXIT_AUTODETECT_FAILURE = 6


class UsageError(Exception):
    """Invalid CLI usage — maps to exit code 2."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.exit_code = EXIT_USAGE_ERROR


class NetworkError(Exception):
    """Network failure — maps to exit code 3."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.exit_code = EXIT_NETWORK_ERROR


class AmbiguousTargetsError(Exception):
    """Multiple targets auto-detected — maps to exit code 6."""

    def __init__(self, detected: list[str]) -> None:
        self.detected = detected
        super().__init__(
            f"Multiple AI targets detected: {detected}. Use --ai to specify the target explicitly."
        )
        self.exit_code = EXIT_AUTODETECT_FAILURE


class NoTargetsFoundError(Exception):
    """No targets auto-detected — maps to exit code 6."""

    def __init__(self) -> None:
        supported = sorted(TARGETS.keys())
        super().__init__(f"No AI targets detected. Use --ai to specify one of: {supported}")
        self.exit_code = EXIT_AUTODETECT_FAILURE


def _validate_request(request: InstallRequest) -> None:
    """Raise UsageError for invalid request fields."""
    if request.artifact_type not in ArtifactType:
        raise UsageError(f"Unknown artifact type: {request.artifact_type!r}. Supported: skill")

    if not _NAME_REGEX.match(request.name):
        raise UsageError(
            f"Invalid artifact name {request.name!r}. Must match ^[a-z][a-z0-9-]{{0,63}}$."
        )

    for t in request.targets:
        if t not in TARGETS:
            raise UsageError(f"Unknown target {t!r}. Supported targets: {sorted(TARGETS.keys())}")


def _resolve_targets(request: InstallRequest, project_root: Path) -> list[str]:
    """Return the list of targets from the request, auto-detecting if empty."""
    if request.targets:
        unknown = [t for t in request.targets if t not in TARGETS]
        if unknown:
            supported = sorted(TARGETS.keys())
            raise UsageError(f"Unknown AI target(s): {unknown!r}. Supported: {supported}")
        return list(request.targets)

    # Auto-detect
    detected: list[str] = []
    for name, ai_target in TARGETS.items():
        for marker in ai_target.autodetect_markers:
            candidate = project_root / marker
            if candidate.exists():
                detected.append(name)
                break

    if len(detected) == 1:
        logger.info("Auto-detected AI target: %s", detected[0])
        return detected
    if len(detected) > 1:
        raise AmbiguousTargetsError(detected)
    raise NoTargetsFoundError()


def _handle_incompatible_targets(
    plan: InstallPlan,
    *,
    assume_yes: bool,
) -> InstallPlan:
    """Prompt for incompatible targets when interactive; skip or warn otherwise.

    Returns an updated plan with INCOMPATIBLE targets removed (skipped) when
    the user declines, or kept when the user confirms.
    In non-TTY mode, skips incompatible targets automatically with a warning.
    """
    from aidriven.install._models import PerTargetAction

    incompatible = [pt for pt in plan.targets if pt.action == PerTargetAction.INCOMPATIBLE]
    if not incompatible:
        return plan

    if assume_yes or not sys.stdin.isatty():
        # Non-interactive: skip incompatible targets with a warning
        for pt in incompatible:
            logger.warning("Skipping incompatible target %s: %s", pt.target.name, pt.reason)
        return plan  # keep them in the plan; installer will skip them

    # Interactive: prompt for each incompatible target
    import builtins

    for pt in incompatible:
        print(
            f"warning: target {pt.target.name!r} is not officially supported for "
            f"{plan.request.name!r}. {pt.reason}",
            file=sys.stderr,
        )
        answer = (
            builtins.input(f"Proceed with installing for {pt.target.name!r} anyway? [y/N] ")
            .strip()
            .lower()
        )
        if answer not in ("y", "yes"):
            logger.info("Skipping incompatible target %s by user choice.", pt.target.name)

    return plan


def _lockfile_path_for_scope(scope: Scope, project_root: Path) -> Path:
    if scope == Scope.USER:
        return user_lockfile_path()
    return project_root / "aidriven-lock.json"


def install_artifact(
    request: InstallRequest,
    *,
    cwd: Path | None = None,
) -> InstallResult:
    """Library entrypoint: install an artifact per *request*.

    Raises subclasses of the module's error hierarchy on fatal errors.
    """
    _validate_request(request)

    project_root = resolve_project_root(cwd)
    resolved_targets = _resolve_targets(request, project_root)

    # Mutate request targets to resolved list
    request.targets = tuple(resolved_targets)

    # 1. Resolve HEAD SHA
    try:
        sha = resolve_head_sha(force=request.force, no_cache=request.no_cache)
    except Exception as exc:
        raise NetworkError(f"Failed to resolve HEAD SHA: {exc}") from exc

    # 2. Fetch manifest
    try:
        manifest = fetch_manifest(sha, force=request.force, no_cache=request.no_cache)
    except ManifestVersionError as exc:
        raise UsageError(str(exc)) from exc
    except Exception as exc:
        raise NetworkError(f"Failed to fetch manifest: {exc}") from exc

    # 3. Lookup skill in manifest
    try:
        entry = lookup_skill(manifest, request.name)
    except ArtifactNotFoundError as exc:
        raise UsageError(str(exc)) from exc

    # 4. Fetch tarball
    try:
        tarball = fetch_tarball(sha, force=request.force, no_cache=request.no_cache)
    except IntegrityError as exc:
        raise IntegrityError(str(exc)) from exc
    except Exception as exc:
        raise NetworkError(f"Failed to fetch tarball: {exc}") from exc

    # 5. Extract skill (with integrity check)
    try:
        skill_dir = extract_skill(tarball, sha, entry, verify_hash=True)
    except IntegrityError:
        raise
    except Exception as exc:
        raise NetworkError(f"Failed to extract skill: {exc}") from exc

    try:
        expected_hash = hash_directory(skill_dir)

        # 6. Read lockfile
        lockfile_path = _lockfile_path_for_scope(request.scope, project_root)
        lockfile = read_lockfile(lockfile_path)

        # 7. Build plan, then handle incompatible targets
        plan = build_install_plan(
            request=request,
            manifest_entry=entry,
            source_commit_sha=sha,
            expected_content_hash=expected_hash,
            lockfile=lockfile,
            project_root=project_root,
        )
        plan = _handle_incompatible_targets(plan, assume_yes=request.force)

        # 8. Dry-run: return plan without writing
        if request.dry_run:
            from aidriven.install._models import PerTargetResult

            dry_results: list[PerTargetResult] = []
            for pt in plan.targets:
                dry_results.append(
                    PerTargetResult(
                        target_name=pt.target.name,
                        action_taken=pt.action,
                        final_mode=request.mode,
                        read_path=pt.read_path,
                        canonical_path=pt.canonical_path,
                        error=None,
                    )
                )
            return InstallResult(
                request=request,
                plan=plan,
                target_results=tuple(dry_results),
                lockfile_path=lockfile_path,
                success=all(
                    r.action_taken
                    in (
                        PerTargetAction.INSTALL_NEW,
                        PerTargetAction.UPDATE,
                        PerTargetAction.SKIP_IDENTICAL,
                    )
                    for r in dry_results
                ),
                exit_code=EXIT_SUCCESS,
            )

        # 9. Execute plan
        target_results = execute_plan(plan, skill_source=skill_dir)

        # 10. Update lockfile
        successful_targets = sorted(
            r.target_name
            for r in target_results
            if r.error is None
            and r.action_taken
            in (PerTargetAction.INSTALL_NEW, PerTargetAction.UPDATE, PerTargetAction.SKIP_IDENTICAL)
        )

        if successful_targets:
            # Merge this install with existing lockfile data
            existing_targets: set[str] = set()
            if request.name in lockfile.skills:
                existing_targets = set(lockfile.skills[request.name].targets)

            # For user scope, keep existing targets from other scope separate
            merged_targets = tuple(sorted(set(successful_targets) | existing_targets))

            lockfile.skills[request.name] = LockfileEntry(
                source="aidriven-resources",
                source_commit_sha=sha,
                computed_hash=expected_hash,
                targets=merged_targets,
                scope=request.scope,
                install_mode=request.mode,
            )
            write_lockfile(
                lockfile,
                lockfile_path,
                include_timestamps=(request.scope == Scope.USER),
            )

        # 11. Compute exit code
        has_conflict = any(r.action_taken == PerTargetAction.CONFLICT for r in target_results)
        has_error = any(r.error is not None for r in target_results)

        if has_conflict and not request.force:
            exit_code = EXIT_CONFLICT
        elif has_error:
            exit_code = EXIT_GENERIC_FAILURE
        else:
            exit_code = EXIT_SUCCESS

        success = exit_code == EXIT_SUCCESS

        return InstallResult(
            request=request,
            plan=plan,
            target_results=target_results,
            lockfile_path=lockfile_path,
            success=success,
            exit_code=exit_code,
        )
    finally:
        shutil.rmtree(skill_dir, ignore_errors=True)
