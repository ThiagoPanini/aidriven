# Tools Catalog

Complete reference for all supported tool categories. Each section contains:
- Supported tool names
- The `pyproject.toml` snippet to append for that tool
- Any additional notes

---

## Build Backends

Use only when the project is a distributable package (library, CLI tool published to PyPI, etc.).
For backend/app projects, `build_backend = none` is valid — pyproject.toml still works as a tool
config hub without a `[build-system]` table.

### `hatchling` (default for libraries)
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]
```
When `versioning = hatch-vcs`, replace the build-system block with:
```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]
```

### `setuptools`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[tool.setuptools.packages.find]
where = ["src"]
```

### `flit-core`
```toml
[build-system]
requires = ["flit_core>=3.9"]
build-backend = "flit_core.buildapi"
```
Note: With flit, `version` must be declared in `src/<package_name>/__init__.py`. Since we don't
create source files, set `version = "0.1.0"` in `[project]` and remind the user.

### `poetry-core`
```toml
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```
Note: poetry-core uses `[tool.poetry]` for project metadata instead of `[project]`. When this
backend is selected, adapt the project metadata section accordingly.

### `pdm-backend`
```toml
[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"
```

### `none`
No `[build-system]` table. Use this for projects that are not distributed as packages (apps,
scripts, backend services). `pyproject.toml` still configures all dev tools.

---

## Package Managers

### `uv` (default)
Add to `pyproject.toml`:
```toml
[tool.uv]
dev-dependencies = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
  # add other dev deps here
]
```
Dev commands: `uv sync`, `uv run pytest`, `uv run ruff check .`

### `poetry`
Add to `pyproject.toml` under `[tool.poetry.dependencies]` and `[tool.poetry.group.dev.dependencies]`:
```toml
[tool.poetry.dependencies]
python = ">=<python-version>"

[tool.poetry.group.dev.dependencies]
pytest = ">=8.0"
pytest-cov = ">=5.0"
```
Dev commands: `poetry install`, `poetry run pytest`, `poetry run ruff check .`

### `pip`
Use `[project.optional-dependencies]` in pyproject.toml:
```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
]
```
Also create a `requirements-dev.txt` pointing to the optional group:
```
-e ".[dev]"
```
Dev commands: `pip install -e ".[dev]"`, `pytest`, `ruff check .`

### `pdm`
```toml
[tool.pdm.dev-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
]
```
Dev commands: `pdm install`, `pdm run pytest`, `pdm run ruff check .`

### `hatch`
```toml
[tool.hatch.envs.default]
dependencies = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
]

[tool.hatch.envs.default.scripts]
test = "pytest {args}"
lint = "ruff check ."
fmt = "ruff format ."
typecheck = "mypy src/"
```
Dev commands: `hatch env create`, `hatch run test`, `hatch run lint`

---

## Linters

### `ruff` (default — also covers formatter when both are ruff)
```toml
[tool.ruff]
line-length = 100
target-version = "py311"  # adjust to selected python version

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP", "B", "N", "SIM", "TCH", "PT", "RUF"]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["<package_name>"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```
When `formatter = ruff` as well, the `[tool.ruff.format]` block covers both concerns.

### `flake8`
Flake8 does not support `pyproject.toml` natively. Create `.flake8` at the project root:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = .git, __pycache__, .venv, dist, build
```
Note: also consider adding `flake8-bugbear` and `flake8-isort` as dev dependencies.

### `pylint`
```toml
[tool.pylint.main]
source-roots = ["src"]

[tool.pylint.format]
max-line-length = 100

[tool.pylint."messages control"]
disable = ["C0114", "C0115", "C0116"]
```

---

## Formatters

### `ruff` (default — handled in `[tool.ruff.format]`)
See the ruff linter section above. No separate block needed.

### `black`
```toml
[tool.black]
line-length = 100
target-version = ["py311"]
```
Also add `isort` separately if not using ruff:
```toml
[tool.isort]
profile = "black"
line_length = 100
src_paths = ["src", "tests"]
```

### `autopep8`
autopep8 does not support `pyproject.toml`. Create `setup.cfg`:
```ini
[pycodestyle]
max-line-length = 100
```
Or pass `--max-line-length 100` as a CLI flag in pre-commit.

---

## Import Sorters

### `none` (default when `linter = ruff`)
When `linter = ruff`, import sorting is handled by ruff's `I` rule — no separate tool needed.
Ensure `known-first-party` is set in `[tool.ruff.lint.isort]`:
```toml
[tool.ruff.lint.isort]
known-first-party = ["<package_name>"]
```

### `isort` (use when ruff is not selected)
```toml
[tool.isort]
profile = "black"
line_length = 100
src_paths = ["src", "tests"]
known_first_party = ["<package_name>"]
```
Add `isort>=5.13` as a dev dependency.

---

## Static Type Checkers

### `mypy` (default)
```toml
[tool.mypy]
python_version = "<python-version>"
strict = true
warn_return_any = true
warn_unused_configs = true
exclude = ["build/", "dist/"]
```

### `pyright`
```toml
[tool.pyright]
pythonVersion = "<python-version>"
typeCheckingMode = "strict"
include = ["src"]
exclude = ["build", "dist"]
```

### `basedpyright`
```toml
[tool.basedpyright]
pythonVersion = "<python-version>"
typeCheckingMode = "strict"
include = ["src"]
exclude = ["build", "dist"]
```

---

## Test Runners

### `pytest` (default)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### `unittest`
No configuration needed in `pyproject.toml`. Tests are run with:
```bash
python -m unittest discover tests/
```

---

## Coverage

### `pytest-cov` (default)
Add as dev dependency. Configure in `pyproject.toml`:
```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
show_missing = true
skip_covered = false
fail_under = 0  # raise this as tests are added
```
Add `--cov=src --cov-report=term-missing --cov-report=xml` to `[tool.pytest.ini_options] addopts`.

> The `--cov-report=xml` flag writes `coverage.xml`, which CI coverage services (Codecov,
> Coveralls, Code Climate, SonarQube) require. Including it by default makes the project
> CI-ready without extra configuration. The file is already excluded by the standard
> `.gitignore` template.

### `coverage`
Same `[tool.coverage.*]` config as above. Run separately with `coverage run -m pytest && coverage report`.
For CI-ready XML output, also run `coverage xml` after `coverage report`.

---

## Versioning

### `hatch-vcs` (default for libraries)
Requires `hatchling` build backend. Reads version from git tags.
```toml
# In [build-system]:
requires = ["hatchling", "hatch-vcs"]

# Add:
[tool.hatch.version]
source = "vcs"
```
Set `dynamic = ["version"]` in `[project]`.

### `none` (default for apps/backends)
No versioning tool configured. Version is managed externally (env vars, deployment tags, etc.).
Remove `dynamic = ["version"]` from `[project]` if present.

### `manual`
Set a literal version in `[project]`:
```toml
version = "0.1.0"
```
Remove `dynamic = ["version"]`.

### `bump2version`
```toml
[tool.bumpversion]
current_version = "0.1.0"
commit = true
tag = true

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'
```
Set `version = "0.1.0"` in `[project]` and remove `dynamic`.

### `commitizen`
```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
tag_format = "v$version"
update_changelog_on_bump = true
version_files = ["pyproject.toml:version"]
```

---

## Security Scanning

### `none` (default)
No additional config.

### `bandit`
```toml
[tool.bandit]
exclude_dirs = ["tests", "build", "dist"]
skips = []
```
Add `bandit` as dev dep.

### `safety`
No pyproject.toml config. Add `safety` as dev dep.
Run manually with: `safety check --full-report`.
