"""Tests for platform detection utilities."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from aidriven.discovery._platform import current_platform, resolve_env_path, resolve_home

# ── TestCurrentPlatform ──────────────────────────────────────────────


class TestCurrentPlatform:
    """Tests for current_platform()."""

    @pytest.mark.parametrize(
        ("system_value", "expected"),
        [
            ("Darwin", "darwin"),
            ("Linux", "linux"),
            ("Windows", "windows"),
        ],
        ids=["macos", "linux", "windows"],
    )
    def test_returns_lowercased_platform_name(self, system_value: str, expected: str) -> None:
        """
        Given a known OS platform,
        When current_platform is called,
        Then the lowercased platform string is returned.
        """
        # ── Given ──
        # (parameter provides the given context)

        # ── When ──
        with patch("platform.system", return_value=system_value):
            result = current_platform()

        # ── Then ──
        assert result == expected

    def test_returns_lowercased_string_for_unknown_platform(self) -> None:
        """
        Given an unrecognized OS platform like FreeBSD,
        When current_platform is called,
        Then the lowercased string is returned.
        """
        # ── When ──
        with patch("platform.system", return_value="FreeBSD"):
            result = current_platform()

        # ── Then ──
        assert result == "freebsd"


# ── TestResolveHome ──────────────────────────────────────────────────


class TestResolveHome:
    """Tests for resolve_home()."""

    def test_returns_path_instance(self) -> None:
        """
        Given a normal environment,
        When resolve_home is called,
        Then it returns a Path instance.
        """
        # ── When ──
        result = resolve_home()

        # ── Then ──
        assert isinstance(result, Path)

    def test_matches_pathlib_home(self) -> None:
        """
        Given a normal environment,
        When resolve_home is called,
        Then it matches Path.home().
        """
        # ── When ──
        result = resolve_home()

        # ── Then ──
        assert result == Path.home()

    def test_returns_mocked_home_directory(self, tmp_path: Path) -> None:
        """
        Given a mocked home directory,
        When resolve_home is called,
        Then the mocked path is returned.
        """
        # ── When ──
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = resolve_home()

        # ── Then ──
        assert result == tmp_path


# ── TestResolveEnvPath ───────────────────────────────────────────────


class TestResolveEnvPath:
    """Tests for resolve_env_path()."""

    def test_returns_path_for_set_variable(self) -> None:
        """
        Given an environment variable set to a path string,
        When resolve_env_path is called with that variable name,
        Then a Path with the value is returned.
        """
        # ── Given ──
        # (env var set via patch)

        # ── When ──
        with patch.dict(os.environ, {"MY_VAR": "/some/path"}):
            result = resolve_env_path("MY_VAR")

        # ── Then ──
        assert result == Path("/some/path")

    def test_returns_none_for_unset_variable(self) -> None:
        """
        Given an environment variable that does not exist,
        When resolve_env_path is called with that variable name,
        Then None is returned.
        """
        # ── Given ──
        env = {k: v for k, v in os.environ.items() if k != "MY_MISSING_VAR"}

        # ── When ──
        with patch.dict(os.environ, env, clear=True):
            result = resolve_env_path("MY_MISSING_VAR")

        # ── Then ──
        assert result is None

    def test_returns_none_for_empty_string(self) -> None:
        """
        Given an environment variable set to an empty string,
        When resolve_env_path is called with that variable name,
        Then None is returned.
        """
        # ── When ──
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            result = resolve_env_path("EMPTY_VAR")

        # ── Then ──
        assert result is None

    def test_handles_windows_style_path(self) -> None:
        """
        Given an environment variable with a Windows-style path,
        When resolve_env_path is called,
        Then a Path with the correct value is returned.
        """
        # ── When ──
        with patch.dict(os.environ, {"APPDATA": r"C:\Users\user\AppData\Roaming"}):
            result = resolve_env_path("APPDATA")

        # ── Then ──
        assert result == Path(r"C:\Users\user\AppData\Roaming")
