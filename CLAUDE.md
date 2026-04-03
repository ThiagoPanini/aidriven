# CLAUDE.md

Repository context for Claude Code sessions working in **aidriven**.

## Project

**aidriven** is a Python CLI library for managing AI development resources — skills, rules,
and spec constitutions — that can be installed into any software project.

- Package: `src/aidriven/`
- Python ≥ 3.11 | Build: hatchling | Package manager: uv
- CLI framework: Typer + Rich
- GitHub: https://github.com/ThiagoPanini/aidriven

**Implementation status:** The package skeleton (`__init__.py`, `py.typed`) exists;
full implementation is in progress. Do not infer a broken state from a minimal source tree.

## Architecture

```
src/aidriven/
  domain/        # Data models and enums — no I/O
  services/      # Orchestration — calls infra + presentation
  infra/         # Filesystem, serialization, resource loading
  presentation/  # Rich console output, prompts, renderers
  resources/     # Embedded Markdown assets (skills/, rules/, specs/)
  cli.py         # Typer CLI — entry point (restore [project.scripts] when ready)
```

The CLI entry point (`aidriven = "aidriven.cli:app"`) is **intentionally omitted** from
`pyproject.toml` until the implementation is in place — see the comment in that file.

## Resource Types

| Type | Directory | Description |
|------|-----------|-------------|
| `skill` | `resources/skills/` | Claude Code skills (SKILL.md per folder) |
| `rule` | `resources/rules/` | Dev rules (RULE.md per folder) |
| `spec` | `resources/specs/` | Specification constitutions (Markdown) |

## Common Commands

```bash
uv sync --group dev          # Install all dependencies
uv run ruff check .          # Lint
uv run ruff format .         # Format (auto-fix)
uv run mypy src/             # Type check
uv run pytest                # Tests
uv run pytest --cov          # Tests + coverage
pre-commit run --all-files   # Run all quality gates
uv build                     # Build distribution
```

## Toolchain

| Tool | Role |
|------|------|
| `uv` | Package manager, venv, lockfile |
| `hatchling` | Build backend |
| `ruff` | Linter + formatter (replaces flake8/black/isort) |
| `mypy` | Static type checking — strict mode |
| `pytest` + `pytest-cov` | Testing + coverage |
| `pre-commit` | Git hook automation |

## Quality Standards

- mypy runs in `strict` mode — all public APIs must be fully typed.
- ruff rules: E, F, I, W, UP, B, N, SIM, TCH, PT, RUF at line-length 100.
- `py.typed` marker present — this package is typed for downstream consumers.
- Coverage threshold: currently 0 (raise it as tests are added).

## Development Workflow

1. Branch from `main` (feature or bugfix branch)
2. Implement + test
3. `pre-commit run --all-files` before committing
4. Open PR to `main` — CI validates lint, type-check, tests
5. Merge when CI passes and reviewed

## Release Workflow

See [docs/RELEASE.md](docs/RELEASE.md) for full details and required manual steps.

Short path:
1. Create version branch `v0.1.0` → triggers `release.yml` (validation + build)
2. Push semver tag `git tag v0.1.0 && git push origin v0.1.0` → triggers `publish.yml`
3. `publish.yml` builds + publishes to PyPI via OIDC (no stored tokens)

## AI Workflow — Skills

Repository-local Claude Code skills are in [.claude/commands/](.claude/commands/).
See [.claude/SKILLS.md](.claude/SKILLS.md) for the catalog and usage guide.

Invoke in Claude Code: `/<skill-name>`
