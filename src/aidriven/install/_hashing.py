"""Deterministic SHA-256 content hash for a directory of files."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def hash_directory(directory: Path) -> str:
    """Compute a deterministic SHA-256 hash over *directory*.

    Algorithm:
    1. Collect all files under *directory* recursively.
    2. Sort by relative path (lexicographic, using POSIX separators for
       cross-platform determinism).
    3. For each file, feed ``path_bytes + b"\\x00" + file_bytes + b"\\x00"``
       into a single SHA-256 digest.
    4. Return ``"sha256:" + hexdigest``.
    """
    digest = hashlib.sha256()
    files = sorted(
        (p for p in directory.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(directory).as_posix(),
    )
    for file_path in files:
        rel = file_path.relative_to(directory).as_posix()
        digest.update(rel.encode() + b"\x00")
        digest.update(file_path.read_bytes() + b"\x00")
    return "sha256:" + digest.hexdigest()
