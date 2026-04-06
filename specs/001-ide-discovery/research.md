# Research: IDE Discovery Service

**Feature**: IDE Discovery Service
**Date**: 2026-04-05
**Status**: Complete

## Research Tasks

### RT-01: Provider Pattern for IDE Detection

**Question**: What pattern should be used for extensible IDE detection providers?

**Decision**: Use a `Protocol` class (`IDEProvider`) with a `ProviderRegistry` that stores providers in a list. Providers register via a decorator or explicit `register()` call.

**Rationale**: Python's `Protocol` (PEP 544) enables structural subtyping, which avoids requiring providers to inherit from a base class. This is idiomatic for Python 3.11+, works cleanly with `mypy --strict`, and allows future providers to be registered without modifying the orchestrator. The registry is a simple list—no framework, no plugin loader, no metaclass magic.

**Alternatives Considered**:
- `abc.ABC` with abstract methods: Rejected because it forces inheritance. Protocol is more Pythonic for a callable interface.
- Entry points (`importlib.metadata`): Rejected as over-engineering for internal-only providers. Entry points are suited for cross-package plugin discovery, not intra-package registration.
- Enum-based dispatch: Rejected because adding a new IDE would require modifying the enum and a switch statement, violating open-closed principle (FR-009, SC-004).

---

### RT-02: Cross-Platform Path Resolution

**Question**: How should platform-specific paths (home directory, app directories, PATH lookup) be resolved?

**Decision**: Use `pathlib.Path.home()` for home directory, `pathlib.Path` for all path construction, `shutil.which()` for CLI binary lookup on PATH, and `platform.system()` to determine the current OS. Windows-specific environment variables (`%LOCALAPPDATA%`, `%APPDATA%`) will be resolved via `os.environ.get()` with `Path` wrapping.

**Rationale**: All of these are stdlib and cross-platform. `pathlib.Path` is mandated by the constitution (G12). `shutil.which()` handles PATH resolution correctly on all three platforms including Windows `.exe` extension handling. No third-party dependency like `platformdirs` is needed because this feature only reads known, fixed paths—it doesn't need XDG-compliant cache/config directories.

**Alternatives Considered**:
- `platformdirs` library: Rejected. It solves the problem of "where should my app store its config" but we need "where does VS Code store its config"—those are fixed, known paths per the spec.
- `os.path.expanduser("~")`: Rejected in favor of `pathlib.Path.home()` per constitution G12.
- `subprocess.run(["which", "code"])`: Rejected in favor of `shutil.which("code")` which is cross-platform and doesn't spawn a subprocess.

---

### RT-03: Confidence Level Calculation

**Question**: How should confidence levels be assigned based on detection evidence?

**Decision**: Define a `ConfidenceLevel` enum (`HIGH`, `MEDIUM`, `LOW`) and implement confidence calculation as a pure function that takes boolean flags for evidence types (binary_found, config_dir_found, version_resolved) and returns the appropriate level per the spec's confidence table.

**Rationale**: The spec defines an explicit mapping table (FR-007). A pure function is testable, deterministic, and avoids spreading confidence logic across providers. Each provider returns raw evidence; the confidence function evaluates it uniformly.

**Alternatives Considered**:
- Per-provider confidence calculation: Rejected because it would lead to inconsistent confidence semantics across providers and duplicate logic.
- Numeric scores (0.0–1.0): Rejected because the spec explicitly defines three named levels. Numeric scores add false precision and require threshold decisions.

---

### RT-04: Failure Isolation Strategy

**Question**: How should the orchestrator isolate provider failures (FR-010, SC-005)?

**Decision**: The orchestrator iterates over registered providers, calls each inside a `try/except Exception` block, and captures any exception as a `ProviderError` diagnostic entry in the `DiscoveryResult`. Remaining providers continue regardless.

**Rationale**: This is the simplest approach that satisfies FR-010. No concurrency is needed (3 providers × filesystem checks will complete well under 2 seconds). A per-provider try/except with diagnostic capture provides both fault tolerance and observability.

**Alternatives Considered**:
- `concurrent.futures.ThreadPoolExecutor`: Rejected as premature optimization. Sequential execution of 3 providers with filesystem checks is fast enough (SC-002: < 2 seconds). Threading adds complexity and potential for race conditions in path resolution.
- Returning `Result[list[DetectedIDE], Exception]` per provider: Considered but adds a result-type dependency or custom implementation. A simple try/except with diagnostic accumulation is sufficient.

