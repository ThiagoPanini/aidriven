# Skills

Repository-local Claude Code skills for **aidriven**. Invoke any skill with `/<name>` in Claude Code.

## Catalog

| Skill | File | Use when |
|-------|------|----------|
| `/skill-creator` | [commands/skill-creator.md](commands/skill-creator.md) | You want to turn a repeated workflow into a reusable skill |
| `/python-library-bootstrap` | [commands/python-library-bootstrap.md](commands/python-library-bootstrap.md) | Setting up a new Python library project from scratch |

## How Skills Work

Skills are Markdown files in `.claude/commands/`. When invoked, the file content becomes
the prompt context for Claude Code — guiding it through the workflow described in the skill.

**Creating a new skill:** Use `/skill-creator` and describe the workflow you want to capture.

**Updating a skill:** Edit the Markdown file directly and update this index if the
name or trigger description changes.

## Design Principles

- Each skill has a single, clearly scoped responsibility.
- Skills encode *why* behind conventions, not just *what*.
- Keep skill files under 100 lines; move extended examples to `commands/refs/<name>.md`.
- Iterate on skills based on real usage — stale skills cause confusion.
