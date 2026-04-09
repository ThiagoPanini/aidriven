# Feature Specification: CLI Artifact Install

**Feature Branch**: `v0.2.0/spec-002-cli-artifact-install`
**Created**: 2026-04-06
**Status**: Draft
**Input**: User description: "CLI feature to fetch and install AI artifacts from remote aidriven-resources repository"

---

## Summary

Developers use multiple AI coding assistants — Claude Code, GitHub Copilot, and others — often side by side. Each AI system expects its artifacts (skills, rules, templates, agents) at different filesystem paths with specific naming and format conventions. Today there is no automated way to fetch those artifacts from a trusted source and place them correctly for the target AI system(s). Developers must manually download, rename, and copy files, with no guarantees of correctness, content integrity, or compatibility with their AI environment.

This feature introduces an `install` CLI command that:
1. Accepts the target AI system(s) explicitly via `--ai` (e.g., `claude`, `copilot`), with optional auto-detection as a fallback
2. Fetches the requested artifact type and name from the remote `aidriven-resources` repository
3. Places files at a canonical shared directory (`.agents/skills/<name>/`) and creates symlinks from each AI target's read path, following the industry-standard model established by `vercel-labs/skills`
4. Records what was installed in a VCS-friendly lockfile (`aidriven-lock.json`) for reproducibility and future updates

The primary installation selector is the **AI target system**, not the IDE. Existing IDE/environment detection may inform defaults or warnings, but the AI target determines where artifacts are placed.

---

## Clarifications

### Session 2026-04-07

