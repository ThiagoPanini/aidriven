"""Tests for the full path table across all target x scope x mode combinations.

Asserts canonical dir and read path for each combination of
(claude, copilot) x (project, user) x (symlink, copy).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aidriven.install._models import Scope
from aidriven.install._paths import (
    canonical_dir,
    needs_symlink,
    read_path_for_target,
    scope_base_path,
    user_cache_dir,
    user_lockfile_path,
)
from aidriven.install._targets import TARGETS


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path / "project"


@pytest.fixture
def user_home(tmp_path: Path) -> Path:
    return tmp_path / "home"


# ── Canonical directory ───────────────────────────────────────────────


class TestCanonicalDir:
    """Tests for ``canonical_dir()``."""

    def test_canonical_dir_is_agents_skills_under_base(self, project_root: Path) -> None:
        """
        Given any base path and skill name,
        When canonical_dir is called,
        Then the result is ``<base>/.agents/skills/<name>``.
        """
        # ── Given ──
        base = project_root
        name = "code-reviewer"

        # ── When ──
        result = canonical_dir(base, name)

        # ── Then ──
        assert result == base / ".agents" / "skills" / "code-reviewer"

    def test_canonical_dir_same_for_all_targets(self, project_root: Path) -> None:
        """
        Given different AI targets,
        When canonical_dir is computed for each,
        Then all produce the same path (canonical is target-independent).
        """
        # ── Given ──
        base = project_root
        name = "my-skill"

        # ── When / Then ──
        for _ in ("claude", "copilot"):
            assert canonical_dir(base, name) == base / ".agents" / "skills" / name


# ── Read paths ────────────────────────────────────────────────────────


class TestReadPaths:
    """Tests for ``read_path_for_target()``."""

    @pytest.mark.parametrize(
        ("target_name", "scope", "expected_rel"),
        [
            # Project scope
            ("claude", Scope.PROJECT, ".claude/skills/s"),
            ("copilot", Scope.PROJECT, ".agents/skills/s"),
            # User scope
            ("claude", Scope.USER, ".claude/skills/s"),
            ("copilot", Scope.USER, ".copilot/skills/s"),
        ],
        ids=[
            "claude-project",
            "copilot-project",
            "claude-user",
            "copilot-user",
        ],
    )
    def test_read_path(
        self,
        target_name: str,
        scope: Scope,
        expected_rel: str,
        project_root: Path,
        user_home: Path,
    ) -> None:
        """
        Given a target, scope, and base path,
        When read_path_for_target is called,
        Then it returns the correct relative path under the base.
        """
        # ── Given ──
        target = TARGETS[target_name]
        base = project_root if scope == Scope.PROJECT else user_home

        # ── When ──
        result = read_path_for_target(target, scope, base, "s")

        # ── Then ──
        assert result == base / expected_rel


# ── needs_symlink ─────────────────────────────────────────────────────


class TestNeedsSymlink:
    """Tests for ``needs_symlink()``."""

    @pytest.mark.parametrize(
        ("target_name", "scope", "expected"),
        [
            # copilot at project scope: read path == canonical path
            ("copilot", Scope.PROJECT, False),
            # claude at project scope: .claude/skills != .agents/skills
            ("claude", Scope.PROJECT, True),
            # claude at user scope: read path is ~/.claude/skills != ~/.agents/skills
            ("claude", Scope.USER, True),
            # copilot at user scope: .copilot/skills != .agents/skills
            ("copilot", Scope.USER, True),
        ],
        ids=[
            "copilot-project-no-symlink",
            "claude-project-symlink",
            "claude-user-symlink",
            "copilot-user-symlink",
        ],
    )
    def test_needs_symlink(
        self,
        target_name: str,
        scope: Scope,
        expected: bool,
        project_root: Path,
        user_home: Path,
    ) -> None:
        """
        Given a target and scope,
        When needs_symlink is called,
        Then it returns whether a symlink is required.
        """
        # ── Given ──
        target = TARGETS[target_name]
        base = project_root if scope == Scope.PROJECT else user_home

        # ── When ──
        result = needs_symlink(target, scope, base, "skill-name")

        # ── Then ──
        assert result is expected


# ── Scope base paths ──────────────────────────────────────────────────


class TestScopeBasePath:
    """Tests for ``scope_base_path()``."""

    def test_project_scope_uses_project_root(self, project_root: Path) -> None:
        """
        Given Scope.PROJECT and a project root,
        When scope_base_path is called,
        Then it returns the project root.
        """
        # ── Given / When ──
        result = scope_base_path(Scope.PROJECT, project_root)

        # ── Then ──
        assert result == project_root

    def test_user_scope_uses_home_dir(self, project_root: Path) -> None:
        """
        Given Scope.USER,
        When scope_base_path is called,
        Then it returns Path.home() (not the project root).
        """
        # ── Given / When ──
        result = scope_base_path(Scope.USER, project_root)

        # ── Then ──
        assert result == Path.home()
        assert result != project_root


# ── User cache directory ──────────────────────────────────────────────


class TestUserCacheDir:
    """Tests for ``user_cache_dir()`` — OS-specific path derivation."""

    def test_linux_cache_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Given Linux environment,
        When user_cache_dir is called,
        Then it returns ~/.cache/aidriven.
        """
        # ── Given ──
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)

        # ── When ──
        result = user_cache_dir()

        # ── Then ──
        assert result == Path.home() / ".cache" / "aidriven"

    def test_macos_cache_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Given macOS environment,
        When user_cache_dir is called,
        Then it returns ~/.cache/aidriven.
        """
        # ── Given ──
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)

        # ── When ──
        result = user_cache_dir()

        # ── Then ──
        assert result == Path.home() / ".cache" / "aidriven"

    def test_windows_cache_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """
        Given Windows environment with LOCALAPPDATA set,
        When user_cache_dir is called,
        Then it returns %LOCALAPPDATA%/aidriven/Cache.
        """
        # ── Given ──
        local_app = tmp_path / "AppData" / "Local"
        local_app.mkdir(parents=True)
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setenv("LOCALAPPDATA", str(local_app))

        # ── When ──
        result = user_cache_dir()

        # ── Then ──
        assert result == local_app / "aidriven" / "Cache"


# ── User lockfile path ────────────────────────────────────────────────


class TestUserLockfilePath:
    """Tests for ``user_lockfile_path()`` — co-located at cache root."""

    def test_linux_lockfile_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Given Linux environment,
        When user_lockfile_path is called,
        Then it returns ~/.cache/aidriven/install-records.json.
        """
        # ── Given ──
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)

        # ── When ──
        result = user_lockfile_path()

        # ── Then ──
        assert result == Path.home() / ".cache" / "aidriven" / "install-records.json"

    def test_windows_lockfile_path(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """
        Given Windows environment,
        When user_lockfile_path is called,
        Then it returns %LOCALAPPDATA%/aidriven/install-records.json.
        """
        # ── Given ──
        local_app = tmp_path / "AppData" / "Local"
        local_app.mkdir(parents=True)
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setenv("LOCALAPPDATA", str(local_app))

        # ── When ──
        result = user_lockfile_path()

        # ── Then ──
        assert result == local_app / "aidriven" / "install-records.json"
