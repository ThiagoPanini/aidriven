"""Data models for the IDE Discovery Service."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ConfidenceLevel(enum.Enum):
    """Detection confidence level based on evidence completeness."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def calculate_confidence(
    binary_found: bool,
    config_dir_found: bool,
    version_resolved: bool,
) -> ConfidenceLevel:
    """Calculate detection confidence from evidence booleans.

    Truth table:
    - binary + config + version → HIGH
    - binary + config (no version) → MEDIUM
    - binary only (no config) → MEDIUM
    - config only (no binary) → LOW
    - nothing → caller must not create a DetectedIDE entry

    Args:
        binary_found: Whether the IDE binary or app bundle was located.
        config_dir_found: Whether the IDE configuration directory was found.
        version_resolved: Whether the IDE version was successfully resolved.

    Returns:
        The appropriate ConfidenceLevel for the evidence combination.
    """
    if binary_found and config_dir_found and version_resolved:
        return ConfidenceLevel.HIGH
    if binary_found and config_dir_found:
        return ConfidenceLevel.MEDIUM
    if binary_found:
        return ConfidenceLevel.MEDIUM
    # config_dir_found only
    return ConfidenceLevel.LOW


@dataclass(frozen=True)
class DetectedIDE:
    """A single detected IDE installation."""

    identifier: str
    display_name: str
    install_path: Path
    version: str | None
    channel: str
    confidence: ConfidenceLevel
    detected_platform: str


@dataclass(frozen=True)
class ProviderDiagnostic:
    """Diagnostic information from a provider that encountered an issue."""

    provider_name: str
    error_type: str
    message: str
    paths_checked: list[Path]


@dataclass(frozen=True)
class DiscoveryResult:
    """Aggregate output of the discovery service."""

    detected_ides: list[DetectedIDE]
    diagnostics: list[ProviderDiagnostic]

    @property
    def is_empty(self) -> bool:
        """Return True if no IDEs were detected."""
        return len(self.detected_ides) == 0

    def by_identifier(self, identifier: str) -> list[DetectedIDE]:
        """Filter results by IDE identifier."""
        return [ide for ide in self.detected_ides if ide.identifier == identifier]

    @property
    def viable_ides(self) -> list[DetectedIDE]:
        """Return only IDEs meeting minimum viability threshold (FR-012).

        An IDE is viable when both identifier is non-empty AND install_path exists.
        """
        return [ide for ide in self.detected_ides if ide.identifier and ide.install_path.exists()]
