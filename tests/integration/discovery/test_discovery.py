"""Integration tests for end-to-end IDE discovery."""

from __future__ import annotations

from pathlib import Path

from aidriven.discovery import (
    ConfidenceLevel,
    DetectedIDE,
    DiscoveryResult,
    ProviderRegistry,
    discover_ides,
)

# ── TestDiscoverIdesStructure ────────────────────────────────────────


class TestDiscoverIdesStructure:
    """Tests for discover_ides() return structure (US1)."""

    def test_returns_discovery_result_instance(self) -> None:
        """
        Given a default environment,
        When discover_ides is called,
        Then a DiscoveryResult instance is returned.
        """
        # ── When ──
        result = discover_ides()

        # ── Then ──
        assert isinstance(result, DiscoveryResult)

    def test_detected_ides_is_a_list(self) -> None:
        """
        Given a default environment,
        When discover_ides is called,
        Then detected_ides is a list.
        """
        # ── When ──
        result = discover_ides()

        # ── Then ──
        assert isinstance(result.detected_ides, list)

    def test_diagnostics_is_a_list(self) -> None:
        """
        Given a default environment,
        When discover_ides is called,
        Then diagnostics is a list.
        """
        # ── When ──
        result = discover_ides()

        # ── Then ──
        assert isinstance(result.diagnostics, list)

    def test_detected_ides_have_correct_field_types(self) -> None:
        """
        Given a default environment,
        When discover_ides is called,
        Then each detected IDE has fields with correct types.
        """
        # ── When ──
        result = discover_ides()

        # ── Then ──
        for ide in result.detected_ides:
            assert isinstance(ide, DetectedIDE)
            assert isinstance(ide.identifier, str)
            assert isinstance(ide.display_name, str)
            assert isinstance(ide.install_path, Path)
            assert ide.version is None or isinstance(ide.version, str)
            assert isinstance(ide.channel, str)
            assert isinstance(ide.confidence, ConfidenceLevel)
            assert isinstance(ide.detected_platform, str)

    def test_never_raises_under_any_circumstances(self) -> None:
        """
        Given a default environment,
        When discover_ides is called,
        Then it completes without raising an exception.
        """
        # ── When ──
        result = discover_ides()

        # ── Then ──
        assert result is not None


# ── TestCustomProviderIntegration ────────────────────────────────────


class TestCustomProviderIntegration:
    """Tests for extensibility via custom providers (FR-009, US4)."""

    def test_custom_registry_only_uses_custom_providers(self) -> None:
        """
        Given a custom registry with a single test provider,
        When discover_ides is called with that registry,
        Then only the custom provider's results are returned.
        """

        # ── Given ──
        class TestIDEProvider:
            @property
            def name(self) -> str:
                return "TestIDE"

            def detect(self) -> list[DetectedIDE]:
                return [
                    DetectedIDE(
                        identifier="testide",
                        display_name="Test IDE",
                        install_path=Path("/fake/testide"),
                        version="9.9.9",
                        channel="stable",
                        confidence=ConfidenceLevel.HIGH,
                        detected_platform="linux",
                    )
                ]

        registry = ProviderRegistry()
        registry.register(TestIDEProvider())

        # ── When ──
        result = discover_ides(registry=registry)

        # ── Then ──
        assert len(result.detected_ides) == 1
        assert result.detected_ides[0].identifier == "testide"

    def test_custom_provider_alongside_builtins(self) -> None:
        """
        Given a registry with built-in and custom providers,
        When discover_ides is called,
        Then the custom provider's results are included.
        """

        # ── Given ──
        class FixedProvider:
            @property
            def name(self) -> str:
                return "Fixed"

            def detect(self) -> list[DetectedIDE]:
                return [
                    DetectedIDE(
                        identifier="fixed",
                        display_name="Fixed IDE",
                        install_path=Path("/fake/fixed"),
                        version="1.0.0",
                        channel="stable",
                        confidence=ConfidenceLevel.HIGH,
                        detected_platform="linux",
                    )
                ]

        from aidriven.discovery.providers._cursor import CursorProvider
        from aidriven.discovery.providers._kiro import KiroProvider
        from aidriven.discovery.providers._vscode import VSCodeProvider

        registry = ProviderRegistry()
        registry.register(VSCodeProvider())
        registry.register(CursorProvider())
        registry.register(KiroProvider())
        registry.register(FixedProvider())

        # ── When ──
        result = discover_ides(registry=registry)

        # ── Then ──
        fixed_entries = result.by_identifier("fixed")
        assert len(fixed_entries) == 1
        assert fixed_entries[0].version == "1.0.0"

    def test_failing_custom_provider_captured_in_diagnostics(self) -> None:
        """
        Given a custom provider that raises RuntimeError,
        When discover_ides is called,
        Then the error appears in diagnostics without crashing.
        """

        # ── Given ──
        class BrokenProvider:
            @property
            def name(self) -> str:
                return "Broken"

            def detect(self) -> list[DetectedIDE]:
                raise RuntimeError("intentional failure")

        registry = ProviderRegistry()
        registry.register(BrokenProvider())

        # ── When ──
        result = discover_ides(registry=registry)

        # ── Then ──
        assert result.is_empty
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].provider_name == "Broken"
        assert result.diagnostics[0].error_type == "RuntimeError"
