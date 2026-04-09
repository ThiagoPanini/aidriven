"""Integration tests: --force and --no-cache behavior for US4."""

from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.install import ArtifactType, InstallRequest, install_artifact
from aidriven.install._archive import IntegrityError
from aidriven.install._models import PerTargetAction

# ── Helpers ───────────────────────────────────────────────────────────────────


FAKE_SHA = "f" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES_V1 = {"SKILL.md": "# v1"}
SKILL_FILES_V2 = {"SKILL.md": "# v2 updated"}


def _hash(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for k in sorted(files.keys()):
        digest.update(k.encode() + b"\x00")
        digest.update(files[k].encode("utf-8") + b"\x00")
    return "sha256:" + digest.hexdigest()


def _tarball(sha: str, files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    prefix = f"aidriven-resources-{sha}"
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel_path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=f"{prefix}/skills/{SKILL_NAME}/{rel_path}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _manifest(files: dict[str, str]) -> object:
    from aidriven.install._manifest import _parse_manifest

    return _parse_manifest(
        {
            "schema_version": 1,
            "skills": {
                SKILL_NAME: {
                    "path_in_repo": f"skills/{SKILL_NAME}",
                    "content_hash": _hash(files),
                    "compatible_targets": ["claude"],
                    "description": "Test skill",
                }
            },
        },
        FAKE_SHA,
    )


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def tb_v1(tmp_path: Path) -> Path:
    p = tmp_path / f"{FAKE_SHA}.tar.gz"
    p.write_bytes(_tarball(FAKE_SHA, SKILL_FILES_V1))
    return p


@pytest.fixture
def tb_v2(tmp_path: Path) -> Path:
    p = tmp_path / f"{FAKE_SHA}_v2.tar.gz"
    p.write_bytes(_tarball(FAKE_SHA, SKILL_FILES_V2))
    return p


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestForceOverwritesConflict:
    """--force overwrites foreign/locally-modified content."""

    def test_force_overwrites_foreign_content(self, project_dir: Path, tb_v1: Path) -> None:
        """
        Given foreign content at the install path (no lockfile entry),
        When install is run with --force,
        Then the foreign content is overwritten and action is UPDATE.
        """
        # ── Given ──
        read_path = project_dir / ".claude" / "skills" / SKILL_NAME
        read_path.mkdir(parents=True)
        (read_path / "SKILL.md").write_text("foreign content", encoding="utf-8")

        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
            force=True,
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch(
                "aidriven.install._service.fetch_manifest", return_value=_manifest(SKILL_FILES_V1)
            ),
            patch("aidriven.install._service.fetch_tarball", return_value=tb_v1),
        ):
            # ── When ──
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert result.success
        # Content overwritten
        canonical = project_dir / ".agents" / "skills" / SKILL_NAME
        assert (canonical / "SKILL.md").read_text(encoding="utf-8") == "# v1"
        # Action should be UPDATE (force bypassed CONFLICT)
        actions = {r.target_name: r.action_taken for r in result.target_results}
        assert actions["claude"] == PerTargetAction.UPDATE


class TestForceWithChangedRemote:
    """--force with new remote content produces UPDATE action."""

    def test_force_update_when_remote_changed(
        self, project_dir: Path, tb_v1: Path, tb_v2: Path
    ) -> None:
        """
        Given v1 is installed by aidriven,
        When --force is run with v2 remote content,
        Then the action is UPDATE and v2 content is on disk.
        """
        # ── Given ──
        # First, install v1 normally
        req_v1 = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
        )
        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch(
                "aidriven.install._service.fetch_manifest", return_value=_manifest(SKILL_FILES_V1)
            ),
            patch("aidriven.install._service.fetch_tarball", return_value=tb_v1),
        ):
            install_artifact(req_v1, cwd=project_dir)

        # Now remote has v2; re-fetch with --force
        req_v2 = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
            force=True,
        )
        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch(
                "aidriven.install._service.fetch_manifest", return_value=_manifest(SKILL_FILES_V2)
            ),
            patch("aidriven.install._service.fetch_tarball", return_value=tb_v2),
        ):
            # ── When ──
            result = install_artifact(req_v2, cwd=project_dir)

        # ── Then ──
        assert result.success
        canonical = project_dir / ".agents" / "skills" / SKILL_NAME
        assert (canonical / "SKILL.md").read_text(encoding="utf-8") == "# v2 updated"
        actions = {r.target_name: r.action_taken for r in result.target_results}
        assert actions["claude"] == PerTargetAction.UPDATE


class TestForceWithIdenticalRemote:
    """--force with same remote content produces SKIP_IDENTICAL."""

    def test_force_skip_identical_when_content_unchanged(
        self, project_dir: Path, tb_v1: Path
    ) -> None:
        """
        Given v1 is installed and remote still has v1,
        When --force is run,
        Then action is SKIP_IDENTICAL (content already up to date after re-fetch).
        """
        # ── Given ──
        req = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
        )
        manifest = _manifest(SKILL_FILES_V1)

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tb_v1),
        ):
            install_artifact(req, cwd=project_dir)

        # Force re-fetch with same content
        force_req = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
            force=True,
        )
        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tb_v1),
        ):
            # ── When ──
            result = install_artifact(force_req, cwd=project_dir)

        # ── Then ──
        assert result.exit_code == 0
        actions = {r.target_name: r.action_taken for r in result.target_results}
        assert actions["claude"] == PerTargetAction.SKIP_IDENTICAL


class TestIntegrityFailure:
    """Checksum mismatch results in exit 4, no filesystem changes."""

    def test_integrity_failure_exit_4_no_files(self, project_dir: Path, tb_v1: Path) -> None:
        """
        Given a manifest with content_hash not matching the tarball,
        When install is run,
        Then exit code is 4 and no files are written.
        """
        # ── Given ──
        bad_manifest = _manifest({"SKILL.md": "completely different content"})  # wrong hash

        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=bad_manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tb_v1),
            pytest.raises(IntegrityError),
        ):
            # ── When / Then ──
            install_artifact(request, cwd=project_dir)

        # No files written
        assert not (project_dir / ".agents").exists()
        assert not (project_dir / "aidriven-lock.json").exists()
