---
name: python-project-setup
description: >
  Configure modern Python development tooling for any Python project — library, backend, CLI, or
  otherwise. Invoke this skill whenever a user wants to set up or improve Python tooling, configure
  pyproject.toml, add pre-commit hooks, set up linting or formatting, configure a type checker or
  test runner, or any request like "set up my Python project", "configure Python tooling",
  "add pre-commit to my project", "set up ruff and mypy", or "bootstrap Python dev tools".
  This skill works on both empty repositories and existing projects with partial configuration.
  It produces ONLY configuration files — no source code, no test logic.
---

# Python Project Setup

Configure modern Python development tooling for any Python project. This skill works on both
new (empty) repositories and existing projects that already have code and partial configuration.
It creates and updates configuration files only — never source code or test logic.

Read `references/tools-catalog.md` for all supported tool options and their `pyproject.toml`
config snippets. Read `references/pre-commit-catalog.md` for all pre-commit hook configurations.

## Mission

Set up, modernize, or complete the local development tooling for a Python project. The skill is
scoped exclusively to developer experience tooling: package management, linting, formatting, type
checking, testing, coverage, pre-commit hooks, and security scanning. It does **not** touch
documentation, CI/CD, GitHub Actions, publishing, release automation, or repository hosting.

## Supported Project Types

| Type | Description | Default adjustments |
|---|---|---|
| `library` | Distributable Python package (PyPI) | `build_backend = hatchling`, `versioning = hatch-vcs` |
| `backend` | Web API / server (FastAPI, Django, Flask) | `build_backend = none`, `versioning = none` |
| `cli` | Command-line tool | `build_backend = hatchling` if published, `none` otherwise |
| `data-science` | Notebooks, data pipelines | `build_backend = none`, `versioning = none` |
| `scripts` | Utility scripts, automation | `build_backend = none`, `versioning = none` |

The project type influences defaults only. All tool categories work the same regardless of type.

---

## Phase 0 — Repository Analysis

**Before asking the user anything**, explore the current state of the repository. Use your file
reading tools to gather the following information:

1. **Existing configuration files** — check which of these exist:
   - `pyproject.toml` / `setup.py` / `setup.cfg`
   - `.pre-commit-config.yaml`
   - `.python-version`
   - `.gitignore`
   - `.editorconfig`
   - `requirements.txt` / `requirements-dev.txt` / `requirements*.txt`
   - `Pipfile` / `poetry.lock` / `uv.lock` / `pdm.lock`

2. **Project structure** — identify the layout:
   - Does `src/<name>/` exist? (src layout)
   - Does a flat `<name>/` package directory exist at the root?
   - Are there `tests/` or `test/` directories?

3. **Currently configured tools** — if `pyproject.toml` exists, read it and identify:
   - Which `[tool.*]` sections are already present (ruff, mypy, pytest, etc.)
   - The `[build-system]` backend in use, if any
   - The declared `requires-python` version
   - Package manager in use (inferred from lock files or tool sections)

4. **Project type signals** — look for:
   - Framework imports or dependencies (fastapi, django, flask, click, typer, etc.) suggesting
     a backend, CLI, or other project type rather than a distributable library
   - Presence of a `[project]` table with `name`, `version`, etc.

After analysis, present a concise summary to the user:

> **Project scan complete**
> - Found: `pyproject.toml` with ruff and pytest configured, `uv.lock` (uv), Python 3.12
> - Missing: mypy, pre-commit, `.editorconfig`
> - Project type looks like: backend web app (fastapi detected)
>
> I'll focus on adding the missing tooling. Continue?

If the repository appears to be empty or brand new, note that and proceed to gather context.

---

## Phase 1 — Gather Context

Based on the Phase 0 analysis, ask only for information that could not be determined automatically.
Keep it concise — you can ask all at once. Do not re-ask for things already found.

1. **Project name** — the distribution name (e.g. `my-project`). Skip if already in `pyproject.toml`.
2. **Package name** — the importable Python name (e.g. `my_project`). Skip if determinable from
   the project structure. Defaults to project name with hyphens replaced by underscores.
3. **Python version** — minimum supported version. Skip if found in `.python-version` or
   `requires-python`. Default: `3.11`.
4. **Author name and email** — for `pyproject.toml`. Skip if already present. Use
   `YOUR NAME` / `your@email.com` as placeholders if the user wants to skip.
5. **Project type** — optional signal to adjust defaults. Examples: `library`, `backend`,
   `cli`, `data-science`, `scripts`. If unsure or irrelevant, skip — the tooling works the same.
