# Data Model: IDE Discovery Service

**Feature**: IDE Discovery Service
**Date**: 2026-04-05
**Spec**: [spec.md](spec.md)

## Entities

### ConfidenceLevel

**Module**: `src/aidriven/discovery/_models.py`
**Type**: `enum.Enum`

Represents the completeness and reliability of a detection result.

| Value | Meaning | Evidence Required |
|-------|---------|-------------------|
| `HIGH` | Full detection evidence | Binary/app + config directory + version data |
| `MEDIUM` | Partial detection evidence | Binary/app + config directory (no version), OR only binary on PATH |
| `LOW` | Minimal detection evidence | Only config directory found (no binary) |

**Derivation**: Spec section "Confidence Level Assignment" (FR-007).

---

### DetectedIDE

**Module**: `src/aidriven/discovery/_models.py`
**Type**: `dataclasses.dataclass` (frozen)

Represents a single detected IDE installation.

| Field | Type | Required | Description | Spec Ref |
|-------|------|----------|-------------|----------|
| `identifier` | `str` | Yes | Machine-readable IDE identifier (e.g., `"vscode"`, `"cursor"`, `"kiro"`) | FR-004 |
| `display_name` | `str` | Yes | Human-readable name (e.g., `"Visual Studio Code"`) | FR-004 |
| `install_path` | `Path` | Yes | Verified installation path | FR-004, FR-012 |
| `version` | `str \| None` | No | Version string or `None` if unknown | FR-005 |
| `channel` | `str` | Yes | Channel/variant label (e.g., `"stable"`, `"insiders"`) | FR-006 |
| `confidence` | `ConfidenceLevel` | Yes | Detection confidence level | FR-007 |
| `detected_platform` | `str` | Yes | Platform where detected (`"darwin"`, `"linux"`, `"windows"`) | Spec entity |

**Invariants**:
- `identifier` is non-empty
- `install_path` is an absolute path that exists on the filesystem at detection time
- `channel` defaults to `"stable"` when only one channel exists (FR-006)
- `frozen=True` for immutability — detection results should not be mutated after creation

**Minimum Viability Threshold** (FR-012): A `DetectedIDE` is viable for downstream artifact installation if and only if both `identifier` is non-empty AND `install_path` points to a verified path.

---

### ProviderDiagnostic

**Module**: `src/aidriven/discovery/_models.py`
**Type**: `dataclasses.dataclass` (frozen)

Captures diagnostic information from a provider that encountered an issue during detection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider_name` | `str` | Yes | Name of the provider that produced this diagnostic |
| `error_type` | `str` | Yes | Exception type name (e.g., `"PermissionError"`) |
| `message` | `str` | Yes | Human-readable description of the issue |
| `paths_checked` | `list[Path]` | No | Paths the provider attempted to check (for debugging) |

---

### DiscoveryResult

**Module**: `src/aidriven/discovery/_models.py`
**Type**: `dataclasses.dataclass` (frozen)

The aggregate output of the discovery service.

| Field | Type | Required | Description | Spec Ref |
|-------|------|----------|-------------|----------|
| `detected_ides` | `list[DetectedIDE]` | Yes | All detected IDE installations (may be empty) | Spec entity |
| `diagnostics` | `list[ProviderDiagnostic]` | Yes | Diagnostic entries from providers that failed or had issues | FR-010 |

**Properties / Computed**:
- `is_empty` → `bool`: Returns `True` if no IDEs were detected
- `by_identifier(identifier: str)` → `list[DetectedIDE]`: Filter results by IDE identifier
- `viable_ides` → `list[DetectedIDE]`: Filter to only IDEs meeting minimum viability threshold (FR-012)

---

### IDEProvider

**Module**: `src/aidriven/discovery/_providers.py`
**Type**: `typing.Protocol`

Defines the contract for an IDE detection provider.

| Method | Signature | Description | Spec Ref |
|--------|-----------|-------------|----------|
| `name` | `@property → str` | Provider display name for diagnostics | — |
| `detect` | `() → list[DetectedIDE]` | Scan the current platform and return zero or more detected installations | FR-001–FR-003 |

**Contract**:
- `detect()` MUST return an empty list (not raise) if no installations are found
- `detect()` MAY raise any `Exception` if an unrecoverable error occurs; the orchestrator will catch it (FR-010)
- `detect()` MUST only inspect the filesystem and optionally invoke known CLI tools — no network I/O, no side effects (FR-014)
- Providers MUST NOT import from other providers — each is independent

---

### ProviderRegistry

**Module**: `src/aidriven/discovery/_providers.py`
**Type**: `class`

Manages the collection of registered IDE detection providers.

| Method | Signature | Description | Spec Ref |
|--------|-----------|-------------|----------|
| `register` | `(provider: IDEProvider) → None` | Add a provider to the registry | FR-009 |
| `providers` | `@property → list[IDEProvider]` | Return all registered providers (insertion order) | — |

**Invariants**:
- Thread-safe is not required (discovery is single-threaded)
- Duplicate providers (same `name`) are rejected with `ValueError`
- The registry does not instantiate providers — it stores pre-constructed instances

---

## Entity Relationships

```text
ProviderRegistry 1──* IDEProvider
       │
       ▼ (used by)
  Orchestrator
       │
       ▼ (produces)
  DiscoveryResult
       ├── 0..* DetectedIDE
       └── 0..* ProviderDiagnostic
```

## State Transitions

No state transitions. All entities are immutable (frozen dataclasses). The discovery flow is a single-pass pipeline:

```text
Registry → Orchestrator → [Provider.detect() for each] → DiscoveryResult
```

## Confidence Calculation Function

**Module**: `src/aidriven/discovery/_models.py`
**Signature**: `calculate_confidence(binary_found: bool, config_dir_found: bool, version_resolved: bool) → ConfidenceLevel`

| binary_found | config_dir_found | version_resolved | Result |
|:---:|:---:|:---:|:---:|
| ✓ | ✓ | ✓ | `HIGH` |
| ✓ | ✓ | ✗ | `MEDIUM` |
| ✓ | ✗ | — | `MEDIUM` |
| ✗ | ✓ | — | `LOW` |
| ✗ | ✗ | — | Not detected (no entry returned) |

This is a pure function with no side effects, derived directly from the spec's confidence table.
