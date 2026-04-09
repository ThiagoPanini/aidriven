"""Unit tests for manifest parsing (T044)."""

from __future__ import annotations

import pytest

from aidriven.install._manifest import (
    ArtifactNotFoundError,
    ManifestVersionError,
    _parse_manifest,
    lookup_skill,
)
from aidriven.install._models import ArtifactType, Manifest, ManifestEntry

FAKE_SHA = "cc" * 20


def _valid_payload(skills: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": 1,
        "skills": skills
        or {
            "code-reviewer": {
                "path_in_repo": "skills/code-reviewer",
                "content_hash": "sha256:" + "a" * 64,
                "compatible_targets": ["claude", "copilot"],
                "description": "Review code",
            }
        },
    }


def _entry(manifest: Manifest, name: str) -> ManifestEntry:
    """Helper to get entry from manifest by skill name."""
    from aidriven.install._models import ArtifactType

    return manifest.entries[(ArtifactType.SKILL, name)]


class TestValidManifestParsing:
    """Well-formed manifest payload parses correctly."""

    def test_parses_valid_v1_manifest(self) -> None:
        """
        Given a valid schema_version=1 manifest,
        When _parse_manifest is called,
        Then a Manifest object with one skill is returned.
        """
        # ── Given / When ──
        manifest = _parse_manifest(_valid_payload(), FAKE_SHA)

        # ── Then ──
        assert manifest.schema_version == 1
        from aidriven.install._models import ArtifactType

        entry = manifest.entries[(ArtifactType.SKILL, "code-reviewer")]
        assert entry.content_hash == "sha256:" + "a" * 64
        assert "claude" in entry.compatible_targets
        assert "copilot" in entry.compatible_targets

    def test_compatible_targets_is_frozenset(self) -> None:
        """
        Given compatible_targets list in JSON,
        When parsed,
        Then ManifestEntry.compatible_targets is a frozenset.
        """
        # ── Given ──
        _parse_manifest(_valid_payload(), FAKE_SHA)

        # ── Then ──
        entry = _entry(_parse_manifest(_valid_payload(), FAKE_SHA), "code-reviewer")
        assert isinstance(entry.compatible_targets, frozenset)

    def test_artifact_type_inferred_as_skill(self) -> None:
        """
        Given a manifest entry under 'skills' key,
        When parsed,
        Then the entry type is ArtifactType.SKILL.
        """
        manifest = _parse_manifest(_valid_payload(), FAKE_SHA)
        assert _entry(manifest, "code-reviewer").type == ArtifactType.SKILL


class TestMissingFieldValidation:
    """Missing required fields raise ValueError."""

    def test_missing_content_hash_raises(self) -> None:
        """
        Given a skill entry without content_hash,
        When parsed,
        Then ValueError is raised.
        """
        payload = {
            "schema_version": 1,
            "skills": {
                "bad-skill": {
                    "path_in_repo": "skills/bad-skill",
                    # missing content_hash
                    "compatible_targets": ["claude"],
                    "description": "Missing hash",
                }
            },
        }
        with pytest.raises((ValueError, KeyError)):
            _parse_manifest(payload, FAKE_SHA)

    def test_missing_schema_version_raises(self) -> None:
        """
        Given a payload without schema_version,
        When parsed,
        Then ValueError or KeyError is raised.
        """
        payload: dict[str, object] = {
            # no schema_version
            "skills": {}
        }
        with pytest.raises((ValueError, KeyError, ManifestVersionError)):
            _parse_manifest(payload, FAKE_SHA)


class TestUnknownSchemaVersion:
    """Unknown schema_version raises ManifestVersionError."""

    def test_schema_version_2_raises_version_error(self) -> None:
        """
        Given schema_version=2,
        When parsed,
        Then ManifestVersionError is raised (not silent).
        """
        payload = {
            "schema_version": 2,
            "skills": {},
        }
        with pytest.raises(ManifestVersionError):
            _parse_manifest(payload, FAKE_SHA)

    def test_schema_version_0_raises_version_error(self) -> None:
        """
        Given schema_version=0,
        When parsed,
        Then ManifestVersionError is raised.
        """
        payload = {
            "schema_version": 0,
            "skills": {},
        }
        with pytest.raises(ManifestVersionError):
            _parse_manifest(payload, FAKE_SHA)


class TestLookupSkill:
    """lookup_skill raises ArtifactNotFoundError for unknown skills."""

    def test_lookup_existing_skill(self) -> None:
        """
        Given a manifest with code-reviewer,
        When lookup_skill is called for code-reviewer,
        Then the entry is returned.
        """
        manifest = _parse_manifest(_valid_payload(), FAKE_SHA)
        entry = lookup_skill(manifest, "code-reviewer")
        assert entry.name == "code-reviewer"

    def test_lookup_missing_skill_raises(self) -> None:
        """
        Given a manifest without 'unknown-skill',
        When lookup_skill is called for it,
        Then ArtifactNotFoundError is raised.
        """
        manifest = _parse_manifest(_valid_payload(), FAKE_SHA)
        with pytest.raises(ArtifactNotFoundError):
            lookup_skill(manifest, "unknown-skill")
