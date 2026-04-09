"""Integration tests: single-target skill install for US1.

These tests use a mock HTTP layer to avoid real network calls.
"""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.install import ArtifactType, InstallRequest, install_artifact
from aidriven.install._models import PerTargetAction

# ── Test helpers ──────────────────────────────────────────────────────────────


def _make_skill_tarball(sha: str, skill_name: str, files: dict[str, str]) -> bytes:
    """Create an in-memory tarball mimicking a GitHub archive structure.

    GitHub archives unpack as ``<repo>-<sha>/<path>``.
    """
    buf = io.BytesIO()
    repo_prefix = f"aidriven-resources-{sha}"
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel_path, content in files.items():
            full_path = f"{repo_prefix}/skills/{skill_name}/{rel_path}"
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=full_path)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _compute_hash(files: dict[str, str]) -> str:
    """Compute the deterministic SHA-256 content hash for a dict of files."""
    digest = hashlib.sha256()
    for rel_path in sorted(files.keys()):
        digest.update(rel_path.encode() + b"\x00")
        digest.update(files[rel_path].encode("utf-8") + b"\x00")
    return "sha256:" + digest.hexdigest()


def _make_manifest(skill_name: str, content_hash: str, compatible_targets: list[str]) -> bytes:
    return json.dumps(
        {
            "schema_version": 1,
            "skills": {
                skill_name: {
                    "path_in_repo": f"skills/{skill_name}",
                    "content_hash": content_hash,
                    "compatible_targets": compatible_targets,
                    "description": "Test skill",
                }
            },
        }
    ).encode("utf-8")


FAKE_SHA = "a" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES = {
    "SKILL.md": "# Code Reviewer\n\nReview code professionally.",
    "README.md": "# README",
}
SKILL_HASH = _compute_hash(SKILL_FILES)
MANIFEST_BYTES = _make_manifest(SKILL_NAME, SKILL_HASH, ["claude", "copilot"])
TARBALL_BYTES = _make_skill_tarball(FAKE_SHA, SKILL_NAME, SKILL_FILES)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """A fresh git-root project directory."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


@pytest.fixture
def mock_network(tmp_path: Path) -> Generator[None, None, None]:
    """Patch all network calls to use in-memory fixtures."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    with (
        patch(
            "aidriven.install._service.resolve_head_sha",
            return_value=FAKE_SHA,
        ),
        patch(
            "aidriven.install._service.fetch_manifest",
            return_value=_build_manifest(),
        ),
        patch(
            "aidriven.install._service.fetch_tarball",
            return_value=_write_tarball(cache_dir),
        ),
    ):
        yield


def _build_manifest() -> object:
    from aidriven.install._manifest import _parse_manifest

    return _parse_manifest(json.loads(MANIFEST_BYTES.decode()), FAKE_SHA)


def _write_tarball(cache_dir: Path) -> Path:
    tb = cache_dir / f"{FAKE_SHA}.tar.gz"
    tb.write_bytes(TARBALL_BYTES)
    return tb


# ── US1 Tests ─────────────────────────────────────────────────────────────────


class TestSingleTargetClaudeInstall:
    """Install code-reviewer --ai claude at project scope."""

    def test_install_claude_creates_canonical_dir_and_symlink(
        self, project_dir: Path, mock_network: None
    ) -> None:
        """
        Given a clean project directory,
        When code-reviewer is installed for claude,
        Then canonical dir is populated and symlink is created.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
        )

        # ── When ──
        result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert result.success
        assert result.exit_code == 0

        canonical = project_dir / ".agents" / "skills" / SKILL_NAME
        assert canonical.is_dir()
        assert (canonical / "SKILL.md").exists()

        symlink = project_dir / ".claude" / "skills" / SKILL_NAME
        assert symlink.exists()
        # On non-Windows the symlink should point to canonical
        import platform

        if platform.system() != "Windows":
            assert symlink.is_symlink()
            assert symlink.resolve() == canonical.resolve()

    def test_install_claude_writes_lockfile(self, project_dir: Path, mock_network: None) -> None:
        """
        Given a clean project directory,
        When code-reviewer is installed for claude,
        Then aidriven-lock.json is written with correct fields.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
        )

        # ── When ──
        install_artifact(request, cwd=project_dir)

        # ── Then ──
        lockfile_path = project_dir / "aidriven-lock.json"
        assert lockfile_path.exists()
        lock_data = json.loads(lockfile_path.read_text(encoding="utf-8"))
        assert lock_data["version"] == 1
        entry = lock_data["skills"][SKILL_NAME]
        assert entry["source"] == "aidriven-resources"
        assert entry["sourceCommitSha"] == FAKE_SHA
        assert entry["computedHash"].startswith("sha256:")
        assert "claude" in entry["targets"]
        assert entry["scope"] == "project"
        assert entry["installMode"] == "symlink"


class TestSingleTargetCopilotInstall:
    """Install code-reviewer --ai copilot at project scope."""

    def test_install_copilot_creates_canonical_dir_no_symlink(
        self, project_dir: Path, mock_network: None
    ) -> None:
        """
        Given a clean project directory,
        When code-reviewer is installed for copilot (project scope),
        Then canonical dir is populated and NO symlink is created.

        At project scope, copilot reads from .agents/skills directly.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("copilot",),
        )

        # ── When ──
        result = install_artifact(request, cwd=project_dir)

        # ── Then ──
        assert result.success
        canonical = project_dir / ".agents" / "skills" / SKILL_NAME
        assert canonical.is_dir()
        assert (canonical / "SKILL.md").exists()

        # No separate symlink/directory at .agents/skills (copilot reads canonical directly)
        # The read_path for copilot at project scope == canonical (no symlink needed)
        assert not (project_dir / ".copilot").exists()


class TestIdempotencyInstall:
    """Re-running the same install should be a no-op."""

    def test_idempotent_reinstall_exits_0_no_changes(
        self, project_dir: Path, mock_network: None
    ) -> None:
        """
        Given a skill already installed for claude,
        When the same install command is run again,
        Then exit code is 0 and action is SKIP_IDENTICAL.
        """
        # ── Given ──
        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=("claude",),
        )
        # First install
        install_artifact(request, cwd=project_dir)

        # ── When ──
        result2 = install_artifact(
            InstallRequest(
                artifact_type=ArtifactType.SKILL,
                name=SKILL_NAME,
                targets=("claude",),
            ),
            cwd=project_dir,
        )

        # ── Then ──
        assert result2.exit_code == 0
        assert len(result2.target_results) == 1
        assert result2.target_results[0].action_taken == PerTargetAction.SKIP_IDENTICAL
