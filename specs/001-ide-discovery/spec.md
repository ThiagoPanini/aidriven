# Feature Specification: IDE Discovery Service

**Feature Branch**: `v0.1.0/spec-001-ide-discovery`
**Created**: 2026-04-05
**Status**: Draft
**Input**: User description: "Internal feature for a CLI library that discovers locally installed AI-oriented IDEs/platforms, in order to support future installation of artifacts such as skills, agents, and specs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover All Installed IDEs (Priority: P1)

As a CLI command that needs to install artifacts, I call the discovery service to get a list of all supported AI-oriented IDEs installed on the user's machine. The service scans for VS Code, Cursor, and Kiro using platform-specific detection strategies and returns a standardized list of detected environments with their metadata.

**Why this priority**: This is the core capability of the feature. Without reliable detection across all three operating systems, no downstream artifact installation can proceed.

**Independent Test**: Can be fully tested by invoking the discovery service on a machine with one or more supported IDEs installed and verifying the returned list contains accurate entries with correct identifiers, paths, and display names.

**Acceptance Scenarios**:

1. **Given** a machine with VS Code installed, **When** the discovery service is invoked, **Then** it returns an entry with identifier `vscode`, the correct installation path, and a display name of "Visual Studio Code".
2. **Given** a machine with Cursor and Kiro installed, **When** the discovery service is invoked, **Then** it returns two entries, one for each IDE, each with correct metadata.
3. **Given** a machine with no supported IDEs installed, **When** the discovery service is invoked, **Then** it returns an empty list with no errors.

---

### User Story 2 - Handle Multiple Installations and Variants (Priority: P2)

As a CLI command, I call the discovery service on a machine where a user has multiple installations of the same IDE (e.g., VS Code Stable and VS Code Insiders, or a system-level and user-level installation). The service returns a separate entry for each distinct installation, each annotated with its channel or variant when applicable.

**Why this priority**: Power users and developers frequently run multiple IDE variants or channels side by side. The service must not silently drop or merge these installations.

**Independent Test**: Can be fully tested by invoking the service on a machine with both VS Code Stable and VS Code Insiders installed and verifying two distinct entries are returned with appropriate channel labels.

**Acceptance Scenarios**:

1. **Given** a machine with VS Code Stable and VS Code Insiders both installed, **When** the discovery service is invoked, **Then** it returns two separate entries with channels `stable` and `insiders` respectively.
2. **Given** a machine with a single Cursor installation, **When** the discovery service is invoked, **Then** it returns one Cursor entry with no channel annotation (or a default channel value).

---

### User Story 3 - Graceful Handling of Incomplete or Corrupt Installations (Priority: P3)

As a CLI command, I call the discovery service on a machine where an IDE installation exists but is incomplete, damaged, or missing version metadata. The service still returns the entry with whatever metadata is available, marks the version as unknown, and assigns a lower confidence level so downstream consumers can decide whether to proceed.

**Why this priority**: Real-world environments are messy. Users uninstall partially, move folders, or have stale configuration directories. The service must not crash or silently skip entries that could still be usable.

**Independent Test**: Can be fully tested by creating a scenario where an IDE's expected configuration directory exists but the version file is missing, and verifying the service returns an entry with version marked as unknown and a reduced confidence level.

**Acceptance Scenarios**:

1. **Given** a machine where the VS Code configuration directory exists but the version metadata file is missing, **When** the discovery service is invoked, **Then** it returns an entry for VS Code with version set to unknown and confidence level set to `low`.
2. **Given** a machine where a Cursor binary exists at the expected path but the configuration directory is absent, **When** the discovery service is invoked, **Then** it returns an entry for Cursor with a reduced confidence level and notes the missing configuration.
3. **Given** a machine where an IDE directory exists but contains no recognizable binary or executable, **When** the discovery service is invoked, **Then** it does not include that directory as a detected IDE.

---

### User Story 4 - Extensible Provider Registration (Priority: P3)

As a developer extending aidriven to support a new IDE (e.g., Windsurf, Zed), I register a new detection provider following the established strategy pattern. The discovery service picks up the new provider and includes its results alongside the built-in providers without modifying existing detection logic.

