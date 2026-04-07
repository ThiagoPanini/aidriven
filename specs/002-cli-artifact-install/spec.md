# Feature Specification: CLI Artifact Install

**Feature Branch**: `v0.2.0/spec-002-cli-artifact-install`
**Created**: 2026-04-06
**Status**: Draft
**Input**: User description: "CLI feature to fetch and install AI artifacts from remote aidriven-resources repository"

---

## Summary

`aidriven` users work across multiple AI-assisted development environments (VS Code, Cursor, Kiro, etc.). Each environment expects AI artifacts — skills, rules, templates, agents — in specific locations with specific formats. Today there is no automated way to fetch those artifacts from a trusted source and place them correctly. Developers must manually download, rename, and copy files, with no guarantees of correctness, version consistency, or compatibility with their current IDE.

This feature introduces an `install` CLI command that:
1. Detects the user's IDE environment (using the existing detection layer)
2. Fetches the requested artifact type and name from the remote `aidriven-resources` repository
3. Places it at the correct location in the format expected by the detected IDE
4. Records what was installed (version, source, path) for reproducibility and future upgrades

---

## Goals

- Provide a single CLI command to fetch and install any supported AI artifact into the user's environment
- Leverage the existing IDE detection capability to automatically determine the correct installation path and format
- Support `skills` as the first artifact type, with a design that accommodates future types (rules, templates, agents, etc.)
- Ensure installations are safe: validated, integrity-checked, and from a trusted source (`aidriven-resources`)
- Enable reproducible installs: same command, same version → same result
- Support caching to avoid redundant network requests
- Give users explicit control over version selection and IDE override when needed

## Non-Goals

- Bundling artifacts inside the `aidriven` Python package (artifacts live in `aidriven-resources`)
- Managing or deploying artifacts to remote or shared team environments
- Creating or authoring new artifacts (fetch and install only)
- Bulk-installing entire artifact catalogs without explicit user intent
- Supporting artifact types beyond `skills` in this iteration (though the design must accommodate them)
- Modifying IDE configurations or settings files beyond placing artifact files in the correct directory
- Uninstall, rollback, or upgrade workflows (outside scope of this iteration)
- Authentication or private repository access (only public `aidriven-resources` is in scope)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install a Skill into a Detected IDE (Priority: P1)

A developer using VS Code runs `aidriven install skill <name>`. The tool detects VS Code automatically, fetches the skill from `aidriven-resources`, and places it at the correct path for VS Code. The user gets a confirmation message with the installed location.

**Why this priority**: This is the core value proposition of the entire feature. Without auto-detection install, nothing else matters.

**Independent Test**: Can be fully tested by running `aidriven install skill <name>` in a VS Code environment and verifying the file appears at the IDE-expected path with the correct content.

**Acceptance Scenarios**:

1. **Given** a user has VS Code as the only detected IDE and requests `aidriven install skill code-reviewer`, **When** the command runs, **Then** the skill file is placed at the VS Code-appropriate skill directory with the correct filename and the CLI outputs the installed path.
2. **Given** the requested skill exists at the latest version in `aidriven-resources`, **When** the command completes, **Then** a local install record (name, version, source URL, installed path, timestamp) is written.
3. **Given** the same skill has already been installed at the same version, **When** the command runs again, **Then** the CLI uses the cached artifact without re-fetching from the network and notifies the user.

---

### User Story 2 - Install a Specific Artifact Version (Priority: P2)

A developer wants to pin their project to a specific known-good version of a skill. They run `aidriven install skill <name> --version 1.2.0` to install that exact version.

**Why this priority**: Reproducibility is a core `aidriven` principle — without version pinning, teams cannot guarantee consistent environments.

**Independent Test**: Can be fully tested by running the command with a concrete version flag and verifying the installed artifact matches that version's content, independent of which version is "latest".

**Acceptance Scenarios**:

1. **Given** a user requests a skill at version `1.2.0` and that version exists in `aidriven-resources`, **When** the command runs, **Then** exactly version `1.2.0` is installed, not the latest.
2. **Given** the requested version does not exist in `aidriven-resources`, **When** the command runs, **Then** the CLI reports the error with the requested version and lists available versions.
3. **Given** the artifact has an integrity checksum in the manifest, **When** the file is installed, **Then** the CLI validates the downloaded content against the checksum and aborts if it does not match.

