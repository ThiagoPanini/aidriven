"""Application orchestration layer - coordinates services for CLI commands."""
from pathlib import Path
from aidev.domain.enums import ResourceType
from aidev.domain.models import InstalledResource, LockFile, Resource
from aidev.services.catalog_service import list_resources as svc_list
from aidev.services.inspect_service import inspect_resource as svc_inspect
from aidev.services.install_service import install_by_type as svc_install_type
from aidev.services.install_service import install_resource as svc_install
from aidev.services.lockfile_service import read_lockfile
from aidev.services.project_service import get_project_dir as svc_get_project_dir
from aidev.services.project_service import init_project as svc_init
from aidev.services.project_service import is_initialized
from aidev.services.remove_service import remove_resource as svc_remove
from aidev.services.update_service import update_all, update_resource as svc_update


def list_resources(
    resource_type: str | None = None,
    search: str | None = None,
) -> list[Resource]:
    rtype = ResourceType(resource_type) if resource_type else None
    return svc_list(resource_type=rtype, search=search)


def inspect_resource(slug: str) -> tuple[Resource, str]:
    return svc_inspect(slug)


def install_resources(
    slugs: list[str],
    project_dir: Path | None = None,
    force: bool = False,
) -> list[InstalledResource]:
    if project_dir is None:
        project_dir = svc_get_project_dir()
    results: list[InstalledResource] = []
    for slug in slugs:
        installed = svc_install(slug, project_dir, force=force)
        results.append(installed)
    return results


def install_by_type(
    resource_type: str,
    project_dir: Path | None = None,
    force: bool = False,
) -> list[InstalledResource]:
    if project_dir is None:
        project_dir = svc_get_project_dir()
    rtype = ResourceType(resource_type)
    return svc_install_type(rtype, project_dir, force=force)


def remove_resource(slug: str, project_dir: Path | None = None) -> bool:
    if project_dir is None:
        project_dir = svc_get_project_dir()
    return svc_remove(slug, project_dir)


def update_resource(slug: str | None = None, project_dir: Path | None = None) -> list[InstalledResource]:
    if project_dir is None:
        project_dir = svc_get_project_dir()
    if slug:
        return [svc_update(slug, project_dir)]
    results, failures = update_all(project_dir)
    if failures:
        raise ValueError(
            "Some resources failed to update: "
            + ", ".join(f"{s} ({e})" for s, e in failures)
        )
    return results


def init_project(project_dir: Path | None = None) -> Path:
    if project_dir is None:
        project_dir = svc_get_project_dir()
    return svc_init(project_dir)


def doctor(project_dir: Path | None = None) -> dict:
    if project_dir is None:
        project_dir = svc_get_project_dir()
    initialized = is_initialized(project_dir)
    lockfile = read_lockfile(project_dir) if initialized else LockFile()
    return {
        "initialized": initialized,
        "project_dir": str(project_dir),
        "lockfile": lockfile,
    }
