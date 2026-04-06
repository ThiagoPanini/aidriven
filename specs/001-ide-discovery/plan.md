# Implementation Plan: IDE Discovery Service

**Branch**: `v0.1.0/spec-001-ide-discovery` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ide-discovery/spec.md`

## Summary

Implement an internal library service that discovers locally installed AI-oriented IDEs (VS Code, Cursor, Kiro) across macOS, Linux, and Windows. The service uses a provider-based strategy pattern where each IDE has a dedicated provider that performs platform-specific detection (binary lookup, configuration directory inspection, CLI availability). A central orchestrator runs all registered providers, isolates failures, and returns a normalized `DiscoveryResult` containing `DetectedIDE` entries with confidence levels based on detection evidence completeness. The design follows the constitution's Library-First principle—no CLI surface, no installation logic, no network I/O—and uses an extensible provider registry to support future IDEs without modifying existing code.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: None (stdlib only — `pathlib`, `shutil`, `platform`, `subprocess`, `dataclasses`, `enum`, `logging`, `abc`)
**Storage**: N/A (read-only filesystem inspection)
**Testing**: pytest 8.0+ with pytest-cov, mypy strict, ruff
**Target Platform**: macOS, Linux, Windows (cross-platform)
**Project Type**: Library (internal module within `aidriven` package)
**Performance Goals**: Full discovery scan < 2 seconds on standard developer machine (SC-002)
**Constraints**: Zero runtime dependencies; read-only filesystem access; no network I/O; no privilege escalation
**Scale/Scope**: 3 initial IDE providers (VS Code, Cursor, Kiro) × 3 platforms; extensible to N providers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| G1 | Library independence | ✅ PASS | All discovery logic resides in `src/aidriven/discovery/`; no CLI imports. Unit tests import library directly. |
| G2 | CLI thin-layer | ✅ PASS (N/A) | This feature has no CLI surface per FR-013. |
| G3 | TTY safety | ✅ PASS (N/A) | No terminal output; library uses `logging` module only. |
| G4 | Non-interactive mode | ✅ PASS (N/A) | No interactive prompts; pure library function. |
| G5 | JSON output | ✅ PASS (N/A) | No CLI command; data models are serializable via dataclass fields. |
| G6 | Dry-run fidelity | ✅ PASS (N/A) | Service is read-only; no write operations to dry-run. |
| G7 | Exit codes | ✅ PASS (N/A) | No CLI command. |
| G8 | Overwrite protection | ✅ PASS (N/A) | No write operations. |
| G9 | Path traversal prevention | ✅ PASS (N/A) | No artifact installation. |
| G10 | No implicit code execution | ✅ PASS | Service only reads filesystem and invokes `--version` on known binaries. No eval/exec/import of external content. |
| G12 | Cross-platform paths | ✅ PASS | All path operations use `pathlib.Path`. No raw string concatenation. |
| G13 | mypy strict | ✅ PASS | All code must pass `mypy --strict`. Enforced by CI and pre-commit. |
| G14 | ruff clean | ✅ PASS | All code must pass `ruff check` and `ruff format --check`. |
| G15 | Test coverage floor | ✅ PASS | Coverage tracked; all new modules have corresponding tests. |
| G18 | No telemetry without consent | ✅ PASS | No network calls of any kind. |
| G19 | Phase boundary enforcement | ✅ PASS | Discovery service is purely read-only; belongs entirely to the Discover phase. |
| G20 | Constitution compliance | ✅ PASS | This plan documents all applicable gates. |

**Principle Alignment**:
- **I. Library-First**: ✅ All logic under `src/aidriven/discovery/`; callable from Python without CLI.
- **VI. Compatibility and Portability**: ✅ `pathlib.Path` for all paths; UTF-8 encoding; cross-platform tested.
- **VII. Engineering Quality**: ✅ mypy strict, ruff, unit + integration tests, docstrings on public APIs.
- **VIII. Observability and Diagnostics**: ✅ Python `logging` module for diagnostic output; structured diagnostics in `DiscoveryResult`.
- **IX. Perceived Performance**: ✅ No heavy initialization; lazy imports not needed (stdlib only).
- **Extensibility Rules**: ✅ New providers added via registry; no modification to orchestrator or existing providers.

## Project Structure

### Documentation (this feature)

```text
specs/001-ide-discovery/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/aidriven/
├── __init__.py
└── discovery/
    ├── __init__.py              # Public API: discover_ides()
    ├── _models.py               # DetectedIDE, DiscoveryResult, ConfidenceLevel, etc.
    ├── _providers.py            # IDEProvider protocol + ProviderRegistry
    ├── _orchestrator.py         # Discovery orchestration logic
    ├── _platform.py             # Platform detection + path resolution utilities
    └── providers/
        ├── __init__.py          # Auto-registration of built-in providers
        ├── _vscode.py           # VS Code + Insiders provider
        ├── _cursor.py           # Cursor provider
        └── _kiro.py             # Kiro provider

tests/
├── unit/
│   └── discovery/
│       ├── __init__.py
│       ├── test_models.py       # Data model validation, confidence logic
│       ├── test_providers.py    # Provider protocol + registry tests
│       ├── test_orchestrator.py # Orchestration, failure isolation
│       ├── test_platform.py     # Platform utilities
│       └── providers/
│           ├── __init__.py
│           ├── test_vscode.py   # VS Code provider unit tests
│           ├── test_cursor.py   # Cursor provider unit tests
│           └── test_kiro.py     # Kiro provider unit tests
└── integration/
    └── discovery/
        ├── __init__.py
        └── test_discovery.py    # End-to-end discovery on real/mocked filesystem
```

**Structure Decision**: Single-project layout (Option 1 from template). The `discovery/` module is a sub-package of `aidriven`, following the library-first pattern. Internal modules use `_` prefix convention to signal private implementation details. The public API is re-exported from `discovery/__init__.py`. Test directory mirrors the source structure with `unit/` and `integration/` separation per constitution (Principle VII).

## Complexity Tracking

> No constitution violations. No complexity tracking needed.