**Why this priority**: The initial set of three IDEs will grow over time. The service must support adding new providers with minimal coupling to existing code.

**Independent Test**: Can be fully tested by implementing a stub provider for a fictitious IDE and verifying the discovery service includes its results when invoked.

**Acceptance Scenarios**:

1. **Given** a new provider registered for IDE "TestIDE", **When** the discovery service is invoked, **Then** the results include entries from the TestIDE provider alongside VS Code, Cursor, and Kiro results.
2. **Given** a new provider that raises an error during detection, **When** the discovery service is invoked, **Then** the remaining providers still return their results and the error is reported without aborting the scan.

---

### Edge Cases

- What happens when the user's home directory is on a non-standard path or a network drive? The service should use platform-standard methods to resolve the home directory rather than hardcoding paths.
- What happens when a detected installation path contains spaces, unicode characters, or symbolic links? The service must handle all valid filesystem paths without errors.
- What happens when the service is run with restricted filesystem permissions and cannot read certain expected paths? The service should skip inaccessible paths gracefully and reduce the confidence level of any partial matches.
- What happens when two different IDEs share the same underlying platform (e.g., Cursor is a VS Code fork)? Each must be detected and reported as a distinct IDE with its own identifier, even if they share similar directory structures.
- What happens when the operating system cannot be determined? The service should raise a clear error indicating that the platform is unsupported.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The service MUST detect VS Code installations on macOS, Linux, and Windows by checking platform-specific default installation paths, configuration directories, and command-line tool availability.
- **FR-002**: The service MUST detect Cursor installations on macOS, Linux, and Windows by checking platform-specific default installation paths and configuration directories.
- **FR-003**: The service MUST detect Kiro installations on macOS, Linux, and Windows by checking platform-specific default installation paths and configuration directories.
- **FR-004**: For each detected IDE, the service MUST return at minimum: an IDE identifier (machine-readable string), a display name (human-readable), and an installation path.
- **FR-005**: For each detected IDE, the service SHOULD return version information when available; when version data cannot be determined, the service MUST return a sentinel value indicating "unknown".
- **FR-006**: For each detected IDE, the service MUST return a channel or variant label when multiple channels exist (e.g., VS Code Stable vs. Insiders); when only one channel is present, the service MUST return a default channel value.
- **FR-007**: For each detected IDE, the service MUST assign a confidence level (`high`, `medium`, or `low`) based on the completeness and consistency of the detection evidence (e.g., binary found + config directory found + version resolved = `high`; only config directory found = `low`).
- **FR-008**: The service MUST detect and return separate entries when multiple installations or variants of the same IDE are found on the same machine.
- **FR-009**: The service MUST provide an extensible mechanism for registering new IDE detection providers without modifying existing provider implementations.
- **FR-010**: The service MUST isolate detection failures in one provider from affecting other providers; if a provider raises an error, the remaining providers MUST still complete their detection.
- **FR-011**: The service MUST separate detection logic (finding installations), metadata normalization (standardizing the output format), and compatibility assessment (deciding if an installation meets minimum requirements for artifact installation) into distinct layers.
- **FR-012**: The service MUST define a minimum data threshold for an installation to be considered viable for artifact installation: at minimum, a valid IDE identifier and a verified installation path.
- **FR-013**: The service MUST operate as an internal library callable by other modules in the codebase; it MUST NOT expose a standalone CLI command or user-facing interface.
- **FR-014**: The service MUST NOT perform any artifact installation, IDE configuration changes, network requests, telemetry collection, or authentication.

### IDE Detection Strategies

