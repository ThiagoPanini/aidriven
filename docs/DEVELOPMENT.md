# Development Guide

Everything you need to contribute to **aidriven** locally.

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| Python ≥ 3.11 | Runtime | [python.org](https://python.org) or `pyenv` |
| uv | Package manager + venv | `curl -Lsf https://astral.sh/uv/install.sh \| sh` |
| git | Version control | System package |

## First-Time Setup

```bash
# Clone
git clone https://github.com/ThiagoPanini/aidriven.git
cd aidriven

# Create virtual environment and install all dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install

# Verify the setup
uv run ruff check .
uv run mypy src/
uv run pytest
```

## Daily Commands

```bash
# Lint (with auto-fix)
uv run ruff check . --fix
uv run ruff format .

# Type check
uv run mypy src/

# Tests
uv run pytest
uv run pytest --cov --cov-report=term-missing  # with coverage
uv run pytest tests/unit/ -v                    # specific directory
uv run pytest -k "test_catalog"                 # by name pattern

# Build (for release validation)
uv build
```

## Running Pre-commit

Pre-commit runs automatically on every commit once installed. To run manually:

```bash
# Run on all files
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run ruff
uv run pre-commit run mypy
```

## Project Structure

```
aidriven/
├── src/aidriven/              # Package source
│   ├── __init__.py         # Version
│   ├── py.typed            # PEP 561 typed marker
│   ├── domain/             # Data models and enums (no I/O)
│   ├── services/           # Orchestration layer
│   ├── infra/              # Filesystem, serialization, loaders
│   ├── presentation/       # Rich console output and prompts
│   ├── resources/          # Embedded Markdown assets
│   └── cli.py              # Typer CLI entry point (implement before wiring)
├── tests/                  # Test suite (mirrors src structure)
├── docs/                   # Extended documentation
├── .claude/commands/       # AI workflow skills
├── .github/workflows/      # CI/CD pipelines
├── pyproject.toml          # Single source of truth for project config
└── CLAUDE.md               # Context for Claude Code sessions
```

## Architecture Principles

The package follows a **clean layered architecture**:

```
CLI (cli.py)
  └─ Services (services/)
       ├─ Domain (domain/) ← no dependencies on other layers
       ├─ Infra (infra/)
       └─ Presentation (presentation/)
```

- **Domain** is pure Python: models, enums, business rules. No I/O.
- **Services** orchestrate: they call infra and presentation, never CLI.
- **Infra** handles I/O: file system, serialization, embedded resource loading.
- **Presentation** handles output: Rich tables, prompts, console messages.
- **CLI** is thin: parse args, call services, exit cleanly.

## Adding a New Command

1. Define any new models/enums in `domain/`.
2. Implement the logic in `services/<name>_service.py`.
3. Add file I/O in `infra/` if needed.
4. Add output in `presentation/` if needed.
5. Wire a Typer command in `cli.py`.
6. Restore `[project.scripts]` in `pyproject.toml` when the CLI is ready.
7. Add tests in `tests/`.

## Coding Standards

- **Typing**: strict mypy compliance required — all public APIs must be fully typed.
- **Formatting**: ruff format (double quotes, 4-space indent, 100-char line).
- **Imports**: ruff `I` rule enforces isort-compatible order.
- **Type-only imports**: use `from __future__ import annotations` or `TYPE_CHECKING` blocks
  (ruff `TCH` rule will suggest these automatically).
- **Naming**: follow PEP 8 (ruff `N` rule enforces it).

## Dependency Management

```bash
# Add a runtime dependency
uv add <package>

# Add a dev dependency
uv add --group dev <package>

# Upgrade all deps
uv lock --upgrade

# Sync environment with lock file
uv sync --group dev
```

Always commit `uv.lock` alongside `pyproject.toml` changes.

## IDE Setup

**VS Code** — recommended extensions:
- `ms-python.python`
- `ms-python.mypy-type-checker`
- `charliermarsh.ruff`

Set the Python interpreter to the uv venv:
```
Ctrl+Shift+P → Python: Select Interpreter → .venv/bin/python
```

**PyCharm** — set the project interpreter to `.venv/bin/python` and enable ruff as an
external linter.
