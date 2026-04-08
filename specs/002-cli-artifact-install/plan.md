# Implementation Plan: CLI Artifact Install

**Branch**: `v0.2.0/spec-002-cli-artifact-install` | **Date**: 2026-04-07 | **Spec**: [spec.md](spec.md)
**Input**: [spec.md](spec.md), [reference-analysis.md](reference-analysis.md)

## Summary

Deliver an `aidriven install` command that fetches AI artifacts (initial type: `skills`) from the trusted `aidriven-resources` GitHub repository and places them at the correct location for one or more user-selected AI targets (`claude`, `copilot`). Files are stored once at a canonical `.agents/skills/<name>/` directory and exposed to target-specific read paths via directory symlinks (the `vercel-labs/skills` model), with `--copy` as an opt-in alternative. Reproducibility is provided by a VCS-friendly `aidriven-lock.json` lockfile pinned to the source commit SHA. The implementation is library-first (per Constitution §I), with the CLI as a thin adapter, and is designed to extend cleanly to additional artifact types and AI targets without changes to core install logic.

## Technical Context

**Language/Version**: Python 3.11+ (dev: 3.14)
**Primary Dependencies**: Python stdlib only — `urllib.request`, `urllib.error`, `ssl`, `json`, `tarfile`, `hashlib`, `pathlib`, `shutil`, `os`, `tempfile`, `dataclasses`, `enum`, `logging`, `re`, `argparse`, `platform`, `sys`. (No third-party runtime deps; aligns with constitution §VII "minimal dependencies".)
**Storage**: Local filesystem only. Project lockfile: `<project-root>/aidriven-lock.json`. User lockfile: `~/.cache/aidriven/install-records.json`. Cache: OS user cache directory (`~/.cache/aidriven/cache/` on Linux/macOS, `%LOCALAPPDATA%\aidriven\Cache\` on Windows).
**Testing**: pytest with `tests/unit/`, `tests/integration/`, `tests/cli/`. Network is mocked at the `urllib` boundary; tarball extraction is exercised against fixture archives.
**Target Platform**: Linux, macOS, Windows. Symlink mode uses POSIX symlinks on Unix and `os.symlink(target_is_directory=True)` (which creates a directory symlink/junction) on Windows; falls back to copy mode per target on failure.
**Project Type**: Single-project Python library + CLI (`src/aidriven/`).
**Performance Goals**: Cold install of one skill (network reachable, no cache) under 10s on a standard connection (SC-001). CLI startup under 500ms (Constitution §IX, G16) — install module imports MUST be lazy.
**Constraints**: HTTPS-only downloads (FR-025), retries with exponential backoff for transient errors (FR-025a), no arbitrary code execution at any phase (Constitution §IV), path-traversal prevention on tarball extraction (G9), idempotent installs (FR-030, G11), deterministic project lockfile output (FR-032, SC-009).
**Scale/Scope**: A handful of AI targets and dozens of skills in v1; designed to grow to many more without core refactors.

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| §I Library-First / G1 | PASS | All install logic lives under `src/aidriven/install/`; the CLI module only parses args and formats output. |
| §II CLI-First UX / G2 | PASS | `install` is a verb-noun subcommand; `--help`, defaults, error/warning/success messages defined in CLI contract. |
| §III Automation / G3–G7 | PASS | `--json`, `--quiet`, `--verbose`, `--dry-run`, `--yes`, distinct exit codes specified in CLI contract. |
| §IV Installation Safety / G8–G10 | PASS | Single trusted source (`aidriven-resources`); per-run SHA pinning (FR-022b); SHA-256 integrity check (FR-024); foreign-file overwrite protection (FR-031); path-traversal validation on tarball entries (G9); no execution of artifact content (G10). |
| §V Idempotency / G11 | PASS | Content-hash comparison (FR-030); atomic writes via tempdir + `os.replace`; partial-install cleanup. |
| §VI Portability / G12 | PASS | All paths via `pathlib.Path`. Windows symlink fallback to copy. UTF-8 explicit. |
| §VII Engineering Quality / G13–G15 | PASS | mypy strict, ruff clean; unit + integration + CLI tests planned; coverage tracked. |
| §VIII Observability | PASS | Uses `logging`; structured JSON includes errors; no telemetry. |
| §IX Perceived Performance / G16 | PASS | Heavy modules (`tarfile`, `urllib`, `ssl`, `hashlib`) lazy-imported inside install entrypoint, not at package import. Manifest cache TTL (FR-028). `--no-cache` bypass available via `--force`. |
| §X Governance | PASS | Plan references gates; deviations documented in Complexity Tracking (none). |
| Phase boundary G19 | PASS | Discover/Resolve/Preview/Install separated in module layout (`resolver`, `planner`, `installer`). |

**No constitutional violations.** Complexity Tracking section is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-cli-artifact-install/
├── spec.md                        # Approved feature spec
├── reference-analysis.md          # vercel-labs/skills inspection notes
├── plan.md                        # This file
├── research.md                    # Phase 0 — design research & decisions
├── data-model.md                  # Phase 1 — entity model
├── quickstart.md                  # Phase 1 — end-to-end usage walkthrough
├── contracts/
│   ├── cli.md                     # CLI surface contract (flags, exit codes, output)
│   ├── manifest.schema.json       # JSON schema for aidriven-resources/manifest.json
│   └── lockfile.schema.json       # JSON schema for aidriven-lock.json
├── checklists/
│   └── requirements.md            # Existing
└── tasks.md                       # /speckit.tasks output (not generated here)
```

### Source Code (repository root)

```text
src/aidriven/
├── __init__.py
├── py.typed
├── discovery/                     # Existing — IDE/env discovery (used as auto-detect input only)
│   └── ...
├── install/                       # NEW — feature root, library-first
│   ├── __init__.py                # Public API: install_artifact(), InstallRequest, InstallResult
│   ├── _models.py                 # Dataclasses: InstallRequest, InstallPlan, InstallResult, Manifest, ManifestEntry, LockEntry, Scope, InstallMode
│   ├── _names.py                  # Artifact-name validator (FR-003 regex)
│   ├── _targets.py                # AI target registry, path table (symlink + copy modes), extensibility hook
│   ├── _scope.py                  # Project-root resolution (walk-up to .git, fallback cwd) — FR-005a
│   ├── _autodetect.py             # AI target auto-detection (uses discovery/ + filesystem markers)
│   ├── _http.py                   # urllib wrapper: HTTPS-only, retry/backoff (FR-025a), User-Agent, timeout
│   ├── _github.py                 # GitHub API: resolve default-branch HEAD SHA (FR-022b); build manifest + tarball URLs
│   ├── _manifest.py               # Fetch + parse + cache manifest.json; schema-version check; lookup
│   ├── _cache.py                  # On-disk cache (manifest TTL + tarball by content-hash); --force invalidation
│   ├── _fetcher.py                # Download tarball; verify SHA-256 against manifest checksum (FR-024)
│   ├── _archive.py                # Safe tarball extraction; path-traversal protection; extract single subdirectory
│   ├── _hashing.py                # SHA-256 of sorted file contents (FR-030)
│   ├── _planner.py                # Build InstallPlan: per-target canonical/read paths, mode, action (skip/install/update/conflict)
│   ├── _installer.py              # Apply plan: write canonical, create symlinks (with Windows junction fallback to copy), atomic via tempdir
│   ├── _lockfile.py               # Read/write project + user lockfiles; sorted keys, no timestamps for project lock
│   └── _errors.py                 # Typed exceptions: NetworkError, ManifestError, IntegrityError, ConflictError, etc. + exit-code mapping
├── cli/                           # NEW — thin CLI adapter
│   ├── __init__.py
│   ├── __main__.py                # `python -m aidriven`
│   ├── _main.py                   # argparse root; subcommand dispatch; lazy imports
│   ├── _install_cmd.py            # `install` subcommand: parse flags → call install.install_artifact(); format text/JSON output
│   └── _output.py                 # TTY detection, NO_COLOR, JSON renderer, logging config

tests/
├── unit/
│   ├── discovery/                 # Existing
│   └── install/
│       ├── test_names.py
│       ├── test_scope.py
│       ├── test_targets.py
│       ├── test_hashing.py
│       ├── test_archive_safety.py # Path-traversal fixtures (G9)
│       ├── test_manifest.py
│       ├── test_lockfile_determinism.py  # SC-009
│       ├── test_planner.py
│       └── test_http_retry.py     # FR-025a backoff
├── integration/
│   ├── discovery/                 # Existing
│   └── install/
│       ├── test_install_single_target.py     # US1
│       ├── test_install_multi_target.py      # US2
│       ├── test_install_user_scope.py        # US3
│       ├── test_force_refetch.py             # US4
│       ├── test_autodetect.py                # US5
│       ├── test_idempotency.py               # G11
│       ├── test_overwrite_protection.py      # G8
│       ├── test_symlink_fallback_windows.py  # FR-008b
│       ├── test_copy_mode.py
│       └── conftest.py            # Local HTTP server fixture serving manifest.json + fake tarballs
└── cli/
    └── install/
        ├── test_cli_help.py
        ├── test_cli_json_output.py            # G5
        ├── test_cli_exit_codes.py             # G7
        ├── test_cli_dry_run.py                # G6
        ├── test_cli_tty_safety.py             # G3
        └── test_cli_non_interactive.py        # G4
```

**Structure Decision**: Single-project layout (DEFAULT). The new `install/` package sits alongside the existing `discovery/` package under `src/aidriven/`, and the new `cli/` package introduces the first CLI surface in the repo. The library/CLI split satisfies Constitution §I (Library-First) — every CLI command is a thin adapter over a library function.

## Complexity Tracking

*(empty — no constitutional violations)*
