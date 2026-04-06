"""Tests for discovery data models and calculate_confidence()."""

from __future__ import annotations

from pathlib import Path

import pytest

from aidriven.discovery._models import (
    ConfidenceLevel,
    DetectedIDE,
    DiscoveryResult,
    ProviderDiagnostic,
    calculate_confidence,
)

# ── TestCalculateConfidence ───────────────────────────────────────────


class TestCalculateConfidence:
    """Tests for calculate_confidence() truth table."""

    def test_returns_high_when_all_evidence_present(self) -> None:
        """
        Given binary, config, and version evidence are all present,
        When confidence is calculated,
        Then the result is HIGH.
        """
        # ── Given ──
        binary_found, config_found, version_resolved = True, True, True

        # ── When ──
        result = calculate_confidence(binary_found, config_found, version_resolved)

        # ── Then ──
        assert result == ConfidenceLevel.HIGH

    def test_returns_medium_when_binary_and_config_without_version(self) -> None:
        """
        Given binary and config evidence but no version,
        When confidence is calculated,
        Then the result is MEDIUM.
        """
        # ── Given ──
        binary_found, config_found, version_resolved = True, True, False

        # ── When ──
        result = calculate_confidence(binary_found, config_found, version_resolved)

        # ── Then ──
        assert result == ConfidenceLevel.MEDIUM

    def test_returns_medium_when_binary_only(self) -> None:
        """
        Given only binary evidence,
        When confidence is calculated,
        Then the result is MEDIUM.
        """
        # ── Given ──
        binary_found, config_found, version_resolved = True, False, False

        # ── When ──
        result = calculate_confidence(binary_found, config_found, version_resolved)

        # ── Then ──
        assert result == ConfidenceLevel.MEDIUM

    def test_returns_medium_when_binary_and_version_without_config(self) -> None:
        """
        Given binary and version evidence but no config,
        When confidence is calculated,
        Then the result is MEDIUM.
        """
        # ── Given ──
        binary_found, config_found, version_resolved = True, False, True

        # ── When ──
        result = calculate_confidence(binary_found, config_found, version_resolved)

        # ── Then ──
        assert result == ConfidenceLevel.MEDIUM

    def test_returns_low_when_config_only(self) -> None:
        """
        Given only config evidence without binary,
        When confidence is calculated,
        Then the result is LOW.
        """
        # ── Given ──
        binary_found, config_found, version_resolved = False, True, False

        # ── When ──
        result = calculate_confidence(binary_found, config_found, version_resolved)

        # ── Then ──
        assert result == ConfidenceLevel.LOW

    def test_returns_low_when_config_and_version_without_binary(self) -> None:
        """
        Given config and version evidence but no binary,
        When confidence is calculated,
        Then the result is LOW.
        """
        # ── Given ──
        binary_found, config_found, version_resolved = False, True, True

        # ── When ──
        result = calculate_confidence(binary_found, config_found, version_resolved)

        # ── Then ──
        assert result == ConfidenceLevel.LOW


# ── TestDetectedIDE ───────────────────────────────────────────────────


class TestDetectedIDE:
    """Tests for DetectedIDE frozen dataclass invariants."""

    def _make(self, **kwargs: object) -> DetectedIDE:
        defaults: dict[str, object] = {
            "identifier": "vscode",
            "display_name": "Visual Studio Code",
            "install_path": Path("/usr/share/code"),
            "version": "1.80.0",
            "channel": "stable",
            "confidence": ConfidenceLevel.HIGH,
            "detected_platform": "linux",
        }
        defaults.update(kwargs)
        return DetectedIDE(**defaults)  # type: ignore[arg-type]

    def test_creates_instance_with_expected_fields(self) -> None:
        """
        Given valid DetectedIDE parameters,
        When the instance is created,
        Then the fields match the provided values.
        """
        # ── When ──
        ide = self._make()

        # ── Then ──
        assert ide.identifier == "vscode"
        assert ide.channel == "stable"

    def test_raises_when_mutating_frozen_instance(self) -> None:
        """
        Given a frozen DetectedIDE instance,
        When a field is mutated,
        Then an AttributeError or TypeError is raised.
        """
        # ── Given ──
        ide = self._make()

        # ── When / Then ──
        with pytest.raises((AttributeError, TypeError)):
            ide.identifier = "cursor"  # type: ignore[misc]

    def test_allows_none_version(self) -> None:
        """
        Given version is set to None,
        When the instance is created,
        Then the version field is None.
        """
        # ── When ──
        ide = self._make(version=None)

        # ── Then ──
        assert ide.version is None


# ── TestProviderDiagnostic ────────────────────────────────────────────


