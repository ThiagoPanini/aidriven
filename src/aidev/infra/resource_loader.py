from pathlib import Path
from aidev.domain.enums import ResourceType
from aidev.domain.models import Resource
from aidev.constants import SKILL_FILENAME, RULE_FILENAME, SPEC_FILENAMES


def _get_resources_dir() -> Path:
    return Path(__file__).parent.parent / "resources"


def _slug_to_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def _read_description(path: Path) -> str:
    """Read first non-empty, non-heading line as description."""
    try:
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    return stripped[:200]
    except OSError:
        pass
    return ""


def _load_skills(resources_dir: Path) -> list[Resource]:
    skills_dir = resources_dir / "skills"
    resources: list[Resource] = []
    if not skills_dir.exists():
        return resources
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / SKILL_FILENAME
        if not skill_file.exists():
            continue
        description = _read_description(skill_file)
        resources.append(
            Resource(
                slug=skill_dir.name,
                name=_slug_to_name(skill_dir.name),
                resource_type=ResourceType.SKILL,
                description=description,
                source_path=skill_dir,
                tags=["skill"],
            )
        )
    return resources


def _load_rules(resources_dir: Path) -> list[Resource]:
    rules_dir = resources_dir / "rules"
    resources: list[Resource] = []
    if not rules_dir.exists():
        return resources
    for rule_dir in sorted(rules_dir.iterdir()):
        if not rule_dir.is_dir():
            continue
        rule_file = rule_dir / RULE_FILENAME
        if not rule_file.exists():
            continue
        description = _read_description(rule_file)
        resources.append(
            Resource(
                slug=rule_dir.name,
                name=_slug_to_name(rule_dir.name),
                resource_type=ResourceType.RULE,
                description=description,
                source_path=rule_dir,
                tags=["rule"],
            )
        )
    return resources


def _load_specs(resources_dir: Path) -> list[Resource]:
    specs_dir = resources_dir / "specs"
    resources: list[Resource] = []
    if not specs_dir.exists():
        return resources
    for spec_dir in sorted(specs_dir.iterdir()):
        if not spec_dir.is_dir():
            continue
        # Check at least one spec file exists
        has_files = any((spec_dir / f).exists() for f in SPEC_FILENAMES)
        if not has_files:
            continue
        # Use first available spec file for description
        description = ""
        for fname in SPEC_FILENAMES:
            fpath = spec_dir / fname
            if fpath.exists():
                description = _read_description(fpath)
                break
        resources.append(
            Resource(
                slug=spec_dir.name,
                name=_slug_to_name(spec_dir.name),
                resource_type=ResourceType.SPEC,
                description=description,
                source_path=spec_dir,
                tags=["spec"],
            )
        )
    return resources


def load_all_resources() -> list[Resource]:
    resources_dir = _get_resources_dir()
    return _load_skills(resources_dir) + _load_rules(resources_dir) + _load_specs(resources_dir)


def load_resource_by_slug(slug: str) -> Resource | None:
    for resource in load_all_resources():
        if resource.slug == slug:
            return resource
    return None
