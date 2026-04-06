"""Public API for the IDE Discovery Service.

Usage::

    from aidriven.discovery import discover_ides

    result = discover_ides()
    for ide in result.detected_ides:
        print(ide.display_name, ide.version)
"""

from __future__ import annotations

from aidriven.discovery._models import (
    ConfidenceLevel,
    DetectedIDE,
    DiscoveryResult,
    ProviderDiagnostic,
    calculate_confidence,
)
from aidriven.discovery._orchestrator import run_discovery
from aidriven.discovery._providers import IDEProvider, ProviderRegistry

__all__ = [
    "ConfidenceLevel",
    "DetectedIDE",
    "DiscoveryResult",
    "IDEProvider",
    "ProviderDiagnostic",
    "ProviderRegistry",
    "calculate_confidence",
    "discover_ides",
]


def discover_ides(
    *,
    registry: ProviderRegistry | None = None,
) -> DiscoveryResult:
    """Discover locally installed AI-oriented IDEs.

    Args:
        registry: Optional custom :class:`ProviderRegistry`. When ``None``,
            the default registry containing VS Code, Cursor, and Kiro
            providers is used. Pass a custom registry to add or replace
            providers without modifying built-in code.

    Returns:
        A :class:`DiscoveryResult` that always returns (never raises).
        Provider failures are captured in ``result.diagnostics``.
    """
    if registry is None:
        # Import lazily to avoid importing all providers when the module is
        # loaded — keeps startup fast and avoids side effects at import time
        # beyond what the user explicitly requests.
        from aidriven.discovery.providers import default_registry

        registry = default_registry

    return run_discovery(registry)
