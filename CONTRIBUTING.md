# Contributing to aidriven

Thank you for your interest in contributing! This document covers everything you
need to get started.

## Development Setup

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the full setup guide.

**Quick start:**

```bash
git clone https://github.com/ThiagoPanini/aidriven.git
cd aidriven
uv sync --group dev
uv run pre-commit install
```

## Workflow

1. **Fork** the repository (external contributors) or create a branch (maintainers).
2. Branch from `main` using a descriptive name: `feat/add-spec-type`, `fix/lockfile-parsing`.
3. Make your changes — keep commits focused and descriptive.
4. Run `pre-commit run --all-files` before pushing.
5. Open a Pull Request to `main` — fill in the PR template.
6. CI must pass before merging.

## Quality Gates

Run these locally before submitting a PR:

```bash
uv run ruff check . --fix   # Lint with auto-fix
uv run ruff format .         # Format
uv run mypy src/             # Type check (strict)
uv run pytest --cov          # Tests with coverage
```

Or run everything at once via pre-commit:

```bash
uv run pre-commit run --all-files
```

## Code Standards

- **Typing**: all public APIs must be fully typed. mypy runs in strict mode.
- **Formatting**: ruff format (enforced by pre-commit and CI).
- **Tests**: new features require tests; bug fixes should include a regression test.
- **Architecture**: respect the layered structure — see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
- **Commits**: use conventional commit style (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).

## Reporting Issues

Use the GitHub issue templates:

- [Bug Report](https://github.com/ThiagoPanini/aidriven/issues/new?template=bug_report.yml)
- [Feature Request](https://github.com/ThiagoPanini/aidriven/issues/new?template=feature_request.yml)

## Release Process

See [docs/RELEASE.md](docs/RELEASE.md).
Only maintainers publish releases.

## License

By contributing, you agree that your contributions will be licensed under the
project's [MIT License](LICENSE).
