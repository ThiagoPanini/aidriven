"""IDE provider protocol and registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from aidriven.discovery._models import DetectedIDE


@runtime_checkable
class IDEProvider(Protocol):
    """Contract for an IDE detection provider."""

    @property
    def name(self) -> str:
        """Provider display name used in diagnostics."""
        ...

    def detect(self) -> list[DetectedIDE]:
        """Scan the current platform and return detected installations.

        Returns an empty list (never raises) when nothing is found.
        May raise any Exception on unrecoverable errors; the orchestrator
        will catch and record these.
        """
        ...


class ProviderRegistry:
    """Manages the collection of registered IDE detection providers."""

    def __init__(self) -> None:
        self._providers: list[IDEProvider] = []

    def register(self, provider: IDEProvider) -> None:
        """Add a provider to the registry.

        Args:
            provider: The provider to register.

        Raises:
            ValueError: If a provider with the same name is already registered.
        """
        for existing in self._providers:
            if existing.name == provider.name:
                raise ValueError(f"A provider named '{provider.name}' is already registered.")
        self._providers.append(provider)

    @property
    def providers(self) -> list[IDEProvider]:
        """Return all registered providers in insertion order."""
        return list(self._providers)
