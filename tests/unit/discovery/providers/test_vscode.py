"""Tests for VS Code provider (stable + Insiders)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from aidriven.discovery._models import ConfidenceLevel
from aidriven.discovery.providers._vscode import VSCodeProvider

_VSCODE_MOD = "aidriven.discovery.providers._vscode"


def _make_provider() -> VSCodeProvider:
    return VSCodeProvider()


def _norm(p: object) -> str:
    """Normalize path separators for cross-platform string matching."""
    return str(p).replace("\\", "/")


# ── TestVSCodeStableMacOS ────────────────────────────────────────────


class TestVSCodeStableMacOS:
    """Tests for VS Code stable detection on macOS."""

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value=None)
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given macOS with no VS Code artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no VS Code presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value="/usr/local/bin/code")
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists")
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
        Given macOS with VS Code binary, config dir, and version output,
        When detect is called,
        Then a HIGH confidence stable result is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.80.0\nabc\ndarwin\n")
        mock_exists.side_effect = lambda p: (
            "Visual Studio Code.app" in _norm(p) and "Insiders" not in _norm(p)
        )
        mock_is_dir.side_effect = lambda p: (
            "Application Support/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        ide = stable[0]
        assert ide.identifier == "vscode"
        assert ide.detected_platform == "darwin"
        assert ide.confidence == ConfidenceLevel.HIGH
        assert ide.version == "1.80.0"


# ── TestVSCodeStableLinux ────────────────────────────────────────────


class TestVSCodeStableLinux:
    """Tests for VS Code stable detection on Linux."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_nothing_found(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with no VS Code artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no VS Code presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/code")
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists")
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
        Given Linux with VS Code binary on PATH and config directory,
        When detect is called,
        Then a HIGH confidence stable result is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.85.0\nhash\nlinux\n")
        mock_exists.side_effect = lambda p: "/usr/share/code" in _norm(p)
        mock_is_dir.side_effect = lambda p: (
            ".config/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        ide = stable[0]
        assert ide.identifier == "vscode"
        assert ide.confidence == ConfidenceLevel.HIGH
        assert ide.detected_platform == "linux"


# ── TestVSCodeStableWindows ──────────────────────────────────────────


class TestVSCodeStableWindows:
    """Tests for VS Code stable detection on Windows."""

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value=None)
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
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
        Given Windows with no VS Code artifacts,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no VS Code presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Windows")
    @patch(
        "shutil.which",
        return_value=r"C:\Users\user\AppData\Local\Programs\Microsoft VS Code\bin\code",
    )
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists")
    @patch("subprocess.run")
    @patch.dict(
        "os.environ",
        {
            "LOCALAPPDATA": r"C:\Users\user\AppData\Local",
            "APPDATA": r"C:\Users\user\AppData\Roaming",
        },
    )
    def test_returns_stable_detection_with_config(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Windows with VS Code binary, config dir, and version output,
        When detect is called,
        Then a stable result for windows is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.87.0\nhash\nwin32\n")
        mock_exists.side_effect = lambda p: (
            "Microsoft VS Code" in _norm(p) and "Insiders" not in _norm(p)
        )
        mock_is_dir.side_effect = lambda p: (
            "AppData" in _norm(p) and "/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        ide = stable[0]
        assert ide.identifier == "vscode"
        assert ide.detected_platform == "windows"


# ── TestVSCodeInsiders ───────────────────────────────────────────────


class TestVSCodeInsiders:
    """Tests for VS Code Insiders detection (US2)."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which")
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_insiders_entry_with_only_insiders_binary(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with only code-insiders binary on PATH,
        When detect is called,
        Then an insiders entry with MEDIUM confidence is returned.
        """
        # ── Given ──
        mock_which.side_effect = lambda name: (
            "/usr/bin/code-insiders" if name == "code-insiders" else None
        )

        # ── When ──
        results = _make_provider().detect()
        insiders = [r for r in results if r.channel == "insiders"]

        # ── Then ──
        assert len(insiders) == 1
        assert insiders[0].confidence == ConfidenceLevel.MEDIUM

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which")
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists")
    @patch("subprocess.run")
    def test_returns_both_stable_and_insiders_entries(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with both stable and insiders binaries,
        When detect is called,
        Then both stable and insiders entries are returned.
        """
        # ── Given ──
        mock_which.side_effect = lambda name: {
            "code": "/usr/bin/code",
            "code-insiders": "/usr/bin/code-insiders",
        }.get(name)
        mock_run.return_value = MagicMock(returncode=0, stdout="1.85.0\nhash\nlinux\n")
        mock_exists.side_effect = lambda p: (
            "/usr/share/code" in _norm(p) and "insiders" not in _norm(p).lower()
        )
        mock_is_dir.side_effect = lambda p: (
            ".config/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len([r for r in results if r.channel == "stable"]) == 1
        assert len([r for r in results if r.channel == "insiders"]) == 1

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_empty_when_neither_installed(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with neither stable nor insiders VS Code,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        # (mocks configure no VS Code presence)

        # ── When ──
        result = _make_provider().detect()

        # ── Then ──
        assert result == []

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which")
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_only_stable_when_no_insiders(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given Linux with only the stable binary on PATH,
        When detect is called,
        Then only a stable entry is returned with no insiders.
        """
        # ── Given ──
        mock_which.side_effect = lambda name: "/usr/bin/code" if name == "code" else None

        # ── When ──
        results = _make_provider().detect()

        # ── Then ──
        assert len([r for r in results if r.channel == "insiders"]) == 0
        assert len([r for r in results if r.channel == "stable"]) == 1


# ── TestVSCodePartialDetection ───────────────────────────────────────


class TestVSCodePartialDetection:
    """Tests for VS Code partial detection scenarios (US3)."""

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_low_confidence_with_config_dir_only(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given only a VS Code config directory without binary,
        When detect is called,
        Then a LOW confidence result is returned.
        """
        # ── Given ──
        mock_is_dir.side_effect = lambda p: (
            ".config/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        assert stable[0].confidence == ConfidenceLevel.LOW

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/code")
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    def test_returns_medium_confidence_with_binary_only(
        self,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given only a VS Code binary without config directory,
        When detect is called,
        Then a MEDIUM confidence result is returned.
        """
        # ── Given ──
        # (mocks configure binary only)

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        assert stable[0].confidence == ConfidenceLevel.MEDIUM

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/code")
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    @patch("subprocess.run")
    def test_returns_medium_confidence_with_binary_and_config_but_no_version(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given a VS Code binary and config dir but failed version resolution,
        When detect is called,
        Then a MEDIUM confidence result with None version is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        mock_is_dir.side_effect = lambda p: (
            ".config/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        assert stable[0].confidence == ConfidenceLevel.MEDIUM
        assert stable[0].version is None

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/code")
    @patch(f"{_VSCODE_MOD}._safe_is_dir")
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
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
        Given a VS Code binary, config dir, and successful version output,
        When detect is called,
        Then a HIGH confidence result with version is returned.
        """
        # ── Given ──
        mock_run.return_value = MagicMock(returncode=0, stdout="1.85.0\nhash\nlinux\n")
        mock_is_dir.side_effect = lambda p: (
            ".config/Code" in _norm(p) and "Insiders" not in _norm(p)
        )

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        assert stable[0].confidence == ConfidenceLevel.HIGH
        assert stable[0].version == "1.85.0"

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/code")
    @patch(f"{_VSCODE_MOD}._safe_is_dir", return_value=False)
    @patch(f"{_VSCODE_MOD}._safe_exists", return_value=False)
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="code", timeout=5))
    def test_returns_none_version_on_subprocess_timeout(
        self,
        mock_run: MagicMock,
        mock_exists: MagicMock,
        mock_is_dir: MagicMock,
        mock_which: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """
        Given a VS Code binary that times out when queried for version,
        When detect is called,
        Then the result has version set to None.
        """
        # ── Given ──
        # (timeout configured via decorator)

        # ── When ──
        results = _make_provider().detect()
        stable = [r for r in results if r.channel == "stable"]

        # ── Then ──
        assert len(stable) == 1
        assert stable[0].version is None
