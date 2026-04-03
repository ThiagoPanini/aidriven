import pytest
from pathlib import Path
from aidev.services.project_service import get_project_dir, init_project, is_initialized
from aidev.constants import AIDEV_DIR


def test_get_project_dir_returns_path():
    result = get_project_dir()
    assert isinstance(result, Path)


def test_init_project_creates_aidev_dir(tmp_path):
    aidev_dir = init_project(tmp_path)
    assert aidev_dir.exists()
    assert aidev_dir.is_dir()
    assert aidev_dir == tmp_path / AIDEV_DIR


def test_init_project_creates_subdirs(tmp_path):
    init_project(tmp_path)
    assert (tmp_path / AIDEV_DIR / "skills").is_dir()
    assert (tmp_path / AIDEV_DIR / "rules").is_dir()
    assert (tmp_path / AIDEV_DIR / "specs").is_dir()


def test_init_project_idempotent(tmp_path):
    init_project(tmp_path)
    init_project(tmp_path)  # should not raise
    assert (tmp_path / AIDEV_DIR).is_dir()


def test_is_initialized_true(tmp_path):
    init_project(tmp_path)
    assert is_initialized(tmp_path) is True


def test_is_initialized_false(tmp_path):
    assert is_initialized(tmp_path) is False
