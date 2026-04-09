"""Atomic lockfile read, write, and schema-version migration guard."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import TYPE_CHECKING

from aidriven.install._models import InstallMode, Lockfile, LockfileEntry, Scope

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

_CURRENT_VERSION = 1


def read_lockfile(path: Path) -> Lockfile:
    """Read a lockfile from *path*.  Returns an empty ``Lockfile`` if absent."""
    if not path.exists():
        return Lockfile()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read lockfile %s: %s — treating as empty.", path, exc)
        return Lockfile()

    version = raw.get("version")
    if version != _CURRENT_VERSION:
        logger.warning(
            "Lockfile at %s has schema version %r (expected %d). "
            "Attempting migration — no entries will be silently discarded.",
            path,
            version,
            _CURRENT_VERSION,
        )
        return _migrate(raw)

    skills: dict[str, LockfileEntry] = {}
    for name, entry_raw in raw.get("skills", {}).items():
        try:
            skills[name] = _parse_entry(entry_raw)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping malformed lockfile entry %r: %s", name, exc)

    return Lockfile(version=_CURRENT_VERSION, skills=skills)


def write_lockfile(lockfile: Lockfile, path: Path, *, include_timestamps: bool = False) -> None:
    """Write *lockfile* to *path* atomically.

    Uses a sibling temp file + ``os.replace`` so readers never see a partial
    write.  Keys are sorted for determinism (VCS-friendly).
    """
    payload = _serialise(lockfile, include_timestamps=include_timestamps)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".aidriven-lock-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        import contextlib

        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _serialise(lockfile: Lockfile, *, include_timestamps: bool = False) -> dict[str, object]:
    skills: dict[str, object] = {}
    for skill_name in sorted(lockfile.skills):
        entry = lockfile.skills[skill_name]
        entry_dict: dict[str, object] = {
            "source": entry.source,
            "sourceCommitSha": entry.source_commit_sha,
            "computedHash": entry.computed_hash,
            "targets": sorted(entry.targets),
            "scope": entry.scope.value,
            "installMode": entry.install_mode.value,
        }
        skills[skill_name] = entry_dict
    return {"version": lockfile.version, "skills": skills}


def _parse_entry(raw: dict[str, object]) -> LockfileEntry:
    targets_raw = raw["targets"]
    if not isinstance(targets_raw, list):
        raise TypeError("'targets' must be a list")
    return LockfileEntry(
        source=str(raw["source"]),
        source_commit_sha=str(raw["sourceCommitSha"]),
        computed_hash=str(raw["computedHash"]),
        targets=tuple(sorted(str(t) for t in targets_raw)),
        scope=Scope(str(raw["scope"])),
        install_mode=InstallMode(str(raw["installMode"])),
    )


def _migrate(raw: dict[str, object]) -> Lockfile:
    """Best-effort migration from an unknown schema version.

    Preserves any entries that can be parsed; warns about those that cannot.
    """
    skills: dict[str, LockfileEntry] = {}
    skills_raw = raw.get("skills")
    if isinstance(skills_raw, dict):
        for name, entry_raw in skills_raw.items():
            try:
                skills[name] = _parse_entry(entry_raw)
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning(
                    "Could not migrate lockfile entry %r: %s — entry discarded.", name, exc
                )
    return Lockfile(version=_CURRENT_VERSION, skills=skills)
