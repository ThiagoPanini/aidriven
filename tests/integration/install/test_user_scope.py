"""Integration tests: user-scope skill install for US3."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from aidriven.install import ArtifactType, InstallRequest, Scope, install_artifact

# ── Helpers ───────────────────────────────────────────────────────────────────


FAKE_SHA = "e" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES = {"SKILL.md": "# Code Reviewer"}


def _compute_hash(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted(files.keys()):
        digest.update(rel_path.encode() + b"\x00")
        digest.update(files[rel_path].encode("utf-8") + b"\x00")
    return "sha256:" + digest.hexdigest()


SKILL_HASH = _compute_hash(SKILL_FILES)


def _make_tarball() -> bytes:
    buf = io.BytesIO()
    prefix = f"aidriven-resources-{FAKE_SHA}"
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel_path, content in SKILL_FILES.items():
            full_path = f"{prefix}/skills/{SKILL_NAME}/{rel_path}"
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=full_path)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _make_manifest() -> object:
    from aidriven.install._manifest import _parse_manifest

    return _parse_manifest(
        {
            "schema_version": 1,
            "skills": {
                SKILL_NAME: {
                    "path_in_repo": f"skills/{SKILL_NAME}",
                    "content_hash": SKILL_HASH,
                    "compatible_targets": ["claude", "copilot"],
                    "description": "Test skill",
                }
            },
        },
        FAKE_SHA,
    )


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Clean project dir — should NOT receive any files in user-scope tests."""
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def fake_home(tmp_path: Path) -> Path:
    """A temp directory acting as HOME/user dir."""
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def tarball_path(tmp_path: Path) -> Path:
    tb = tmp_path / f"{FAKE_SHA}.tar.gz"
    tb.write_bytes(_make_tarball())
    return tb


# ── Helper to patch Path.home() ───────────────────────────────────────────────


def _with_home(fake_home: Path) -> Any:
    return patch("aidriven.install._paths.Path.home", return_value=fake_home)


# ── US3 Tests ─────────────────────────────────────────────────────────────────


class TestUserScopeClaude:
    """--scope user --ai claude installs to home-based paths."""

    def test_canonical_under_home_agents(
        self, project_dir: Path, fake_home: Path, tarball_path: Path
    ) -> None:
        """
        Given --scope user --ai claude,
        When install succeeds,
        Then canonical dir is ~/.agents/skills/<name>.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
            scope=Scope.USER,
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=_make_manifest()),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
            _with_home(fake_home),
        ):
            # ── When ──
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert result.success
        canonical = fake_home / ".agents" / "skills" / SKILL_NAME
        assert canonical.is_dir()
        assert (canonical / "SKILL.md").exists()

    def test_symlink_at_claude_skills(
        self, project_dir: Path, fake_home: Path, tarball_path: Path
    ) -> None:
        """
        Given --scope user --ai claude,
        When install succeeds,
        Then symlink at ~/.claude/skills/<name> points to canonical.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
            scope=Scope.USER,
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=_make_manifest()),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
            _with_home(fake_home),
        ):
            install_artifact(request, cwd=project_dir)

        # ── Then ──
        symlink = fake_home / ".claude" / "skills" / SKILL_NAME
        assert symlink.exists()
        import platform

        if platform.system() != "Windows":
            assert symlink.is_symlink()

    def test_project_lockfile_absent_user_lockfile_written(
        self, project_dir: Path, fake_home: Path, tarball_path: Path
    ) -> None:
        """
        Given --scope user,
        When install succeeds,
        Then project aidriven-lock.json is NOT written; user lockfile IS written.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
            scope=Scope.USER,
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=_make_manifest()),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
            _with_home(fake_home),
        ):
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert not (project_dir / "aidriven-lock.json").exists()
        assert result.lockfile_path is not None
        assert result.lockfile_path.exists()
        lock_data = json.loads(result.lockfile_path.read_text())
        assert lock_data["skills"][SKILL_NAME]["scope"] == "user"


class TestUserScopeCopilot:
    """--scope user --ai copilot installs with symlink at ~/.copilot/skills/."""

    def test_copilot_user_scope_symlink_at_copilot_path(
        self, project_dir: Path, fake_home: Path, tarball_path: Path
    ) -> None:
        """
        Given --scope user --ai copilot,
        When install succeeds,
        Then symlink at ~/.copilot/skills/<name> exists.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("copilot",),
            scope=Scope.USER,
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=_make_manifest()),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
            _with_home(fake_home),
        ):
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert result.success
        canonical = fake_home / ".agents" / "skills" / SKILL_NAME
        assert canonical.is_dir()

        copilot_read = fake_home / ".copilot" / "skills" / SKILL_NAME
        assert copilot_read.exists()
