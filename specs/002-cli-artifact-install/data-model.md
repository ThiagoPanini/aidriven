# Phase 1 Data Model: CLI Artifact Install

**Date**: 2026-04-07
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

All entities below are Python dataclasses (frozen where they represent immutable values) defined in `src/aidriven/install/_models.py`. They are part of the library's public surface unless prefixed with `_`.

---

## Enums

### `Scope`
```python
class Scope(str, Enum):
    PROJECT = "project"
    USER = "user"
```
- **PROJECT**: base directory is the resolved project root (walk up from cwd to find `.git`; fall back to cwd) — FR-005a.
- **USER**: base directory is the user home directory.

### `InstallMode`
```python
class InstallMode(str, Enum):
    SYMLINK = "symlink"
    COPY = "copy"
```

### `ArtifactType`
```python
class ArtifactType(str, Enum):
    SKILL = "skill"
```
v1 supports `SKILL` only. New variants are added here when new types ship.

### `PerTargetAction`
```python
class PerTargetAction(str, Enum):
    INSTALL_NEW    = "install_new"     # nothing at read path
    UPDATE         = "update"          # aidriven-installed; content changed
    SKIP_IDENTICAL = "skip_identical"  # already up-to-date (FR-030)
    CONFLICT       = "conflict"        # foreign or modified content (FR-031); requires --force
    INCOMPATIBLE   = "incompatible"    # manifest declares this target unsupported
```

---

## Value Objects

### `AITarget`  *(frozen)*
| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Identifier — `"claude"` or `"copilot"` |
| `project_read_path` | `str` | Relative path under project root (e.g. `.claude/skills`) |
| `user_read_path` | `str` | Relative path under user home (e.g. `.claude/skills`) |
| `autodetect_markers` | `tuple[str, ...]` | Filesystem markers that indicate this target is present |

The `aidriven.install._targets.TARGETS` dict is the single registry. Adding a target = one dict entry (FR-011, SC-007).

### `ManifestEntry`  *(frozen)*
| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Skill name; matches `^[a-z][a-z0-9-]{0,63}$` |
| `type` | `ArtifactType` | `SKILL` in v1 |
| `path_in_repo` | `str` | Relative path within the `aidriven-resources` repo (e.g. `skills/code-reviewer`) |
| `archive_sha256` | `str` | SHA-256 of the *full repository tarball* at the resolved commit (FR-024) |
| `compatible_targets` | `frozenset[str]` | AI targets the skill officially supports (FR-021) |
| `description` | `str` | Human-readable summary |

### `Manifest`  *(frozen)*
| Field | Type | Notes |
|-------|------|-------|
| `schema_version` | `int` | Currently `1`; FR-022 |
| `source_commit_sha` | `str` | The commit SHA the manifest was fetched at; mirrors what the lockfile records |
| `entries` | `Mapping[tuple[ArtifactType, str], ManifestEntry]` | Keyed by `(type, name)` |

### `ProjectContext`  *(frozen)*
| Field | Type | Notes |
|-------|------|-------|
| `cwd` | `Path` | Original working directory |
| `project_root` | `Path` | Resolved per FR-005a; equal to `cwd` if no `.git` ancestor |
| `user_home` | `Path` | `Path.home()` |
| `cache_dir` | `Path` | Resolved cache root |

---

## Request / Plan / Result

### `InstallRequest`
The library entrypoint takes one of these. Built by the CLI from parsed flags, but constructible directly from Python.

| Field | Type | Notes |
|-------|------|-------|
| `artifact_type` | `ArtifactType` | |
| `name` | `str` | Locally validated against the regex *before* construction |
| `targets` | `tuple[str, ...]` | Empty tuple → triggers auto-detection (FR-013) |
| `scope` | `Scope` | Default `PROJECT` |
| `mode` | `InstallMode` | Default `SYMLINK` |
| `force` | `bool` | FR-007 |
| `dry_run` | `bool` | Constitution G6 |
| `assume_yes` | `bool` | Non-interactive confirmation bypass (G4) |

