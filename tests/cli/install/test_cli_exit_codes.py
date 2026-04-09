"""CLI contract tests: exit codes, JSON output, and dry-run fidelity."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.cli._install_cmd import run_install_cmd
from aidriven.install._service import (
    EXIT_AUTODETECT_FAILURE,
    EXIT_CONFLICT,
    EXIT_INTEGRITY_ERROR,
    EXIT_NETWORK_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
)

# ── Shared fixtures ───────────────────────────────────────────────────────────


FAKE_SHA = "b" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES = {"SKILL.md": "# Code Reviewer"}


def _compute_hash(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted(files.keys()):
        digest.update(rel_path.encode() + b"\x00")
        digest.update(files[rel_path].encode("utf-8") + b"\x00")
    return "sha256:" + digest.hexdigest()


SKILL_HASH = _compute_hash(SKILL_FILES)


def _make_tarball(sha: str, skill_name: str, files: dict[str, str]) -> bytes:
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


def _make_manifest(skill_name: str, content_hash: str) -> object:
    from aidriven.install._manifest import _parse_manifest

    payload = {
        "schema_version": 1,
        "skills": {
            skill_name: {
                "path_in_repo": f"skills/{skill_name}",
                "content_hash": content_hash,
                "compatible_targets": ["claude", "copilot"],
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
    tb.write_bytes(_make_tarball(FAKE_SHA, SKILL_NAME, SKILL_FILES))
    return tb


@pytest.fixture
def mock_network(tarball_path: Path) -> Generator[None, None, None]:
    with (
        patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
        patch(
            "aidriven.install._service.fetch_manifest",
            return_value=_make_manifest(SKILL_NAME, SKILL_HASH),
        ),
        patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
    ):
        yield


# ── Exit codes ────────────────────────────────────────────────────────────────


class TestExitCodes:
    """Assert each of the six exit codes (0-6) on the correct trigger."""

    def test_exit_0_on_success(
        self, project_dir: Path, mock_network: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given a valid install request,
        When install succeeds,
        Then exit code is 0.
        """
        monkeypatch.chdir(project_dir)
        code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude"])
        assert code == EXIT_SUCCESS

    def test_exit_2_on_invalid_artifact_type(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given an unknown artifact type,
        When install is invoked,
        Then exit code is 2.
        """
        monkeypatch.chdir(project_dir)
        with pytest.raises(SystemExit) as exc_info:
            run_install_cmd(["gadget", SKILL_NAME, "--ai", "claude"])
        assert exc_info.value.code == EXIT_USAGE_ERROR

    def test_exit_2_on_invalid_artifact_name(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given an invalid name (uppercase),
        When install is invoked,
        Then exit code is 2.
        """
        monkeypatch.chdir(project_dir)

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
        ):
            code = run_install_cmd(["skill", "InvalidName", "--ai", "claude"])
        assert code == EXIT_USAGE_ERROR

    def test_exit_2_on_unknown_target(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given an unknown --ai target,
        When install is invoked,
        Then exit code is 2.
        """
        monkeypatch.chdir(project_dir)
        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
        ):
            code = run_install_cmd(["skill", SKILL_NAME, "--ai", "unknowntarget"])
        assert code == EXIT_USAGE_ERROR

    def test_exit_2_on_mutually_exclusive_flags(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given --quiet and --verbose together,
        When install is invoked,
        Then argparse exits (exit code 2).
        """
        monkeypatch.chdir(project_dir)
        with pytest.raises(SystemExit) as exc_info:
            run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--quiet", "--verbose"])
        assert exc_info.value.code == EXIT_USAGE_ERROR

    def test_exit_3_on_network_error(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given a network error during SHA resolution,
        When install is invoked,
        Then exit code is 3.
        """
        monkeypatch.chdir(project_dir)
        with patch(
            "aidriven.install._service.resolve_head_sha",
            side_effect=Exception("Connection refused"),
        ):
            code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude"])
        assert code == EXIT_NETWORK_ERROR

    def test_exit_4_on_integrity_error(
        self, project_dir: Path, tarball_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given a manifest with a wrong content hash,
        When install is invoked,
        Then exit code is 4.
        """
        monkeypatch.chdir(project_dir)
        # Manifest says hash is wrong
        bad_manifest = _make_manifest(SKILL_NAME, "sha256:" + "f" * 64)
        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=bad_manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude"])
        assert code == EXIT_INTEGRITY_ERROR

    def test_exit_5_on_conflict(
        self, project_dir: Path, mock_network: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given foreign content at the install location,
        When install is invoked without --force,
        Then exit code is 5.
        """
        monkeypatch.chdir(project_dir)
        # Create foreign content at the read path
        read_path = project_dir / ".claude" / "skills" / SKILL_NAME
        read_path.mkdir(parents=True)
        (read_path / "SKILL.md").write_text("# foreign content", encoding="utf-8")

        code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude"])
        assert code == EXIT_CONFLICT

    def test_exit_6_on_autodetect_failure_no_markers(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given a project with no AI markers and no --ai flag,
        When install is invoked,
        Then exit code is 6.
        """
        monkeypatch.chdir(project_dir)
        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
        ):
            code = run_install_cmd(["skill", SKILL_NAME])
        assert code == EXIT_AUTODETECT_FAILURE


# ── JSON output ────────────────────────────────────────────────────────────────


class TestJsonOutput:
    """Assert --json output matches the CLI contract schema."""

    def test_json_output_is_valid_on_success(
        self,
        project_dir: Path,
        mock_network: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given a successful install with --json,
        When the command runs,
        Then stdout is a single valid JSON object matching the contract schema.
        """
        monkeypatch.chdir(project_dir)
        code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--json"])

        captured = capsys.readouterr()
        assert code == EXIT_SUCCESS
        data = json.loads(captured.out)

        # Top-level required fields
        assert data["success"] is True
        assert data["exitCode"] == 0
        assert "sourceCommitSha" in data
        assert "computedHash" in data
        assert "lockfilePath" in data
        assert "targets" in data
        assert "request" in data

        # Per-target fields
        target_entry = data["targets"][0]
        assert target_entry["target"] == "claude"
        assert target_entry["action"] in (
            "install_new",
            "update",
            "skip_identical",
            "conflict",
            "incompatible",
        )
        assert "finalMode" in target_entry
        assert "readPath" in target_entry

    def test_json_output_on_error(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Given a network error with --json,
        When the command runs,
        Then stdout is a JSON error envelope with success=false.
        """
        monkeypatch.chdir(project_dir)
        with patch(
            "aidriven.install._service.resolve_head_sha",
            side_effect=Exception("timeout"),
        ):
            code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--json"])

        captured = capsys.readouterr()
        assert code == EXIT_NETWORK_ERROR
        data = json.loads(captured.out)
        assert data["success"] is False
        assert data["exitCode"] == EXIT_NETWORK_ERROR


# ── Dry-run ───────────────────────────────────────────────────────────────────


class TestDryRun:
    """--dry-run leaves filesystem and lockfile unchanged."""

    def test_dry_run_leaves_filesystem_unchanged(
        self, project_dir: Path, mock_network: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given a clean project dir and --dry-run,
        When install is invoked,
        Then no files are written and lockfile does not appear.
        """
        monkeypatch.chdir(project_dir)
        code = run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--dry-run"])

        assert code == EXIT_SUCCESS
        assert not (project_dir / ".agents").exists()
        assert not (project_dir / ".claude").exists()
        assert not (project_dir / "aidriven-lock.json").exists()

    def test_dry_run_json_includes_dry_run_flag(
        self,
        project_dir: Path,
        mock_network: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given --dry-run and --json,
        When install is invoked,
        Then JSON output includes dryRun=true.
        """
        monkeypatch.chdir(project_dir)
        run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--dry-run", "--json"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data.get("dryRun") is True
