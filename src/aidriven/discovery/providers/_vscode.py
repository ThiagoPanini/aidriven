"""VS Code (Stable + Insiders) provider."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from aidriven.discovery._models import DetectedIDE, calculate_confidence
from aidriven.discovery._platform import current_platform, resolve_env_path, resolve_home

logger = logging.getLogger(__name__)

_TIMEOUT = 5  # seconds


class _ChannelSpec(NamedTuple):
    """Static description of one VS Code channel (stable or insiders)."""

    channel: str
    display_name: str
    binary_name: str
    # Platform-specific install paths (app bundle / install dir)
    macos_app: str
    linux_install: list[str]
    windows_install_subpath: str
    # Platform-specific config directories (relative to home / env var)
    macos_config_subpath: str
    linux_config_subpath: str
    windows_config_subpath: str  # relative to APPDATA


_STABLE = _ChannelSpec(
    channel="stable",
    display_name="Visual Studio Code",
    binary_name="code",
    macos_app="/Applications/Visual Studio Code.app",
    linux_install=["/usr/share/code", "/usr/lib/code", "/opt/visual-studio-code"],
    windows_install_subpath=r"Programs\Microsoft VS Code",
    macos_config_subpath="Library/Application Support/Code",
    linux_config_subpath=".config/Code",
    windows_config_subpath="Code",
)

_INSIDERS = _ChannelSpec(
    channel="insiders",
    display_name="Visual Studio Code - Insiders",
    binary_name="code-insiders",
    macos_app="/Applications/Visual Studio Code - Insiders.app",
    linux_install=["/usr/share/code-insiders", "/opt/visual-studio-code-insiders"],
    windows_install_subpath=r"Programs\Microsoft VS Code Insiders",
    macos_config_subpath="Library/Application Support/Code - Insiders",
    linux_config_subpath=".config/Code - Insiders",
    windows_config_subpath="Code - Insiders",
)


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


def _detect_version(binary_name: str, install_dir: Path | None) -> str | None:
    """Try to resolve the VS Code version.

    Strategy:
    1. Read ``package.json`` from the install directory.
    2. Fall back to ``<binary> --version`` CLI output.
    """
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
        for candidate_name in [f"{binary_name}.cmd", binary_name]:
            bin_path = install_dir / "bin" / candidate_name
            if _safe_exists(bin_path):
                binary = str(bin_path)
                break
    if binary is None:
        binary = shutil.which(binary_name)
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


def _detect_channel(spec: _ChannelSpec) -> DetectedIDE | None:
    """Detect a single VS Code channel installation."""
    platform = current_platform()
    home = resolve_home()

    binary_found = shutil.which(spec.binary_name) is not None
    install_path: Path | None = None
    config_dir_found = False

    if platform == "darwin":
        app_path = Path(spec.macos_app)
        if _safe_exists(app_path):
            binary_found = True
            install_path = app_path
        config_path = home / spec.macos_config_subpath
        config_dir_found = _safe_is_dir(config_path)

    elif platform == "linux":
        for candidate in spec.linux_install:
            p = Path(candidate)
            if _safe_exists(p):
                install_path = p
                break
        config_path = home / spec.linux_config_subpath
        config_dir_found = _safe_is_dir(config_path)

    else:  # windows
        localappdata = resolve_env_path("LOCALAPPDATA")
        appdata = resolve_env_path("APPDATA")
        if localappdata:
            win_install = localappdata / spec.windows_install_subpath
            if _safe_exists(win_install):
                install_path = win_install
        if appdata:
            config_dir_found = _safe_is_dir(appdata / spec.windows_config_subpath)

    if not binary_found and not config_dir_found:
        return None

    # Determine install_path for the result
    if install_path is None:
        # binary on PATH but no known install dir — use binary dir if available
        which_result = shutil.which(spec.binary_name)
        if which_result:
            install_path = Path(which_result).parent
        elif config_dir_found:
            # Only config dir found — use config dir as install_path indicator
            if platform == "darwin":
                install_path = home / spec.macos_config_subpath
            elif platform == "linux":
                install_path = home / spec.linux_config_subpath
            else:
                appdata_path = resolve_env_path("APPDATA")
                install_path = (
                    appdata_path / spec.windows_config_subpath
                    if appdata_path
                    else Path(spec.windows_config_subpath)
                )

    if install_path is None:
        return None

    version = _detect_version(spec.binary_name, install_path) if binary_found else None
    version_resolved = version is not None
    confidence = calculate_confidence(binary_found, config_dir_found, version_resolved)

    return DetectedIDE(
        identifier="vscode",
        display_name=spec.display_name,
        install_path=install_path,
        version=version,
        channel=spec.channel,
        confidence=confidence,
        detected_platform=platform,
    )


class VSCodeProvider:
    """Detects VS Code Stable and Insiders installations."""

    @property
    def name(self) -> str:
        return "VSCode"

    def detect(self) -> list[DetectedIDE]:
        """Detect VS Code (stable + insiders) on the current platform."""
        results: list[DetectedIDE] = []
        for spec in (_STABLE, _INSIDERS):
            try:
                ide = _detect_channel(spec)
                if ide is not None:
                    results.append(ide)
            except Exception:
                logger.debug(
                    "Unexpected error detecting VS Code channel '%s'",
                    spec.channel,
                    exc_info=True,
                )
        return results
