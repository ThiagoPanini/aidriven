# Tasks: CLI Remote Artifact Install

**Feature**: `spec-002-cli-artifact-install`
**Branch**: `v0.2.0/spec-002-cli-artifact-install`
**Input**: Design documents from `/specs/002-cli-artifact-install/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Included — the feature specification marks "User Scenarios & Testing" as mandatory, and `plan.md` contains a detailed Testing Plan section.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1–US5) — required for all user story phase tasks
- Exact file paths included in every description

---

## Phase 1: Setup

**Purpose**: Create package skeletons for the new `install` and `cli` modules.

- [ ] T001 Create `src/aidriven/install/` package with empty `__init__.py`; verify `src/aidriven/cli/` package exists and create with empty `__init__.py` if absent
- [ ] T002 [P] Create test directory tree `tests/unit/install/`, `tests/integration/install/`, `tests/cli/install/` each with an `__init__.py` file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement all shared, business-logic-free infrastructure modules that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Implement all enums (`Scope`, `InstallMode`, `ArtifactType`, `PerTargetAction`) and dataclasses (`AITarget`, `ManifestEntry`, `Manifest`, `ProjectContext`, `InstallRequest`, `PlannedTarget`, `InstallPlan`, `PerTargetResult`, `InstallResult`, `LockfileEntry`, `Lockfile`) as frozen where appropriate in `src/aidriven/install/_models.py`
- [ ] T004 [P] Implement `TARGETS` dict with frozen `AITarget` entries for `claude` (`project_read_path=".claude/skills"`, `user_read_path=".claude/skills"`, `autodetect_markers=(".claude/",)`) and `copilot` (`project_read_path=".agents/skills"`, `user_read_path=".copilot/skills"`, `autodetect_markers=(".github/copilot-instructions.md",)`) in `src/aidriven/install/_targets.py`
- [ ] T005 [P] Implement `.git` walk-up project-root resolver (fallback to `cwd`), canonical-dir helper (`.agents/skills/<name>/`), scope-based base-path resolver, and OS-specific user-cache-dir helper (`~/.cache/aidriven` on Linux/macOS; `%LOCALAPPDATA%\aidriven\Cache` on Windows) in `src/aidriven/install/_paths.py`
- [ ] T006 [P] Implement deterministic SHA-256 content hash: iterate sorted relative file paths, feed `path_bytes + b"\x00" + file_bytes + b"\x00"` into a single SHA-256 digest, return `"sha256:" + hexdigest` in `src/aidriven/install/_hashing.py`
- [ ] T007 [P] Implement HTTPS-only fetch wrapper: assert `https://` URL scheme, `ssl.create_default_context()`, 3-retry exponential backoff (1 s / 2 s / 4 s) on network errors, HTTP 5xx, and HTTP 429; fail-fast on all other 4xx responses in `src/aidriven/install/_http.py`
- [ ] T008 [P] Implement GitHub default-branch HEAD SHA resolution via `GET https://api.github.com/repos/<owner>/aidriven-resources/commits/<branch>`; cache resolved SHA for 1 h at `~/.cache/aidriven/manifest/_head.json`; `--force` bypasses cache in `src/aidriven/install/_github.py`
- [ ] T009 [P] Implement manifest fetch at pinned SHA via `https://raw.githubusercontent.com/<owner>/aidriven-resources/<sha>/manifest.json`; SHA-keyed cache at `~/.cache/aidriven/manifest/<sha>.json`; validate `schema_version == 1`; inject `source_commit_sha` into `Manifest`; `--force` bypasses cache in `src/aidriven/install/_manifest.py`
- [ ] T010 [P] Implement tarball fetch at `https://github.com/<owner>/aidriven-resources/archive/<sha>.tar.gz` with SHA-keyed cache at `~/.cache/aidriven/cache/<sha>.tar.gz`; traversal-safe extraction (reject `../`, absolute paths, symlink/hardlink members; `filter='data'` on Python 3.12+); post-extraction content-hash verification against `ManifestEntry.content_hash`; `--force` bypasses cache in `src/aidriven/install/_archive.py`
- [ ] T011 [P] Implement atomic lockfile read (`Lockfile` ← JSON file), atomic write (`tempfile.NamedTemporaryFile` in same dir + `os.replace`), schema-version migration guard (warn/migrate, never silently discard entries), and deterministic JSON serialization (sorted keys, no timestamps for project lockfile) in `src/aidriven/install/_lockfile.py`

