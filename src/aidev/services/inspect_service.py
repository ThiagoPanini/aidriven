from pathlib import Path
from aidev.domain.models import Resource
from aidev.infra.resource_loader import load_resource_by_slug
from aidev.constants import SKILL_FILENAME, RULE_FILENAME, SPEC_FILENAMES


def _read_content(source_path: Path) -> str:
    """Read the primary content file of a resource."""
    candidates = [
        source_path / SKILL_FILENAME,
        source_path / RULE_FILENAME,
    ] + [source_path / f for f in SPEC_FILENAMES]

    parts: list[str] = []
    for candidate in candidates:
        if candidate.exists():
            parts.append(candidate.read_text())
    return "\n\n---\n\n".join(parts) if parts else ""


def inspect_resource(slug: str) -> tuple[Resource, str]:
    resource = load_resource_by_slug(slug)
    if resource is None:
        raise ValueError(f"Resource '{slug}' not found.")
    content = _read_content(resource.source_path)
    return resource, content
