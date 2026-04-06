"""Tests for run_discovery() orchestrator."""

from __future__ import annotations

from pathlib import Path

from aidriven.discovery._models import ConfidenceLevel, DetectedIDE, DiscoveryResult
from aidriven.discovery._orchestrator import run_discovery
from aidriven.discovery._providers import ProviderRegistry

# ── Fixtures ──────────────────────────────────────────────────────────


class StubProvider:
    """Minimal IDEProvider-conformant stub for testing."""

    def __init__(
        self,
        name: str,
        results: list[DetectedIDE] | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._name = name
        self._results = results or []
        self._raises = raises

    @property
    def name(self) -> str:
        return self._name

    def detect(self) -> list[DetectedIDE]:
        if self._raises is not None:
            raise self._raises
        return self._results


def _make_ide(identifier: str = "vscode") -> DetectedIDE:
    return DetectedIDE(
        identifier=identifier,
        display_name="IDE",
        install_path=Path("/usr/share/code"),
        version=None,
        channel="stable",
        confidence=ConfidenceLevel.HIGH,
        detected_platform="linux",
    )


# ── TestRunDiscovery ─────────────────────────────────────────────────


class TestRunDiscovery:
    """Tests for run_discovery()."""

    def test_returns_empty_result_for_empty_registry(self) -> None:
        """
        Given an empty provider registry,
        When run_discovery is called,
        Then an empty DiscoveryResult with no diagnostics is returned.
        """
        # ── Given ──
        registry = ProviderRegistry()

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert isinstance(result, DiscoveryResult)
        assert result.is_empty
        assert result.diagnostics == []

    def test_returns_detected_ides_from_provider(self) -> None:
        """
        Given a registry with one provider returning an IDE,
        When run_discovery is called,
        Then the result contains the detected IDE.
        """
        # ── Given ──
        ide = _make_ide()
        registry = ProviderRegistry()
        registry.register(StubProvider("VSCode", results=[ide]))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert result.detected_ides == [ide]
        assert result.diagnostics == []

    def test_aggregates_results_from_multiple_providers(self) -> None:
        """
        Given a registry with two providers each returning one IDE,
        When run_discovery is called,
        Then both IDEs appear in the result.
        """
        # ── Given ──
        vscode = _make_ide("vscode")
        cursor = _make_ide("cursor")
        registry = ProviderRegistry()
        registry.register(StubProvider("VSCode", results=[vscode]))
        registry.register(StubProvider("Cursor", results=[cursor]))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert set(r.identifier for r in result.detected_ides) == {"vscode", "cursor"}

    def test_captures_failing_provider_as_diagnostic(self) -> None:
        """
        Given a registry with a provider that raises RuntimeError,
        When run_discovery is called,
        Then the error is captured as a diagnostic.
        """
        # ── Given ──
        error = RuntimeError("something broke")
        registry = ProviderRegistry()
        registry.register(StubProvider("Broken", raises=error))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert result.is_empty
        assert len(result.diagnostics) == 1
        diag = result.diagnostics[0]
        assert diag.provider_name == "Broken"
        assert diag.error_type == "RuntimeError"
        assert "something broke" in diag.message

    def test_isolates_failure_so_other_providers_continue(self) -> None:
        """
        Given a registry with a failing and a working provider,
        When run_discovery is called,
        Then the working provider's results are returned alongside the diagnostic.
        """
        # ── Given ──
        ide = _make_ide("cursor")
        registry = ProviderRegistry()
        registry.register(StubProvider("Broken", raises=ValueError("oops")))
        registry.register(StubProvider("Cursor", results=[ide]))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert len(result.detected_ides) == 1
        assert result.detected_ides[0].identifier == "cursor"
        assert len(result.diagnostics) == 1

    def test_handles_mixed_success_and_failure(self) -> None:
        """
        Given providers with success, failure, and empty results,
        When run_discovery is called,
        Then successful IDEs and failure diagnostics are both collected.
        """
        # ── Given ──
        vscode = _make_ide("vscode")
        registry = ProviderRegistry()
        registry.register(StubProvider("VSCode", results=[vscode]))
        registry.register(StubProvider("Failing", raises=OSError("disk error")))
        registry.register(StubProvider("Kiro", results=[]))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert result.detected_ides == [vscode]
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].error_type == "OSError"

    def test_returns_empty_result_when_provider_returns_nothing(self) -> None:
        """
        Given a provider that returns an empty list,
        When run_discovery is called,
        Then the result is empty with no diagnostics.
        """
        # ── Given ──
        registry = ProviderRegistry()
        registry.register(StubProvider("Empty"))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert result.is_empty
        assert result.diagnostics == []

    def test_uses_custom_registry_when_provided(self) -> None:
        """
        Given a custom registry with a stub provider,
        When run_discovery is called with that registry,
        Then only the custom provider's results are returned.
        """
        # ── Given ──
        stub_ide = _make_ide("custom")
        registry = ProviderRegistry()
        registry.register(StubProvider("Custom", results=[stub_ide]))

        # ── When ──
        result = run_discovery(registry)

        # ── Then ──
        assert result.detected_ides == [stub_ide]
