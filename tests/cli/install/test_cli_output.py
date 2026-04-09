"""CLI contract tests: output formatting, color suppression, quiet/verbose modes (T045)."""

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

FAKE_SHA = "bb" * 20
SKILL_NAME = "code-reviewer"
SKILL_FILES = {"SKILL.md": "# Color Test"}


def _hash(files: dict[str, str]) -> str:
    d = hashlib.sha256()
    for k in sorted(files.keys()):
        d.update(k.encode() + b"\x00")
        d.update(files[k].encode("utf-8") + b"\x00")
    return "sha256:" + d.hexdigest()


def _tarball() -> bytes:
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
                    "compatible_targets": ["claude"],
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
    p = tmp_path / f"{FAKE_SHA}.tar.gz"
    p.write_bytes(_tarball())
    return p


@pytest.fixture
def mock_network(tarball_path: Path) -> Generator[None, None, None]:
    with (
        patch("aidriven.install._service.resolve_head_sha", return_value=FAKE_SHA),
        patch("aidriven.install._service.fetch_manifest", return_value=_manifest()),
        patch("aidriven.install._service.fetch_tarball", return_value=tarball_path),
    ):
        yield


class TestNoColorSuppressesAnsi:
    """NO_COLOR env var and non-TTY suppress ANSI escape codes."""

    def test_no_color_suppresses_ansi(
        self,
        project_dir: Path,
        mock_network: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given NO_COLOR is set in the environment,
        When output is produced,
        Then no ANSI escape sequences appear in stdout or stderr.
        """
        monkeypatch.chdir(project_dir)
        monkeypatch.setenv("NO_COLOR", "1")

        run_install_cmd(["skill", SKILL_NAME, "--ai", "claude"])

        captured = capsys.readouterr()
        assert "\x1b[" not in captured.out
        assert "\x1b[" not in captured.err

    def test_json_always_has_no_ansi(
        self,
        project_dir: Path,
        mock_network: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given --json flag,
        When output is produced,
        Then stdout is pure JSON with no ANSI sequences.
        """
        monkeypatch.chdir(project_dir)

        run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--json"])

        captured = capsys.readouterr()
        assert "\x1b[" not in captured.out
        # Validate it's parseable JSON
        data = json.loads(captured.out)
        assert "success" in data


class TestQuietMode:
    """--quiet suppresses all non-error output."""

    def test_quiet_suppresses_stdout(
        self,
        project_dir: Path,
        mock_network: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given --quiet flag,
        When install succeeds,
        Then stdout is empty (no success output).
        """
        monkeypatch.chdir(project_dir)
        monkeypatch.setenv("NO_COLOR", "1")

        run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--quiet"])

        captured = capsys.readouterr()
        assert captured.out.strip() == ""


class TestJsonSuppressesColor:
    """--json output is always parseable regardless of TTY state."""

    def test_json_output_parseable_no_extra_text(
        self,
        project_dir: Path,
        mock_network: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Given --json and various environment states,
        When install runs,
        Then stdout contains only the JSON object (no extra lines).
        """
        monkeypatch.chdir(project_dir)

        run_install_cmd(["skill", SKILL_NAME, "--ai", "claude", "--json"])

        captured = capsys.readouterr()
        # Should be exactly one JSON object with no extra whitespace/text before or after
        data = json.loads(captured.out.strip())
        assert data["success"] is True
