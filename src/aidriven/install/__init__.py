"""Public API for the aidriven install subsystem."""

from __future__ import annotations

from aidriven.install._models import (
    ArtifactType,
    InstallMode,
    InstallRequest,
    InstallResult,
    Scope,
)
from aidriven.install._service import install_artifact

__all__ = [
    "ArtifactType",
    "InstallMode",
    "InstallRequest",
    "InstallResult",
    "Scope",
    "install_artifact",
]
