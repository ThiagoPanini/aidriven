"""Tests for Kiro provider."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from aidriven.discovery._models import ConfidenceLevel
from aidriven.discovery.providers._kiro import KiroProvider

_KIRO_MOD = "aidriven.discovery.providers._kiro"


def _make_provider() -> KiroProvider:
    return KiroProvider()


def _norm(p: object) -> str:
    """Normalize path separators for cross-platform string matching."""
    return str(p).replace("\\", "/")


# ── TestKiroMacOS ────────────────────────────────────────────────────


class TestKiroMacOS:
    """Tests for Kiro detection on macOS."""

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value=None)
    @patch(f"{_KIRO_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_KIRO_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given macOS with no Kiro artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no Kiro presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value="/usr/local/bin/kiro")
    @patch(f"{_KIRO_MOD}._safe_is_dir")
    @patch(f"{_KIRO_MOD}._safe_exists")
    @patch("subprocess.run")
    def test_returns_high_confidence_with_binary_config_and_version(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given macOS with Kiro binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence result with version is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0\nhash\ndarwin\n")
        mock_exists.side_effect = lambda p: "Kiro.app" in _norm(p)
        mock_is_dir.side_effect = lambda p: "Application Support/Kiro" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        ide = results[0]
        assert ide.identifier == "kiro"
        assert ide.channel == "stable"
        assert ide.confidence == ConfidenceLevel.HIGH
        assert ide.detected_platform == "darwin"
        assert ide.version == "1.0.0"


# ── TestKiroLinux ────────────────────────────────────────────────────


class TestKiroLinux:
    """Tests for Kiro detection on Linux."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_KIRO_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_KIRO_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with no Kiro artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no Kiro presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/kiro")
    @patch(f"{_KIRO_MOD}._safe_is_dir")
    @patch(f"{_KIRO_MOD}._safe_exists")
    @patch("subprocess.run")
    def test_returns_high_confidence_with_binary_and_config(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with Kiro binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence result for linux is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0\nhash\nlinux\n")
        mock_exists.side_effect = lambda p: "/opt/kiro" in _norm(p)
        mock_is_dir.side_effect = lambda p: ".config/Kiro" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].detected_platform == "linux"
        assert results[0].confidence == ConfidenceLevel.HIGH


# ── TestKiroWindows ──────────────────────────────────────────────────


class TestKiroWindows:
    """Tests for Kiro detection on Windows."""

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value=None)
    @patch(f"{_KIRO_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_KIRO_MOD}._safe_exists", return_value=False)
    @patch.dict(
        "os.environ",
        {
            "LOCALAPPDATA": r"C:\Users\user\AppData\Local",
            "APPDATA": r"C:\Users\user\AppData\Roaming",
        },
    )
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Windows with no Kiro artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no Kiro presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value=r"C:\Users\user\AppData\Local\Programs\Kiro\kiro.exe")
    @patch(f"{_KIRO_MOD}._safe_is_dir")
    @patch(f"{_KIRO_MOD}._safe_exists")
    @patch("subprocess.run")
    @patch.dict(
        "os.environ",
        {
            "LOCALAPPDATA": r"C:\Users\user\AppData\Local",
            "APPDATA": r"C:\Users\user\AppData\Roaming",
        },
    )
    def test_returns_high_confidence_with_binary_and_config(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Windows with Kiro binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence result for windows is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0\nhash\nwin32\n")
        mock_exists.side_effect = lambda p: "Programs/Kiro" in _norm(p)
        mock_is_dir.side_effect = lambda p: "AppData" in _norm(p) and "/Kiro" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].detected_platform == "windows"


# ── TestKiroPartialDetection ────────────────────────────────────────


class TestKiroPartialDetection:
    """Tests for Kiro partial detection scenarios (US3)."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_KIRO_MOD}._safe_is_dir")
    @patch(f"{_KIRO_MOD}._safe_exists", return_value=False)
    def test_returns_low_confidence_with_config_only(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given only a Kiro config directory without binary,
        When detect is called,
        Then a LOW confidence result is returned.
        """
        # ── Given ──
        mock_is_dir.side_effect = lambda p: ".config/Kiro" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].confidence == ConfidenceLevel.LOW

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/kiro")
    @patch(f"{_KIRO_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_KIRO_MOD}._safe_exists", return_value=False)
    def test_returns_medium_confidence_with_binary_only(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given only a Kiro binary without config directory,
        When detect is called,
        Then a MEDIUM confidence result is returned.
        """
        # ── Given ──
        # (mocks configure binary only)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].confidence == ConfidenceLevel.MEDIUM

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/kiro")
    @patch(f"{_KIRO_MOD}._safe_is_dir")
    @patch(f"{_KIRO_MOD}._safe_exists", return_value=False)
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="kiro", timeout=5))
    def test_returns_none_version_on_subprocess_timeout(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given a Kiro binary that times out when queried for version,
        When detect is called,
        Then the result has version set to None.
        """
        # ── Given ──
        mock_is_dir.side_effect = lambda p: ".config/Kiro" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].version is None
