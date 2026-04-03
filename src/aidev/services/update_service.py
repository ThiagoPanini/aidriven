from pathlib import Path
from aidev.domain.models import InstalledResource
from aidev.services.install_service import install_resource
from aidev.services.lockfile_service import read_lockfile


def update_resource(slug: str, project_dir: Path) -> InstalledResource:
    return install_resource(slug, project_dir, force=True)


def update_all(project_dir: Path) -> tuple[list[InstalledResource], list[tuple[str, str]]]:
    lockfile = read_lockfile(project_dir)
    results: list[InstalledResource] = []
    failures: list[tuple[str, str]] = []
    for entry in lockfile.installed_resources:
        try:
            updated = update_resource(entry.slug, project_dir)
            results.append(updated)
        except ValueError as e:
            failures.append((entry.slug, str(e)))
    return results, failures
