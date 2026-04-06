"""Kiro IDE provider."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from aidriven.discovery._models import DetectedIDE, calculate_confidence
from aidriven.discovery._platform import current_platform, resolve_env_path, resolve_home

logger = logging.getLogger(__name__)

_TIMEOUT = 5  # seconds

_LINUX_INSTALL_CANDIDATES = [
    "/usr/share/kiro",
    "/opt/kiro",
    "/usr/lib/kiro",
]

_MACOS_APP = "/Applications/Kiro.app"


def _safe_exists(path: Path) -> bool:
    try:
        return path.exists()
    except (OSError, PermissionError):
        return False


def _safe_is_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except (OSError, PermissionError):
        return False


def _detect_version(install_dir: Path | None) -> str | None:
    """Attempt to detect Kiro version via package.json or CLI."""
    if install_dir is not None and _safe_exists(install_dir):
        pkg = install_dir / "resources" / "app" / "package.json"
        if _safe_exists(pkg):
            try:
                import json

                data = json.loads(pkg.read_text(encoding="utf-8"))
                version = data.get("version")
                if isinstance(version, str) and version:
                    return version
            except (OSError, ValueError, KeyError):
                pass

    # Prefer the CLI wrapper in install_dir/bin/ to avoid launching the GUI on Windows
    binary: str | None = None
    if install_dir is not None and _safe_is_dir(install_dir / "bin"):
        for candidate_name in ["kiro.cmd", "kiro"]:
            bin_path = install_dir / "bin" / candidate_name
            if _safe_exists(bin_path):
                binary = str(bin_path)
                break
    if binary is None:
        binary = shutil.which("kiro")
    if binary is None:
        return None
    try:
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE
            proc = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
                startupinfo=si,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            proc = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


class KiroProvider:
    """Detects Kiro IDE installations."""

    @property
    def name(self) -> str:
        return "Kiro"

    def detect(self) -> list[DetectedIDE]:
        """Detect Kiro on the current platform."""
        platform = current_platform()
        home = resolve_home()

        binary_found = shutil.which("kiro") is not None
        install_path: Path | None = None
        config_dir_found = False

        if platform == "darwin":
            app_path = Path(_MACOS_APP)
            if _safe_exists(app_path):
                binary_found = True
                install_path = app_path
            config_dir_found = _safe_is_dir(home / "Library/Application Support/Kiro")

        elif platform == "linux":
            for candidate in _LINUX_INSTALL_CANDIDATES:
                p = Path(candidate)
                if _safe_exists(p):
                    install_path = p
                    break
            config_dir_found = _safe_is_dir(home / ".config/Kiro")

        else:  # windows
            localappdata = resolve_env_path("LOCALAPPDATA")
            appdata = resolve_env_path("APPDATA")
            if localappdata:
                win_install = localappdata / "Programs" / "Kiro"
                if _safe_exists(win_install):
                    install_path = win_install
            if appdata:
                config_dir_found = _safe_is_dir(appdata / "Kiro")

        if not binary_found and not config_dir_found:
            return []

        if install_path is None:
            which_result = shutil.which("kiro")
            if which_result:
                install_path = Path(which_result).parent
            elif config_dir_found:
                if platform == "darwin":
                    install_path = home / "Library/Application Support/Kiro"
                elif platform == "linux":
                    install_path = home / ".config/Kiro"
                else:
                    appdata_path = resolve_env_path("APPDATA")
                    install_path = appdata_path / "Kiro" if appdata_path else Path("Kiro")

        if install_path is None:
            return []

        version = _detect_version(install_path) if binary_found else None
        version_resolved = version is not None
        confidence = calculate_confidence(binary_found, config_dir_found, version_resolved)

        return [
            DetectedIDE(
                identifier="kiro",
                display_name="Kiro",
                install_path=install_path,
                version=version,
                channel="stable",
                confidence=confidence,
                detected_platform=platform,
            )
        ]
