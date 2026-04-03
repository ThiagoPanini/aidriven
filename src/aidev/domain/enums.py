from enum import Enum


class ResourceType(str, Enum):
    SKILL = "skill"
    RULE = "rule"
    SPEC = "spec"
