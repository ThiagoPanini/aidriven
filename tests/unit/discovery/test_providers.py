"""Tests for IDEProvider protocol and ProviderRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from aidriven.discovery._models import ConfidenceLevel, DetectedIDE
from aidriven.discovery._providers import IDEProvider, ProviderRegistry

# ── Fixtures ──────────────────────────────────────────────────────────


class StubProvider:
    """Minimal IDEProvider-conformant stub for testing."""

    def __init__(self, name: str, results: list[DetectedIDE] | None = None) -> None:
        self._name = name
        self._results = results or []

    @property
    def name(self) -> str:
        return self._name

    def detect(self) -> list[DetectedIDE]:
        return self._results


# ── TestIDEProviderProtocol ──────────────────────────────────────────


class TestIDEProviderProtocol:
    """Tests for IDEProvider protocol conformance."""

    def test_stub_conforms_to_protocol(self) -> None:
        """
        Given a class implementing name and detect,
        When checked against IDEProvider protocol,
        Then it is recognized as a conforming instance.
        """
        # ── When ──
        provider: IDEProvider = StubProvider("Test")

        # ── Then ──
        assert isinstance(provider, IDEProvider)

    def test_name_property_returns_expected_value(self) -> None:
        """
        Given a provider with name 'MyProvider',
        When the name property is accessed,
        Then 'MyProvider' is returned.
        """
        # ── Given ──
        provider = StubProvider("MyProvider")

        # ── When ──
        result = provider.name

        # ── Then ──
        assert result == "MyProvider"

    def test_detect_returns_empty_list_by_default(self) -> None:
        """
        Given a provider with no configured results,
        When detect is called,
        Then an empty list is returned.
        """
        # ── Given ──
        provider = StubProvider("Empty")

        # ── When ──
        result = provider.detect()

        # ── Then ──
        assert result == []


# ── TestProviderRegistry ─────────────────────────────────────────────


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_empty_registry_has_no_providers(self) -> None:
        """
        Given a newly created registry,
        When providers is accessed,
        Then an empty list is returned.
        """
        # ── Given ──
        registry = ProviderRegistry()

        # ── Then ──
        assert registry.providers == []

    def test_register_adds_provider(self) -> None:
        """
        Given an empty registry,
        When a provider is registered,
        Then the registry contains that provider.
        """
        # ── Given ──
        registry = ProviderRegistry()
        provider = StubProvider("Alpha")

        # ── When ──
        registry.register(provider)

        # ── Then ──
        assert registry.providers == [provider]

    def test_register_preserves_insertion_order(self) -> None:
        """
        Given three providers registered in order,
        When providers is accessed,
        Then they appear in insertion order.
        """
        # ── Given ──
        registry = ProviderRegistry()
        a = StubProvider("Alpha")
        b = StubProvider("Beta")
        c = StubProvider("Gamma")

        # ── When ──
        registry.register(a)
        registry.register(b)
        registry.register(c)

        # ── Then ──
        assert registry.providers == [a, b, c]

    def test_raises_value_error_for_duplicate_name(self) -> None:
        """
        Given a registry with an 'Alpha' provider,
        When another provider named 'Alpha' is registered,
        Then a ValueError is raised.
        """
        # ── Given ──
        registry = ProviderRegistry()
        registry.register(StubProvider("Alpha"))

        # ── When / Then ──
        with pytest.raises(ValueError, match="Alpha"):
            registry.register(StubProvider("Alpha"))

    def test_providers_returns_defensive_copy(self) -> None:
        """
        Given a registry with one provider,
        When the returned providers list is cleared,
        Then the registry still contains the original provider.
        """
        # ── Given ──
        registry = ProviderRegistry()
        provider = StubProvider("Alpha")
        registry.register(provider)

        # ── When ──
        providers_copy = registry.providers
        providers_copy.clear()

        # ── Then ──
        assert len(registry.providers) == 1

    def test_register_multiple_different_names(self) -> None:
        """
        Given three providers with unique names,
        When all are registered,
        Then the registry contains all three.
        """
        # ── Given ──
        registry = ProviderRegistry()

        # ── When ──
        for name in ["VSCode", "Cursor", "Kiro"]:
            registry.register(StubProvider(name))

        # ── Then ──
        assert len(registry.providers) == 3

    def test_registered_provider_returns_detection_results(self) -> None:
        """
        Given a provider configured with IDE results,
        When detect is called through the registry,
        Then the expected IDEs are returned.
        """
        # ── Given ──
        ide = DetectedIDE(
            identifier="vscode",
            display_name="Visual Studio Code",
            install_path=Path("/usr/share/code"),
            version="1.80.0",
            channel="stable",
            confidence=ConfidenceLevel.HIGH,
            detected_platform="linux",
        )
        provider = StubProvider("VSCode", results=[ide])
        registry = ProviderRegistry()
        registry.register(provider)

        # ── When ──
        result = registry.providers[0].detect()

        # ── Then ──
        assert result == [ide]
