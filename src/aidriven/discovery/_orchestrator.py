"""Discovery orchestration logic."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aidriven.discovery._models import DetectedIDE, DiscoveryResult, ProviderDiagnostic

if TYPE_CHECKING:
    from aidriven.discovery._providers import ProviderRegistry

logger = logging.getLogger(__name__)


def run_discovery(registry: ProviderRegistry) -> DiscoveryResult:
    """Run all registered providers and aggregate results.

    Each provider is called inside an isolated try/except block so that a
    single failing provider does not prevent others from running (FR-010).

    Args:
        registry: The registry containing the providers to run.

    Returns:
        A :class:`DiscoveryResult` with all detected IDEs and any diagnostics
        captured from providers that raised exceptions.
    """
    detected_ides: list[DetectedIDE] = []
    diagnostics: list[ProviderDiagnostic] = []

    for provider in registry.providers:
        try:
            results = provider.detect()
            detected_ides.extend(results)
            logger.debug("Provider '%s' returned %d result(s).", provider.name, len(results))
        except Exception as exc:
            logger.warning(
                "Provider '%s' raised %s: %s",
                provider.name,
                type(exc).__name__,
                exc,
            )
            diagnostics.append(
                ProviderDiagnostic(
                    provider_name=provider.name,
                    error_type=type(exc).__name__,
                    message=str(exc),
                    paths_checked=[],
                )
            )

    return DiscoveryResult(
        detected_ides=detected_ides,
        diagnostics=diagnostics,
    )


__all__ = ["run_discovery"]
