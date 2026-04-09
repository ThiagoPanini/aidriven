"""Path helpers: project-root resolution, canonical dirs, scope roots, cache dir."""

from __future__ import annotations

import os
import platform
from pathlib import Path

from aidriven.install._models import AITarget, Scope


def resolve_project_root(cwd: Path | None = None) -> Path:
    """Walk up from *cwd* looking for a `.git` directory; fall back to *cwd*."""
    start = (cwd or Path.cwd()).resolve()
    current = start
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            # Reached filesystem root — fall back to start
            return start
        current = parent


def user_cache_dir() -> Path:
    """Return the OS-specific user cache directory for aidriven.

    - Linux/macOS: ``~/.cache/aidriven``
    - Windows: ``%LOCALAPPDATA%\\aidriven\\Cache``
    """
    system = platform.system()
    if system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local_app_data) / "aidriven" / "Cache"
    # Linux, macOS, and fallback
    xdg = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(xdg) / "aidriven"


def user_lockfile_path() -> Path:
    """Return the path to the user-scope install-records lockfile.

    Co-located at the cache root (NOT inside the ``cache/`` subdirectory):
    - Linux/macOS: ``~/.cache/aidriven/install-records.json``
    - Windows: ``%LOCALAPPDATA%\\aidriven\\install-records.json``
    """
    system = platform.system()
    if system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local_app_data) / "aidriven" / "install-records.json"
    xdg = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(xdg) / "aidriven" / "install-records.json"


def scope_base_path(scope: Scope, project_root: Path) -> Path:
    """Return the base path for a given scope."""
    if scope == Scope.USER:
        return Path.home()
    return project_root


def canonical_dir(base: Path, name: str) -> Path:
    """Return ``<base>/.agents/skills/<name>`` — the canonical install directory."""
    return base / ".agents" / "skills" / name


def read_path_for_target(target: AITarget, scope: Scope, base: Path, name: str) -> Path:
    """Return the read path for *target* at *scope*.

    For project scope the read path is ``<base>/<project_read_path>/<name>``.
    For user scope the read path is ``<base>/<user_read_path>/<name>``.
    """
    if scope == Scope.USER:
        return base / target.user_read_path / name
    return base / target.project_read_path / name


def needs_symlink(target: AITarget, scope: Scope, base: Path, name: str) -> bool:
    """Return True if the read path differs from the canonical path."""
    canon = canonical_dir(base, name)
    read = read_path_for_target(target, scope, base, name)
    return canon != read
