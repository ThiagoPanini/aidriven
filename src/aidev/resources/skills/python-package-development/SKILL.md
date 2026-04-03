# Python Package Development Skill

Building, testing, and publishing Python packages with modern tooling.

## Overview

Modern Python packaging uses `pyproject.toml` as the single source of truth. This skill covers src layout, build tools, and publishing to PyPI.

## Layout

Use the `src/` layout to prevent accidental imports:

```
my-package/
  src/
    mypackage/
      __init__.py
      module.py
  tests/
    test_module.py
  pyproject.toml
  README.md
  LICENSE
```

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mypackage"
version = "0.1.0"
description = "A short description"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.28",
]
```

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Publishing

```bash
pip install build twine
python -m build
twine check dist/*
twine upload dist/*
```

## Testing

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```
