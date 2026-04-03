from pathlib import Path
from aidev.constants import AIDEV_DIR, INSTALL_DIRS


def get_project_dir() -> Path:
    return Path.cwd()


def init_project(project_dir: Path) -> Path:
    aidev_dir = project_dir / AIDEV_DIR
    aidev_dir.mkdir(parents=True, exist_ok=True)
    for subdir in INSTALL_DIRS.values():
        (aidev_dir / subdir).mkdir(parents=True, exist_ok=True)
    return aidev_dir


def is_initialized(project_dir: Path) -> bool:
    return (project_dir / AIDEV_DIR).is_dir()
