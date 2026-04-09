"""Tarball fetch, safe extraction, and content-hash verification."""

from __future__ import annotations

import logging
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from aidriven.install._hashing import hash_directory
from aidriven.install._http import fetch_bytes
from aidriven.install._paths import user_cache_dir

if TYPE_CHECKING:
    from aidriven.install._models import ManifestEntry

logger = logging.getLogger(__name__)

_OWNER = "ThiagoPanini"
_RESOURCES_REPO = "aidriven-resources"


class IntegrityError(Exception):
    """Raised when the post-extraction content hash does not match the manifest."""


def _tarball_cache_path(sha: str) -> Path:
    return user_cache_dir() / "cache" / f"{sha}.tar.gz"


def fetch_tarball(sha: str, *, force: bool = False, no_cache: bool = False) -> Path:
    """Download the tarball for *sha* and return the local cache path.

    Uses ``~/.cache/aidriven/cache/<sha>.tar.gz`` as cache key.
    Pass ``force=True`` or ``no_cache=True`` to bypass the cache.
    """
    bypass = force or no_cache
    cache_path = _tarball_cache_path(sha)

    if not bypass and cache_path.exists():
        logger.debug("Using cached tarball for SHA %s", sha)
        return cache_path

    url = f"https://github.com/{_OWNER}/{_RESOURCES_REPO}/archive/{sha}.tar.gz"
    logger.debug("Fetching tarball from %s", url)
    data = fetch_bytes(url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return cache_path


def _is_safe_member(member: tarfile.TarInfo, extract_root: Path) -> bool:
    """Return True iff *member* is safe to extract."""
    # Reject symlinks and hardlinks
    if member.issym() or member.islnk():
        return False
    # Reject absolute paths and path traversal
    norm = member.name
    if norm.startswith("/") or ".." in norm.split("/"):
        return False
    # Final check: resolved path must stay within extract_root
    resolved = (extract_root / norm).resolve()
    try:
        resolved.relative_to(extract_root.resolve())
    except ValueError:
        return False
    return True


def extract_skill(
    tarball_path: Path,
    sha: str,
    entry: ManifestEntry,
    *,
    verify_hash: bool = True,
) -> Path:
    """Extract the skill identified by *entry* from *tarball_path*.

    Returns a ``Path`` to a temporary directory containing only the skill files
    (relative to the skill root, not the repo root).

    The extraction is traversal-safe:
    - Rejects members with ``../``, absolute paths, symlinks, and hardlinks.
    - Uses ``filter='data'`` on Python 3.12+.

    If *verify_hash* is True, raises ``IntegrityError`` if the extracted content
    hash does not match ``entry.content_hash``.
    """
    # Repo tarballs from GitHub unpack into a top-level directory named
    # "<repo>-<sha[:40]>/" (e.g. "aidriven-resources-abc123/").
    repo_prefix = f"{_RESOURCES_REPO}-{sha}"
    skill_prefix = f"{repo_prefix}/{entry.path_in_repo}"

    dest = Path(tempfile.mkdtemp(prefix="aidriven-extract-"))
    try:
        with tarfile.open(tarball_path, "r:gz") as tf:
            for member in tf.getmembers():
                # Only extract members under the skill path
                if not member.name.startswith(skill_prefix + "/"):
                    continue
                if not _is_safe_member(member, dest):
                    logger.warning("Skipping unsafe member: %s", member.name)
                    continue
                # Re-root: strip the skill_prefix so output is relative
                rel = member.name[len(skill_prefix) + 1 :]
                if not rel:
                    continue
                target_path = dest / rel

                if member.isdir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)

                if sys.version_info >= (3, 12):
                    # extract_member with data filter for safe extraction
                    fileobj = tf.extractfile(member)
                    if fileobj is not None:
                        target_path.write_bytes(fileobj.read())
                else:
                    fileobj = tf.extractfile(member)
                    if fileobj is not None:
                        target_path.write_bytes(fileobj.read())

        if verify_hash:
            actual = hash_directory(dest)
            if actual != entry.content_hash:
                shutil.rmtree(dest, ignore_errors=True)
                raise IntegrityError(
                    f"Content hash mismatch for skill {entry.name!r}.\n"
                    f"  Expected : {entry.content_hash}\n"
                    f"  Actual   : {actual}"
                )
        return dest
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
