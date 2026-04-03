from pathlib import Path
from aidev.constants import AIDEV_DIR, LOCK_FILE_NAME
from aidev.domain.models import InstalledResource, LockFile
from aidev.infra.serializers import lockfile_from_dict, lockfile_to_dict, read_json, write_json


def _lockfile_path(project_dir: Path) -> Path:
    return project_dir / AIDEV_DIR / LOCK_FILE_NAME


def read_lockfile(project_dir: Path) -> LockFile:
    path = _lockfile_path(project_dir)
    if not path.exists():
        return LockFile()
    data = read_json(path)
    return lockfile_from_dict(data)


def write_lockfile(lockfile: LockFile, project_dir: Path) -> None:
    path = _lockfile_path(project_dir)
    write_json(path, lockfile_to_dict(lockfile))


def add_to_lockfile(installed_resource: InstalledResource, project_dir: Path) -> None:
    lockfile = read_lockfile(project_dir)
    # Replace if already exists
    lockfile.installed_resources = [
        r for r in lockfile.installed_resources if r.slug != installed_resource.slug
    ]
    lockfile.installed_resources.append(installed_resource)
    write_lockfile(lockfile, project_dir)


def remove_from_lockfile(slug: str, project_dir: Path) -> None:
    lockfile = read_lockfile(project_dir)
    lockfile.installed_resources = [
        r for r in lockfile.installed_resources if r.slug != slug
    ]
    write_lockfile(lockfile, project_dir)


def get_installed(slug: str, project_dir: Path) -> InstalledResource | None:
    lockfile = read_lockfile(project_dir)
    for r in lockfile.installed_resources:
        if r.slug == slug:
            return r
    return None
