Set up a professional Python library development foundation from scratch or from a bare repository.

## When to Use

When starting a new Python library project, modernizing an existing project's toolchain,
or bringing a bare repository up to professional standards. This skill captures the
conventions established during the aidriven repository bootstrap.

## Checklist

### 1. Audit First
- [ ] Read `pyproject.toml` — build backend, deps, metadata, entry points
- [ ] Check existing workflows, pre-commit, `.gitignore`
- [ ] Note which package manager is in use (uv / poetry / pip)
- [ ] Check layout: src-style vs flat
- [ ] Identify what conflicts with the target conventions

### 2. pyproject.toml
- [ ] Build backend: **hatchling** (standard, src-layout friendly, pyproject-native)
- [ ] Package manager: **uv** with `[dependency-groups]` (not `[project.optional-dependencies]`)
- [ ] Add: authors, license, keywords, classifiers, `[project.urls]`
- [ ] Set `requires-python` explicitly (recommend `>=3.11`)
- [ ] **Remove** `[project.scripts]` if CLI implementation does not exist yet — leave a comment
- [ ] mypy: `strict = true` + `[[tool.mypy.overrides]]` for third-party stubs
- [ ] ruff: select E, F, I, W, UP, B, N, SIM, TCH, PT, RUF; `line-length = 100`
- [ ] `[tool.coverage.run]`: source, branch=true; `[tool.coverage.report]`: fail_under=0 initially
- [ ] pytest: `testpaths`, `pythonpath = ["src"]`, `addopts = "--tb=short -q"`
- [ ] Dev deps: pytest>=8.0, pytest-cov>=5.0, pytest-mock, ruff, mypy>=1.10, pre-commit>=4.5.1

### 3. Package Markers
- [ ] `src/<package>/__init__.py` — minimal: docstring + `__version__`
- [ ] `src/<package>/py.typed` — empty marker (PEP 561, signals typed package)

### 4. Development Tooling
- [ ] `.editorconfig` — charset utf-8, LF endings, 4-space Python, 2-space YAML/TOML
- [ ] `CLAUDE.md` — repo context: architecture, commands, toolchain, workflow links

### 5. pre-commit
- [ ] `astral-sh/ruff-pre-commit` — ruff + ruff-format hooks
- [ ] `pre-commit/pre-commit-hooks` — trailing-whitespace, end-of-file-fixer, check-yaml,
      check-toml, check-json, check-merge-conflict, check-added-large-files, detect-private-key,
      no-commit-to-branch (main)
- [ ] `pre-commit/mirrors-mypy` — mypy --strict with `additional_dependencies` (runtime deps)

### 6. GitHub Actions
- [ ] `ci.yml`: push/main + PRs → lint job, type-check job (guarded until source exists), test job
- [ ] `release.yml`: push to `v*` branches → validate (lint + type-check + test + build)
- [ ] `publish.yml`: push `v*` tags + release published → build artifact + OIDC PyPI publish
- [ ] `permissions: contents: read` at workflow level; `id-token: write` only in publish job
- [ ] Matrix: 3.11, 3.12, 3.13; `fail-fast: false`

### 7. GitHub Automation
- [ ] `dependabot.yml` — pip (weekly) + github-actions (weekly)
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `.github/ISSUE_TEMPLATE/bug_report.yml`
- [ ] `.github/ISSUE_TEMPLATE/feature_request.yml`

### 8. Documentation
- [ ] `README.md` — badges, description, install, usage stub, links
- [ ] `CONTRIBUTING.md` — setup, workflow, standards, pre-commit install
- [ ] `docs/DEVELOPMENT.md` — detailed dev setup, architecture overview
- [ ] `docs/RELEASE.md` — full release process + **exact manual platform steps**
- [ ] `CHANGELOG.md` — initial stub with Keep a Changelog format

### 9. AI Workflow
- [ ] `.claude/commands/skill-creator.md` — skill for creating new skills
- [ ] `.claude/commands/python-library-bootstrap.md` — this skill
- [ ] `.claude/SKILLS.md` — skills index

## Key Conventions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build backend | hatchling | Standard, src-layout native, no config duplication |
| Package manager | uv | Fast, lockfile-native, replaces pip/venv/pip-tools |
| Linter/formatter | ruff | Single tool replaces flake8, black, isort |
| Entry points | Omit if unimplemented | A broken entry point causes install failures |
| Type checking | mypy strict | Library-grade correctness; overrides only for stubs |
| CI matrix | 3.11, 3.12, 3.13 | Cover active Python releases |
| Publish auth | OIDC Trusted Publishing | No stored secrets; requires manual PyPI setup |
| Release trigger | semver tags (v*) | Immutable; version branches are for validation only |

## Required Manual Steps After Bootstrap

These cannot be encoded in files — they require GitHub/PyPI web UI actions:

1. **GitHub: Create `pypi` environment** (Settings → Environments → New environment)
   - Add required reviewers if desired
   - No secrets needed (OIDC handles auth)

2. **PyPI: Configure Trusted Publisher**
   - Project Settings → Publishing → Add publisher
   - Owner: `ThiagoPanini`, Repo: `aidriven`, Workflow: `publish.yml`, Env: `pypi`

3. **GitHub: Branch protection for `main`**
   - Require PR + CI pass before merge
   - Optionally enforce `no-commit-to-branch` from pre-commit server-side too

See `docs/RELEASE.md` for full details.
