import pytest
from pathlib import Path
from aidev.services.install_service import install_resource
from aidev.services.lockfile_service import get_installed, read_lockfile
from aidev.domain.enums import ResourceType


def test_install_resource_creates_files(tmp_path):
    installed = install_resource("pytest-unit-testing", tmp_path)
    assert installed.slug == "pytest-unit-testing"
    assert installed.resource_type == ResourceType.SKILL
    assert Path(installed.target_path).exists()


def test_install_resource_updates_lockfile(tmp_path):
    install_resource("pytest-unit-testing", tmp_path)
    entry = get_installed("pytest-unit-testing", tmp_path)
    assert entry is not None
    assert entry.slug == "pytest-unit-testing"


def test_install_resource_force_overwrites(tmp_path):
    install_resource("pytest-unit-testing", tmp_path)
    # Install again with force - should succeed
    installed = install_resource("pytest-unit-testing", tmp_path, force=True)
    assert installed.slug == "pytest-unit-testing"


def test_install_resource_raises_if_exists_without_force(tmp_path):
    install_resource("pytest-unit-testing", tmp_path)
    with pytest.raises(FileExistsError):
        install_resource("pytest-unit-testing", tmp_path, force=False)


def test_install_resource_not_found_raises(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        install_resource("nonexistent-resource-xyz", tmp_path)


def test_install_resource_installed_at_is_iso(tmp_path):
    installed = install_resource("pytest-unit-testing", tmp_path)
    # Should be parseable as ISO datetime
    from datetime import datetime
    dt = datetime.fromisoformat(installed.installed_at)
    assert dt is not None
