"""Unit tests for AI target auto-detection (US5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aidriven.install._models import ArtifactType, InstallRequest
from aidriven.install._service import (
    AmbiguousTargetsError,
    NoTargetsFoundError,
    _resolve_targets,
)


def _request(targets: tuple[str, ...] = ()) -> InstallRequest:
    return InstallRequest(
        artifact_type=ArtifactType.SKILL,
        name="code-reviewer",
        targets=targets,
    )


class TestAutoDetectSingleMarker:
    """Single marker present → returns the matching target."""

    def test_claude_marker_detects_claude(self, tmp_path: Path) -> None:
        """
        Given a project with .claude/ directory (Claude marker),
        When _resolve_targets is called with no explicit targets,
        Then it returns ('claude',) without raising.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude").mkdir()

        # ── When ──
        result = _resolve_targets(_request(), tmp_path)

        # ── Then ──
        assert set(result) == {"claude"}

    def test_copilot_marker_detects_copilot(self, tmp_path: Path) -> None:
        """
        Given a project with .github/copilot-instructions.md (Copilot marker),
        When _resolve_targets is called with no explicit targets,
        Then it returns ('copilot',).
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "copilot-instructions.md").write_text("# Copilot", encoding="utf-8")

        # ── When ──
        result = _resolve_targets(_request(), tmp_path)

        # ── Then ──
        assert set(result) == {"copilot"}


class TestAutoDetectMultipleMarkers:
    """Multiple markers present → raises AmbiguousTargetsError."""

    def test_raises_ambiguous_when_both_markers_present(self, tmp_path: Path) -> None:
        """
        Given a project with both .claude/ and .github/copilot-instructions.md,
        When _resolve_targets is called with no explicit targets,
        Then AmbiguousTargetsError is raised listing both targets.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude").mkdir()
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "copilot-instructions.md").write_text("# Copilot", encoding="utf-8")

        # ── When / Then ──
        with pytest.raises(AmbiguousTargetsError) as exc_info:
            _resolve_targets(_request(), tmp_path)

        error = exc_info.value
        assert hasattr(error, "exit_code")
        assert "claude" in str(error).lower() or "copilot" in str(error).lower()


class TestAutoDetectNoMarkers:
    """No markers → raises NoTargetsFoundError."""

    def test_raises_no_targets_when_no_markers(self, tmp_path: Path) -> None:
        """
        Given a project with no AI markers,
        When _resolve_targets is called with no explicit targets,
        Then NoTargetsFoundError is raised.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()

        # ── When / Then ──
        with pytest.raises(NoTargetsFoundError) as exc_info:
            _resolve_targets(_request(), tmp_path)

        assert exc_info.value.exit_code == 6


class TestExplicitTargetsPassedThrough:
    """Explicit --ai targets bypass auto-detection."""

    def test_explicit_target_used_without_detection(self, tmp_path: Path) -> None:
        """
        Given explicit --ai targets and no markers on disk,
        When _resolve_targets is called,
        Then the provided targets are returned without raising.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        request = _request(targets=("claude",))

        # ── When ──
        result = _resolve_targets(request, tmp_path)

        # ── Then ──
        assert list(result) == ["claude"]

    def test_unknown_explicit_target_raises_usage_error(self, tmp_path: Path) -> None:
        """
        Given an explicit --ai target that doesn't exist in TARGETS,
        When _resolve_targets is called,
        Then UsageError is raised.
        """
        # ── Given ──
        (tmp_path / ".git").mkdir()
        request = _request(targets=("unknowntarget",))

        from aidriven.install._service import UsageError

        # ── When / Then ──
        with pytest.raises(UsageError):
            _resolve_targets(request, tmp_path)
