"""Platform detection and path resolution utilities."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def current_platform() -> str:
    """Return the current platform as a lowercase string.

    Returns:
        One of ``"darwin"``, ``"linux"``, or ``"windows"``.
        Falls back to the raw ``platform.system()`` value (lowercased) for
        unrecognised platforms.
    """
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    if system == "linux":
        return "linux"
    if system == "windows":
        return "windows"
    return system


def resolve_home() -> Path:
    """Return the current user's home directory as a Path."""
    return Path.home()


def resolve_env_path(var_name: str) -> Path | None:
    """Resolve an environment variable to a Path.

    Args:
        var_name: The environment variable name to look up.

    Returns:
        A ``Path`` constructed from the variable's value, or ``None`` if the
        variable is unset or empty.
    """
    value = os.environ.get(var_name)
    if not value:
        return None
    return Path(value)
