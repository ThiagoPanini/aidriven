"""Integration tests: auto-detect AI targets from filesystem markers (US5)."""

from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.cli._install_cmd import run_install_cmd
from aidriven.install import ArtifactType, InstallRequest, install_artifact
from aidriven.install._service import EXIT_AUTODETECT_FAILURE

# ── Helpers ───────────────────────────────────────────────────────────────────


FAKE_SHA = "9" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES = {"SKILL.md": "# AutoDetect"}


def _hash(files: dict[str, str]) -> str:
    d = hashlib.sha256()
    for k in sorted(files.keys()):
        d.update(k.encode() + b"\x00")
        d.update(files[k].encode("utf-8") + b"\x00")
    return "sha256:" + d.hexdigest()


def _make_tarball() -> bytes:
    buf = io.BytesIO()
    prefix = f"aidriven-resources-{FAKE_SHA}"
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel, content in SKILL_FILES.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=f"{prefix}/skills/{SKILL_NAME}/{rel}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _manifest() -> object:
    from aidriven.install._manifest import _parse_manifest

    return _parse_manifest(
        {
            "schema_version": 1,
            "skills": {
                SKILL_NAME: {
                    "path_in_repo": f"skills/{SKILL_NAME}",
                    "content_hash": _hash(SKILL_FILES),
                    "compatible_targets": ["claude", "copilot"],
                    "description": "Test",
                }
            },
        },
        FAKE_SHA,
    )


@pytest.fixture
def tarball_path(tmp_path: Path) -> Path:
    p = tmp_path / f"{FAKE_SHA}.tar.gz"
    p.write_bytes(_make_tarball())
    return p


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestSingleMarkerAutoDetect:
    """Project with one marker → auto-detects and installs successfully."""

    def test_claude_marker_auto_detected(self, tmp_path: Path, tarball_path: Path) -> None:
        """
        Given a project with .claude/ marker and no --ai flag,
        When install is run,
        Then claude is auto-detected and install succeeds.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude").mkdir()

        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=(),  # no explicit targets
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=_manifest()),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            # ── When ──
            result = install_artifact(request, cwd=tmp_path)

        # ── Then ──
        assert result.success
        assert len(result.target_results) == 1
        assert result.target_results[0].target_name == "claude"

    def test_copilot_marker_auto_detected(self, tmp_path: Path, tarball_path: Path) -> None:
        """
        Given a project with .github/copilot-instructions.md marker,
        When install is run without --ai,
        Then copilot is auto-detected and install succeeds.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "copilot-instructions.md").write_text("# CI", encoding="utf-8")

        request = InstallRequest(
            artifact_type=ArtifactType.SKILL,
            name=SKILL_NAME,
            targets=(),
        )

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=_manifest()),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            result = install_artifact(request, cwd=tmp_path)

        assert result.success
        assert result.target_results[0].target_name == "copilot"


class TestMultipleMarkersExit6:
    """Project with two markers → exit code 6, both targets listed."""

    def test_exit_6_with_both_markers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given a project with both .claude/ and copilot-instructions.md,
        When install is run without --ai via CLI,
        Then exit code is 6.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude").mkdir()
        gh = tmp_path / ".github"
        gh.mkdir()
        (gh / "copilot-instructions.md").write_text("# CI", encoding="utf-8")

        monkeypatch.chdir(tmp_path)

        # ── When ──
        with patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA):
            code = run_install_cmd(["skill", SKILL_NAME])

        # ── Then ──
        assert code == EXIT_AUTODETECT_FAILURE


class TestNoMarkersExit6:
    """Project with no markers → exit code 6, supported targets listed."""

    def test_exit_6_with_no_markers(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Given a project with no AI markers,
        When install is run without --ai,
        Then exit code is 6.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        # ── When ──
        with patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA):
            code = run_install_cmd(["skill", SKILL_NAME])

        # ── Then ──
        assert code == EXIT_AUTODETECT_FAILURE
