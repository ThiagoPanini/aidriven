# Implementation Plan: CLI Remote Artifact Install

**Branch**: `v0.2.0/spec-002-cli-artifact-install` | **Date**: 2026-04-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-cli-artifact-install/spec.md`

## Summary

Deliver `aidriven install skill <name>` end-to-end using explicit AI target selection (`--ai`) as the primary routing signal, with optional auto-detect fallback. The installer fetches from `aidriven-resources` at a run-pinned commit SHA, verifies archive integrity, extracts one skill directory, installs into canonical `.agents/skills/<name>/` (symlink mode default), links/copies to AI read paths for `claude` and `copilot`, and writes deterministic lock state for reproducibility.

This plan adopts the strongest product and implementation patterns from `vercel-labs/skills` (canonical shared directory, symlink-first installation, copy fallback, deterministic lockfile), adapts them to `aidriven` constraints (single trusted source and stdlib-only Python), and avoids known pitfalls (dual-lock fragmentation and destructive silent overwrites).

## Planning Assumptions

- Source of truth is public `aidriven-resources`; no auth/private source support in v1.
- Initial artifact type is `skill`; design leaves extension seams for future artifact types.
- Initial AI targets are `claude` and `copilot`; explicit `--ai` is preferred.
- Project scope resolves from nearest `.git` ancestor, else `cwd`.
- Skills are unversioned in v1; run pins current default-branch SHA and records it.
- Existing IDE detection remains helper signal only for `--ai` omission.

## Technical Context

**Language/Version**: Python 3.11+ (dev 3.14)
**Primary Dependencies**: Python stdlib only (`argparse`, `urllib`, `ssl`, `json`, `tarfile`, `hashlib`, `pathlib`, `shutil`, `os`, `tempfile`, `dataclasses`, `enum`, `logging`, `re`, `platform`, `sys`)
**Storage**: Local filesystem only (`aidriven-lock.json`, `~/.cache/aidriven/install-records.json`, tar/manifest cache)
**Testing**: `pytest`, `pytest-cov`, `mypy --strict`, `ruff check`, `ruff format --check`
**Target Platform**: Windows, macOS, Linux
**Project Type**: Python library-first package with CLI adapter
**Performance Goals**: Standard install path under 10s on typical internet; idempotent re-run avoids rewrites and re-download when cache is valid
**Constraints**: No runtime third-party deps, deterministic install records, strict path safety, non-destructive default behavior
**Scale/Scope**: v1 focuses on one artifact type and two AI targets, with table-driven extensibility

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| G1 Library independence | PASS | Install/resolve/fetch/lock logic implemented in library modules under `src/aidriven/`; CLI is adapter only |
| G2 CLI thin-layer | PASS | CLI contract restricts CLI to parsing/output/exit mapping |
| G3 Color/no-color | PASS | ANSI color and glyphs emitted only when stdout is TTY and `NO_COLOR` is unset; `--json` suppresses unconditionally |
| G4 Non-interactive mode | PASS | `--yes`, no forced prompts in non-TTY contexts |
| G5 JSON output | PASS | Contracted single JSON output envelope for success and errors |
| G6 Dry-run fidelity | PASS | Planner produces full action plan with zero writes |
| G7 Exit codes | PASS | Six stable, documented exit codes (0–6) asserted by `test_cli_exit_codes.py` |
| G8 Overwrite protection | PASS | Conflict guard and `--force` gate required for foreign/modified content |
| G9 Path traversal prevention | PASS | Manifest path and tar extraction path checks are explicit |
| G11 Idempotent install | PASS | Hash-based no-op and deterministic writes |
| G12 Cross-platform paths | PASS | `pathlib` and platform abstraction for symlink/junction behavior; user lockfile path resolved per OS |
| G13/G14 Quality | PASS | Existing toolchain enforces strict typing and lint/format cleanliness |
| G19 Phase boundaries | PASS | Resolve/Preview/Install split into separate modules |

### Post-Phase 1 Re-Check

All gates above remain PASS after Phase 1 artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) with no unresolved clarifications.

## Design Decisions

### 1. Source and Manifest Strategy

- **Decision**: Resolve default-branch HEAD SHA once per run, then fetch both `manifest.json` and repository tarball at that SHA. Integrity is verified against a per-skill `contentHash` in the manifest (SHA-256 of sorted file contents, same algorithm as `computedHash` in the lockfile), computed post-extraction. This replaces a whole-tarball `archiveSha256` approach, which was both circular (manifest cannot store checksum of the commit it lives in) and fragile (GitHub tarballs are not byte-stable across regenerations).
- **Adopted from vercel-labs/skills**: Deterministic install state keyed by immutable source snapshot.
- **Adapted**: Single trusted source flow (`aidriven-resources`) instead of multi-repo source parser.
- **Avoided**: Whole-archive checksum dependency on GitHub tarball byte-stability.

### 2. Canonical Install Model

- **Decision**: Default mode is canonical `.agents/skills/<name>/` + per-target links where needed.
- **Adopted**: Shared canonical directory and symlink-first strategy.
- **Adapted**: Copilot project scope reads canonical directly (no link), Claude gets link.
- **Avoided**: Per-target duplicate storage in default path.

### 3. Copy Mode and Fallback

- **Decision**: `--copy` provides explicit copy mode; symlink/junction failure on a target falls back to copy for that target with warning.
- **Adopted**: Optional copy strategy for restricted environments.
- **Avoided**: Hard failure for one target causing all targets to fail when fallback is safe.

### 4. Lockfile and Determinism

- **Decision**: Project `aidriven-lock.json` and user `~/.cache/aidriven/install-records.json` share schema version 1.
- **Adopted**: Sorted keys and SHA-256 content hash computed from sorted file paths.
- **Adapted**: One lockfile per scope with common schema.
- **Avoided**: Dual-lock cross-command fragmentation and silent migration loss.

### 5. Extensibility Without Overengineering

- **Decision**: Keep v1 type/target registries table-driven (`ArtifactType`, `AITarget` mapping) and phase-separated internals.
- **Adopted**: Registry-style expansion pattern.
- **Adapted**: Minimal seam sufficient for adding new artifact types/targets later.
- **Avoided**: Plugin system or dynamic source adapters in first delivery.

## Proposed CLI

Primary command:

```bash
aidriven install <artifact-type> <artifact-name> [--ai <target>]... [--scope project|user] [--force] [--copy] [--dry-run] [--json] [--quiet | --verbose] [--yes] [--no-cache]
```

UX policy:

- Explicit `--ai` is authoritative; no auto-detect when provided.
- Omitted `--ai`: detect targets; proceed if exactly one found; error (exit 6) if zero or multiple found.
- `--force` bypasses cache and conflict guards; idempotency hash check (`SKIP_IDENTICAL`) still applies after fetch — no write occurs if extracted content is identical to installed content.
- `--no-cache` bypasses fetch cache only; does NOT enable overwrite of foreign/modified content (distinct from `--force`).
- `--quiet` and `--verbose` are mutually exclusive (exit 2 if both given).
- `--json` suppresses spinners and color regardless of TTY.
- Human output is concise per-target status with mode/path details.
- `--dry-run` computes complete plan and emits output, no writes.

Key validation:

- Artifact type must be supported (`skill` in v1).
- Artifact name must match `^[a-z][a-z0-9-]{0,63}$` before network calls.
- Unknown target values fail fast with actionable guidance.

## Architecture/Modules

### Planned library modules under `src/aidriven/install/`

- `_models.py`: request/plan/result dataclasses and enums
- `_targets.py`: AI target registry and path mapping
- `_paths.py`: project root, scope roots, canonical/read path resolution
- `_http.py`: HTTPS fetch wrapper with retry/backoff policy
- `_github.py`: default-branch commit SHA resolution
- `_manifest.py`: manifest fetch/cache/validation and skill lookup
- `_archive.py`: tarball fetch, checksum verify, safe extraction by subdirectory
- `_hashing.py`: deterministic directory hash logic
- `_planner.py`: per-target planning and conflict evaluation
- `_installer.py`: write/update/install-mode operations and link/copy behavior
- `_lockfile.py`: read/write/migrate lockfiles atomically
- `_service.py`: orchestrated library entrypoint for install operation
- `__init__.py`: public API exports

### CLI adapter

- Add install command parsing and dispatch in `src/aidriven/cli/_install_cmd.py`.
- CLI layer maps flags to `InstallRequest`, delegates to `_service.py`, and formats text/JSON output and exit code.

### Existing modules reused

- `src/aidriven/discovery/` reused only as secondary signal during auto-detect flow.

## Install/Data Flow

1. Parse CLI args and validate artifact type/name/flag interactions.
2. Resolve scope roots (`project` by `.git` walk-up else `cwd`, `user` by home).
3. Resolve targets:
   - use explicit `--ai` list if present
   - otherwise auto-detect; error for 0 or >1 targets
4. Resolve current source commit SHA from GitHub API.
5. Fetch manifest at pinned SHA (using cache policy) and resolve requested skill entry.
6. Fetch tarball at same SHA (cache-aware unless forced).
7. Compute content hash of extracted skill files and verify against manifest `contentHash` (FR-024).
8. Extract only requested skill subdirectory with traversal-safe extraction checks.
9. Compute expected skill content hash.
10. Build install plan per target:
    - install_new / skip_identical / update / conflict / incompatible
11. If dry-run, emit plan and exit.
12. Apply installs per target:
    - symlink mode: write canonical once, then create links where required
    - copy mode: write direct target copies
    - on link/junction creation failure (any platform, any reason): fall back to copy for that target with warning; other targets proceed unaffected
13. Write lockfile state atomically for scope.
14. Emit per-target summary and overall exit code.

## Lockfile/Cache Model

### Lockfile

- **Project**: `<project-root>/aidriven-lock.json` (deterministic, VCS-friendly, no timestamps)
- **User**: `~/.cache/aidriven/install-records.json` on Linux/macOS; `%LOCALAPPDATA%\aidriven\install-records.json` on Windows (co-located with cache root, resolved by same `_paths.py` helper)
- Key fields: `version`, `skills.<name>.{source,sourceCommitSha,computedHash,targets,scope,installMode}`

### Cache

- Manifest cache: keyed by SHA and optional HEAD-resolution TTL metadata (default 1h)
- Tarball cache: keyed by commit SHA
- Cache location: OS-specific user cache directory
- `--force` bypasses network caches and triggers re-fetch

## Testing Plan

### Unit tests

- Name/type validation and CLI argument normalization.
- Target path mapping for each (`claude`,`copilot`) x (`project`,`user`) x (`symlink`,`copy`).
- Retry behavior classification (transient vs fail-fast).
- Manifest schema parsing and lookup errors.
- Tar extraction safety (reject traversal and link entries).
- Deterministic content hashing and idempotency checks.
- Planner decisions (install_new/update/skip/conflict/incompatible).
- Lockfile serialization determinism and migration guards.

### Integration tests

- End-to-end single target install (`claude`, `copilot`) for project scope.
- Multi-target install in one run with mixed outcomes and non-zero aggregate exit.
- User scope install path and user lockfile behavior.
- Re-run idempotency, force refresh behavior, and integrity-check failure path.
- Windows-specific link failure fallback simulation.

### CLI contract tests

- Human output and JSON envelope correctness.
- `--dry-run`, `--quiet`, `--verbose`, non-interactive behavior, and exit codes.

## Phased Implementation Plan

### Phase A: Core domain and contracts

- Implement `_models.py`, `_targets.py`, `_paths.py`, and lock/manifest schema validators.
- Add strict type coverage and baseline unit tests.

### Phase B: Remote resolution and fetch integrity

- Implement `_http.py`, `_github.py`, `_manifest.py`, `_archive.py`, `_hashing.py`.
- Add retry, checksum, and extraction safety tests.

### Phase C: Planner and installer engine

- Implement `_planner.py`, `_installer.py`, `_lockfile.py`, `_service.py`.
- Validate idempotency, conflict handling, fallback behavior.

### Phase D: CLI integration and UX

- Add `install` command parser/handler, human and JSON formatters, exit mapping.
- Add CLI tests for required stories and edge cases.

### Phase E: Hardening and rollout

- Cross-platform validation (especially Windows link semantics).
- Documentation updates and quickstart verification.
- Release with skills-only support and extension seam documented.

## Risks and Trade-offs

- **GitHub API rate limiting**: one SHA resolution call per run is simple and deterministic, but could hit limits in heavy CI.
- **Symlink/junction behavior on Windows**: fallback-to-copy improves reliability but can produce mixed modes across targets.
- **Unversioned skills model**: operationally simple and ecosystem-aligned, but explicit version pin UX is deferred.
- **No concurrency lock in v1**: keeps implementation lean; rare simultaneous installs may race.
- **Single trusted source**: strengthens safety and consistency, but does not satisfy multi-source use cases yet.

## Project Structure

### Documentation (this feature)

```text
specs/002-cli-artifact-install/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── reference-analysis.md
├── contracts/
│   ├── cli.md
│   ├── lockfile.schema.json
│   └── manifest.schema.json
└── tasks.md                # generated later by /speckit.tasks
```

### Source Code (repository root)

```text
src/
└── aidriven/
    ├── __init__.py
    ├── discovery/
    ├── install/            # new package for remote artifact install flow
    │   ├── __init__.py
    │   ├── _models.py
    │   ├── _targets.py
    │   ├── _paths.py
    │   ├── _http.py
    │   ├── _github.py
    │   ├── _manifest.py
    │   ├── _archive.py
    │   ├── _hashing.py
    │   ├── _planner.py
    │   ├── _installer.py
    │   ├── _lockfile.py
    │   └── _service.py
    └── cli/                # new CLI adapter package
        ├── __init__.py
        ├── _main.py
        └── _install_cmd.py

tests/
├── unit/
│   ├── discovery/
│   └── install/
├── integration/
│   ├── discovery/
│   └── install/
└── cli/
    └── install/
```

**Structure Decision**: Single-project Python package with library-first core and thin CLI adapter. Existing discovery package remains intact and is only consulted as fallback signal during target autodetection.

## Complexity Tracking

No constitution violations identified. No complexity exemptions required.