**Checkpoint**: All infrastructure modules implemented — user story phases can now proceed.

---

## Phase 3: User Story 1 — Single-Target Skill Install at Project Scope (Priority: P1) 🎯 MVP

**Goal**: `aidriven install skill <name> --ai claude` (or `--ai copilot`) fetches the skill from `aidriven-resources`, places files at `.agents/skills/<name>/` (canonical), creates a directory symlink at `.claude/skills/<name>/` for Claude (no symlink needed for Copilot at project scope), writes `aidriven-lock.json`, and is fully idempotent.

**Independent Test**: Run `aidriven install skill code-reviewer --ai claude` in any git repository. Verify `.agents/skills/code-reviewer/SKILL.md` exists, `.claude/skills/code-reviewer` is a directory symlink pointing to the canonical dir, and `aidriven-lock.json` contains a `code-reviewer` entry with correct `source`, `sourceCommitSha`, `computedHash`, `targets`, `scope`, `installMode` fields. Re-run the same command and verify exit 0 with "already up to date" and no file changes.

### Tests for User Story 1

> **Write these tests FIRST — they MUST FAIL before the T016–T021 implementation below.**

- [ ] T012 [P] [US1] Write unit tests for artifact-name regex validation (`^[a-z][a-z0-9-]{0,63}$`): valid names pass, names with uppercase/spaces/leading-digit/length>64 are rejected before any network call in `tests/unit/install/test_validation.py`
- [ ] T013 [P] [US1] Write unit tests for the full path table: assert canonical dir and read path for each combination of (`claude`, `copilot`) × (`project`, `user`) × (`symlink`, `copy`) using `_paths.py` helpers and `TARGETS` registry in `tests/unit/install/test_paths.py`
- [ ] T014 [P] [US1] Write unit tests for all five planner decisions: `INSTALL_NEW` (read path absent), `SKIP_IDENTICAL` (hash matches expected), `UPDATE` (aidriven-installed, hash differs), `CONFLICT` (no lockfile entry or locally modified, `--force` absent), `INCOMPATIBLE` (target not in `ManifestEntry.compatible_targets`) in `tests/unit/install/test_planner.py`
- [ ] T015 [P] [US1] Write unit tests for lockfile determinism: same skills in different insertion order produce identical JSON; project lockfile contains no timestamp fields; schema-version mismatch triggers migration guard, not silent data loss in `tests/unit/install/test_lockfile.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement per-target action planner (all five `PerTargetAction` decisions, lockfile-read integration, content-hash idempotency comparison) and `InstallPlan` construction in `src/aidriven/install/_planner.py`
- [ ] T017 [US1] Implement canonical-dir population, POSIX directory symlink (`os.symlink(..., target_is_directory=True)`), Windows directory-junction creation, copy-mode direct install, and per-target symlink failure catch-and-fallback to copy with warning in `src/aidriven/install/_installer.py`
- [ ] T018 [US1] Implement orchestrated single-explicit-target install flow: resolve SHA → fetch manifest → validate name → fetch/extract archive → build `InstallPlan` → execute `_installer` → write lockfile atomically; support `--dry-run` (plan only, no writes) in `src/aidriven/install/_service.py`
- [ ] T019 [US1] Export public library API (`install_artifact`, `InstallRequest`, `ArtifactType`, `Scope`, `InstallMode`, `InstallResult`) in `src/aidriven/install/__init__.py`
- [ ] T020 [US1] Implement `install` subcommand: argparse parser with all flags (`--ai`, `--scope`, `--copy`, `--force`, `--dry-run`, `--json`, `--quiet`, `--verbose`, `--yes`, `--no-cache`); mutual-exclusion check (`--quiet`/`--verbose` → exit 2); `InstallRequest` construction; human output (TTY + `NO_COLOR`-gated ANSI color and `✓ ✗ •` glyphs); JSON envelope output matching `contracts/cli.md` schema in `src/aidriven/cli/_install_cmd.py`
- [ ] T021 [US1] Register `install` subcommand in CLI entry point and ensure `aidriven install --help` shows both the single-target and multi-target usage examples in `src/aidriven/cli/_main.py`

### Integration and CLI contract tests for User Story 1

- [ ] T022 [US1] Write integration test: install `code-reviewer --ai claude` (verify canonical dir populated, symlink correct); install `code-reviewer --ai copilot` (verify canonical dir populated, no symlink created); re-run each and verify idempotency (exit 0, no file changes) in `tests/integration/install/test_single_target.py`
- [ ] T023 [US1] Write CLI contract tests: assert each of the six exit codes (0–6) on the correct trigger; assert `--json` output is a single valid JSON object matching the schema in `contracts/cli.md`; assert `--dry-run` leaves the filesystem and `aidriven-lock.json` unchanged in `tests/cli/install/test_cli_exit_codes.py`

**Checkpoint**: US1 fully functional — `aidriven install skill <name> --ai claude|copilot` works end-to-end.

---

## Phase 4: User Story 2 — Multi-Target Install (Priority: P2)

**Goal**: `aidriven install skill <name> --ai claude --ai copilot` installs once at the canonical dir, creates per-target links as needed, reports per-target results, isolates per-target failures (one failure does not abort others), and handles `INCOMPATIBLE` targets with a warning and `--yes` bypass.

**Independent Test**: Run with `--ai claude --ai copilot`; verify one canonical dir, one symlink for claude, no symlink for copilot at project scope, and lockfile `targets` is `["claude", "copilot"]` (sorted). Then simulate a permission error on one target and verify the other target still succeeds with a non-zero aggregate exit code.

### Tests for User Story 2

- [ ] T024 [P] [US2] Write unit tests for HTTP retry classifier: network errors, HTTP 5xx, and HTTP 429 are transient (retry up to 3×); HTTP 404 and other 4xx fail fast without retry; verify backoff delay values in `tests/unit/install/test_http.py`

### Implementation for User Story 2

- [ ] T025 [US2] Extend `_service.py` for multi-target orchestration: iterate targets, run `_planner` + `_installer` per target with isolated `try/except`, collect all `PerTargetResult` objects, compute aggregate `success` and `exit_code` in `src/aidriven/install/_service.py`
- [ ] T026 [US2] Add `INCOMPATIBLE` target handling in `_service.py`: emit warning for each incompatible target, prompt user to confirm or skip when TTY and `--yes` not set, skip automatically in non-TTY or with `--yes` in `src/aidriven/install/_service.py`
- [ ] T027 [US2] Implement Windows junction creation in `_installer.py`: wrap `os.symlink` in `try/except OSError`; on failure emit a warning and fall back to copy mode for that target only; other targets in the same run are not affected in `src/aidriven/install/_installer.py`
- [ ] T028 [US2] Extend `_install_cmd.py` output formatter: emit one `✓`/`✗` line per target; set exit code non-zero when any target failed; include per-target `error` fields in the `--json` envelope in `src/aidriven/cli/_install_cmd.py`

### Integration tests for User Story 2

- [ ] T029 [US2] Write integration test: `--ai claude --ai copilot` produces one canonical dir, one Claude symlink, no Copilot symlink at project scope; lockfile `targets` sorted alphabetically; `installMode` correct in `tests/integration/install/test_multi_target.py`
- [ ] T030 [US2] Write integration test: simulate permission error on one target (mock `os.symlink`); verify other target succeeds, exit code non-zero, per-target error message present in JSON output in `tests/integration/install/test_multi_target.py`

**Checkpoint**: US1 and US2 both fully functional independently.

---

## Phase 5: User Story 3 — User-Scope Install (Priority: P3)

**Goal**: `aidriven install skill <name> --ai claude --scope user` installs to `~/.agents/skills/<name>/` (canonical) with a symlink at `~/.claude/skills/<name>/` and records in the OS-specific user lockfile; the project `aidriven-lock.json` is NOT written.

**Independent Test**: Run `--scope user --ai claude`; verify install paths are under `Path.home()`, not the project dir; user lockfile is created/updated at `~/.cache/aidriven/install-records.json` (Linux/macOS) or `%LOCALAPPDATA%\aidriven\install-records.json` (Windows); project lockfile is untouched.

### Tests for User Story 3

- [ ] T031 [P] [US3] Write unit tests for user-scope path derivation: assert `cache_dir` and user-lockfile path match `~/.cache/aidriven/` on Linux/macOS and `%LOCALAPPDATA%\aidriven\` on Windows using `monkeypatch` on `platform.system()` and env vars in `tests/unit/install/test_paths.py`

### Implementation for User Story 3

- [ ] T032 [US3] Extend `_paths.py` to derive the OS-specific user lockfile path co-located at the cache root (not inside `cache/` subdirectory) via the same `cache_dir` helper in `src/aidriven/install/_paths.py`
- [ ] T033 [US3] Extend `_service.py` to route lockfile writes to the user lockfile when `scope=USER`, resolve user-scope base paths (`Path.home() / ".agents/skills/<name>"`) for canonical and read-path computation in `src/aidriven/install/_service.py`
- [ ] T034 [US3] Expose `--scope project|user` CLI flag with `project` as default in `src/aidriven/cli/_install_cmd.py`

### Integration tests for User Story 3

- [ ] T035 [US3] Write integration test: `--scope user --ai claude` installs canonical at `~/.agents/skills/code-reviewer/`, symlink at `~/.claude/skills/code-reviewer/`; `--scope user --ai copilot` installs canonical at `~/.agents/skills/code-reviewer/`, symlink at `~/.copilot/skills/code-reviewer/`; user lockfile written, project lockfile absent in `tests/integration/install/test_user_scope.py`

**Checkpoint**: US1, US2, and US3 all fully functional independently.

---

## Phase 6: User Story 4 — Force Re-fetch (Priority: P4)

**Goal**: `aidriven install skill <name> --ai claude --force` bypasses all caches, re-fetches from `aidriven-resources`, overwrites foreign/modified content, reports "updated" if content changed or "already up to date" if content is identical after re-fetch, and validates integrity (exit 4 on checksum mismatch).

**Independent Test**: Install a skill; run with `--force`; verify tarball re-downloaded (cache bypassed). Tamper the cached tarball and set a mismatched `contentHash` in the manifest; verify exit code 4 and no install occurs. Install a skill, manually modify a file (conflict), run with `--force`; verify overwrite proceeds.

### Implementation for User Story 4

- [ ] T036 [US4] Thread `force=True` from `_service.py` into `_github.py` (bypass `_head.json` TTL cache), `_manifest.py` (bypass SHA-keyed manifest cache), and `_archive.py` (bypass tarball cache); also bypass conflict guards in `_planner.py` when `force=True` in `src/aidriven/install/`
- [ ] T037 [US4] Implement `--no-cache` flag as fetch-cache bypass only (distinct from `--force`): bypass `_github.py` HEAD cache, `_manifest.py` manifest cache, and `_archive.py` tarball cache without enabling overwrite of foreign/modified content in `src/aidriven/install/_service.py` and `src/aidriven/cli/_install_cmd.py`

### Integration tests for User Story 4

- [ ] T038 [US4] Write integration tests: `--force` with changed remote content (→ `UPDATE`, "updated"); `--force` with identical remote content (→ `SKIP_IDENTICAL` after re-fetch); simulated integrity failure (mock `contentHash` mismatch → exit code 4, no filesystem changes) in `tests/integration/install/test_force_refetch.py`

**Checkpoint**: US1–US4 all fully functional independently.

---

## Phase 7: User Story 5 — Auto-Detect AI Targets (Priority: P5)

**Goal**: `aidriven install skill <name>` (no `--ai`) auto-detects AI targets from filesystem markers; if exactly one is found, proceeds and notifies the user; if zero or multiple are found, exits with code 6 and actionable guidance.

**Independent Test**: In a project with `.claude/` but no Copilot marker, run without `--ai`; verify `claude` is selected and install proceeds with a "auto-detected: claude" notice. Add `.github/copilot-instructions.md` and re-run; verify exit code 6 listing both detected targets. In a project with no markers, verify exit code 6 listing supported targets.

### Tests for User Story 5

- [ ] T039 [P] [US5] Write unit tests for auto-detection: single marker present → returns the matching target; multiple markers present → raises `AmbiguousTargetsError`; no markers present → raises `NoTargetsFoundError` in `tests/unit/install/test_autodetect.py`

### Implementation for User Story 5

- [ ] T040 [US5] Implement auto-detection in `_service.py`: inspect each `AITarget.autodetect_markers` relative to the resolved project root; optionally use `aidriven.discovery` IDE result as a secondary hint; dispatch: exactly 1 found → use it and emit notice; >1 found → exit 6 (list detected targets, instruct to use `--ai`); 0 found → exit 6 (list supported targets, instruct to use `--ai`) in `src/aidriven/install/_service.py`

### Integration tests for User Story 5

- [ ] T041 [US5] Write integration tests: project with one marker (exact target selected, install proceeds); project with two markers (exit code 6, both targets listed); project with no markers (exit code 6, supported targets listed) in `tests/integration/install/test_autodetect.py`

**Checkpoint**: All five user stories (US1–US5) fully functional independently.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Harden security-sensitive paths and complete remaining unit tests for shared infrastructure modules.

- [X] T042 [P] Write unit tests for tarball extraction safety: reject members with `../` in path, absolute paths, symlink members, hardlink members; assert all extracted paths resolve within `extract_root`; verify `filter='data'` is applied on Python 3.12+ in `tests/unit/install/test_archive.py`
- [X] T043 [P] Write unit tests for deterministic content hash: same file set in different iteration order produces identical digest; two skills with swapped filenames produce different digests; empty directory produces a stable value in `tests/unit/install/test_hashing.py`
- [X] T044 [P] Write unit tests for manifest parsing: valid v1 manifest parses correctly; missing required fields raise `ValueError`; unknown `schema_version` raises a version error; skill not in manifest raises `ArtifactNotFoundError`; `compatible_targets` populates `ManifestEntry.compatible_targets` correctly in `tests/unit/install/test_manifest.py`
- [X] T045 [P] Write CLI contract tests: ANSI color and glyphs suppressed when `NO_COLOR` is set or stdout is non-TTY; `--quiet` suppresses all non-error output; `--verbose` enables DEBUG-level messages; `--json` always suppresses spinners and color regardless of TTY in `tests/cli/install/test_cli_output.py`
- [X] T046 Run the complete `quickstart.md` acceptance checklist end-to-end and confirm all nine success criteria (SC-001 through SC-009) are met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user stories**
- **Phase 3 (US1)**: Depends on Phase 2 — MVP deliverable
- **Phase 4 (US2)**: Depends on Phase 3
- **Phase 5 (US3)**: Depends on Phase 3; independent of Phase 4 — can run in parallel with Phase 4
- **Phase 6 (US4)**: Depends on Phase 2; independent of US2/US3 — can run in parallel with Phases 4–5
- **Phase 7 (US5)**: Depends on Phase 3; independent of US2/US3/US4
- **Phase 8 (Polish)**: Depends on all user story phases completing

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — no story dependencies
- **US2 (P2)**: Starts after US1 — extends multi-target orchestration in `_service.py`
- **US3 (P3)**: Starts after US1 — extends scope routing; independent of US2
- **US4 (P4)**: Starts after Phase 2 — touches infrastructure modules; independent of US2/US3
- **US5 (P5)**: Starts after US1 — adds auto-detect path in `_service.py`; independent of US2/US3/US4

### Within Each User Story

- Unit tests → implementation (TDD: written first, must FAIL before implementation)
- `_planner.py` → `_installer.py` → `_service.py` → `__init__.py` → `_install_cmd.py` → `_main.py` (US1 implementation chain)
- Integration and CLI tests after all implementation in that story is complete

### Parallel Opportunities

- **Phase 2**: T004–T007 in parallel (after T003); then T008–T011 in parallel (after T003–T007)
- **Phase 3 unit tests**: T012, T013, T014, T015 all in parallel
- **Phase 3 integration + CLI**: T022, T023 in parallel (after T021)
- **Phase 4**: T024 in parallel with T025–T030
- **Phase 5**: T031 in parallel with T032–T035
- **Phase 8**: T042, T043, T044, T045 all in parallel

---

## Parallel Execution Examples

### Phase 2 (Foundational)

```
Step 1 (sequential): T003 — _models.py (everything depends on it)
Step 2 (parallel):   T004, T005, T006, T007 — _targets, _paths, _hashing, _http
Step 3 (parallel):   T008, T009, T010, T011 — _github, _manifest, _archive, _lockfile
```

### Phase 3 (US1)

```
Step 1 (parallel):   T012, T013, T014, T015 — write all unit tests first (TDD)
Step 2 (sequential): T016 → T017 → T018 → T019 → T020 → T021 — implement each module
Step 3 (parallel):   T022, T023 — integration + CLI contract tests
```

### Phase 8 (Polish)

```
Parallel:   T042, T043, T044, T045 — all independent test files
Sequential: T046 — end-to-end quickstart acceptance checklist
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T011)
3. Complete Phase 3: US1 (T012–T023)
4. **STOP and VALIDATE**: run `aidriven install skill code-reviewer --ai claude` end-to-end
5. Single-target project-scope install is the MVP deliverable

