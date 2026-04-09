"""Tests for artifact-name regex validation.

The regex ``^[a-z][a-z0-9-]{0,63}$`` is enforced before any network call.
"""

from __future__ import annotations

import re

import pytest

# The validation regex — matches the spec (FR-003).
NAME_REGEX = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def validate_name(name: str) -> bool:
    return bool(NAME_REGEX.match(name))


# ── Valid names ────────────────────────────────────────────────────────


class TestValidArtifactNames:
    """Tests for names that should pass validation."""

    @pytest.mark.parametrize(
        "name",
        [
            "code-reviewer",
            "a",
            "a0",
            "my-skill",
            "skill123",
            "a" * 64,  # max length: 1 leading + 63 more = 64 chars total
            "x" + "0" * 63,
        ],
        ids=[
            "typical",
            "single-char",
            "letter-digit",
            "hyphen",
            "digits",
            "max-length",
            "max-digits",
        ],
    )
    def test_valid_name_passes(self, name: str) -> None:
        """
        Given a name matching ``^[a-z][a-z0-9-]{0,63}$``,
        When validated,
        Then it passes.
        """
        # ── Given ──
        # (name provided via parametrize)

        # ── When ──
        result = validate_name(name)

        # ── Then ──
        assert result is True


# ── Invalid names ─────────────────────────────────────────────────────


class TestInvalidArtifactNames:
    """Tests for names that should fail validation."""

    @pytest.mark.parametrize(
        "name",
        [
            "Code-reviewer",  # uppercase
            "SKILL",  # all uppercase
            "1skill",  # leading digit
            "-skill",  # leading hyphen
            "skill name",  # space
            "skill_name",  # underscore
            "",  # empty
            "a" * 65,  # too long (65 chars)
        ],
        ids=[
            "capital-first",
            "all-caps",
            "leading-digit",
            "leading-hyphen",
            "space",
            "underscore",
            "empty",
            "too-long-65",
        ],
    )
    def test_invalid_name_rejected(self, name: str) -> None:
        """
        Given a name that violates ``^[a-z][a-z0-9-]{0,63}$``,
        When validated,
        Then it is rejected.
        """
        # ── Given ──
        # (name provided via parametrize)

        # ── When ──
        result = validate_name(name)

        # ── Then ──
        assert result is False

    def test_name_with_64_chars_body_is_too_long(self) -> None:
        """
        Given a name with 1 leading letter + 63 suffix chars = 64 total (valid boundary),
        and another with 1 + 64 = 65 total (invalid),
        When validated,
        Then the 64-char name passes and the 65-char name fails.
        """
        # ── Given ──
        valid = "a" + "b" * 63  # 64 chars total — max allowed
        invalid = "a" + "b" * 64  # 65 chars total — exceeds max

        # ── When ──
        valid_result = validate_name(valid)
        invalid_result = validate_name(invalid)

        # ── Then ──
        assert valid_result is True
        assert invalid_result is False