6. **Tool selections** — see the table below. Show what is already configured and only ask
   about what is missing or what the user may want to change.

### Tool Selection Table

| Category | Default | Alternatives |
|---|---|---|
| `package_manager` | `uv` | `pip`, `poetry`, `pdm`, `hatch` |
| `build_backend` | `hatchling` (library) / `none` (app) | `setuptools`, `flit-core`, `poetry-core`, `pdm-backend`, `none` |
| `linter` | `ruff` | `flake8`, `pylint`, `none` |
| `formatter` | `ruff` | `black`, `autopep8`, `none` |
| `import_sorter` | `none` (ruff's `I` rule covers it) | `isort` |
| `static_type_checker` | `mypy` | `pyright`, `basedpyright`, `none` |
| `test_runner` | `pytest` | `unittest`, `none` |
| `coverage` | `pytest-cov` | `coverage`, `none` |
| `versioning` | `hatch-vcs` (library) / `none` (app) | `bump2version`, `commitizen`, `manual`, `none` |
| `security_scanning` | `none` | `bandit`, `safety` |

**Notes on project type defaults:**
- For distributable **libraries/packages**: `build_backend = hatchling`, `versioning = hatch-vcs`
- For **backend/app/CLI** projects not distributed via PyPI: `build_backend = none`,
  `versioning = none` (or `manual`); pyproject.toml still serves as a tool config hub

If the user says "just use the defaults" or provides no selections, apply the defaults above
based on the inferred project type.

---

## Phase 2 — Resolve and Confirm

Before modifying any files, summarize what will be created or updated and ask the user to confirm.
Distinguish clearly between **new files**, **files that will be updated**, and **files already
present with no changes needed**. Example:

> I'll configure your project with:
> - uv · ruff (lint + format) · mypy · pytest + pytest-cov
> - pre-commit with ruff, mypy, and hygiene hooks
>
> **New files:** `.python-version`, `.editorconfig`, `.pre-commit-config.yaml`
> **Update:** `pyproject.toml` (add mypy and coverage sections)
> **Already present, no change:** `.gitignore`, ruff config in pyproject.toml
>
> Ready to proceed?

Only proceed after confirmation (or if the user says "just do it").

---

## Phase 3 — Create and Update Files

Work through the files below. For each file: check whether it already exists. If it exists with
real content, **update or merge** rather than overwrite — add missing sections, update stale
versions, and preserve existing configuration unless the user explicitly asks to replace it.

### File Update Strategy

For every file the skill touches, apply one of these actions and report it in the final summary:

| Action | When to use |
|---|---|
| **Create** | File does not exist. Generate from scratch. |
| **Update** | File exists but is missing sections or has outdated config. Merge new content. |
| **Preserve** | File exists and its content is already correct. Leave untouched. |
| **Skip** | File is irrelevant to the selected tools or project type. Do not create. |

**Idempotency rule:** Running the skill twice with the same inputs must produce the same result.
Never duplicate sections, hooks, or dependencies. Always check before appending.

### 3.1 Directory Scaffolding

Only create these if they are missing and relevant:

- `src/<package_name>/` — only for library/package projects with src layout; add `.gitkeep`
- `tests/` — add `.gitkeep` if the directory does not exist

> Never create `.py` files — only `.gitkeep` placeholders.
> Do not create `docs/` or any documentation directory.

### 3.2 `pyproject.toml`

This is the primary configuration hub. If it already exists, read it fully first and only add or
update the sections relevant to selected tools. Never remove existing sections unless the user
explicitly requests it.

**[build-system]** — include only when `build_backend != none`. See `references/tools-catalog.md § Build Backends`.

**[project]** — if absent, create with:
```toml
[project]
name = "<project-name>"
description = "<description>"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "<author>", email = "<email>" }]
requires-python = ">= <python-version>"
dynamic = ["version"]   # omit if versioning = manual or none; add version = "0.1.0" instead
dependencies = []
```
If `[project]` already exists, only add missing fields — do not overwrite existing ones.

**[tool.*] sections** — append one per selected tool that is not already configured. Pull exact
snippets from `references/tools-catalog.md`. Key rules:
- `linter: ruff` and `formatter: ruff` → single `[tool.ruff]` block covering both
- `import_sorter: none` when `linter: ruff` — the `I` rule handles it; ensure `known-first-party`
  is set in `[tool.ruff.lint.isort]`
- `import_sorter: isort` when ruff is not selected → add `[tool.isort]` block and `isort` dev dep
- `versioning: hatch-vcs` → affects `[build-system]` and adds `[tool.hatch.version]`
- `package_manager: uv` → add `[tool.uv]` with `dev-dependencies` group

**[project.optional-dependencies]** — add `dev` group when `package_manager` is not `uv`:
```toml
[project.optional-dependencies]
dev = []  # list dev deps here
```

If a `[tool.*]` section for a selected tool already exists, do not add a duplicate — instead
verify it is reasonably configured and note any recommended updates to the user.

### 3.3 `.python-version`

Single line: the minimum Python version (e.g. `3.11`). Create if missing. Skip if already present
with a valid version.

### 3.4 `.gitignore`

Copy content from `assets/gitignore-python.txt` verbatim if `.gitignore` does not exist.
If `.gitignore` already exists, append only the lines that are missing from it.

### 3.5 `.editorconfig`

Copy content from `assets/editorconfig.txt` verbatim. Skip if already present.

### 3.6 `.pre-commit-config.yaml`

**Always create or update this file.** Pre-commit is part of every setup regardless of other
selections.

If the file does not exist, create it starting with the base hygiene hooks:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
      - id: detect-private-key
      - id: mixed-line-ending
```

If the file already exists, check which hooks are already present and only add the missing ones.
Do not duplicate repos or hooks.

Then append tool-specific hooks from `references/pre-commit-catalog.md` for:
- `linter` (if not `none` and not already present)
- `formatter` (if not `none` and different from `linter`, and not already present)
- `static_type_checker` (if not `none` and not already present)
- `security_scanning` (if not `none` and not already present)
- `versioning: commitizen` → append commitizen hook for commit-msg stage

---

## Phase 4 — Validation Checklist

After all files are created or updated, verify:

- [ ] `pyproject.toml` is valid TOML (mentally parse for syntax errors)
- [ ] `[build-system]` block is present and matches selected backend (only when `build_backend != none`)
- [ ] No duplicate `[tool.*]` sections introduced
- [ ] `.pre-commit-config.yaml` is present and has at minimum the base hygiene hooks
- [ ] `.gitignore` exists
- [ ] `.editorconfig` exists
- [ ] `.python-version` exists with the correct version
- [ ] No `.py` files were created
- [ ] No invented/fabricated metadata — only placeholders where info was missing
- [ ] Existing file content was preserved and only extended, not replaced
- [ ] Running the skill again with the same inputs would produce no additional changes (idempotent)

---

## Phase 5 — Final Summary and Next Steps

### Summary Format

Present the results in this format:

> **Setup complete**
>
> | File | Action | Details |
> |---|---|---|
> | `pyproject.toml` | Updated | Added `[tool.mypy]`, `[tool.coverage.*]` |
> | `.pre-commit-config.yaml` | Created | Hygiene + ruff + mypy hooks |
> | `.editorconfig` | Created | Standard Python config |
> | `.python-version` | Created | `3.12` |
> | `.gitignore` | Preserved | Already complete |
> | `tests/` | Preserved | Already exists |

### Next Steps

After completing setup, tell the user what to do next. Tailor to their tool selections.
Example for `uv` + `ruff` + `mypy` + `pytest`:

```bash
# Install pre-commit and activate hooks
uv tool install pre-commit
pre-commit install

# Install project dependencies
uv sync

# Run all pre-commit hooks on existing files
pre-commit run --all-files

# Verify lint and type check pass
uv run ruff check .
uv run mypy src/

# Run tests
uv run pytest
```

Also remind them to:
1. Replace any placeholder values in `pyproject.toml` (name, author, email, description)
2. Review the `known-first-party` setting in `[tool.ruff.lint.isort]` to match their package name
3. Adjust `fail_under` in `[tool.coverage.report]` as test coverage grows

---

## Important Rules

- **Never** create `.py` files — only `.gitkeep` for placeholder directories.
- **Never** invent project metadata. Use explicit placeholders like `<project-name>`, `YOUR NAME`.
- **Preserve** existing configuration — update and extend, never blindly overwrite.
- **Always** create or update `.pre-commit-config.yaml`.
- **Prefer** `pyproject.toml` over separate config files (`setup.cfg`, `tox.ini`, `.flake8`, `mypy.ini`).
- When the user selects `ruff` for both linter and formatter, configure both in a single `[tool.ruff]` block.
- When unsure about a user's tool selection, default to the table in Phase 1.
- **Do not** create documentation files, CI workflows, GitHub community health files, publishing configs, or any file unrelated to local development tooling.
- **Do not** assume the project is a library — always check or ask for the project type.
- **Do not** expand scope beyond the tool categories listed in the Tool Selection Table.
