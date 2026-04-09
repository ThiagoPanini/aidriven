"""AI target registry for the install subsystem."""

from __future__ import annotations

from aidriven.install._models import AITarget

TARGETS: dict[str, AITarget] = {
    "claude": AITarget(
        name="claude",
        project_read_path=".claude/skills",
        user_read_path=".claude/skills",
        autodetect_markers=(".claude/",),
    ),
    "copilot": AITarget(
        name="copilot",
        project_read_path=".agents/skills",
        user_read_path=".copilot/skills",
        autodetect_markers=(".github/copilot-instructions.md",),
    ),
}
