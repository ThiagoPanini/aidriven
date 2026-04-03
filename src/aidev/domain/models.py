from dataclasses import dataclass, field
from pathlib import Path
from aidev.domain.enums import ResourceType


@dataclass
class Resource:
    slug: str
    name: str
    resource_type: ResourceType
    description: str
    source_path: Path
    tags: list[str] = field(default_factory=list)


@dataclass
class InstalledResource:
    slug: str
    resource_type: ResourceType
    source_path: str
    target_path: str
    installed_at: str  # ISO format datetime


@dataclass
class LockFile:
    lockfile_version: int = 1
    installed_resources: list[InstalledResource] = field(default_factory=list)
