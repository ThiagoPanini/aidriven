# Quickstart: IDE Discovery Service

**Feature**: IDE Discovery Service
**Date**: 2026-04-05

## Overview

The IDE Discovery Service is an internal library module within `aidriven` that detects locally installed AI-oriented IDEs (VS Code, Cursor, Kiro) across macOS, Linux, and Windows. It returns structured detection results with confidence levels and diagnostic information.

## Architecture at a Glance

```text
aidriven.discovery.discover_ides()
        │
        ▼
   Orchestrator
   ┌────┴────┐
   │ Registry │──▶ [VSCodeProvider, CursorProvider, KiroProvider]
   └─────────┘
        │
        ▼ (for each provider)
   provider.detect()
   ┌─────────────────────────────────┐
   │ 1. Check binary/app paths       │
   │ 2. Check config directories     │
   │ 3. Check CLI on PATH            │
   │ 4. Attempt version detection    │
   │ 5. Calculate confidence level   │
   │ 6. Return DetectedIDE entries   │
   └─────────────────────────────────┘
        │
        ▼
   DiscoveryResult
   ├── detected_ides: [DetectedIDE, ...]
   └── diagnostics:   [ProviderDiagnostic, ...]
```

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Provider interface | `typing.Protocol` | Structural subtyping; no forced inheritance; mypy-strict compatible |
| Path handling | `pathlib.Path` everywhere | Constitution G12; cross-platform |
| Binary lookup | `shutil.which()` | Stdlib; cross-platform PATH resolution |
| Confidence model | `enum` with pure function | Spec defines exactly 3 levels; pure function is testable and deterministic |
| Failure isolation | Per-provider try/except | Simplest approach; no concurrency needed for 3 providers |
| Version detection | File-first, CLI-fallback | Faster; handles broken installations gracefully |
| Channel field | `str` (not enum) | Extensible without code changes when new channels appear |
| Dependencies | Zero runtime deps | Stdlib only; constitution principle VII |

## Module Map

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `discovery/__init__.py` | Public API surface | `discover_ides()` |
| `discovery/_models.py` | Data models + confidence logic | `DetectedIDE`, `DiscoveryResult`, `ConfidenceLevel`, `ProviderDiagnostic`, `calculate_confidence()` |
| `discovery/_providers.py` | Provider protocol + registry | `IDEProvider`, `ProviderRegistry` |
| `discovery/_orchestrator.py` | Runs providers, isolates failures | `run_discovery()` |
| `discovery/_platform.py` | Platform detection + path utils | `current_platform()`, `resolve_home()`, `resolve_env_path()` |
| `discovery/providers/_vscode.py` | VS Code + Insiders detection | `VSCodeProvider` |
| `discovery/providers/_cursor.py` | Cursor detection | `CursorProvider` |
| `discovery/providers/_kiro.py` | Kiro detection | `KiroProvider` |

## Implementation Phases

1. **Foundation** — Data models, confidence logic, platform utilities
2. **Core Infrastructure** — Provider protocol, registry, orchestrator
3. **Providers** — VS Code, Cursor, Kiro implementations
4. **Integration** — Public API, end-to-end testing, documentation

## Traceability

Each implementation task traces back to the spec:

- FR-001–FR-003 → Provider implementations (VS Code, Cursor, Kiro)
- FR-004–FR-006 → `DetectedIDE` data model
- FR-007 → `ConfidenceLevel` + `calculate_confidence()`
- FR-008 → VS Code provider (Stable + Insiders as separate entries)
- FR-009 → `IDEProvider` Protocol + `ProviderRegistry`
- FR-010 → Orchestrator failure isolation
- FR-011 → Module separation (detection/normalization/assessment layers)
- FR-012 → `viable_ides` property on `DiscoveryResult`
- FR-013 → No CLI module; library-only
- FR-014 → No installation, no network I/O, no telemetry