- Q: How should `--scope project` resolve the base directory? → A: Walk up to find `.git`, fall back to `cwd` if no `.git` found.
- Q: Is the skill content identical across AI targets, or target-specific? → A: One universal skill directory per skill, placed identically for all AI targets. A skill is a directory of files (SKILL.md plus optional references, scripts, templates, etc.), not a single file.
- Q: How should the CLI handle installing a newer version over an older one? → A: Allow silent upgrade when the new version is newer — print "upgrading X from 1.0.0 to 2.0.0", no `--force` needed. *(Superseded by Q4 — skills are unversioned; upgrade logic replaced by content-hash comparison.)*
- Q: Should skills be versioned with semver, or identified by name and fetched at latest? → A: No versioning. Skills are fetched at latest from `aidriven-resources`. The install record tracks the commit SHA for reproducibility. `--force` re-fetches. This aligns with ecosystem convention (e.g., skills.sh). Version pinning can be added later via git refs if needed.
- Q: What are the validation rules for `<artifact-name>`? → A: `^[a-z][a-z0-9-]{0,63}$` — lowercase letters, digits, and hyphens only; must start with a letter; max 64 chars. Matches `vercel-labs/skills` convention, prevents path-traversal/shell-quoting issues, portable across Windows/macOS/Linux.
- Q: What is the network retry/failure policy for HTTP fetches? → A: Retry transient failures (network errors, HTTP 5xx, HTTP 429) up to 3 times with exponential backoff (1s, 2s, 4s); fail fast on other 4xx responses. Balances resilience with predictable CLI latency.
- Q: When fetching at "latest", which commit SHA does the CLI pin to? → A: Resolve the default branch's current HEAD SHA via the GitHub API once per run, then use that SHA for both the `manifest.json` fetch and the tarball fetch. Guarantees manifest and bundle come from the same commit (no race) and the resolved SHA is recorded in `aidriven-lock.json`.
- Q: Where in `aidriven-resources` should the manifest live, and in what format? → A: `manifest.json` at the repository root. JSON is parseable with the Python stdlib (no extra deps), root placement is the conventional discovery point, and it is fetchable via `https://raw.githubusercontent.com/<owner>/aidriven-resources/<sha>/manifest.json`.
- Q: How should the artifact bundle be fetched from `aidriven-resources`? → A: GitHub repository tarball at a pinned commit SHA (`/archive/<sha>.tar.gz`); extract only the requested skill subdirectory. One HTTP call, one checksum over the archive, no publishing pipeline, and `sourceCommitSha` is already first-class in the lockfile.
- Q: Should the installation model adopt patterns from `vercel-labs/skills` (the industry-standard skills CLI)? → A: Yes. Deep inspection of the `vercel-labs/skills` codebase (v1.4.9) identified the canonical `.agents/skills/` directory + symlink model as the correct architecture. **Adopt**: canonical `.agents/skills/<name>/` directory (read by 40+ agents including Copilot), symlink from target-specific dirs (e.g., `.claude/skills/`), `--copy` as opt-in alternative, VCS-friendly project lockfile (sorted, no timestamps, SHA-256 content hash). **Avoid**: dual lockfile fragmentation (#542, #775), silent lock migration (#542), aggressive rm-rf before install. Full analysis: [reference-analysis.md](reference-analysis.md).

---

## Goals

- Provide a single CLI command to fetch and install any supported AI artifact for one or more AI target systems
- Use explicit `--ai` targeting as the primary selector for installation paths; auto-detection serves as a fallback, not the driver
- Define canonical placement paths for each AI target × artifact type × scope combination so correct placement is deterministic. Use `.agents/skills/` as the shared canonical directory with symlinks to target-specific read paths, following the `vercel-labs/skills` model
- Support `skills` as the first artifact type, with a design that accommodates future types (rules, templates, agents, etc.)
- Support `claude` and `copilot` as initial AI targets, with a design that accommodates future targets
- Allow installation into multiple AI targets in a single invocation (e.g., `--ai claude --ai copilot`)
- Support project-scope and user-scope installation controlled by a `--scope` flag
- Ensure installations are safe: validated, integrity-checked, and from a trusted source (`aidriven-resources`)
- Enable reproducible installs: install record tracks source commit SHA so exact content can be traced back
- Support caching to avoid redundant network requests

## Non-Goals

- Bundling artifacts inside the `aidriven` Python package (artifacts live in `aidriven-resources`)
- Managing or deploying artifacts to remote or shared team environments
- Creating or authoring new artifacts (fetch and install only)
- Bulk-installing entire artifact catalogs without explicit user intent
- Supporting artifact types beyond `skills` in this iteration (though the design must accommodate them)
- Supporting AI targets beyond `claude` and `copilot` in this iteration (though the design must accommodate them)
- Modifying AI system configurations or settings files beyond placing artifact files in the correct directory
- Uninstall, rollback, or upgrade workflows (outside scope of this iteration)
- Authentication or private repository access (only public `aidriven-resources` is in scope)
- Managing Copilot customization files (`.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md`, `.github/agents/*.md`) — those are distinct from skills

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install a Skill for a Single AI Target (Priority: P1)

A developer runs `aidriven install skill <name> --ai claude`. The tool fetches the skill from `aidriven-resources`, places it at `.agents/skills/<name>/` (canonical), creates a symlink at `.claude/skills/<name>/`, and prints a confirmation message with both paths.

**Why this priority**: This is the core value proposition — installing a skill to the correct path for a specific AI target. Everything else depends on this working.

**Independent Test**: Can be fully tested by running `aidriven install skill <name> --ai claude` in any directory and verifying the files appear at `.agents/skills/<name>/` with a symlink at `.claude/skills/<name>/`.

**Acceptance Scenarios**:

1. **Given** a user requests `aidriven install skill code-reviewer --ai claude`, **When** the command runs, **Then** the skill files are placed at `<project-root>/.agents/skills/code-reviewer/` (canonical) and a directory symlink is created at `<project-root>/.claude/skills/code-reviewer/` pointing to the canonical directory, and the CLI outputs both paths.
2. **Given** a user requests `aidriven install skill code-reviewer --ai copilot`, **When** the command runs, **Then** the skill files are placed at `<project-root>/.agents/skills/code-reviewer/` (Copilot reads this directly; no symlink needed).
3. **Given** the requested skill exists in `aidriven-resources`, **When** the command completes, **Then** a lockfile entry (name, source commit SHA, computed hash, AI targets, scope, install mode) is written to `<project-root>/aidriven-lock.json`.
4. **Given** the same skill has already been installed with identical content for the same AI target and scope, **When** the command runs again, **Then** the CLI compares content hashes, skips the write, notifies the user that the skill is already installed, and exits successfully.

---

### User Story 2 - Install a Skill for Multiple AI Targets (Priority: P2)

A developer uses both Claude and Copilot in their project. They run `aidriven install skill <name> --ai claude --ai copilot` to install the same skill for both AI systems in one command.

**Why this priority**: Multi-AI environments are the primary motivation for `aidriven` — supporting single-command multi-target install is essential.

**Independent Test**: Can be fully tested by running the command with two `--ai` flags and verifying files appear at both AI target paths.

**Acceptance Scenarios**:

1. **Given** a user runs `aidriven install skill code-reviewer --ai claude --ai copilot`, **When** the command runs, **Then** the skill is placed at `.agents/skills/code-reviewer/` (canonical), a symlink is created at `.claude/skills/code-reviewer/` for Claude, and the CLI reports both targets as installed. Only one copy of files exists on disk (at canonical); Copilot reads canonical directly, Claude reads via symlink.
2. **Given** the skill is compatible with `claude` but the manifest marks it as incompatible with `copilot`, **When** the command runs, **Then** the CLI warns about the incompatibility for `copilot`, installs for `claude`, and asks the user to confirm or skip the `copilot` install.
3. **Given** installation succeeds for `claude` but fails for `copilot` (e.g., permission error), **When** the command completes, **Then** the CLI reports per-target success/failure and exits with a non-zero code.

---

### User Story 3 - Install a Skill at User Scope (Priority: P3)

A developer wants a skill available across all their projects, not just the current one. They run `aidriven install skill <name> --ai claude --scope user`.

**Why this priority**: User-scope installation is required for developers who want shared skills without duplicating files per project.

**Independent Test**: Can be fully tested by running the command with `--scope user` and verifying the file appears at the user-level path (`~/.claude/skills/<name>/SKILL.md`).

**Acceptance Scenarios**:

1. **Given** a user runs `aidriven install skill code-reviewer --ai claude --scope user`, **When** the command runs, **Then** the skill is placed at `~/.agents/skills/code-reviewer/` (canonical) with a symlink at `~/.claude/skills/code-reviewer/`.
2. **Given** a user runs `aidriven install skill code-reviewer --ai copilot --scope user`, **When** the command runs, **Then** the skill is placed at `~/.agents/skills/code-reviewer/` (canonical) with a symlink at `~/.copilot/skills/code-reviewer/`.
3. **Given** no `--scope` flag is provided, **When** the command runs, **Then** `project` scope is used as the default.

---

### User Story 4 - Re-fetch Latest Skill Content (Priority: P4)

A developer wants to update a previously installed skill to the latest content from `aidriven-resources`. They run `aidriven install skill <name> --ai claude --force`.

**Why this priority**: Since skills are unversioned and fetched at latest, `--force` is the mechanism to pull fresh content bypassing the cache.

**Independent Test**: Can be fully tested by installing a skill, modifying it remotely, then running with `--force` and verifying the content is updated.

**Acceptance Scenarios**:

1. **Given** a skill was previously installed and the remote content has changed, **When** the user runs with `--force`, **Then** the skill is re-fetched and the installed content is updated, and the CLI prints "updated <name>".
2. **Given** a skill was previously installed and the remote content is identical, **When** the user runs with `--force`, **Then** the skill is re-fetched but the CLI reports "already up to date" after comparing content hashes.
3. **Given** the download succeeds, **When** the file is installed, **Then** the CLI validates the downloaded content against the checksum in the manifest and aborts if it does not match.

---

### User Story 5 - Auto-Detect AI Targets When --ai Is Omitted (Priority: P5)

A developer runs `aidriven install skill <name>` without specifying `--ai`. The tool auto-detects which AI systems are present by inspecting the environment (e.g., existing `.claude/` or `.github/copilot-instructions.md` directories, IDE detection, config markers).

**Why this priority**: Convenience fallback that reduces friction for common cases, but is not the primary workflow.

**Independent Test**: Can be fully tested by setting up a project with Claude and/or Copilot markers and running without `--ai`, verifying the correct targets are selected.

**Acceptance Scenarios**:

1. **Given** auto-detection finds exactly one AI system and no `--ai` flag is provided, **When** the command runs, **Then** that AI system is used and the CLI informs the user which target was auto-detected.
2. **Given** auto-detection finds multiple AI systems and no `--ai` flag is provided, **When** the command runs, **Then** the CLI exits with a non-zero code, lists detected targets, and instructs the user to specify `--ai` explicitly.
3. **Given** auto-detection finds no AI systems and no `--ai` flag is provided, **When** the command runs, **Then** the CLI exits with a non-zero code, lists supported targets, and instructs the user to specify `--ai`.

---

### Edge Cases

- What happens when the `aidriven-resources` remote is unreachable (no network)?
- What happens when the remote manifest exists but the requested artifact name is absent?
- What happens when the local install target directory does not exist or is not writable?
- What happens when a file already exists at the install path from a different source (not an `aidriven` install)?
- What happens when the manifest references an artifact but the download URL is missing or the content is corrupted?
- What happens when two runs of the same command execute simultaneously?
- What happens when the user specifies `--ai` with a target not supported by the requested artifact?
- What happens when `--ai copilot` is used and a `.claude/skills/` directory already exists with the same skill (cross-target conflict)?
- What happens when `--scope user` is used on a system where the user home directory is not writable?
- What happens when the same skill is installed at both project and user scope for the same AI target?
- What happens when the OS does not support symlinks or directory junctions (e.g., Windows without developer mode with junctions disabled)?
- What happens when a symlink already exists at the target path but points to a different canonical location?
- What happens when the canonical directory is deleted but symlinks still reference it?
- What happens when `--copy` is used for one install and then the same skill is later installed without `--copy` (mode switch)?
- What happens when the user modifies files in the canonical directory and then runs install for a new AI target (symlinks would expose modified content)?

---

## Requirements *(mandatory)*

### Functional Requirements

**CLI Interface**

- **FR-001**: The system MUST expose an `install` command with the signature: `aidriven install <artifact-type> <artifact-name> [--ai <target>]... [--scope project|user] [--force] [--copy]`
- **FR-002**: The `<artifact-type>` argument MUST be validated against a list of supported types; for this iteration `skill` is the only supported type.
- **FR-003**: The `<artifact-name>` argument MUST first be validated locally against the regex `^[a-z][a-z0-9-]{0,63}$` (lowercase letters, digits, and hyphens; must start with a letter; max 64 characters). Names failing this check MUST be rejected before any network call. After local validation passes, the name MUST also be validated against the remote manifest before download.
- **FR-004**: The `--ai` flag MUST accept a supported AI target identifier (initial: `claude`, `copilot`). It MAY be specified multiple times to install for multiple targets in one invocation.
- **FR-005**: The `--scope` flag MUST accept `project` (default) or `user`. It controls whether the artifact is placed in the project root directory or the user home directory.
- **FR-005a**: For `--scope project`, the system MUST resolve the project root by walking up from `cwd` to find a `.git` directory. If no `.git` is found, `cwd` is used as the fallback. The resolved project root is the base for all project-scope placement paths.
- **FR-006**: *(Removed — skills are unversioned; always fetched at latest.)*
- **FR-007**: The `--force` flag MUST cause the CLI to re-fetch and overwrite an already-installed artifact, bypassing the cache and overwrite protections (including foreign-file protection).
- **FR-007a**: The `--copy` flag MUST cause the CLI to place files directly at each AI target's read path instead of using the canonical directory + symlink model. When `--copy` is used, no canonical directory is created and no symlinks are created.

**Artifact Placement Rules**

- **FR-008**: The system MUST use the following installation model for `skill` artifacts.

  **Symlink mode (default):** Files are stored once at a **canonical directory** and symlinked to each AI target's read path. The canonical directory is the single source of truth.

  | AI Target  | Scope     | Canonical Dir                  | Target Read Path               | Linking             |
  |------------|-----------|--------------------------------|--------------------------------|---------------------|
  | `claude`   | `project` | `.agents/skills/<name>/`       | `.claude/skills/<name>/`       | symlink → canonical |
  | `claude`   | `user`    | `~/.agents/skills/<name>/`     | `~/.claude/skills/<name>/`     | symlink → canonical |
  | `copilot`  | `project` | `.agents/skills/<name>/`       | *(reads canonical directly)*   | none                |
  | `copilot`  | `user`    | `~/.agents/skills/<name>/`     | `~/.copilot/skills/<name>/`    | symlink → canonical |

  **Copy mode (`--copy`):** Independent copies are placed directly at each AI target's read path. No canonical directory, no symlinks.

  | AI Target  | Scope     | Install Dir                    |
  |------------|-----------|--------------------------------|
  | `claude`   | `project` | `.claude/skills/<name>/`       |
  | `claude`   | `user`    | `~/.claude/skills/<name>/`     |
  | `copilot`  | `project` | `.agents/skills/<name>/`       |
  | `copilot`  | `user`    | `~/.copilot/skills/<name>/`    |

- **FR-008a**: The **canonical directory** is `.agents/skills/<name>/` for project scope and `~/.agents/skills/<name>/` for user scope. In symlink mode, all skill files are placed at this location first. Targets that read from a different path receive a directory symlink pointing to the canonical directory. Targets whose read path IS the canonical directory (e.g., Copilot at project scope) require no linking.
- **FR-008b**: **Symlink mode** is the default installation mode. On Windows, directory junctions MUST be used as the symlink equivalent. If junction/symlink creation fails (e.g., insufficient permissions), the system MUST fall back to copy mode for the affected target and log a warning. **Copy mode** (`--copy`) is opt-in and creates independent file copies at each target path with no canonical directory.
- **FR-009**: The canonical directory `.agents/skills/` is chosen because it is the industry-standard shared location for AI agent skills, defined and supported by the `vercel-labs/skills` ecosystem. Over 40 AI agents — including GitHub Copilot, Cursor, Codex CLI, Kilo Code, and Warp — read skills from `.agents/skills/` at project scope. Using this path ensures maximum compatibility. Claude Code reads from `.claude/skills/`, so it receives a symlink. Copilot also reads from `.claude/skills/` and `.github/skills/` as aliases, but `.agents/skills/` is the primary install location.
- **FR-010**: Each path entry MUST create the `<skill-name>/` subdirectory and place all files belonging to the skill within it. Every skill directory MUST contain a `SKILL.md` file and MAY contain additional files (references, scripts, templates, etc.). Intermediate directories MUST be created if they do not exist.
- **FR-010a**: The skill content is universal — the same set of files is placed for every AI target. The manifest stores one skill artifact per name, not per-target variants. Skills are unversioned; the manifest always points to the latest content.
- **FR-011**: The path table MUST be extensible: adding a new AI target or artifact type requires only adding rows to this mapping, not changing the core install logic.

**AI Target Resolution**

- **FR-012**: If one or more `--ai` flags are provided, the system MUST use exactly those AI targets. No auto-detection is performed.
- **FR-013**: If no `--ai` flag is provided, the system MUST attempt auto-detection of AI targets present in the current environment.
- **FR-014**: Auto-detection MAY use the existing IDE detection layer as one signal (e.g., detecting VS Code suggests Copilot availability), and MAY also inspect filesystem markers (e.g., `.claude/` directory, `.github/copilot-instructions.md`).
- **FR-015**: If auto-detection finds exactly one AI target, the system MUST use it and inform the user which target was auto-detected.
- **FR-016**: If auto-detection finds multiple AI targets, the system MUST exit with a non-zero code listing detected targets and instruct the user to specify `--ai` explicitly.
- **FR-017**: If auto-detection finds no AI targets and no `--ai` flag is provided, the system MUST exit with a non-zero code listing supported targets and instruct the user to specify `--ai`.
- **FR-018**: The user MUST be able to pass `--ai` values that are not currently auto-detectable; `--ai` always takes precedence and does not require detection to succeed.

**Remote Manifest & Metadata**

- **FR-019**: The system MUST fetch a remote manifest from `aidriven-resources` that lists available artifact types, names, the source commit SHA to fetch, the path of the skill subdirectory within the repository archive, the SHA-256 checksum of the repository tarball at that commit, and AI target compatibility metadata. Skills are unversioned — the manifest always points to the latest commit SHA on the default branch.
- **FR-020**: The manifest MUST be consulted before any download to validate that the requested artifact type and name exist.
- **FR-021**: The manifest MUST declare which AI targets are compatible with each artifact, so the system can warn when installing for a target the artifact does not officially support.
- **FR-022**: The manifest schema MUST be versioned so future additions do not break existing CLI versions.
- **FR-022a**: The manifest MUST be a single JSON file named `manifest.json` located at the root of the `aidriven-resources` repository, fetched via `https://raw.githubusercontent.com/<owner>/aidriven-resources/<sha>/manifest.json`.
- **FR-022b**: At the start of each install run, the system MUST resolve the current HEAD commit SHA of the `aidriven-resources` default branch via the GitHub API (`GET /repos/<owner>/aidriven-resources/commits/<default-branch>`). The resolved SHA MUST be used for BOTH the `manifest.json` fetch and the tarball fetch within that run, ensuring manifest and bundle originate from the same commit. The resolved SHA MUST be recorded as `sourceCommitSha` in the lockfile.

**Download & Integrity**

- **FR-023**: The system MUST download the `aidriven-resources` repository tarball at the pinned commit SHA via GitHub's archive URL (`https://github.com/<owner>/aidriven-resources/archive/<sha>.tar.gz`), then extract only the skill subdirectory referenced by the manifest. No `git` binary dependency is required; no per-skill publishing pipeline is required.
- **FR-024**: The system MUST verify the downloaded bundle's integrity against a checksum provided in the manifest; if verification fails, the artifact MUST NOT be installed and an error MUST be reported.
- **FR-025**: Downloads MUST be performed over HTTPS only.
- **FR-025a**: For all HTTP requests (GitHub API SHA resolution, manifest fetch, tarball fetch), the system MUST retry transient failures up to 3 times with exponential backoff (1s, 2s, 4s). Transient failures are: network/connection errors, HTTP 5xx responses, and HTTP 429 (rate limited). All other 4xx responses MUST fail fast without retry. After exhausting retries, the system MUST report a clear error and exit non-zero.

**Caching**

- **FR-026**: The system MUST cache downloaded artifacts locally (keyed by artifact type + name + content hash) to avoid redundant network requests. The cache is AI-target-agnostic — the same downloaded file is reused for all targets.
- **FR-027**: The cache MUST be invalidated when `--force` is passed.
- **FR-028**: The system MUST also cache the remote manifest for a configurable TTL (default: 1 hour) to reduce latency on repeated commands.

**Installation & Idempotency**

- **FR-029**: In symlink mode, the system MUST first place the artifact files at the canonical directory for each selected AI target, creating intermediate directories if they do not exist. Then, for each AI target whose read path differs from the canonical directory, the system MUST create a directory symlink from the read path to the canonical directory. In copy mode, the system MUST place independent copies at each AI target's read path. The canonical directory MUST be verified as populated before any symlinks are created.
- **FR-030**: If the skill directory already exists at the canonical path (symlink mode) or target path (copy mode) with identical content (all files match by SHA-256 hash computed from file contents sorted by relative path), the system MUST skip the write, report "already installed", and exit successfully.
- **FR-031**: If the skill directory already exists at the canonical path (symlink mode) or target path (copy mode) with different content:
  - If the install record shows the existing content was previously installed by `aidriven`, the system MUST treat it as an **update**: overwrite the directory, print "updated <name>", and proceed without requiring `--force`.
  - If the existing content was not installed by `aidriven` (no install record) or was locally modified (content hash does not match the install record's hash), the system MUST warn the user and abort for that target unless `--force` is passed.
  - If installing for multiple targets, a failure on one MUST NOT prevent installation for others.
- **FR-032**: After successful installation, the system MUST write a lockfile entry for the installed skill. For project scope, the lockfile is `<project-root>/aidriven-lock.json`. For user scope, the lockfile is `~/.cache/aidriven/install-records.json`. The lockfile MUST use the following design:
  - Schema version field (`"version": 1`) to support future migrations (migrations MUST preserve data or warn — never silently discard entries).
  - Skills keyed by name, sorted alphabetically for deterministic output.
  - Each entry MUST contain: `source` (repository name), `sourceCommitSha`, `computedHash` (SHA-256 of all file contents sorted by relative path), `targets` (list of AI target identifiers), `scope`, and `installMode` (`"symlink"` or `"copy"`).
  - The project lockfile (`aidriven-lock.json`) MUST NOT contain timestamps or other non-deterministic fields, to minimize VCS merge conflicts. It is designed to be committed to version control.
  - The user lockfile MAY include timestamps for user convenience.
- **FR-033**: The system MUST print a concise per-target success summary to stdout including the installed path, AI target, scope, and install mode (symlink or copy).

**Error Handling**

- **FR-034**: All error cases (network failure, manifest not found, artifact not found, checksum mismatch, permission error, unknown AI target) MUST produce human-readable messages with actionable guidance.
- **FR-035**: All error exits MUST use a non-zero exit code.
- **FR-036**: When installing for multiple AI targets, per-target errors MUST be reported individually. The exit code MUST be non-zero if any target failed.

### Key Entities

- **Artifact**: A named AI resource (e.g., a skill). Unversioned — always fetched at latest from the remote repository. Consists of a directory of files (at minimum a `SKILL.md`, plus optional references, scripts, templates, etc.). Has a type, name, download URL, checksum, and AI target compatibility list. Content is universal across AI targets — the same files are placed for every target.
- **Manifest**: A remote index hosted in `aidriven-resources` that describes all available artifacts. Has a schema version and is fetched over HTTPS.
- **AI Target**: A supported AI coding assistant (e.g., `claude`, `copilot`). Each AI target defines a read path per artifact type and scope. Targets whose read path matches the canonical directory (e.g., Copilot at project scope) require no symlink; others receive a symlink.
- **Scope**: Either `project` (relative to the detected project root — nearest ancestor with `.git`, falling back to `cwd`) or `user` (relative to user home). Controls where the artifact is placed within the AI target's path structure.
- **Canonical Directory**: The shared installation location where skill files are physically stored in symlink mode. Project scope: `.agents/skills/<name>/`. User scope: `~/.agents/skills/<name>/`. This is the industry-standard location supported by 40+ AI agents (including GitHub Copilot, Cursor, Codex, Warp). In copy mode, no canonical directory is used.
- **Lockfile**: A JSON file recording what was installed. Project scope: `<project-root>/aidriven-lock.json` (VCS-friendly — sorted keys, no timestamps). User scope: `~/.cache/aidriven/install-records.json`. Each entry tracks: source, source commit SHA, computed hash (SHA-256 of file contents), AI targets, scope, install mode.
- **Cache Entry**: A locally stored artifact bundle keyed by type + name + content hash, reused across targets to avoid redundant network requests.
- **Install Mode**: Either `symlink` (default — files at canonical directory, symlinks from target read paths) or `copy` (`--copy` flag — independent copies at each target read path).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can install a skill for a specific AI target with a single command in under 10 seconds on a standard internet connection.
- **SC-002**: Re-running the same install command produces no file changes when content hashes match, and completes using the cached artifact.
- **SC-003**: Installing a skill with the same source commit SHA produces byte-identical results across different machines and operating systems.
- **SC-004**: Every error path produces a non-zero exit code and a human-readable message — zero silent failures.
- **SC-005**: The feature installs to the correct canonical path and creates proper symlinks for each AI target (`claude`, `copilot`) × scope (`project`, `user`) combination, verified by path assertion tests and symlink target verification.
- **SC-006**: A single command can install the same skill for multiple AI targets, with per-target success/failure reporting.
- **SC-007**: A new AI target or artifact type can be supported by extending the placement-path table and manifest metadata without changes to the core install logic.
- **SC-008**: In symlink mode, installing for multiple AI targets creates exactly one copy of skill files (at the canonical directory) plus symlinks — verified by checking that target read paths are symlinks pointing to the canonical directory.
- **SC-009**: The project lockfile `aidriven-lock.json` produces deterministic output (sorted keys, no timestamps) suitable for version control.

---

## Assumptions

- Users have Python 3.11+ and `aidriven` installed and accessible on their PATH.
- Users have outbound HTTPS access to `github.com` (raw content and/or GitHub Releases).
- The `aidriven-resources` repository is public; no authentication is required to fetch manifests or artifacts.
- The primary installation selector is the AI target system (e.g., `claude`, `copilot`), not the IDE. IDE/environment detection is a supporting signal for auto-detection, not the driver.
- Skills are directories placed under a named subdirectory. Each skill directory MUST contain a `SKILL.md` file and MAY contain additional files (references, scripts, templates, etc.). No AI-system-level registration or plugin activation is required beyond file placement.
- Skill content is universal across AI targets — one artifact is fetched and placed identically for all targets. Per-target content variants are out of scope for this iteration.
- The canonical project-scope installation directory is `.agents/skills/<name>/`, which is the industry-standard shared location for AI agent skills (used by `vercel-labs/skills`, read by 40+ agents including GitHub Copilot and Cursor). Copilot reads from `.agents/skills/` directly; Claude Code reads from `.claude/skills/` and receives a symlink.
- Copilot customization files (`.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md`, `.github/agents/*.md`) are unrelated to skill artifacts and are not managed by this feature.
- Default scope is `project`. Project scope resolves the base directory by walking up from `cwd` to find `.git`; if no `.git` is found, `cwd` is used as fallback. User scope installs to the home directory.
- The `aidriven-resources` manifest will be designed and published as part of this feature's delivery; its schema is to be defined during planning.
- Concurrent execution of two `aidriven install` commands targeting the same artifact is an unlikely edge case; file-level write failures are sufficient protection for v1.
- Cache storage uses the OS standard user cache directory; no user configuration is required for cache location in this iteration.
- Skills are unversioned — always fetched at latest from `aidriven-resources`. The install record tracks the source commit SHA for traceability. This aligns with ecosystem conventions (e.g., skills.sh) where skills are living documents, not semver-versioned packages.
- Auto-detection of AI targets may use IDE detection (from the existing discovery layer) as one heuristic, but also inspects filesystem markers (e.g., presence of `.claude/`, `.github/copilot-instructions.md`).
- On Windows, directory junctions are used as the symlink equivalent. If junction creation fails, the system falls back to copy mode for the affected target.
- The project lockfile (`aidriven-lock.json`) is designed to be committed to version control. It uses sorted keys and no timestamps to minimize merge conflicts, following the design of `skills-lock.json` from `vercel-labs/skills`.