---

### User Story 3 - Override IDE Target Manually (Priority: P3)

A developer has multiple IDEs detected (e.g., VS Code and Cursor) or wants to install for a specific IDE regardless of what is detected. They pass `--ide cursor` to target Cursor explicitly.

**Why this priority**: Multiple-IDE environments and cross-environment setups are real use cases that need to work without confusion or silent errors.

**Independent Test**: Can be fully tested by passing `--ide <name>` in an environment where a different IDE would be auto-detected, and verifying the file is placed at the overridden IDE's path.

**Acceptance Scenarios**:

1. **Given** only VS Code is detected but the user passes `--ide cursor`, **When** the command runs, **Then** the skill is installed at the Cursor-specific location and the CLI confirms the override was applied.
2. **Given** the user passes an unrecognized IDE name via `--ide`, **When** the command runs, **Then** the CLI reports an error listing supported IDE targets.
3. **Given** multiple IDEs are detected and no `--ide` flag is provided, **When** the command runs, **Then** the CLI prompts the user to choose one or exits with a clear message explaining the ambiguity and how to resolve it.

---

### User Story 4 - No IDE Detected (Priority: P4)

A user runs `aidriven install skill <name>` on a machine where no supported IDE is detected.

**Why this priority**: Graceful failure with actionable guidance is critical to trust and adoption.

**Independent Test**: Can be fully tested by simulating no-IDE conditions and verifying the CLI output and exit code.

**Acceptance Scenarios**:

1. **Given** no supported IDE is detected and no `--ide` flag is provided, **When** the command runs, **Then** the CLI exits with a non-zero code and explains which IDEs are supported and how to use `--ide` to force one.
2. **Given** the user passes `--ide vscode` when no IDE was detected, **When** the command runs, **Then** the forced IDE target is honored and the skill is installed at the VS Code path.

---

### Edge Cases

- What happens when the `aidriven-resources` remote is unreachable (no network)?
- What happens when the remote manifest exists but the requested artifact name is absent?
- What happens when the local install target directory does not exist or is not writable?
- What happens when a file already exists at the install path from a different source (not an `aidriven` install)?
- What happens when the manifest references a version but the artifact file at that URL is missing or corrupted?
- What happens when two runs of the same command execute simultaneously?
- What happens when the IDE is detected but its artifact directory does not yet exist on disk?

---

## Requirements *(mandatory)*

### Functional Requirements

**CLI Interface**

- **FR-001**: The system MUST expose an `install` command with the signature: `aidriven install <artifact-type> <artifact-name> [--version <version>] [--ide <ide-name>] [--force]`
- **FR-002**: The `<artifact-type>` argument MUST be validated against a list of supported types; for this iteration `skills` is the only supported type.
- **FR-003**: The `<artifact-name>` argument MUST be validated against the remote manifest before download.
- **FR-004**: The `--version` flag MUST accept a semantic version string (e.g., `1.2.0`); if omitted, the latest published version is used.
- **FR-005**: The `--ide` flag MUST accept a supported IDE identifier (e.g., `vscode`, `cursor`, `kiro`); if omitted, auto-detection is performed.
- **FR-006**: The `--force` flag MUST cause the CLI to re-fetch and overwrite an already-installed artifact, bypassing the cache.

**IDE Detection & Target Resolution**

- **FR-007**: The system MUST invoke the existing IDE detection layer before determining the installation target path.
- **FR-008**: If exactly one IDE is detected, the system MUST use it as the installation target without user interaction.
- **FR-009**: If multiple IDEs are detected and no `--ide` flag is given, the system MUST ask the user to disambiguate and exit with a clear error if running non-interactively.
- **FR-010**: If no IDE is detected and no `--ide` flag is given, the system MUST exit with a non-zero code and guide the user on using `--ide`.
- **FR-011**: Each supported IDE MUST have a defined artifact-type → directory mapping that controls where each artifact type is placed and under what filename/format.

**Remote Manifest & Metadata**

