"""Unit tests for deterministic content hash (T043)."""

from __future__ import annotations

from pathlib import Path

from aidriven.install._hashing import hash_directory


class TestDeterministicHash:
    """Same content → same hash regardless of iteration order."""

    def test_same_content_produces_same_hash(self, tmp_path: Path) -> None:
        """
        Given two directories with identical files,
        When hash_directory is called on each,
        Then both produce the identical digest.
        """
        # ── Given ──
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        files = {"SKILL.md": "# Hello", "config.yaml": "version: 1", "README.md": "readme"}
        for name, content in files.items():
            (dir_a / name).write_text(content, encoding="utf-8")
            (dir_b / name).write_text(content, encoding="utf-8")

        # ── When ──
        hash_a = hash_directory(dir_a)
        hash_b = hash_directory(dir_b)

        # ── Then ──
        assert hash_a == hash_b

    def test_different_content_produces_different_hash(self, tmp_path: Path) -> None:
        """
        Given two directories with swapped file contents,
        When hash_directory is called,
        Then the hashes differ.
        """
        # ── Given ──
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        (dir_a / "SKILL.md").write_text("# Skill A", encoding="utf-8")
        (dir_b / "SKILL.md").write_text("# Skill B", encoding="utf-8")

        # ── When ──
        hash_a = hash_directory(dir_a)
        hash_b = hash_directory(dir_b)

        # ── Then ──
        assert hash_a != hash_b

    def test_swapped_filenames_produce_different_hash(self, tmp_path: Path) -> None:
        """
        Given two directories where filenames and contents are swapped,
        When hash_directory is called,
        Then the hashes differ (hash includes file paths).
        """
        # ── Given ──
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        (dir_a / "alpha.md").write_text("content-one", encoding="utf-8")
        (dir_a / "beta.md").write_text("content-two", encoding="utf-8")
        # Swapped names
        (dir_b / "alpha.md").write_text("content-two", encoding="utf-8")
        (dir_b / "beta.md").write_text("content-one", encoding="utf-8")

        # ── When ──
        hash_a = hash_directory(dir_a)
        hash_b = hash_directory(dir_b)

        # ── Then ──
        assert hash_a != hash_b


class TestEmptyDirectory:
    """Empty directory produces a stable, deterministic value."""

    def test_empty_directory_stable(self, tmp_path: Path) -> None:
        """
        Given an empty directory,
        When hash_directory is called twice,
        Then both calls produce the same result.
        """
        # ── Given ──
        empty = tmp_path / "empty"
        empty.mkdir()

        # ── When ──
        h1 = hash_directory(empty)
        h2 = hash_directory(empty)

        # ── Then ──
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_empty_directory_differs_from_non_empty(self, tmp_path: Path) -> None:
        """
        Given an empty and non-empty directory,
        When hash_directory is called on each,
        Then the hashes differ.
        """
        # ── Given ──
        empty = tmp_path / "empty"
        nonempty = tmp_path / "nonempty"
        empty.mkdir()
        nonempty.mkdir()
        (nonempty / "file.md").write_text("content", encoding="utf-8")

        # ── When ──
        assert hash_directory(empty) != hash_directory(nonempty)


class TestHashFormat:
    """Hash output format matches sha256: prefix."""

    def test_hash_starts_with_sha256_prefix(self, tmp_path: Path) -> None:
        """
        Given any directory,
        When hash_directory is called,
        Then the result starts with 'sha256:'.
        """
        dir_ = tmp_path / "d"
        dir_.mkdir()
        (dir_ / "f.txt").write_text("data", encoding="utf-8")

        result = hash_directory(dir_)
        assert result.startswith("sha256:")
        assert len(result) == len("sha256:") + 64  # SHA-256 in hex
