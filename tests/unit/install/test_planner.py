"""Tests for all five planner decisions.

These tests MUST FAIL until _planner.py is implemented (T016).
"""

from __future__ import annotations

from pathlib import Path

from aidriven.install._models import (
    ArtifactType,
    InstallMode,
    InstallRequest,
    Lockfile,
    LockfileEntry,
    ManifestEntry,
    PerTargetAction,
    Scope,
)
from aidriven.install._targets import TARGETS


def _make_request(
    name: str = "code-reviewer",
    targets: tuple[str, ...] = ("claude",),
    force: bool = False,
    mode: InstallMode = InstallMode.SYMLINK,
) -> InstallRequest:
    return InstallRequest(
        artifact_type=ArtifactType.SKILL,
        name=name,
        targets=targets,
        force=force,
        mode=mode,
    )


def _make_entry(
    name: str = "code-reviewer",
    content_hash: str = "sha256:" + "a" * 64,
    compatible_targets: frozenset[str] = frozenset({"claude", "copilot"}),
) -> ManifestEntry:
    return ManifestEntry(
        name=name,
        type=ArtifactType.SKILL,
        path_in_repo=f"skills/{name}",
        content_hash=content_hash,
        compatible_targets=compatible_targets,
        description="Test skill",
    )


def _make_lockfile_entry(
    computed_hash: str = "sha256:" + "a" * 64,
    targets: tuple[str, ...] = ("claude",),
) -> LockfileEntry:
    return LockfileEntry(
        source="aidriven-resources",
        source_commit_sha="a" * 40,
        computed_hash=computed_hash,
        targets=targets,
        scope=Scope.PROJECT,
        install_mode=InstallMode.SYMLINK,
    )


# ── Import planner (fails until T016) ─────────────────────────────────

from aidriven.install._planner import plan_target  # noqa: E402

# ── INSTALL_NEW ───────────────────────────────────────────────────────


class TestInstallNew:
    """Planner returns INSTALL_NEW when read path is absent."""

    def test_install_new_when_read_path_missing(self, tmp_path: Path) -> None:
        """
        Given a base path where the skill's read path does not exist,
        When plan_target is called,
        Then the action is INSTALL_NEW.
        """
        # ── Given ──
        target = TARGETS["claude"]
        request = _make_request()
        entry = _make_entry()
        lockfile = Lockfile()
        base = tmp_path  # skill read path doesn't exist

        # ── When ──
        result = plan_target(
            target=target,
            request=request,
            manifest_entry=entry,
            expected_hash=entry.content_hash,
            lockfile=lockfile,
            base=base,
        )

        # ── Then ──
        assert result.action == PerTargetAction.INSTALL_NEW


# ── SKIP_IDENTICAL ────────────────────────────────────────────────────


class TestSkipIdentical:
    """Planner returns SKIP_IDENTICAL when hash matches expected."""

    def test_skip_identical_when_hash_matches(self, tmp_path: Path) -> None:
        """
        Given a read path that exists and its hash matches the expected hash,
        When plan_target is called,
        Then the action is SKIP_IDENTICAL.
        """
        from aidriven.install._hashing import hash_directory
        from aidriven.install._paths import read_path_for_target

        # ── Given ──
        target = TARGETS["claude"]
        request = _make_request()

        base = tmp_path
        read_path = read_path_for_target(target, Scope.PROJECT, base, "code-reviewer")
        read_path.mkdir(parents=True)
        # Write a real file so the content hash is deterministic
        (read_path / "SKILL.md").write_text("# test skill", encoding="utf-8")

        # Compute the actual hash of that directory
        actual_hash = hash_directory(read_path)

        entry = _make_entry(content_hash=actual_hash)

        # Lockfile says aidriven installed it with this hash
        lockfile = Lockfile(
            skills={"code-reviewer": _make_lockfile_entry(computed_hash=actual_hash)}
        )

        # ── When ──
        result = plan_target(
            target=target,
            request=request,
            manifest_entry=entry,
            expected_hash=actual_hash,
            lockfile=lockfile,
            base=base,
        )

        # ── Then ──
        assert result.action == PerTargetAction.SKIP_IDENTICAL


# ── UPDATE ────────────────────────────────────────────────────────────