- **FR-012**: The system MUST fetch a remote manifest from `aidriven-resources` that lists available artifact types, names, versions, download URLs, checksums, and IDE compatibility metadata.
- **FR-013**: The manifest MUST be consulted before any download to validate that the requested artifact type, name, and version exist.
- **FR-014**: The manifest MUST declare which IDEs are compatible with each artifact, so the system can warn when installing for an IDE the artifact does not officially support.
- **FR-015**: The manifest schema MUST be versioned so future additions do not break existing CLI versions.

**Download & Integrity**

- **FR-016**: The system MUST download the artifact file from the URL specified in the manifest.
- **FR-017**: The system MUST verify the downloaded file's integrity against a checksum provided in the manifest; if verification fails, the file MUST NOT be installed and an error MUST be reported.
- **FR-018**: Downloads MUST be performed over HTTPS only.

**Caching**

- **FR-019**: The system MUST cache downloaded artifacts locally (keyed by artifact type + name + version) to avoid redundant network requests.
- **FR-020**: The cache MUST be invalidated when `--force` is passed.
- **FR-021**: The system MUST also cache the remote manifest for a configurable TTL (default: 1 hour) to reduce latency on repeated commands.

**Installation**

- **FR-022**: The system MUST place the artifact file at the IDE-specific directory for the given artifact type, creating intermediate directories if they do not exist.
- **FR-023**: If a file already exists at the target path, the system MUST warn the user and abort unless `--force` is passed.
- **FR-024**: After successful installation, the system MUST write a local install record containing: artifact type, name, version, source URL, installed path, IDE target, and timestamp.
- **FR-025**: The system MUST print a concise success summary to stdout including the installed path, version, and IDE target.

**Error Handling**

- **FR-026**: All error cases (network failure, manifest not found, artifact not found, checksum mismatch, permission error) MUST produce human-readable messages with actionable guidance.
- **FR-027**: All error exits MUST use a non-zero exit code.

### Key Entities

- **Artifact**: A named, versioned AI resource (e.g., a skill). Has a type, name, version, download URL, checksum, and IDE compatibility list.
- **Manifest**: A remote index hosted in `aidriven-resources` that describes all available artifacts. Has a schema version and is fetched over HTTPS.
- **IDE Target**: A resolved combination of IDE identifier + artifact-type-specific directory and filename format. Derived from detection or `--ide` override.
- **Install Record**: A local file recording what was installed: artifact coordinates, source URL, resolved IDE target path, timestamp.
- **Cache Entry**: A locally stored artifact file keyed by type + name + version, reused to avoid network requests.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can install a skill into their IDE environment with a single command in under 10 seconds on a standard internet connection.
- **SC-002**: Re-running the same install command uses the local cache and completes without a network request (verified by network monitoring or dry-run output).
- **SC-003**: Installing a skill at a pinned version produces byte-identical results across different machines and operating systems.
- **SC-004**: Every error path produces a non-zero exit code and a human-readable message — zero silent failures.
- **SC-005**: The feature works for all currently detected IDE types (at minimum: VS Code, Cursor, Kiro) without code changes.
- **SC-006**: A new artifact type can be supported by extending the manifest and IDE target mappings without changes to the core install command logic.

---

## Assumptions

- Users have Python 3.11+ and `aidriven` installed and accessible on their PATH.
- Users have outbound HTTPS access to `github.com` (raw content and/or GitHub Releases).
- The `aidriven-resources` repository is public; no authentication is required to fetch manifests or artifacts.
- The existing IDE detection layer returns a stable, consistent result on the same machine.
- "Skills" in each IDE are single files placed in a well-known directory; no IDE-level registration or plugin activation is required beyond file placement.
- The `aidriven-resources` manifest will be designed and published as part of this feature's delivery; its schema is to be defined during planning.
- Concurrent execution of two `aidriven install` commands targeting the same artifact is an unlikely edge case; file-level write failures are sufficient protection for v1.
- Cache storage uses the OS standard user cache directory; no user configuration is required for cache location in this iteration.
- Version strings follow semantic versioning (`MAJOR.MINOR.PATCH`); non-semver version identifiers are out of scope.
