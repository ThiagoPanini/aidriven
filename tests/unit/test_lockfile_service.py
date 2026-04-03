import pytest
from pathlib import Path
from datetime import datetime, timezone
from aidev.services.lockfile_service import (
    add_to_lockfile,
    get_installed,
    read_lockfile,
    remove_from_lockfile,
    write_lockfile,
)
from aidev.domain.models import InstalledResource, LockFile
from aidev.domain.enums import ResourceType


def _make_installed(slug="test-skill"):
    return InstalledResource(
        slug=slug,
        resource_type=ResourceType.SKILL,
        source_path="/fake/source",
        target_path="/fake/target",
        installed_at=datetime.now(timezone.utc).isoformat(),
    )


def test_write_and_read_roundtrip(tmp_path):
    lockfile = LockFile(installed_resources=[_make_installed()])
    write_lockfile(lockfile, tmp_path)
    loaded = read_lockfile(tmp_path)
    assert loaded.lockfile_version == 1
    assert len(loaded.installed_resources) == 1
    assert loaded.installed_resources[0].slug == "test-skill"


def test_read_lockfile_returns_empty_if_missing(tmp_path):
    lockfile = read_lockfile(tmp_path)
    assert lockfile.lockfile_version == 1
    assert lockfile.installed_resources == []


def test_add_to_lockfile(tmp_path):
    add_to_lockfile(_make_installed("skill-a"), tmp_path)
    add_to_lockfile(_make_installed("skill-b"), tmp_path)
    lockfile = read_lockfile(tmp_path)
    slugs = [r.slug for r in lockfile.installed_resources]
    assert "skill-a" in slugs
    assert "skill-b" in slugs


def test_add_to_lockfile_replaces_existing(tmp_path):
    add_to_lockfile(_make_installed("skill-a"), tmp_path)
    add_to_lockfile(_make_installed("skill-a"), tmp_path)
    lockfile = read_lockfile(tmp_path)
    assert len([r for r in lockfile.installed_resources if r.slug == "skill-a"]) == 1


def test_remove_from_lockfile(tmp_path):
    add_to_lockfile(_make_installed("skill-a"), tmp_path)
    remove_from_lockfile("skill-a", tmp_path)
    lockfile = read_lockfile(tmp_path)
    assert not any(r.slug == "skill-a" for r in lockfile.installed_resources)


def test_remove_from_lockfile_nonexistent_is_noop(tmp_path):
    add_to_lockfile(_make_installed("skill-a"), tmp_path)
    remove_from_lockfile("skill-z", tmp_path)
    lockfile = read_lockfile(tmp_path)
    assert len(lockfile.installed_resources) == 1


def test_get_installed_found(tmp_path):
    add_to_lockfile(_make_installed("skill-a"), tmp_path)
    result = get_installed("skill-a", tmp_path)
    assert result is not None
    assert result.slug == "skill-a"


def test_get_installed_not_found(tmp_path):
    result = get_installed("nonexistent", tmp_path)
    assert result is None
