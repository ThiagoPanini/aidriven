from datetime import datetime, timezone
from pathlib import Path
from aidev.constants import AIDEV_DIR, INSTALL_DIRS
from aidev.domain.enums import ResourceType
from aidev.domain.models import InstalledResource
from aidev.infra.filesystem import copy_dir, dir_exists
from aidev.infra.resource_loader import load_all_resources, load_resource_by_slug
from aidev.services.lockfile_service import add_to_lockfile


def install_resource(slug: str, project_dir: Path, force: bool = False) -> InstalledResource:
    resource = load_resource_by_slug(slug)
    if resource is None:
        raise ValueError(f"Resource '{slug}' not found in catalog.")

    install_subdir = INSTALL_DIRS[resource.resource_type]
    target_path = project_dir / AIDEV_DIR / install_subdir / slug

    if dir_exists(target_path) and not force:
        raise FileExistsError(
            f"Resource '{slug}' is already installed. Use --force to overwrite."
        )

    copy_dir(resource.source_path, target_path)

    installed = InstalledResource(
        slug=slug,
        resource_type=resource.resource_type,
        source_path=str(resource.source_path),
        target_path=str(target_path),
        installed_at=datetime.now(timezone.utc).isoformat(),
    )
    add_to_lockfile(installed, project_dir)
    return installed


def install_by_type(
    resource_type: ResourceType, project_dir: Path, force: bool = False
) -> list[InstalledResource]:
    resources = [r for r in load_all_resources() if r.resource_type == resource_type]
    results: list[InstalledResource] = []
    for resource in resources:
        try:
            installed = install_resource(resource.slug, project_dir, force=force)
            results.append(installed)
        except FileExistsError:
            pass
    return results
