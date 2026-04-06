# Tasks: IDE Discovery Service

**Input**: Design documents from `/specs/001-ide-discovery/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/library-api.md

**Tests**: Included — plan.md project structure explicitly defines test directories and files; technical context specifies pytest 8.0+ with pytest-cov, mypy strict, ruff.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — package structure, configuration, and tooling

- [X] T001 Create package directory structure: `src/aidriven/__init__.py`, `src/aidriven/discovery/__init__.py`, `src/aidriven/discovery/providers/__init__.py`, `tests/unit/discovery/__init__.py`, `tests/unit/discovery/providers/__init__.py`, `tests/integration/discovery/__init__.py`
- [X] T002 [P] Configure pytest with pytest-cov in `pyproject.toml` (test paths, coverage settings, mypy strict, ruff rules)
- [X] T003 [P] Add `py.typed` marker file at `src/aidriven/py.typed` for PEP 561 compliance

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, platform utilities, provider protocol, and orchestration — MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `ConfidenceLevel` enum (`HIGH`, `MEDIUM`, `LOW`) and `calculate_confidence(binary_found, config_dir_found, version_resolved) → ConfidenceLevel` pure function in `src/aidriven/discovery/_models.py`
- [X] T005 Implement `DetectedIDE` frozen dataclass with fields: `identifier`, `display_name`, `install_path` (Path), `version` (str | None), `channel` (str), `confidence` (ConfidenceLevel), `detected_platform` (str) in `src/aidriven/discovery/_models.py`
- [X] T006 Implement `ProviderDiagnostic` frozen dataclass with fields: `provider_name`, `error_type`, `message`, `paths_checked` (list[Path]) in `src/aidriven/discovery/_models.py`
- [X] T007 Implement `DiscoveryResult` frozen dataclass with fields: `detected_ides` (list[DetectedIDE]), `diagnostics` (list[ProviderDiagnostic]) and computed properties `is_empty`, `by_identifier(identifier)`, `viable_ides` in `src/aidriven/discovery/_models.py`
- [X] T008 [P] Implement platform utilities in `src/aidriven/discovery/_platform.py`: `current_platform() → str`, `resolve_home() → Path`, `resolve_env_path(var_name) → Path | None` using `pathlib.Path`, `platform.system()`, `os.environ`
- [X] T009 [P] Implement `IDEProvider` Protocol class (with `name` property and `detect()` method) and `ProviderRegistry` class (with `register()` and `providers` property, duplicate-name rejection) in `src/aidriven/discovery/_providers.py`
- [X] T010 Implement `run_discovery(registry: ProviderRegistry) → DiscoveryResult` orchestration function in `src/aidriven/discovery/_orchestrator.py` with per-provider try/except failure isolation and diagnostic capture (FR-010)
- [X] T011 [P] Write unit tests for data models and `calculate_confidence()` in `tests/unit/discovery/test_models.py` — cover all confidence truth table rows, frozen invariants, `is_empty`, `by_identifier`, `viable_ides`
- [X] T012 [P] Write unit tests for platform utilities in `tests/unit/discovery/test_platform.py` — mock `platform.system()`, `Path.home()`, `os.environ` for all 3 OSes
- [X] T013 [P] Write unit tests for `IDEProvider` Protocol conformance and `ProviderRegistry` (register, duplicate rejection, providers list) in `tests/unit/discovery/test_providers.py`
- [X] T014 Write unit tests for `run_discovery()` orchestrator in `tests/unit/discovery/test_orchestrator.py` — test happy path, provider failure isolation, empty registry, mixed success/failure

**Checkpoint**: Foundation ready — all data models, platform utils, provider protocol, registry, and orchestrator are implemented and tested. User story implementation can now begin.

---

## Phase 3: User Story 1 — Discover All Installed IDEs (Priority: P1) 🎯 MVP

**Goal**: Detect VS Code, Cursor, and Kiro installations on macOS, Linux, and Windows using platform-specific detection strategies. Return standardized `DetectedIDE` entries with correct identifiers, paths, display names, and confidence levels.

**Independent Test**: Invoke `discover_ides()` on a machine with one or more supported IDEs installed and verify the returned list contains accurate entries.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Write unit tests for VS Code stable detection (all 3 platforms) in `tests/unit/discovery/providers/test_vscode.py` — mock `Path.exists()`, `shutil.which()`, `subprocess.run()` for binary, config dir, version detection
- [X] T016 [P] [US1] Write unit tests for Cursor detection (all 3 platforms) in `tests/unit/discovery/providers/test_cursor.py` — mock filesystem and PATH for binary, config dir, version detection
- [X] T017 [P] [US1] Write unit tests for Kiro detection (all 3 platforms) in `tests/unit/discovery/providers/test_kiro.py` — mock filesystem and PATH for binary, config dir, version detection

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement `VSCodeProvider` in `src/aidriven/discovery/providers/_vscode.py` — detect VS Code stable installation on macOS (`/Applications/Visual Studio Code.app`, `~/Library/Application Support/Code/`, `code` on PATH), Linux (`/usr/share/code/`, `~/.config/Code/`, `code` on PATH), Windows (`%LOCALAPPDATA%\Programs\Microsoft VS Code\`, `%APPDATA%\Code\`, `code` on PATH); extract version via `package.json` or `code --version`; assign confidence per truth table
- [X] T019 [P] [US1] Implement `CursorProvider` in `src/aidriven/discovery/providers/_cursor.py` — detect Cursor installation on macOS (`/Applications/Cursor.app`, `~/Library/Application Support/Cursor/`, `cursor` on PATH), Linux (`/usr/share/cursor/`, `/opt/cursor/`, `~/.config/Cursor/`, `cursor` on PATH), Windows (`%LOCALAPPDATA%\Programs\Cursor\`, `%APPDATA%\Cursor\`, `cursor` on PATH); extract version; assign confidence
- [X] T020 [P] [US1] Implement `KiroProvider` in `src/aidriven/discovery/providers/_kiro.py` — detect Kiro installation on macOS (`/Applications/Kiro.app`, `~/Library/Application Support/Kiro/`, `kiro` on PATH), Linux (common locations, `~/.config/Kiro/`, `kiro` on PATH), Windows (`%LOCALAPPDATA%\Programs\Kiro\`, `%APPDATA%\Kiro\`, `kiro` on PATH); extract version; assign confidence
- [X] T021 [US1] Implement auto-registration of built-in providers (VSCodeProvider, CursorProvider, KiroProvider) in `src/aidriven/discovery/providers/__init__.py` — create default `ProviderRegistry` instance with all three providers
- [X] T022 [US1] Implement public API `discover_ides()` function and `__all__` re-exports in `src/aidriven/discovery/__init__.py` per library-api.md contract — accept optional `registry` parameter, delegate to `run_discovery()`
- [X] T023 [US1] Write integration test for end-to-end discovery in `tests/integration/discovery/test_discovery.py` — invoke `discover_ides()` and verify result structure (DiscoveryResult with correct types, no exceptions)

**Checkpoint**: User Story 1 complete — `discover_ides()` returns detected IDEs with correct identifiers, paths, display names, and confidence levels. Core MVP is functional.

---

## Phase 4: User Story 2 — Handle Multiple Installations and Variants (Priority: P2)

**Goal**: Detect and return separate entries when multiple installations or variants of the same IDE exist (e.g., VS Code Stable and VS Code Insiders). Each entry has its own channel label.

**Independent Test**: On a machine with both VS Code Stable and Insiders installed, verify two distinct entries are returned with channels `stable` and `insiders`.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US2] Write unit tests for VS Code Insiders detection alongside Stable in `tests/unit/discovery/providers/test_vscode.py` — test scenarios: only Stable installed, only Insiders installed, both installed (expect 2 entries with distinct channels), neither installed (empty list)

### Implementation for User Story 2

- [X] T025 [US2] Extend `VSCodeProvider` in `src/aidriven/discovery/providers/_vscode.py` to detect VS Code Insiders as a separate entry — check Insiders-specific paths on macOS (`/Applications/Visual Studio Code - Insiders.app`, `~/Library/Application Support/Code - Insiders/`, `code-insiders` on PATH), Linux (`code-insiders` on PATH, `~/.config/Code - Insiders/`), Windows (`%LOCALAPPDATA%\Programs\Microsoft VS Code Insiders\`, `%APPDATA%\Code - Insiders\`, `code-insiders` on PATH); set `channel="insiders"` and `display_name="Visual Studio Code - Insiders"`

**Checkpoint**: User Story 2 complete — VS Code Stable and Insiders are reported as separate `DetectedIDE` entries with distinct channel labels.

---

## Phase 5: User Story 3 — Graceful Handling of Incomplete or Corrupt Installations (Priority: P3)

**Goal**: When an IDE installation is incomplete (missing binary, missing config dir, missing version), still return an entry with reduced confidence and `version=None` rather than crashing or silently skipping.

**Independent Test**: Create a scenario where an IDE's config directory exists but the version file is missing, and verify the service returns an entry with `version=None` and confidence `low` or `medium`.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T026 [P] [US3] Write unit tests for partial detection scenarios in `tests/unit/discovery/providers/test_vscode.py` — test: config dir exists but no binary (expect LOW confidence), binary exists but no config dir (expect MEDIUM), binary + config but no version (expect MEDIUM), binary + config + version (expect HIGH)
- [X] T027 [P] [US3] Write unit tests for partial detection scenarios in `tests/unit/discovery/providers/test_cursor.py` and `tests/unit/discovery/providers/test_kiro.py` — same partial evidence matrix as T026

### Implementation for User Story 3

- [X] T028 [P] [US3] Harden `VSCodeProvider` in `src/aidriven/discovery/providers/_vscode.py` for partial detection — handle `PermissionError` and `OSError` on path checks, `subprocess.TimeoutExpired` on version CLI (5s timeout), gracefully set `version=None` and reduce confidence when evidence is incomplete
- [X] T029 [P] [US3] Harden `CursorProvider` in `src/aidriven/discovery/providers/_cursor.py` for partial detection — same error handling pattern: catch path permission errors, subprocess timeouts, return entries with reduced confidence for partial evidence
- [X] T030 [P] [US3] Harden `KiroProvider` in `src/aidriven/discovery/providers/_kiro.py` for partial detection — same error handling pattern as T028/T029

**Checkpoint**: User Story 3 complete — all providers gracefully handle incomplete installations, returning partial results with appropriate confidence levels instead of crashing.

---

## Phase 6: User Story 4 — Extensible Provider Registration (Priority: P3)

**Goal**: A developer can register a new IDE detection provider via the `ProviderRegistry` and pass it to `discover_ides(registry=...)`. The new provider's results appear alongside built-in results without modifying existing code.

**Independent Test**: Implement a stub provider for a fictitious IDE, register it, invoke `discover_ides()`, and verify results include the stub provider's entries.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T031 [P] [US4] Write unit tests for custom provider registration in `tests/unit/discovery/test_orchestrator.py` — test: register stub provider → results include stub entries; register failing provider → other providers still return results and diagnostic is captured; custom registry passed to `discover_ides()` overrides default

### Implementation for User Story 4

- [X] T032 [US4] Verify and refine custom registry flow in `src/aidriven/discovery/__init__.py` — ensure `discover_ides(registry=custom_registry)` correctly uses only the custom registry's providers; ensure default registry is used when `registry=None`
- [X] T033 [US4] Write integration test with a stub provider in `tests/integration/discovery/test_discovery.py` — create a `TestIDEProvider` that returns a fake `DetectedIDE`, register it, invoke `discover_ides()`, verify it appears in results alongside built-in providers

**Checkpoint**: User Story 4 complete — new providers can be registered and used without modifying any existing code. Extensibility contract (FR-009, SC-004) is verified.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final quality checks, type safety, and validation across all stories

- [X] T034 [P] Run `mypy --strict` on all source files under `src/aidriven/discovery/` and fix any type errors
- [X] T035 [P] Run `ruff check .` and `ruff format --check` on all source and test files; fix any violations
- [X] T036 Run full test suite with coverage: `pytest --cov=src/aidriven/discovery --cov-report=term-missing` — verify all tests pass and review coverage
- [X] T037 Run `quickstart.md` validation — execute the usage patterns from `specs/001-ide-discovery/quickstart.md` and `contracts/library-api.md` to verify public API works as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (extends VSCodeProvider)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (hardens existing providers)
- **User Story 4 (Phase 6)**: Depends on Foundational phase (uses registry + orchestrator); can run in parallel with US2/US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 — extends the VSCodeProvider built in US1
- **User Story 3 (P3)**: Depends on US1 — hardens providers built in US1
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — tests extensibility independent of specific providers; can run in parallel with US2/US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/utilities before services
- Services before public API
- Core implementation before integration tests

### Parallel Opportunities

- T002, T003 can run in parallel (Setup phase)
- T008, T009 can run in parallel (Foundational — different files)
- T011, T012, T013 can run in parallel (Foundational tests — different test files)
- T015, T016, T017 can run in parallel (US1 tests — different test files)
- T018, T019, T020 can run in parallel (US1 providers — different files)
- T026, T027 can run in parallel (US3 tests — different test files)
- T028, T029, T030 can run in parallel (US3 provider hardening — different files)
- T034, T035 can run in parallel (Polish — different tools)
- US4 (Phase 6) can run in parallel with US2 (Phase 4) or US3 (Phase 5)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (write-first, expect failures):
Task T015: "Unit tests for VS Code stable detection in tests/unit/discovery/providers/test_vscode.py"
Task T016: "Unit tests for Cursor detection in tests/unit/discovery/providers/test_cursor.py"
Task T017: "Unit tests for Kiro detection in tests/unit/discovery/providers/test_kiro.py"

# Launch all US1 provider implementations together:
Task T018: "VSCodeProvider in src/aidriven/discovery/providers/_vscode.py"
Task T019: "CursorProvider in src/aidriven/discovery/providers/_cursor.py"
Task T020: "KiroProvider in src/aidriven/discovery/providers/_kiro.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently — `discover_ides()` returns correct results
5. Deploy/demo if ready — core discovery is functional

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP! Core detection works
3. Add User Story 2 → Test independently → VS Code variants detected
4. Add User Story 3 → Test independently → Robust partial detection
5. Add User Story 4 → Test independently → Extensibility verified
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (must complete first — US2/US3 depend on it)
3. Once US1 is done:
   - Developer A: User Story 2
   - Developer B: User Story 3
   - Developer C: User Story 4 (can also start after Foundational, parallel with US1)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All providers use `pathlib.Path` for paths (G12), `shutil.which()` for binary lookup, `platform.system()` for OS detection
- `subprocess.run()` with 5-second timeout for CLI version detection (RT-05)
- No network I/O, no side effects, no privilege escalation (FR-014)
