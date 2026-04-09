"""Canonical-dir population, symlink/junction creation, and copy-mode installation."""

from __future__ import annotations

import logging
import os
import platform
import shutil
from typing import TYPE_CHECKING

from aidriven.install._models import (
    InstallMode,
    InstallPlan,
    InstallRequest,
    PerTargetAction,
    PerTargetResult,
    PlannedTarget,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def _remove_path(path: Path) -> None:
    """Remove *path* regardless of whether it is a regular dir, symlink, or Windows junction.

    ``shutil.rmtree`` raises on Windows junctions in Python 3.12+; fall back to
    ``os.unlink`` which correctly removes the junction without touching its target.
    """
    if not path.exists() and not path.is_symlink():
        return
    try:
        shutil.rmtree(path)
    except (OSError, NotADirectoryError):
        # Symlink or Windows junction: unlink removes only the pointer, not the target.
        os.unlink(str(path))


def _copy_tree(src: Path, dest: Path) -> None:
    """Copy files from *src* into *dest*, replacing any existing content."""
    _remove_path(dest)
    shutil.copytree(src, dest)


def _create_symlink(target_dir: Path, link_path: Path) -> None:
    """Create a directory symlink at *link_path* pointing to *target_dir*.

    On Windows, attempts to create a directory junction (mklink /J).
    Falls back to a regular symlink (requires Developer Mode or elevation).
    """
    link_path.parent.mkdir(parents=True, exist_ok=True)
    _remove_path(link_path)

    if platform.system() == "Windows":
        # Try junction first (no elevation needed)
        import subprocess

        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target_dir)],
            capture_output=True,
        )
        if result.returncode != 0:
            # Fallback: regular symlink (requires Developer Mode)
            os.symlink(target_dir, link_path, target_is_directory=True)
    else:
        os.symlink(target_dir, link_path, target_is_directory=True)


def execute_target(
    planned: PlannedTarget,
    *,
    skill_source: Path,
    request: InstallRequest,
) -> PerTargetResult:
    """Execute an install action for a single planned target.

    Returns a ``PerTargetResult`` including any per-target error.
    Errors in symlink creation fall back to copy mode for this target only.
    Other targets in the same run are unaffected.
    """
    action = planned.action
    final_mode = request.mode

    # Actions that require no writes
    if action == PerTargetAction.SKIP_IDENTICAL:
        return PerTargetResult(
            target_name=planned.target.name,
            action_taken=action,
            final_mode=final_mode,
            read_path=planned.read_path,
            canonical_path=planned.canonical_path,
            error=None,
        )

    if action == PerTargetAction.INCOMPATIBLE:
        return PerTargetResult(
            target_name=planned.target.name,
            action_taken=action,
            final_mode=final_mode,
            read_path=planned.read_path,
            canonical_path=planned.canonical_path,
            error=planned.reason,
        )

    if action == PerTargetAction.CONFLICT:
        return PerTargetResult(
            target_name=planned.target.name,
            action_taken=action,
            final_mode=final_mode,
            read_path=planned.read_path,
            canonical_path=planned.canonical_path,
            error=planned.reason,
        )

    # INSTALL_NEW or UPDATE
    try:
        if request.mode == InstallMode.SYMLINK and planned.canonical_path is not None:
            # 1. Populate canonical dir
            _copy_tree(skill_source, planned.canonical_path)

            # 2. Create symlink if needed, fall back to copy on error
            if planned.needs_symlink:
                try:
                    _create_symlink(planned.canonical_path, planned.read_path)
                except (OSError, Exception) as sym_err:
                    logger.warning(
                        "Symlink creation failed for target %s: %s — falling back to copy.",
                        planned.target.name,
                        sym_err,
                    )
                    _copy_tree(skill_source, planned.read_path)
                    final_mode = InstallMode.COPY
        else:
            # Copy mode: write directly to read path
            _copy_tree(skill_source, planned.read_path)
            final_mode = InstallMode.COPY

    except Exception as exc:
        logger.error("Failed to install for target %s: %s", planned.target.name, exc)
        return PerTargetResult(
            target_name=planned.target.name,
            action_taken=action,
            final_mode=final_mode,
            read_path=planned.read_path,
            canonical_path=planned.canonical_path,
            error=str(exc),
        )

    return PerTargetResult(
        target_name=planned.target.name,
        action_taken=action,
        final_mode=final_mode,
        read_path=planned.read_path,
        canonical_path=planned.canonical_path,
        error=None,
    )


def execute_plan(
    plan: InstallPlan,
    *,
    skill_source: Path,
) -> tuple[PerTargetResult, ...]:
    """Execute all targets in *plan* and return per-target results.

    Each target is executed independently; a failure in one does not abort others.
    """
    results: list[PerTargetResult] = []
    for planned in plan.targets:
        result = execute_target(
            planned,
            skill_source=skill_source,
            request=plan.request,
        )
        results.append(result)
    return tuple(results)
