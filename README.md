# aidriven

[![CI](https://github.com/ThiagoPanini/aidriven/actions/workflows/ci.yml/badge.svg)](https://github.com/ThiagoPanini/aidriven/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ThiagoPanini/aidriven/branch/main/graph/badge.svg)](https://codecov.io/gh/ThiagoPanini/aidriven)
[![PyPI](https://img.shields.io/pypi/v/aidriven)](https://pypi.org/project/aidriven/)
[![Python](https://img.shields.io/pypi/pyversions/aidriven)](https://pypi.org/project/aidriven/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**aidriven** is a Python library that helps developers discover and manage AI-oriented IDEs and install useful AI resources such as skills, agents, and specs.

---

## Features

- **IDE Discovery** — detects locally installed AI-oriented IDEs (VS Code, Cursor, Kiro) across Windows, macOS, and Linux
- **Multi-installation support** — handles multiple variants and channels (e.g., VS Code Stable and Insiders) as separate entries
- **Graceful degradation** — partial or corrupted installations are returned with a reduced confidence level rather than silently dropped
- **Extensible providers** — register custom IDE providers without touching built-in detection logic
- **Zero dependencies** — stdlib only (`pathlib`, `shutil`, `platform`, `subprocess`, `dataclasses`, `enum`)

---

## Installation

Requires Python 3.11+.

```bash
pip install aidriven
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add aidriven
```

---

## Usage

### Discover installed IDEs

```python
from aidriven.discovery import discover_ides

result = discover_ides()

for ide in result.detected_ides:
    print(ide.identifier, ide.display_name, ide.version, ide.confidence)
```

Each `DetectedIDE` entry contains:

| Field | Type | Description |
|---|---|---|
| `identifier` | `str` | Normalized IDE key (e.g. `vscode`, `cursor`, `kiro`) |
| `display_name` | `str` | Human-readable name |
| `install_path` | `Path` | Path to the installation |
| `version` | `str \| None` | Resolved version string, or `None` if unavailable |
| `channel` | `str` | Variant channel (e.g. `stable`, `insiders`) |
| `confidence` | `ConfidenceLevel` | `HIGH`, `MEDIUM`, or `LOW` |
| `detected_platform` | `str` | Platform the detection ran on |

### Register a custom provider

```python
from aidriven.discovery import discover_ides, ProviderRegistry

registry = ProviderRegistry()
registry.register(MyCustomIDEProvider())

result = discover_ides(registry=registry)
```

---

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies (including dev extras)
uv sync

# Run tests with coverage
uv run pytest

# Lint
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check
uv run mypy src/

# Serve docs locally
uv run mkdocs serve
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Install dev dependencies and set up pre-commit hooks:

```bash
uv sync
uv tool install pre-commit
pre-commit install
```

3. Make your changes, add tests, and ensure all checks pass:

```bash
pre-commit run --all-files
uv run pytest
```

4. Open a pull request against `main`.

Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/ThiagoPanini/aidriven/issues).

---

## License

MIT — see [LICENSE](LICENSE).
