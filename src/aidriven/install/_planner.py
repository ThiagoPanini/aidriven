"""Per-target action planner and InstallPlan construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from aidriven.install._hashing import hash_directory
from aidriven.install._models import (
    AITarget,
    InstallMode,
    InstallPlan,
    InstallRequest,
    Lockfile,
    ManifestEntry,
    PerTargetAction,
    PlannedTarget,
)
from aidriven.install._paths import (
    canonical_dir,
    needs_symlink,
    read_path_for_target,
    scope_base_path,
)
from aidriven.install._targets import TARGETS

if TYPE_CHECKING:
    from pathlib import Path


def plan_target(
    *,
    target: AITarget,
    request: InstallRequest,
    manifest_entry: ManifestEntry,
    expected_hash: str,
    lockfile: Lockfile,
    base: Path,
) -> PlannedTarget:
    """Compute the planned action for a single target."""
    scope = request.scope
    name = request.name

    rp = read_path_for_target(target, scope, base, name)
    cp = canonical_dir(base, name) if request.mode == InstallMode.SYMLINK else None
    sym = needs_symlink(target, scope, base, name) and request.mode == InstallMode.SYMLINK

    # 1. Incompatible check (highest priority)
    if target.name not in manifest_entry.compatible_targets:
        return PlannedTarget(
            target=target,
            canonical_path=cp,
            read_path=rp,
            needs_symlink=sym,
            action=PerTargetAction.INCOMPATIBLE,
            existing_hash=None,
            reason=f"Skill {name!r} does not support target {target.name!r}.",
        )

    # 2. Check if read path exists
    if not rp.exists():
        return PlannedTarget(
            target=target,
            canonical_path=cp,
            read_path=rp,
            needs_symlink=sym,
            action=PerTargetAction.INSTALL_NEW,
            existing_hash=None,
            reason=None,
        )

    # 3. Read path exists — compute existing hash
    # If read path is a symlink pointing to canonical, hash the canonical dir content
    resolve_dir = rp.resolve() if rp.is_symlink() else rp
    existing_hash: str | None = None
    if resolve_dir.is_dir():
        try:
            existing_hash = hash_directory(resolve_dir)
        except OSError:
            existing_hash = None

    # 4. Hash match → SKIP_IDENTICAL
    if existing_hash == expected_hash:
        return PlannedTarget(
            target=target,
            canonical_path=cp,
            read_path=rp,
            needs_symlink=sym,
            action=PerTargetAction.SKIP_IDENTICAL,
            existing_hash=existing_hash,
            reason=None,
        )

    # 5. Hash differs — check lockfile ownership
    lock_entry = lockfile.skills.get(name)
    aidriven_owns = lock_entry is not None and lock_entry.computed_hash == existing_hash

    if aidriven_owns:
        return PlannedTarget(
            target=target,
            canonical_path=cp,
            read_path=rp,
            needs_symlink=sym,
            action=PerTargetAction.UPDATE,
            existing_hash=existing_hash,
            reason=None,
        )

    # 6. Foreign/modified content
    if request.force:
        # Force overrides conflict — treat as UPDATE
        return PlannedTarget(
            target=target,
            canonical_path=cp,
            read_path=rp,
            needs_symlink=sym,
            action=PerTargetAction.UPDATE,
            existing_hash=existing_hash,
            reason=None,
        )

    return PlannedTarget(
        target=target,
        canonical_path=cp,
        read_path=rp,
        needs_symlink=sym,
        action=PerTargetAction.CONFLICT,
        existing_hash=existing_hash,
        reason=(
            f"Refusing to overwrite {rp} — content was not installed by aidriven "
            "or has been locally modified. Re-run with --force to overwrite."
        ),
    )


def build_install_plan(
    *,
    request: InstallRequest,
    manifest_entry: ManifestEntry,
    source_commit_sha: str,
    expected_content_hash: str,
    lockfile: Lockfile,
    project_root: Path,
) -> InstallPlan:
    """Build a full ``InstallPlan`` across all requested targets."""
    base = scope_base_path(request.scope, project_root)
    resolved_targets = [TARGETS[t] for t in request.targets]

    planned: list[PlannedTarget] = []
    for target in resolved_targets:
        pt = plan_target(
            target=target,
            request=request,
            manifest_entry=manifest_entry,
            expected_hash=expected_content_hash,
            lockfile=lockfile,
            base=base,
        )
        planned.append(pt)

    # overall_status
    conflict_any = any(p.action == PerTargetAction.CONFLICT for p in planned)
    noop_all = all(p.action == PerTargetAction.SKIP_IDENTICAL for p in planned)

    overall_status: Literal["ready", "blocked", "noop"]
    if conflict_any and not request.force:
        overall_status = "blocked"
    elif noop_all:
        overall_status = "noop"
    else:
        overall_status = "ready"
    return InstallPlan(
        request=request,
        manifest_entry=manifest_entry,
        source_commit_sha=source_commit_sha,
        expected_content_hash=expected_content_hash,
        targets=tuple(planned),
        overall_status=overall_status,
    )
