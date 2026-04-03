from pathlib import Path
from aidev.infra.filesystem import remove_path
from aidev.services.lockfile_service import get_installed, remove_from_lockfile


def remove_resource(slug: str, project_dir: Path) -> bool:
    installed = get_installed(slug, project_dir)
    if installed is None:
        return False
    target = Path(installed.target_path)
    remove_path(target)
    remove_from_lockfile(slug, project_dir)
    return True
