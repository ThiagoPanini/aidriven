from aidev.domain.enums import ResourceType
from aidev.domain.models import Resource
from aidev.infra.resource_loader import load_all_resources


def list_resources(
    resource_type: ResourceType | None = None,
    search: str | None = None,
) -> list[Resource]:
    resources = load_all_resources()
    if resource_type is not None:
        resources = [r for r in resources if r.resource_type == resource_type]
    if search:
        term = search.lower()
        resources = [
            r
            for r in resources
            if term in r.slug.lower()
            or term in r.name.lower()
            or term in r.description.lower()
            or any(term in tag.lower() for tag in r.tags)
        ]
    return resources