### Incremental Delivery

1. Phase 1 + Phase 2 → infrastructure ready
2. Phase 3 → **US1 MVP**: single-target install working
3. Phase 4 → **US2**: multi-target install working
4. Phase 5 → **US3**: user-scope install working
5. Phase 6 → **US4**: force re-fetch working
6. Phase 7 → **US5**: auto-detect working
7. Phase 8 → **Polish**: full test coverage and hardening complete

---

## Notes

- No third-party runtime dependencies — stdlib only: `urllib.request`, `urllib.error`, `ssl`, `json`, `tarfile`, `hashlib`, `pathlib`, `shutil`, `os`, `tempfile`, `dataclasses`, `enum`, `logging`, `re`, `argparse`, `platform`, `sys`
- `[P]` tasks = different files with no blocking dependencies between them
- `[US#]` label maps each task to its user story for traceability
- TDD: unit tests must be written BEFORE the module they test, and must FAIL initially
- Atomic lockfile writes: `tempfile.NamedTemporaryFile` in same directory → `os.replace`
- Windows junctions: `os.symlink(..., target_is_directory=True)`; catch `OSError` → fall back to copy for that target only
- Symlink created only AFTER canonical directory is verified as populated (per research §10)
- `--force` bypasses both caches AND conflict guards; `--no-cache` bypasses caches only (distinct)
