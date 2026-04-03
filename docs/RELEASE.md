# Release Process

This document describes how to release a new version of **aidriven** to PyPI, including
all manual platform steps that cannot be encoded in files.

## Overview

```
Feature branch → PR → main
                              ↓
                    Create version branch (v0.1.0)
                              ↓
                    release.yml: validate + build
                              ↓
                    Push semver tag (v0.1.0)
                              ↓
                    publish.yml: build → PyPI (OIDC)
```

## Workflow Responsibilities

| Trigger | Workflow | What runs |
|---------|----------|-----------|
| PR / push to `main` | `ci.yml` | Lint, type-check, tests (matrix 3.11–3.13) |
| Push to `v*` branch | `release.yml` | Full validation + `uv build` |
| Push `v*` tag | `publish.yml` | Build + publish to PyPI via OIDC |
| GitHub Release published | `publish.yml` | Same as above (alternative path) |
| Manual dispatch | — | Not configured; use tag-based path |

## Step-by-Step Release

### 1. Prepare the release

Ensure `main` is stable and all changes are merged.

```bash
git checkout main
git pull origin main
```

Update the version in `pyproject.toml` and `src/aidriven/__init__.py`:

```toml
# pyproject.toml
version = "0.2.0"
```

```python
# src/aidriven/__init__.py
__version__ = "0.2.0"
```

Update `CHANGELOG.md` with the release notes.

Commit and open a PR if needed, or commit directly if permitted:

```bash
git add pyproject.toml src/aidriven/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

### 2. Create the version branch

```bash
git checkout -b v0.2.0
git push origin v0.2.0
```

This triggers `release.yml` which validates the full quality gate and builds the
distribution. Check the Actions tab for results.

### 3. Push the semver tag

Once the version branch CI passes:

```bash
git tag v0.2.0
git push origin v0.2.0
```

This triggers `publish.yml`, which builds the distribution and publishes to PyPI
via OIDC Trusted Publishing. No API token is needed.

### 4. Create a GitHub Release (optional)

In the GitHub UI: Releases → Draft a new release → Select tag `v0.2.0` → Publish.

Publishing a release also triggers `publish.yml` — so only use this path if you have
not already pushed the tag, or if you want to add release notes in the GitHub UI.

---

## Required Manual Platform Steps

These must be completed **once before the first publish**. They cannot be encoded in files.

### A. GitHub: Create the `pypi` Environment

1. Go to the repository: **Settings → Environments → New environment**
2. Name it exactly: **`pypi`**
3. (Optional) Add required reviewers for an extra approval gate before publishing
4. (Optional) Add a deployment branch rule matching `v*` tags only
5. Save

> The `publish.yml` workflow references `environment: pypi`. If this environment
> does not exist, the publish job will fail.

### B. PyPI: Configure Trusted Publisher

1. Log in to [pypi.org](https://pypi.org)
2. If this is the **first release**: claim the package name by publishing manually
   once, or use the "pending publisher" feature to pre-configure before first release.
3. Go to your project → **Settings → Publishing → Add a new publisher**
4. Fill in:
   - **Owner**: `ThiagoPanini`
   - **Repository**: `aidriven`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `pypi`
5. Save

> OIDC Trusted Publishing eliminates the need for stored PyPI API tokens. GitHub
> Actions requests a short-lived OIDC token and exchanges it directly with PyPI.

### C. GitHub: Branch Protection for `main`

In **Settings → Branches → Add rule** for `main`:

- [x] Require a pull request before merging
- [x] Require status checks to pass (add: `lint`, `type-check`, `test`)
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings

This complements the `no-commit-to-branch` pre-commit hook.

### D. (Optional) Test with TestPyPI First

Edit `publish.yml` temporarily to use TestPyPI:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
```

Revert this change before the real release.

---

## Rollback

If a bad release reaches PyPI:

- PyPI does not allow deleting releases (only yanking).
- Yank the release: **PyPI project → Settings → Releases → Yank**.
- A yanked release is hidden from `pip install <package>` but still installable
  with `pip install <package>==<bad-version>`.
- Publish a patched version immediately as a new release.

## Versioning

This project follows [Semantic Versioning](https://semver.org):

- `MAJOR.MINOR.PATCH`
- Breaking changes → MAJOR bump
- New features (backward-compatible) → MINOR bump
- Bug fixes → PATCH bump
- Pre-releases: `v1.0.0-rc1`, `v1.0.0-beta1` (also supported by tag patterns)
