"""CLI tests: multi-target output formatting for US2."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.cli._install_cmd import run_install_cmd

FAKE_SHA = "d" * 40
SKILL_NAME = "code-reviewer"
SKILL_FILES = {"SKILL.md": "# Code Reviewer"}


def _compute_hash(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted(files.keys()):
        digest.update(rel_path.encode() + b"\x00")
        digest.update(files[rel_path].encode("utf-8") + b"\x00")
    return "sha256:" + digest.hexdigest()


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


def _make_manifest(compatible: list[str]) -> object:
    from aidriven.install._manifest import _parse_manifest

    return _parse_manifest(
        {
            "schema_version": 1,
            "skills": {
                SKILL_NAME: {
                    "path_in_repo": f"skills/{SKILL_NAME}",
                    "content_hash": _compute_hash(SKILL_FILES),
                    "compatible_targets": compatible,
                    "description": "Test",
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
def tarball_path(tmp_path: Path) -> Path:
    tb = tmp_path / f"{FAKE_SHA}.tar.gz"
    tb.write_bytes(_make_tarball())
    return tb


class TestMultiTargetJsonOutput:
    """Multi-target JSON output includes one entry per target."""

    def test_json_output_has_entry_per_target(
        self,
        project_dir: Path,
        tarball_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given a successful 2-target install with --json,
        When the command completes,
        Then JSON contains two entries in targets[], one per target.
        """
        monkeypatch.chdir(project_dir)
        manifest = _make_manifest(["claude", "copilot"])

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--ai", "copilot", "--json"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data["targets"]) == 2
        target_names = {t["target"] for t in data["targets"]}
        assert target_names == {"claude", "copilot"}

    def test_json_includes_incompatible_target_entry(
        self,
        project_dir: Path,
        tarball_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given one compatible and one incompatible target,
        When the command completes with --json,
        Then the incompatible target entry has action='incompatible'.
        """
        monkeypatch.chdir(project_dir)
        manifest = _make_manifest(["claude"])  # copilot incompatible

        with (
            patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
            patch("aidriven.install._service.fetch_manifest", return_value=manifest),
            patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
        ):
            run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--ai", "copilot", "--json"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        by_target = {t["target"]: t for t in data["targets"]}
        assert by_target["claude"]["action"] == "install_new"
        assert by_target["copilot"]["action"] == "incompatible"