**VS Code**:
- **macOS**: Check for application bundle at `/Applications/Visual Studio Code.app` and `/Applications/Visual Studio Code - Insiders.app`; check for CLI tool `code` / `code-insiders` on PATH; check for configuration directory at `~/Library/Application Support/Code/` and `~/Library/Application Support/Code - Insiders/`.
- **Linux**: Check for binary `code` / `code-insiders` on PATH; check for installation in `/usr/share/code/`, `/usr/lib/code/`, `/snap/code/`, or `~/.local/share/code/`; check for configuration directory at `~/.config/Code/` and `~/.config/Code - Insiders/`.
- **Windows**: Check for installation in `%LOCALAPPDATA%\Programs\Microsoft VS Code\` and `%LOCALAPPDATA%\Programs\Microsoft VS Code Insiders\`; check for CLI tool `code` / `code-insiders` on PATH; check for configuration directory at `%APPDATA%\Code\` and `%APPDATA%\Code - Insiders\`.

**Cursor**:
- **macOS**: Check for application bundle at `/Applications/Cursor.app`; check for CLI tool `cursor` on PATH; check for configuration directory at `~/Library/Application Support/Cursor/`.
- **Linux**: Check for binary `cursor` on PATH; check for installation in common locations (`/usr/share/cursor/`, `/opt/cursor/`, `~/.local/share/cursor/`); check for configuration directory at `~/.config/Cursor/`.
- **Windows**: Check for installation in `%LOCALAPPDATA%\Programs\Cursor\`; check for CLI tool `cursor` on PATH; check for configuration directory at `%APPDATA%\Cursor\`.

**Kiro**:
- **macOS**: Check for application bundle at `/Applications/Kiro.app`; check for CLI tool `kiro` on PATH; check for configuration directory at `~/Library/Application Support/Kiro/`.
- **Linux**: Check for binary `kiro` on PATH; check for installation in common locations; check for configuration directory at `~/.config/Kiro/`.
- **Windows**: Check for installation in `%LOCALAPPDATA%\Programs\Kiro\`; check for CLI tool `kiro` on PATH; check for configuration directory at `%APPDATA%\Kiro\`.

### Confidence Level Assignment

| Evidence Found                                      | Confidence |
| --------------------------------------------------- | ---------- |
| Binary/app exists + config directory + version data | `high`     |
| Binary/app exists + config directory, no version    | `medium`   |
| Only config directory found (no binary)             | `low`      |
| Only binary on PATH (no config directory)           | `medium`   |
| No binary, no config directory                      | Not listed |

### Key Entities

- **DetectedIDE**: Represents a single detected IDE installation. Attributes: IDE identifier, display name, installation path, version (or unknown), channel/variant, confidence level, platform where detected.
- **IDEProvider**: Represents a detection strategy for a specific IDE. Responsible for scanning the current platform and returning zero or more DetectedIDE entries.
- **DiscoveryResult**: The aggregate output of the discovery service. Contains a list of DetectedIDE entries and optional diagnostic information (e.g., providers that failed, paths that were inaccessible).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The discovery service correctly identifies 100% of supported IDEs that are installed via standard installation methods on all three operating systems.
- **SC-002**: The discovery service completes a full scan in under 2 seconds on a standard developer machine.
- **SC-003**: When a supported IDE is installed in a non-standard location and is not on PATH, the service does not report a false positive; it omits the entry or reports it with `low` confidence only if partial evidence (e.g., config directory) is found.
- **SC-004**: Adding a new IDE provider requires implementing only the provider itself; no changes to the discovery orchestration logic or existing providers are needed.
- **SC-005**: A provider failure (e.g., permission error, unexpected directory structure) does not prevent other providers from returning results; the service always returns partial results rather than failing entirely.
- **SC-006**: Every DetectedIDE entry returned includes at minimum an IDE identifier and a verified installation path, ensuring downstream artifact installation has sufficient data to proceed.

## Assumptions

- Users install IDEs via standard installation methods provided by each IDE vendor (official installers, package managers, snap packages, etc.). Manually extracted or portable installations in arbitrary locations may not be detected.
- The discovery service runs with the same filesystem permissions as the invoking CLI process; it does not escalate privileges.
- Kiro's directory structure and installation conventions follow patterns similar to VS Code and Cursor (Electron-based IDE with a configuration directory and optional CLI tool). If Kiro's actual layout differs significantly at implementation time, the Kiro provider strategy may need to be revised.
- The service does not need to detect IDEs installed inside containers, virtual machines, or remote environments.
- Version detection relies on reading metadata files or invoking CLI tools with version flags; if an IDE changes its versioning mechanism, the corresponding provider will need updating.
- The three confidence levels (`high`, `medium`, `low`) are sufficient for initial use; the granularity can be refined in future iterations if needed.