**Validation rules**:
- `name` must match `^[a-z][a-z0-9-]{0,63}$` (FR-003).
- `targets`: each entry must exist in `TARGETS` (FR-018 still allows targets that aren't autodetectable, but they must be *known*).
- `force` and `mode=COPY` are independent — both may be set together.

### `PlannedTarget`
One per (target, scope) computed by the planner.

| Field | Type | Notes |
|-------|------|-------|
| `target` | `AITarget` | |
| `canonical_path` | `Path` | `<base>/.agents/skills/<name>` (symlink mode only; `None` in copy mode) |
| `read_path` | `Path` | Where the AI tool will read from |
| `needs_symlink` | `bool` | False if read_path == canonical_path |
| `action` | `PerTargetAction` | What the installer will do |
| `existing_hash` | `str \| None` | Content hash currently on disk, if any |
| `reason` | `str \| None` | Human-readable explanation when action is CONFLICT or INCOMPATIBLE |

### `InstallPlan`
The full preview — pure data, no side effects (G19).

| Field | Type | Notes |
|-------|------|-------|
| `request` | `InstallRequest` | |
| `manifest_entry` | `ManifestEntry` | |
| `source_commit_sha` | `str` | Resolved at the start of the run (FR-022b) |
| `expected_content_hash` | `str` | Computed from the cached/extracted skill files (`computedHash`) |
| `targets` | `tuple[PlannedTarget, ...]` | One per target × scope |
| `overall_status` | `Literal["ready", "blocked", "noop"]` | `blocked` if any target needs `--force` and it's not set |

### `PerTargetResult`
| Field | Type | Notes |
|-------|------|-------|
| `target_name` | `str` | |
| `action_taken` | `PerTargetAction` | What actually happened (may differ from planned if symlink fell back to copy) |
| `final_mode` | `InstallMode` | Reflects per-target fallback |
| `read_path` | `Path` | |
| `canonical_path` | `Path \| None` | |
| `error` | `str \| None` | Set when this target failed; other targets still proceed (FR-031, FR-036) |

### `InstallResult`
| Field | Type | Notes |
|-------|------|-------|
| `request` | `InstallRequest` | |
| `plan` | `InstallPlan` | |
| `target_results` | `tuple[PerTargetResult, ...]` | |
| `lockfile_path` | `Path` | Updated lockfile location |
| `success` | `bool` | True iff every target ended with `INSTALL_NEW`, `UPDATE`, or `SKIP_IDENTICAL` |
| `exit_code` | `int` | 0 on success; non-zero per CLI contract |

---

## Persistence: Lockfile Entry

### `LockfileEntry`
Maps 1-to-1 to one skill key inside `aidriven-lock.json`.

| Field | Type | JSON key | Notes |
|-------|------|----------|-------|
| `source` | `str` | `source` | `"aidriven-resources"` in v1 |
| `source_commit_sha` | `str` | `sourceCommitSha` | The commit the files were fetched from |
| `computed_hash` | `str` | `computedHash` | `"sha256:" + hex` of sorted-file-contents hash |
| `targets` | `tuple[str, ...]` | `targets` | Sorted alphabetically for determinism (SC-009) |
| `scope` | `Scope` | `scope` | |
| `install_mode` | `InstallMode` | `installMode` | Reflects what was actually applied |

### `Lockfile`
| Field | Type | JSON key | Notes |
|-------|------|----------|-------|
| `version` | `int` | `version` | `1` |
| `skills` | `dict[str, LockfileEntry]` | `skills` | Keyed by skill name; serialized with sorted keys, no timestamps for project lockfile |

The user-scope lockfile MAY add a `lastInstalledAt` ISO-8601 string per entry; the project lockfile MUST NOT.

---

## State Transitions

### Per-target action decision (computed in `_planner.py`)

```
            ┌─ read_path missing ──────────────────► INSTALL_NEW
            │
            ├─ read_path exists, hash == expected ─► SKIP_IDENTICAL
            │
read_path ──┤
            ├─ read_path exists, hash != expected
            │   ├─ lockfile says aidriven installed it ─► UPDATE
            │   └─ no lockfile entry OR hash mismatch ──► CONFLICT  (needs --force)
            │
            └─ target not in manifest's compatible_targets ─► INCOMPATIBLE  (warn + ask)
```

### Lockfile lifecycle
- Created lazily on first successful install for a given scope.
- Read at the start of every install to drive the planner.
- Rewritten atomically (`tempfile` in same dir → `os.replace`) after every successful install, with sorted keys and no whitespace variation.
- Schema-version mismatch → migrate or warn; **never silently discard** entries.

---

## Cross-references to spec

| Entity / Field | Spec source |
|---|---|
| `Scope.PROJECT` resolution | FR-005a, Clarification Q (scope resolution) |
| `Manifest`, `ManifestEntry` | FR-019, FR-020, FR-021, FR-022, FR-022a |
| `source_commit_sha` resolution | FR-022b |
| `archive_sha256` integrity check | FR-024 |
| `InstallMode` and path tables | FR-008, FR-008a, FR-008b, FR-009 |
| Idempotency hash | FR-030 |
| Foreign-file conflict | FR-031 |
| Lockfile fields & determinism | FR-032, SC-009 |
| Per-target success/failure | FR-033, FR-036 |
| Name regex | FR-003 |
| Retry policy | FR-025a |
