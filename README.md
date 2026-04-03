# aidriven

[![CI](https://github.com/ThiagoPanini/aidriven/actions/workflows/ci.yml/badge.svg)](https://github.com/ThiagoPanini/aidriven/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/aidriven)](https://pypi.org/project/aidriven/)
[![PyPI](https://img.shields.io/pypi/v/aidriven)](https://pypi.org/project/aidriven/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python CLI tool for getting and installing AI development resources — skills, rules,
and spec constitutions — into software projects.

> **Status:** Early development. The library foundation and toolchain are in place;
> CLI commands are being implemented.

---

## What It Does

`aidriven` manages a catalog of reusable AI development assets:

| Type | Description |
|------|-------------|
| **Skills** | Claude Code skills (SKILL.md) for common development workflows |
| **Rules** | Engineering rules and conventions (RULE.md) |
| **Specs** | Specification constitutions for backend, tests, observability |

You can list, install, inspect, update, and remove these assets in any project.

---

## Installation

```bash
pip install aidriven
```

Or with uv:

```bash
uv add aidriven
```

> CLI commands will be available once the implementation is complete.
> See [CONTRIBUTING.md](CONTRIBUTING.md) to follow or contribute to the progress.

---

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the full setup guide.

**Quick start:**

```bash
git clone https://github.com/ThiagoPanini/aidriven.git
cd aidriven
uv sync --group dev
uv run pre-commit install
uv run pytest
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow,
coding standards, and quality gates.

---

## Release

See [docs/RELEASE.md](docs/RELEASE.md) for the full release process including
required manual platform steps (GitHub environments, PyPI Trusted Publishing).

---

## License

[MIT](LICENSE) — Thiago Panini, 2026