class TestProviderDiagnostic:
    """Tests for ProviderDiagnostic frozen dataclass."""

    def test_creates_instance_with_expected_fields(self) -> None:
        """
        Given valid diagnostic parameters,
        When the instance is created,
        Then all fields match the provided values.
        """
        # ── When ──
        diag = ProviderDiagnostic(
            provider_name="VSCode",
            error_type="PermissionError",
            message="Access denied",
            paths_checked=[Path("/opt/vscode")],
        )

        # ── Then ──
        assert diag.provider_name == "VSCode"
        assert diag.paths_checked == [Path("/opt/vscode")]

    def test_raises_when_mutating_frozen_instance(self) -> None:
        """
        Given a frozen ProviderDiagnostic instance,
        When a field is mutated,
        Then an AttributeError or TypeError is raised.
        """
        # ── Given ──
        diag = ProviderDiagnostic(
            provider_name="VSCode",
            error_type="PermissionError",
            message="err",
            paths_checked=[],
        )

        # ── When / Then ──
        with pytest.raises((AttributeError, TypeError)):
            diag.message = "changed"  # type: ignore[misc]


# ── TestDiscoveryResult ──────────────────────────────────────────────


class TestDiscoveryResult:
    """Tests for DiscoveryResult properties."""

    def _make_ide(
        self, identifier: str = "vscode", install_path: Path | None = None
    ) -> DetectedIDE:
        return DetectedIDE(
            identifier=identifier,
            display_name="IDE",
            install_path=install_path or Path("/usr/share/code"),
            version=None,
            channel="stable",
            confidence=ConfidenceLevel.HIGH,
            detected_platform="linux",
        )

    def test_is_empty_returns_true_when_no_ides(self) -> None:
        """
        Given a result with no detected IDEs,
        When is_empty is checked,
        Then it returns True.
        """
        # ── Given ──
        result = DiscoveryResult(detected_ides=[], diagnostics=[])

        # ── Then ──
        assert result.is_empty is True

    def test_is_empty_returns_false_when_ides_present(self) -> None:
        """
        Given a result with one detected IDE,
        When is_empty is checked,
        Then it returns False.
        """
        # ── Given ──
        result = DiscoveryResult(detected_ides=[self._make_ide()], diagnostics=[])

        # ── Then ──
        assert result.is_empty is False

    def test_by_identifier_returns_matching_ides(self) -> None:
        """
        Given a result with vscode and cursor IDEs,
        When filtering by 'vscode',
        Then only the vscode IDE is returned.
        """
        # ── Given ──
        vscode = self._make_ide("vscode")
        cursor = self._make_ide("cursor")
        result = DiscoveryResult(detected_ides=[vscode, cursor], diagnostics=[])

        # ── When ──
        filtered = result.by_identifier("vscode")

        # ── Then ──
        assert filtered == [vscode]

    def test_by_identifier_returns_empty_for_unknown(self) -> None:
        """
        Given a result with only vscode,
        When filtering by 'kiro',
        Then an empty list is returned.
        """
        # ── Given ──
        result = DiscoveryResult(detected_ides=[self._make_ide()], diagnostics=[])

        # ── When ──
        filtered = result.by_identifier("kiro")

        # ── Then ──
        assert filtered == []

    def test_by_identifier_returns_all_matching_entries(self) -> None:
        """
        Given a result with stable and insiders vscode entries,
        When filtering by 'vscode',
        Then both entries are returned.
        """
        # ── Given ──
        stable = self._make_ide("vscode")
        insiders = DetectedIDE(
            identifier="vscode",
            display_name="VS Code Insiders",
            install_path=Path("/usr/share/code-insiders"),
            version=None,
            channel="insiders",
            confidence=ConfidenceLevel.MEDIUM,
            detected_platform="linux",
        )
        result = DiscoveryResult(detected_ides=[stable, insiders], diagnostics=[])

        # ── When ──
        filtered = result.by_identifier("vscode")

        # ── Then ──
        assert len(filtered) == 2

    def test_viable_ides_excludes_nonexistent_paths(self, tmp_path: Path) -> None:
        """
        Given IDEs with one real and one nonexistent install path,
        When viable_ides is accessed,
        Then only the IDE with the existing path is returned.
        """
        # ── Given ──
        real_path = tmp_path / "vscode"
        real_path.mkdir()
        nonexistent = Path("/does/not/exist/vscode")

        viable = self._make_ide("vscode", install_path=real_path)
        not_viable = self._make_ide("cursor", install_path=nonexistent)
        result = DiscoveryResult(detected_ides=[viable, not_viable], diagnostics=[])

        # ── When ──
        viable_list = result.viable_ides

        # ── Then ──
        assert viable_list == [viable]

    def test_raises_when_mutating_frozen_instance(self) -> None:
        """
        Given a frozen DiscoveryResult instance,
        When detected_ides is reassigned,
        Then an AttributeError or TypeError is raised.
        """
        # ── Given ──
        result = DiscoveryResult(detected_ides=[], diagnostics=[])

        # ── When / Then ──
        with pytest.raises((AttributeError, TypeError)):
            result.detected_ides = [self._make_ide()]  # type: ignore[misc]
