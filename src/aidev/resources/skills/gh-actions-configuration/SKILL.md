# GitHub Actions Configuration Skill

Writing efficient, reliable GitHub Actions workflows.

## Overview

GitHub Actions automates CI/CD directly in your GitHub repository. Workflows are defined in `.github/workflows/` as YAML files.

## Basic Workflow Structure

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v
```

## Matrix Strategy

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    os: [ubuntu-latest, macos-latest]
```

## Caching

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
```

## Best Practices

1. **Pin action versions** to a specific SHA for security
2. **Use caching** for dependencies to speed up workflows
3. **Limit permissions** with `permissions:` block
4. **Concurrency control** to cancel outdated runs
5. **Use `needs:`** to define job dependencies
