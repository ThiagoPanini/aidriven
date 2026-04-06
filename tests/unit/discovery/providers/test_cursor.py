"""Tests for Cursor provider."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from aidriven.discovery._models import ConfidenceLevel
from aidriven.discovery.providers._cursor import CursorProvider

_CURSOR_MOD = "aidriven.discovery.providers._cursor"


def _make_provider() -> CursorProvider:
    return CursorProvider()


def _norm(p: object) -> str:
    """Normalize path separators for cross-platform string matching."""
    return str(p).replace("\\", "/")


# ── TestCursorMacOS ──────────────────────────────────────────────────


class TestCursorMacOS:
    """Tests for Cursor detection on macOS."""

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value=None)
    @patch(f"{_CURSOR_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_CURSOR_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given macOS with no Cursor artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no Cursor presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value="/usr/local/bin/cursor")
    @patch(f"{_CURSOR_MOD}._safe_is_dir")
    @patch(f"{_CURSOR_MOD}._safe_exists")
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
        Given macOS with Cursor binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence result with version is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="0.42.0\nhash\ndarwin\n")
        mock_exists.side_effect = lambda p: "Cursor.app" in _norm(p)
        mock_is_dir.side_effect = lambda p: "Application Support/Cursor" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        ide = results[0]
        assert ide.identifier == "cursor"
        assert ide.channel == "stable"
        assert ide.confidence == ConfidenceLevel.HIGH
        assert ide.detected_platform == "darwin"
        assert ide.version == "0.42.0"


# ── TestCursorLinux ──────────────────────────────────────────────────


class TestCursorLinux:
    """Tests for Cursor detection on Linux."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_CURSOR_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_CURSOR_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with no Cursor artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no Cursor presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/cursor")
    @patch(f"{_CURSOR_MOD}._safe_is_dir")
    @patch(f"{_CURSOR_MOD}._safe_exists")
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
        Given Linux with Cursor binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence result for linux is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="0.42.0\nhash\nlinux\n")
        mock_exists.side_effect = lambda p: "/opt/cursor" in _norm(p)
        mock_is_dir.side_effect = lambda p: ".config/Cursor" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].detected_platform == "linux"
        assert results[0].confidence == ConfidenceLevel.HIGH


# ── TestCursorWindows ────────────────────────────────────────────────


class TestCursorWindows:
    """Tests for Cursor detection on Windows."""

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value=None)
    @patch(f"{_CURSOR_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_CURSOR_MOD}._safe_exists", return_value=False)
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
        Given Windows with no Cursor artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no Cursor presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value=r"C:\Users\user\AppData\Local\Programs\Cursor\cursor.exe")
    @patch(f"{_CURSOR_MOD}._safe_is_dir")
    @patch(f"{_CURSOR_MOD}._safe_exists")
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
        Given Windows with Cursor binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence result for windows is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="0.42.0\nhash\nwin32\n")
        mock_exists.side_effect = lambda p: "Programs/Cursor" in _norm(p)
        mock_is_dir.side_effect = lambda p: "AppData" in _norm(p) and "/Cursor" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].detected_platform == "windows"


# ── TestCursorPartialDetection ───────────────────────────────────────


class TestCursorPartialDetection:
    """Tests for Cursor partial detection scenarios (US3)."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_CURSOR_MOD}._safe_is_dir")
    @patch(f"{_CURSOR_MOD}._safe_exists", return_value=False)
    def test_returns_low_confidence_with_config_only(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given only a Cursor config directory without binary,
        When detect is called,
        Then a LOW confidence result is returned.
        """
        # ── Given ──
        mock_is_dir.side_effect = lambda p: ".config/Cursor" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].confidence == ConfidenceLevel.LOW

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/cursor")
    @patch(f"{_CURSOR_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_CURSOR_MOD}._safe_exists", return_value=False)
    def test_returns_medium_confidence_with_binary_only(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given only a Cursor binary without config directory,
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
    @patch("shutil.which", return_value="/usr/bin/cursor")
    @patch(f"{_CURSOR_MOD}._safe_is_dir")
    @patch(f"{_CURSOR_MOD}._safe_exists", return_value=False)
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="cursor", timeout=5))
    def test_returns_none_version_on_subprocess_timeout(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given a Cursor binary that times out when queried for version,
        When detect is called,
        Then the result has version set to None.
        """
        # ── Given ──
        mock_is_dir.side_effect = lambda p: ".config/Cursor" in _norm(p)

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len(results) == 1
        assert results[0].version is None