class TestUpdate:
    """Planner returns UPDATE when aidriven installed it and hash differs."""

    def test_update_when_aidriven_installed_and_hash_differs(self, tmp_path: Path) -> None:
        """
        Given a read path that exists, with a lockfile entry indicating aidriven
        installed it (with a hash matching the current on-disk content), and the
        expected (remote) hash differs from the on-disk content,
        When plan_target is called,
        Then the action is UPDATE.
        """
        from aidriven.install._hashing import hash_directory
        from aidriven.install._paths import read_path_for_target

        # ── Given ──
        target = TARGETS["claude"]
        request = _make_request()

        base = tmp_path
        read_path = read_path_for_target(target, Scope.PROJECT, base, "code-reviewer")
        read_path.mkdir(parents=True)
        # Write old content
        (read_path / "SKILL.md").write_text("# old skill", encoding="utf-8")
        old_hash = hash_directory(read_path)

        # Remote has a different (new) hash
        new_hash = "sha256:" + "b" * 64

        entry = _make_entry(content_hash=new_hash)
        # Lockfile records the old on-disk hash (aidriven installed the old version)
        lockfile = Lockfile(skills={"code-reviewer": _make_lockfile_entry(computed_hash=old_hash)})

        # ── When ──
        result = plan_target(
            target=target,
            request=request,
            manifest_entry=entry,
            expected_hash=new_hash,
            lockfile=lockfile,
            base=base,
        )

        # ── Then ──
        assert result.action == PerTargetAction.UPDATE


# ── CONFLICT ─────────────────────────────────────────────────────────


class TestConflict:
    """Planner returns CONFLICT for foreign/modified content without --force."""

    def test_conflict_when_no_lockfile_entry(self, tmp_path: Path) -> None:
        """
        Given a read path that exists but has no lockfile entry,
        When plan_target is called without --force,
        Then the action is CONFLICT.
        """
        from aidriven.install._paths import read_path_for_target

        # ── Given ──
        target = TARGETS["claude"]
        request = _make_request(force=False)
        entry = _make_entry()
        lockfile = Lockfile()  # no entry for this skill
        base = tmp_path

        read_path = read_path_for_target(target, Scope.PROJECT, base, "code-reviewer")
        read_path.mkdir(parents=True)

        # ── When ──
        result = plan_target(
            target=target,
            request=request,
            manifest_entry=entry,
            expected_hash=entry.content_hash,
            lockfile=lockfile,
            base=base,
        )

        # ── Then ──
        assert result.action == PerTargetAction.CONFLICT

    def test_conflict_overridden_by_force(self, tmp_path: Path) -> None:
        """
        Given a read path with no lockfile entry (would normally be CONFLICT),
        When plan_target is called with force=True,
        Then the action is NOT CONFLICT (should be UPDATE or INSTALL_NEW).
        """
        from aidriven.install._paths import read_path_for_target

        # ── Given ──
        target = TARGETS["claude"]
        request = _make_request(force=True)
        entry = _make_entry()
        lockfile = Lockfile()
        base = tmp_path

        read_path = read_path_for_target(target, Scope.PROJECT, base, "code-reviewer")
        read_path.mkdir(parents=True)

        # ── When ──
        result = plan_target(
            target=target,
            request=request,
            manifest_entry=entry,
            expected_hash=entry.content_hash,
            lockfile=lockfile,
            base=base,
        )

        # ── Then ──
        assert result.action != PerTargetAction.CONFLICT


# ── INCOMPATIBLE ──────────────────────────────────────────────────────


class TestIncompatible:
    """Planner returns INCOMPATIBLE when target not in manifest's compatible_targets."""

    def test_incompatible_when_target_not_in_manifest(self, tmp_path: Path) -> None:
        """
        Given a manifest entry that lists only 'claude' as compatible,
        When plan_target is called for 'copilot',
        Then the action is INCOMPATIBLE.
        """
        # ── Given ──
        target = TARGETS["copilot"]
        request = _make_request(targets=("copilot",))
        entry = _make_entry(compatible_targets=frozenset({"claude"}))  # copilot not listed
        lockfile = Lockfile()
        base = tmp_path

        # ── When ──
        result = plan_target(
            target=target,
            request=request,
            manifest_entry=entry,
            expected_hash=entry.content_hash,
            lockfile=lockfile,
            base=base,
        )

        # ── Then ──
        assert result.action == PerTargetAction.INCOMPATIBLE
