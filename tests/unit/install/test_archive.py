"""Unit tests for tarball extraction safety (T042)."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from aidriven.install._archive import IntegrityError, _is_safe_member, extract_skill
from aidriven.install._models import ManifestEntry


def _make_safe_tarball(sha: str, skill_name: str, files: dict[str, str]) -> bytes:
    """Create a well-formed tarball matching GitHub archive layout."""
    buf = io.BytesIO()
    prefix = f"aidriven-resources-{sha}"
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=f"{prefix}/skills/{skill_name}/{rel}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _make_bad_tarball(member_name: str, content: bytes = b"evil") -> bytes:
    """Create a tarball with a dangerous member."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


FAKE_SHA = "aa" * 20
SKILL_NAME = "test-skill"
SAFE_FILES = {"SKILL.md": "# Safe"}


def _make_entry(content_hash: str, compatible: list[str] | None = None) -> ManifestEntry:
    """Create a ManifestEntry for tests."""
    from aidriven.install._manifest import _parse_manifest
    from aidriven.install._models import ArtifactType

    compatible = compatible or ["claude"]
    manifest = _parse_manifest(
        {
            "schema_version": 1,
            "skills": {
                SKILL_NAME: {
                    "path_in_repo": f"skills/{SKILL_NAME}",
                    "content_hash": content_hash,
                    "compatible_targets": compatible,
                    "description": "Test skill",
                }
            },
        },
        FAKE_SHA,
    )
    return manifest.entries[(ArtifactType.SKILL, SKILL_NAME)]


def _real_hash(files: dict[str, str]) -> str:
    import hashlib

    d = hashlib.sha256()
    for k in sorted(files.keys()):
        d.update(k.encode() + b"\x00")
        d.update(files[k].encode("utf-8") + b"\x00")
    return "sha256:" + d.hexdigest()


class TestSafeMemberHelper:
    """_is_safe_member rejects dangerous archive entries."""

    def _ti(self, name: str) -> tarfile.TarInfo:
        return tarfile.TarInfo(name=name)

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        """
        Given a TarInfo member named '../evil.txt',
        When _is_safe_member is called,
        Then it returns False.
        """
        member = self._ti("../evil.txt")
        assert _is_safe_member(member, tmp_path) is False

    def test_absolute_path_rejected(self, tmp_path: Path) -> None:
        """
        Given a TarInfo member with an absolute path,
        When _is_safe_member is called,
        Then it returns False.
        """
        member = self._ti("/etc/passwd")
        assert _is_safe_member(member, tmp_path) is False

    def test_symlink_member_rejected(self, tmp_path: Path) -> None:
        """
        Given a TarInfo member that is a symlink,
        When _is_safe_member is called,
        Then it returns False.
        """
        member = tarfile.TarInfo(name="skill.md")
        member.type = tarfile.SYMTYPE
        assert _is_safe_member(member, tmp_path) is False

    def test_hardlink_member_rejected(self, tmp_path: Path) -> None:
        """
        Given a TarInfo member that is a hardlink,
        When _is_safe_member is called,
        Then it returns False.
        """
        member = tarfile.TarInfo(name="skill.md")
        member.type = tarfile.LNKTYPE
        assert _is_safe_member(member, tmp_path) is False

    def test_safe_file_accepted(self, tmp_path: Path) -> None:
        """
        Given a safe relative file path,
        When _is_safe_member is called,
        Then it returns True.
        """
        member = self._ti("SKILL.md")
        assert _is_safe_member(member, tmp_path) is True


class TestExtractionSafety:
    """Dangerous members are skipped during extraction (not written to disk)."""

    def test_safe_tarball_extracts_correctly(self, tmp_path: Path) -> None:
        """
        Given a well-formed tarball,
        When extracted,
        Then skill files are accessible at the returned path.
        """
        # ── Given ──
        content_hash = _real_hash(SAFE_FILES)
        tb = tmp_path / "safe.tar.gz"
        tb.write_bytes(_make_safe_tarball(FAKE_SHA, SKILL_NAME, SAFE_FILES))
        entry = _make_entry(content_hash)

        # ── When ──
        skill_dir = extract_skill(tb, FAKE_SHA, entry, verify_hash=True)

        # ── Then ──
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "# Safe"


class TestContentHashVerification:
    """Integrity check rejects mismatched hashes."""

    def test_integrity_error_on_hash_mismatch(self, tmp_path: Path) -> None:
        """
        Given a tarball whose content doesn't match the manifest hash,
        When extracted with verify_hash=True,
        Then IntegrityError is raised.
        """
        # ── Given ──
        tb = tmp_path / "bad_hash.tar.gz"
        tb.write_bytes(_make_safe_tarball(FAKE_SHA, SKILL_NAME, SAFE_FILES))
        wrong_entry = _make_entry("sha256:" + "f" * 64)  # wrong hash

        # ── When / Then ──
        with pytest.raises(IntegrityError):
            extract_skill(tb, FAKE_SHA, wrong_entry, verify_hash=True)

    def test_no_error_when_verify_hash_false(self, tmp_path: Path) -> None:
        """
        Given a hash mismatch but verify_hash=False,
        When extracted,
        Then no IntegrityError is raised.
        """
        # ── Given ──
        tb = tmp_path / "skip_verify.tar.gz"
        tb.write_bytes(_make_safe_tarball(FAKE_SHA, SKILL_NAME, SAFE_FILES))
        wrong_entry = _make_entry("sha256:" + "f" * 64)

        # ── When ──
        skill_dir = extract_skill(tb, FAKE_SHA, wrong_entry, verify_hash=False)

        # ── Then ──
        assert skill_dir.is_dir()
