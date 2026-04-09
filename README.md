# aidriven

[![CI](https://github.com/ThiagoPanini/aidriven/actions/workflows/ci.yml/badge.svg)](https://github.com/ThiagoPanini/aidriven/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ThiagoPanini/aidriven/branch/main/graph/badge.svg)](https://codecov.io/gh/ThiagoPanini/aidriven)
[![PyPI](https://img.shields.io/pypi/v/aidriven)](https://pypi.org/project/aidriven/)
[![Python](https://img.shields.io/pypi/pyversions/aidriven)](https://pypi.org/project/aidriven/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**aidriven** is a Python library and CLI that helps developers discover AI-oriented IDEs and install AI resources — skills, agents, and specs — into the correct locations for each AI coding assistant.

---

## Features

- **`aidriven install`** — fetch and install AI skills from [aidriven-resources](https://github.com/ThiagoPanini/aidriven-resources) for Claude Code, GitHub Copilot, and more
- **IDE Discovery** — detects locally installed AI-oriented IDEs (VS Code, Cursor, Kiro) across Windows, macOS, and Linux
- **Multi-target installs** — install one skill for multiple AI targets in a single command
- **Canonical placement** — one copy under `.agents/skills/<name>/`, symlinks from each AI's read path (follows the [vercel-labs/skills](https://github.com/vercel-labs/skills) model)
- **Reproducible** — lockfile (`aidriven-lock.json`) records the source commit SHA and content hash for every install
- **Graceful degradation** — partial or corrupted IDE installations are returned with a reduced confidence level rather than silently dropped
- **Zero runtime dependencies** — stdlib only

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

## CLI: `aidriven install`

### Install a skill for one AI target

```bash
aidriven install skill code-reviewer --ai claude
```

Creates:
- `.agents/skills/code-reviewer/` — canonical shared directory (all AI targets read from here)
- `.claude/skills/code-reviewer` → `.agents/skills/code-reviewer` — directory symlink for Claude Code
- `aidriven-lock.json` — updated with source SHA, content hash, and target list

Re-running the same command is a no-op — the CLI detects that the content is already up to date and exits `0` without modifying any files.

### Install a skill for multiple AI targets

```bash
aidriven install skill code-reviewer --ai claude --ai copilot
```

A single canonical copy is placed at `.agents/skills/code-reviewer/`. Claude Code gets a symlink; Copilot reads `.agents/skills/` directly so no symlink is needed.

### Install at user scope

```bash
aidriven install skill code-reviewer --ai claude --scope user
```

Installs to `~/.agents/skills/code-reviewer/` with a symlink at `~/.claude/skills/code-reviewer`. Records the entry in the user lockfile (`~/.cache/aidriven/install-records.json` on Linux/macOS or `%LOCALAPPDATA%\aidriven\install-records.json` on Windows) instead of the project lockfile.

### Auto-detect AI targets

When exactly one supported AI target is detected in the current project, `--ai` can be omitted:

```bash
aidriven install skill code-reviewer
```

If zero or multiple targets are detected, the command exits with code `6` and lists what was found with instructions to specify `--ai` explicitly.

### Preview without writing (dry run)

```bash
aidriven install skill code-reviewer --ai claude --ai copilot --dry-run
```

Prints the install plan — which actions would be taken for each target — without touching the filesystem or lockfile. Combine with `--json` for machine-readable output.

### Force re-fetch

```bash
aidriven install skill code-reviewer --ai claude --force
```

Bypasses the local cache and re-downloads the skill tarball. Useful after upstream changes or to verify integrity. Also overwrites files that were modified after installation.

### Copy mode

```bash
aidriven install skill code-reviewer --ai claude --ai copilot --copy
```

Places independent copies of the skill files at each AI target's read path instead of using a canonical directory + symlinks. Useful in environments where symlinks are not supported. Lockfile records `installMode: "copy"`.

### Machine-readable output

```bash
aidriven install skill code-reviewer --ai claude --json
```

Emits a single JSON object on stdout — no spinners or color — regardless of TTY:

```json
{
  "request": { "artifactType": "skill", "name": "code-reviewer", "targets": ["claude"], "scope": "project", "mode": "symlink", "force": false, "dryRun": false },
  "sourceCommitSha": "a1b2c3d4…",
  "computedHash": "sha256:e5f6…",
  "lockfilePath": "/your/project/aidriven-lock.json",
  "targets": [
    {
      "target": "claude",
      "action": "install_new",
      "finalMode": "symlink",
      "readPath": "/your/project/.claude/skills/code-reviewer",
      "canonicalPath": "/your/project/.agents/skills/code-reviewer",
      "error": null
    }
  ],
  "success": true,
  "exitCode": 0
}
```

### All options

| Flag | Default | Description |
|------|---------|-------------|
| `--ai <target>` | *(auto-detect)* | AI target to install for (`claude`, `copilot`). Repeatable. |
| `--scope project\|user` | `project` | Installation scope. |
| `--copy` | off | Copy files instead of creating symlinks. |
| `--force` | off | Re-fetch from remote; overwrite modified or foreign content. |
| `--dry-run` | off | Print the plan without writing anything. |
| `--json` | off | Emit JSON on stdout instead of human text. |
| `--quiet` | off | Suppress all non-error output. |
| `--verbose` | off | Enable DEBUG-level diagnostic messages. |
| `--yes` | off | Skip interactive confirmation prompts. |
| `--no-cache` | off | Bypass the download cache (does not force overwrite). |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success — every target installed, updated, or already up to date |
| `1` | Generic failure — at least one target failed |
| `2` | Usage error — invalid argument or unknown target/type |
| `3` | Network error — manifest or tarball unreachable after retries |
| `4` | Integrity error — checksum mismatch |
| `5` | Conflict — foreign/modified content present; re-run with `--force` |
| `6` | Auto-detection failure — zero or multiple targets detected |

### The lockfile

`aidriven-lock.json` is placed at the project root and is designed to be committed to version control. It is deterministic — keys are sorted, content is stable across runs with identical inputs — so diffs are meaningful.

```json
{
  "version": 1,
  "skills": {
    "code-reviewer": {
      "source": "aidriven-resources",
      "sourceCommitSha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      "computedHash": "sha256:e5f6…",
      "targets": ["claude", "copilot"],
      "scope": "project",
      "installMode": "symlink"
    }
  }
}
```

### Library API

Every CLI invocation maps 1:1 to a single library call:

```python
from aidriven.install import install_artifact, InstallRequest, ArtifactType, Scope, InstallMode

result = install_artifact(InstallRequest(
    artifact_type=ArtifactType.SKILL,
    name="code-reviewer",
    targets=("claude", "copilot"),
    scope=Scope.PROJECT,
    mode=InstallMode.SYMLINK,
    force=False,
    dry_run=False,
    assume_yes=False,
))

for tr in result.target_results:
    print(tr.target, tr.action_taken)
```

---

## Library: IDE Discovery

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
