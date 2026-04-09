"""Integration tests: multi-target skill install for US2."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.install import ArtifactType, InstallRequest, install_artifact
from aidriven.install._models import PerTargetAction

# ── Shared helpers ────────────────────────────────────────────────────────────


FAKE_SHA = "c" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES = {"SKILL.md": "# Code Reviewer", "config.yaml": "version: 1"}


def _compute_hash(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted(files.keys()):
        digest.update(rel_path.encode() + b"\x00")
        digest.update(files[rel_path].encode("utf-8") + b"\x00")
    return "sha256:" + digest.hexdigest()


SKILL_HASH = _compute_hash(SKILL_FILES)


def _make_tarball(sha: str) -> bytes:
    buf = io.BytesIO()
    prefix = f"aidriven-resources-{sha}"
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel_path, content in SKILL_FILES.items():
            full_path = f"{prefix}/skills/{SKILL_NAME}/{rel_path}"
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=full_path)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _make_manifest(compatible: list[str]) -> object:
    from aidriven.install._manifest import _parse_manifest

    payload = {
        "schema_version": 1,
        "skills": {
            SKILL_NAME: {
                "path_in_repo": f"skills/{SKILL_NAME}",
                "content_hash": SKILL_HASH,
                "compatible_targets": compatible,
                "description": "Test skill",
            }
        },
    }
    return _parse_manifest(payload, FAKE_SHA)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def tarball_path(tmp_path: Path) -> Path:
    tb = tmp_path / f"{FAKE_SHA}.tar.gz"
    tb.write_bytes(_make_tarball(FAKE_SHA))
    return tb


# ── US2 Tests ─────────────────────────────────────────────────────────────────


class TestMultiTargetBothCompatible:
    """Install --ai claude,copilot when both are compatible."""

    def test_installs_for_both_targets(self, project_dir: Path, tarball_path: Path) -> None:
        """
        Given a skill compatible with both claude and copilot,
        When installed with --ai claude,copilot,
        Then canonical dir is populated and each target's read path exists.
        """
        # ── Given ──
        manifest = _make_manifest(["claude", "copilot"])
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude", "copilot"),
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            # ── When ──
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert result.success
        assert result.exit_code == 0
        assert len(result.target_results) == 2

        # Canonical dir populated
        canonical = project_dir / ".agents" / "skills" / SKILL_NAME
        assert canonical.is_dir()

        # Both targets acted on
        actions = {r.target_name: r.action_taken for r in result.target_results}
        assert actions["claude"] == PerTargetAction.INSTALL_NEW
        assert actions["copilot"] == PerTargetAction.INSTALL_NEW

        # Lockfile records both targets
        lock_data = json.loads((project_dir / "aidriven-lock.json").read_text())
        assert "claude" in lock_data["skills"][SKILL_NAME]["targets"]
        assert "copilot" in lock_data["skills"][SKILL_NAME]["targets"]


class TestMultiTargetOneIncompatible:
    """Install --ai claude,copilot when one target is incompatible."""

    def test_incompatible_target_generates_incompatible_action(
        self, project_dir: Path, tarball_path: Path
    ) -> None:
        """
        Given a skill only compatible with claude,
        When installed with --ai claude,copilot,
        Then claude is INSTALL_NEW and copilot is INCOMPATIBLE.
        """
        # ── Given ──
        manifest = _make_manifest(["claude"])  # copilot not listed
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude", "copilot"),
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            # ── When ──
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        actions = {r.target_name: r.action_taken for r in result.target_results}
        assert actions["claude"] == PerTargetAction.INSTALL_NEW
        assert actions["copilot"] == PerTargetAction.INCOMPATIBLE


class TestMultiTargetPartialConflict:
    """Conflict on one target does not block the other."""

    def test_clean_target_succeeds_when_other_conflicts(
        self, project_dir: Path, tarball_path: Path
    ) -> None:
        """
        Given foreign content at claude read path but clean copilot,
        When installed with --ai claude,copilot,
        Then copilot is INSTALL_NEW and claude is CONFLICT (exit 5).
        """
        # ── Given ──
        manifest = _make_manifest(["claude", "copilot"])

        # Foreign content at claude's read path
        read_path = project_dir / ".claude" / "skills" / SKILL_NAME
        read_path.mkdir(parents=True)
        (read_path / "SKILL.md").write_text("foreign", encoding="utf-8")

        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude", "copilot"),
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            # ── When ──
            result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        actions = {r.target_name: r.action_taken for r in result.target_results}
        assert actions["copilot"] == PerTargetAction.INSTALL_NEW

        from aidriven.install._service import EXIT_CONFLICT

        assert result.exit_code == EXIT_CONFLICT