---

### RT-05: Version Detection Strategy

**Question**: How should IDE version information be extracted?

**Decision**: Version detection will use two strategies in order of preference:
1. Read version metadata from known files (e.g., `package.json` in the IDE installation directory, or platform-specific version files).
2. If no metadata file is found, attempt `<cli-tool> --version` via `subprocess.run()` with a short timeout (5 seconds).

If neither strategy succeeds, the version field is set to `None` (sentinel for "unknown") per FR-005.

**Rationale**: File-based version detection is faster and doesn't require the IDE to be in a working state. CLI-based detection is a fallback that handles cases where the binary exists but version files are not in expected locations. The 5-second timeout prevents hangs from broken installations.

**Alternatives Considered**:
- CLI-only detection: Rejected because spawning a subprocess is slower and may not work if the binary is broken or hangs.
- File-only detection: Rejected because installation layouts vary; the CLI fallback handles edge cases.
- No version detection: Rejected because FR-005 explicitly requires version information when available.

---

### RT-06: Variant/Channel Detection

**Question**: How should IDE variants (e.g., VS Code Stable vs. Insiders) be handled?

**Decision**: VS Code's provider will check for both Stable and Insiders paths as separate detection targets, returning distinct `DetectedIDE` entries with `channel` set to `"stable"` or `"insiders"`. Cursor and Kiro will use `"stable"` as the default channel value since they currently have a single channel. The `channel` field will be a `str` (not an enum) to allow future variants without code changes.

**Rationale**: The spec explicitly requires separate entries for variants (FR-006, FR-008, User Story 2). Using `str` for channel avoids needing to modify an enum when a new IDE adds channels (e.g., if Cursor adds a beta channel).

**Alternatives Considered**:
- Enum for channels: Rejected because it couples the data model to specific IDEs' channel names, violating extensibility goals.
- Omitting channel for single-channel IDEs: Rejected because FR-006 requires a default channel value.

---

### RT-07: Testing Strategy for Cross-Platform Code

**Question**: How should cross-platform detection logic be tested when CI may only run on one OS?

**Decision**: Unit tests will mock filesystem and platform at the boundary:
- `unittest.mock.patch` on `pathlib.Path.exists()`, `pathlib.Path.is_dir()`, `shutil.which()`, `platform.system()`, and `subprocess.run()`.
- Each provider's unit tests will parametrize across all three platforms by patching `platform.system()` return value.
- Integration tests will run on the actual platform and verify real detection (these naturally pass only for IDEs actually installed).

**Rationale**: Mocking at the stdlib boundary gives full control over simulated environments while keeping tests fast and deterministic. The integration test layer provides confidence on real installations. This follows the constitution's testing requirements (Principle VII: unit tests fast, isolated, deterministic; integration tests for filesystem interactions).

**Alternatives Considered**:
- `pyfakefs` (fake filesystem): Rejected as an unnecessary new dependency. Simple mocks on `Path.exists()` and `Path.is_dir()` are sufficient for the paths being checked.
- Docker-based multi-OS testing: Rejected for unit tests (too slow). Real multi-OS CI (GitHub Actions matrix) can run integration tests.
- `tmp_path` fixture with created directories: Viable for integration tests but providers check fixed system paths, not arbitrary paths. Mocking is more appropriate for unit tests.

---

### RT-08: Module Naming and Privacy Convention

**Question**: What naming convention should be used for internal modules?

**Decision**: Internal implementation modules use `_` prefix (`_models.py`, `_providers.py`, `_orchestrator.py`, `_platform.py`). Public API is re-exported from `discovery/__init__.py`. Provider implementations use `_` prefix (`_vscode.py`, `_cursor.py`, `_kiro.py`).

**Rationale**: The `_` prefix is Python's standard convention for "internal" modules. It signals to consumers that they should use the public `discovery` API, not import from `_models` directly. This aligns with the constitution's library-first principle—clean public API surface.

**Alternatives Considered**:
- No prefix (all public): Rejected because it blurs the public API boundary.
- `internal/` sub-package: Rejected as over-nesting for a small module.
