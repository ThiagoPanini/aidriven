# Pre-Commit Hooks Catalog

Complete hook blocks to append to `.pre-commit-config.yaml` based on selected tools.

The base hygiene hooks are defined inline in `SKILL.md`. Append the blocks below **after** the
base hooks, in the order: formatter → linter → type-checker → security.

---

## Formatters

### `ruff` (format mode)
```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.9
    hooks:
      - id: ruff-format
```
> If `linter = ruff` as well, combine with the linter block below into a single repo entry
> (ruff provides both `ruff` and `ruff-format` hooks under the same repo).

### `black`
```yaml
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3
```

### `isort` (used alongside black or flake8)
```yaml
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
```

### `autopep8`
```yaml
  - repo: https://github.com/pre-commit/mirrors-autopep8
    rev: v2.0.4
    hooks:
      - id: autopep8
        args: ["--max-line-length", "100", "--in-place"]
```

---

## Linters

### `ruff` (lint mode — combined with formatter when both are ruff)
```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.9
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
```
> Use this combined block when both `linter = ruff` and `formatter = ruff`.
> If only the linter is ruff (formatter is something else), use just the `ruff` hook:
```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.9
    hooks:
      - id: ruff
        args: ["--fix"]
```

### `flake8`
```yaml
  - repo: https://github.com/PyCQA/flake8
    rev: 7.1.1
    hooks:
      - id: flake8
        additional_dependencies:
          - flake8-bugbear
          - flake8-isort
```

### `pylint`
```yaml
  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        args: ["--rcfile=pyproject.toml"]
```
> `pylint` runs as a local hook because it needs access to the installed package.
> Ensure `pylint` is in the dev dependencies.

---

## Static Type Checkers

### `mypy`
```yaml
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.1
    hooks:
      - id: mypy
        args: ["--config-file=pyproject.toml"]
        additional_dependencies:
          - types-requests  # add any stub packages needed
```
> Adjust `additional_dependencies` based on the project's runtime dependencies.

### `pyright`
```yaml
  - repo: local
    hooks:
      - id: pyright
        name: pyright
        entry: pyright
        language: system
        types: [python]
        pass_filenames: false
```
> `pyright` runs as a local hook. Ensure `pyright` is available in the environment.

### `basedpyright`
```yaml
  - repo: local
    hooks:
      - id: basedpyright
        name: basedpyright
        entry: basedpyright
        language: system
        types: [python]
        pass_filenames: false
```
> Ensure `basedpyright` is in dev dependencies.

---

## Security Scanning

### `bandit`
```yaml
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
```

### `safety`
```yaml
  - repo: local
    hooks:
      - id: safety
        name: safety
        entry: safety check --full-report
        language: system
        pass_filenames: false
```
> Requires `safety` installed in the environment.

---

## Versioning

### `commitizen` (commit message linting)
```yaml
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.1.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```
> Only add when `versioning = commitizen`.

---

## Additional Useful Hooks (Optional)

These are not automatically added but can be suggested to the user:

### `pyproject-fmt` (keep pyproject.toml tidy)
```yaml
  - repo: https://github.com/tox-dev/pyproject-fmt
    rev: 2.5.0
    hooks:
      - id: pyproject-fmt
```

---

## Version Pinning Note

The `rev:` values above reflect stable versions at time of writing. Always verify the latest
version tags on GitHub or pre-commit.ci before using. You can also use `pre-commit autoupdate`
after generating the file to pull the latest hook versions.
