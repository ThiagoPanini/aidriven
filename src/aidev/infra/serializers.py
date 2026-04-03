import json
from pathlib import Path
from aidev.domain.models import LockFile, InstalledResource
from aidev.domain.enums import ResourceType


def lockfile_to_dict(lockfile: LockFile) -> dict:
    return {
        "lockfile_version": lockfile.lockfile_version,
        "installed_resources": [
            {
                "slug": r.slug,
                "resource_type": r.resource_type.value,
                "source_path": r.source_path,
                "target_path": r.target_path,
                "installed_at": r.installed_at,
            }
            for r in lockfile.installed_resources
        ],
    }


def lockfile_from_dict(data: dict) -> LockFile:
    installed = [
        InstalledResource(
            slug=r["slug"],
            resource_type=ResourceType(r["resource_type"]),
            source_path=r["source_path"],
            target_path=r["target_path"],
            installed_at=r["installed_at"],
        )
        for r in data.get("installed_resources", [])
    ]
    return LockFile(
        lockfile_version=data.get("lockfile_version", 1),
        installed_resources=installed,
    )


def read_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
