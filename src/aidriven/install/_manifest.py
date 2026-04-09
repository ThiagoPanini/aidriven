"""Manifest fetch, cache, validation and skill lookup."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from aidriven.install._http import fetch_bytes

if TYPE_CHECKING:
    from pathlib import Path
from aidriven.install._models import ArtifactType, Manifest, ManifestEntry
from aidriven.install._paths import user_cache_dir

logger = logging.getLogger(__name__)

_OWNER = "ThiagoPanini"
_RESOURCES_REPO = "aidriven-resources"


class ArtifactNotFoundError(Exception):
    """Raised when the requested artifact is not listed in the manifest."""


class ManifestVersionError(Exception):
    """Raised when the manifest schema_version is unsupported."""


def _manifest_cache_path(sha: str) -> Path:
    return user_cache_dir() / "manifest" / f"{sha}.json"


def fetch_manifest(sha: str, *, force: bool = False, no_cache: bool = False) -> Manifest:
    """Fetch and validate the manifest at *sha*.

    The parsed ``Manifest`` has ``source_commit_sha`` injected from *sha*
    (it is not present in the raw JSON payload).

    Results are cached at ``~/.cache/aidriven/manifest/<sha>.json``.
    Pass ``force=True`` or ``no_cache=True`` to bypass the cache.
    """
    bypass = force or no_cache
    cache_path = _manifest_cache_path(sha)

    raw: bytes | None = None
    if not bypass and cache_path.exists():
        try:
            raw = cache_path.read_bytes()
            logger.debug("Using cached manifest for SHA %s", sha)
        except OSError:
            raw = None

    if raw is None:
        url = f"https://raw.githubusercontent.com/{_OWNER}/{_RESOURCES_REPO}/{sha}/manifest.json"
        logger.debug("Fetching manifest from %s", url)
        raw = fetch_bytes(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(raw)

    payload = json.loads(raw.decode("utf-8"))
    return _parse_manifest(payload, sha)


def _parse_manifest(payload: dict[str, object], source_sha: str) -> Manifest:
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        raise ManifestVersionError(
            f"Unsupported manifest schema_version: {schema_version!r}. Expected 1."
        )

    entries: dict[tuple[ArtifactType, str], ManifestEntry] = {}
    raw_skills: object = payload.get("skills", {})
    if not isinstance(raw_skills, dict):
        raise ValueError("Manifest 'skills' field must be an object.")

    for name, raw_entry in raw_skills.items():
        if not isinstance(raw_entry, dict):
            raise ValueError(f"Manifest skill entry for {name!r} must be an object.")
        entry = _parse_entry(name, raw_entry)
        entries[(ArtifactType.SKILL, name)] = entry

    return Manifest(
        schema_version=int(str(schema_version)),
        source_commit_sha=source_sha,
        entries=entries,
    )


def _parse_entry(name: str, raw: dict[str, object]) -> ManifestEntry:
    required = ("path_in_repo", "content_hash", "compatible_targets", "description")
    for field in required:
        if field not in raw:
            raise ValueError(f"Manifest entry {name!r} is missing required field {field!r}.")

    compatible: object = raw["compatible_targets"]
    if not isinstance(compatible, list):
        raise ValueError(f"Manifest entry {name!r}: 'compatible_targets' must be an array.")

    return ManifestEntry(
        name=name,
        type=ArtifactType.SKILL,
        path_in_repo=str(raw["path_in_repo"]),
        content_hash=str(raw["content_hash"]),
        compatible_targets=frozenset(str(t) for t in compatible),
        description=str(raw.get("description", "")),
    )


def lookup_skill(manifest: Manifest, name: str) -> ManifestEntry:
    """Return the ``ManifestEntry`` for *name*, or raise ``ArtifactNotFoundError``."""
    key = (ArtifactType.SKILL, name)
    entry = manifest.entries.get(key)
    if entry is None:
        available = [n for (_, n) in manifest.entries]
        raise ArtifactNotFoundError(
            f"Skill {name!r} not found in manifest. Available: {sorted(available)}"
        )
    return entry
