"""Cursor IDE provider."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from aidriven.discovery._models import DetectedIDE, calculate_confidence
from aidriven.discovery._platform import current_platform, resolve_env_path, resolve_home

logger = logging.getLogger(__name__)

_TIMEOUT = 5  # seconds

_LINUX_INSTALL_CANDIDATES = [
    "/usr/share/cursor",
    "/opt/cursor",
    "/usr/lib/cursor",
]

_MACOS_APP = "/Applications/Cursor.app"


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
    """Attempt to detect Cursor version via package.json or CLI."""
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

    binary = shutil.which("cursor")
    if binary is None:
        return None
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


class CursorProvider:
    """Detects Cursor IDE installations."""

    @property
    def name(self) -> str:
        return "Cursor"

    def detect(self) -> list[DetectedIDE]:
        """Detect Cursor on the current platform."""
        platform = current_platform()
        home = resolve_home()

        binary_found = shutil.which("cursor") is not None
        install_path: Path | None = None
        config_dir_found = False

        if platform == "darwin":
            app_path = Path(_MACOS_APP)
            if _safe_exists(app_path):
                binary_found = True
                install_path = app_path
            config_dir_found = _safe_is_dir(home / "Library/Application Support/Cursor")

        elif platform == "linux":
            for candidate in _LINUX_INSTALL_CANDIDATES:
                p = Path(candidate)
                if _safe_exists(p):
                    install_path = p
                    break
            config_dir_found = _safe_is_dir(home / ".config/Cursor")

        else:  # windows
            localappdata = resolve_env_path("LOCALAPPDATA")
            appdata = resolve_env_path("APPDATA")
            if localappdata:
                win_install = localappdata / "Programs" / "Cursor"
                if _safe_exists(win_install):
                    install_path = win_install
            if appdata:
                config_dir_found = _safe_is_dir(appdata / "Cursor")

        if not binary_found and not config_dir_found:
            return []

        if install_path is None:
            which_result = shutil.which("cursor")
            if which_result:
                install_path = Path(which_result).parent
            elif config_dir_found:
                if platform == "darwin":
                    install_path = home / "Library/Application Support/Cursor"
                elif platform == "linux":
                    install_path = home / ".config/Cursor"
                else:
                    appdata_path = resolve_env_path("APPDATA")
                    install_path = appdata_path / "Cursor" if appdata_path else Path("Cursor")

        if install_path is None:
            return []

        version = _detect_version(install_path) if binary_found else None
        version_resolved = version is not None
        confidence = calculate_confidence(binary_found, config_dir_found, version_resolved)

        return [
            DetectedIDE(
                identifier="cursor",
                display_name="Cursor",
                install_path=install_path,
                version=version,
                channel="stable",
                confidence=confidence,
                detected_platform=platform,
            )
        ]
