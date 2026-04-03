from aidev.domain.enums import ResourceType

AIDEV_DIR = ".aidev"
LOCK_FILE_NAME = "aidev.lock.json"
RESOURCES_BASE_DIR = "resources"
SKILL_FILENAME = "SKILL.md"
RULE_FILENAME = "RULE.md"
SPEC_FILENAMES = ["constitution_backend.md", "constitution_tests.md", "constitution_observability.md"]
INSTALL_DIRS = {
    ResourceType.SKILL: "skills",
    ResourceType.RULE: "rules",
    ResourceType.SPEC: "specs",
}
